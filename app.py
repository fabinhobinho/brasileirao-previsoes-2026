import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from supabase import create_client, Client
import json
import time
import itertools

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Brasileirão 2026", layout="centered", page_icon="⚽")

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    .stTextInput input { text-align: center; font-size: 20px; font-weight: bold; padding: 5px; }
    div[data-testid="stTextInput"] { width: 60px !important; margin: 0 auto !important; }
    div[data-testid="column"] { text-align: center !important; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- CONEXÕES ---
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 1. GERADOR DE JOGOS (MOCKUP 38 RODADAS) ---
# Como não temos a tabela de 2026 ainda, geramos uma fixa com times reais
@st.cache_data
def gerar_campeonato():
    times = [
        "Flamengo", "Palmeiras", "São Paulo", "Corinthians", "Vasco",
        "Internacional", "Grêmio", "Atlético-MG", "Cruzeiro", "Botafogo",
        "Santos", "Bahia", "Fortaleza", "Athletico-PR", "RB Bragantino",
        "Fluminense", "Vitória", "Criciúma", "Juventude", "Atlético-GO"
    ]
    # Algoritmo simples de Round-Robin para gerar confrontos
    jogos_por_rodada = {}
    n = len(times)
    mapa_times = times[:]
    
    for rodada in range(1, 39):
        jogos = []
        # Apenas lógica de rotação para criar confrontos diferentes
        for i in range(n // 2):
            t1 = mapa_times[i]
            t2 = mapa_times[n - 1 - i]
            # Alternar mando de campo nas rodadas pares
            if rodada % 2 == 1:
                jogos.append(f"{t1} x {t2}")
            else:
                jogos.append(f"{t2} x {t1}")
        
        jogos_por_rodada[rodada] = jogos
        # Rotaciona a lista (mantendo o primeiro fixo)
        mapa_times = [mapa_times[0]] + [mapa_times[-1]] + mapa_times[1:-1]
        
    return times, jogos_por_rodada

LISTA_TIMES, TABELA_JOGOS = gerar_campeonato()

def obter_jogos_rodada(rodada):
    return TABELA_JOGOS.get(rodada, [])

# --- 2. CALCULADORA DE TABELA ---
def calcular_classificacao(palpites_dict, rodada_limite):
    """
    palpites_dict: Dicionário {'Rodada_Jogo': 'Placar'} ex: {'1_Flamengo x Vasco': '2x1'}
    rodada_limite: Calcula pontos até esta rodada
    """
    # Inicializa tabela zerada
    dados = {t: {'P': 0, 'J': 0, 'V': 0, 'E': 0, 'D': 0, 'GP': 0, 'GC': 0, 'SG': 0} for t in LISTA_TIMES}
    
    for chave, placar in palpites_dict.items():
        try:
            # Chave vem do banco como possivelmente composta ou precisa ser filtrada
            # Vamos assumir que passamos um dict filtrado ou processamos aqui
            # Formato esperado da chave vinda do BD: "Jogo" (mas precisamos saber a rodada para filtrar)
            # O ideal é passar uma lista de objetos contendo {rodada, jogo, placar}
            pass
        except:
            continue

    # Para facilitar, vamos processar uma lista de tuplas (rodada, jogo, placar)
    # Reimplementando logica abaixo na chamada da função
    return pd.DataFrame()

def processar_tabela_pandas(lista_palpites_bd, rodada_max):
    # Inicializa estatísticas
    stats = {t: {'P': 0, 'J': 0, 'V': 0, 'E': 0, 'D': 0, 'GP': 0, 'GC': 0, 'SG': 0} for t in LISTA_TIMES}
    
    for item in lista_palpites_bd:
        r = item['rodada']
        if r > rodada_max: continue # Ignora jogos futuros
        
        jogo = item['jogo']
        placar = item['placar']
        
        try:
            time_mandante, time_visitante = jogo.split(' x ')
            gols_m, gols_v = map(int, placar.lower().split('x'))
        except:
            continue # Pula palpites inválidos
            
        # Atualiza Jogos e Gols
        stats[time_mandante]['J'] += 1; stats[time_visitante]['J'] += 1
        stats[time_mandante]['GP'] += gols_m; stats[time_visitante]['GP'] += gols_v
        stats[time_mandante]['GC'] += gols_v; stats[time_visitante]['GC'] += gols_m
        stats[time_mandante]['SG'] = stats[time_mandante]['GP'] - stats[time_mandante]['GC']
        stats[time_visitante]['SG'] = stats[time_visitante]['GP'] - stats[time_visitante]['GC']
        
        # Pontuação
        if gols_m > gols_v: # Mandante venceu
            stats[time_mandante]['P'] += 3
            stats[time_mandante]['V'] += 1
            stats[time_visitante]['D'] += 1
        elif gols_v > gols_m: # Visitante venceu
            stats[time_visitante]['P'] += 3
            stats[time_visitante]['V'] += 1
            stats[time_mandante]['D'] += 1
        else: # Empate
            stats[time_mandante]['P'] += 1; stats[time_visitante]['P'] += 1
            stats[time_mandante]['E'] += 1; stats[time_visitante]['E'] += 1

    # Cria DataFrame
    df = pd.DataFrame.from_dict(stats, orient='index')
    df.index.name = 'Time'
    df = df.reset_index()
    
    # ORDENAÇÃO: Pontos (desc), Saldo (desc), Nome (asc)
    df = df.sort_values(by=['P', 'SG', 'Time'], ascending=[False, False, True])
    df = df.reset_index(drop=True)
    df.index += 1 # Começar do 1
    
    # Selecionar colunas para exibição
    return df[['Time', 'P', 'J', 'V', 'E', 'D', 'GP', 'GC', 'SG']]

# --- FUNÇÕES BANCO E IA ---
def processar_foto(imagem, lista_jogos):
    model = genai.GenerativeModel('gemini-flash-latest')
    img = Image.open(imagem)
    prompt = f"Extraia placares. Lista oficial: {lista_jogos}. JSON: {{'Jogo': '2x0'}}. Separe com 'x' minusculo."
    try:
        response = model.generate_content([prompt, img])
        return json.loads(response.text.strip().replace("```json", "").replace("```", "").strip())
    except: return {}

def db_salvar(user, rod, jogo, placar):
    supabase.table("palpites").upsert({"usuario": user, "rodada": rod, "jogo": jogo, "placar": placar}, on_conflict="usuario,rodada,jogo").execute()

def db_carregar_rodada(user, rod):
    res = supabase.table("palpites").select("jogo, placar").eq("usuario", user).eq("rodada", rod).execute()
    return {item['jogo']: item['placar'] for item in res.data}

def db_carregar_todos(user):
    # Carrega TUDO do usuário para montar a tabela
    res = supabase.table("palpites").select("rodada, jogo, placar").eq("usuario", user).execute()
    return res.data

# --- LÓGICA DE NAVEGAÇÃO ---
if "page" not in st.session_state: st.session_state.page = "palpites"
if "usuario" not in st.session_state:
    st.title("⚽ Bolão 2026")
    c1, c2 = st.columns(2)
    if c1.button("🙋‍♂️ Fabinho", use_container_width=True):
        st.session_state["usuario"] = "Fabinho"; st.rerun()
    if c2.button("🤴 Maicolas", use_container_width=True):
        st.session_state["usuario"] = "Maicon"; st.rerun()
    st.stop()

usuario = st.session_state["usuario"]
rodada_atual = 2 # Pode vir do banco no futuro

# =========================================================
# TELA 1: TABELAS (AGORA FUNCIONAIS)
# =========================================================
if st.session_state.page == "tabelas":
    st.button("⬅️ Voltar para Palpites", on_click=lambda: st.session_state.update(page="palpites"))
    st.title("📊 Classificação Projetada")
    
    # Filtro de Rodada
    rodada_view = st.selectbox("Simular classificação considerando jogos até a rodada:", range(1, 39), index=rodada_atual-1)
    
    # Carregar dados REAIS do banco
    palpites_fabinho = db_carregar_todos("Fabinho")
    palpites_maicon = db_carregar_todos("Maicon")
    
    # Calcular Tabelas
    df_fabinho = processar_tabela_pandas(palpites_fabinho, rodada_view)
    df_maicon = processar_tabela_pandas(palpites_maicon, rodada_view)
    
    # Tabela Oficial (Como não temos jogos reais de 2026, criaremos uma vazia ou mockada)
    # Se quiser testar, pode criar um usuário "Oficial" no banco e lançar resultados lá
    palpites_oficial = db_carregar_todos("Oficial") 
    df_oficial = processar_tabela_pandas(palpites_oficial, rodada_view)
    
    t1, t2, t3 = st.tabs(["Brasileirão (Real/Oficial)", "Simulação Fabinho", "Simulação Maicolas"])
    
    with t1:
        if df_oficial.empty or df_oficial['P'].sum() == 0:
            st.info("Ainda não há resultados oficiais lançados para 2026.")
        else:
            st.dataframe(df_oficial, use_container_width=True, hide_index=False)
            
    with t2:
        st.markdown(f"**Como ficaria a tabela se os palpites do Fabinho estivessem certos:**")
        st.dataframe(df_fabinho, use_container_width=True, height=800)
        
    with t3:
        st.markdown(f"**Como ficaria a tabela se os palpites do Maicolas estivessem certos:**")
        st.dataframe(df_maicon, use_container_width=True, height=800)
        
    st.stop()

# =========================================================
# TELA 2: PALPITES
# =========================================================
st.subheader(f"Olá, {usuario}! 🏆")

modo_edicao_ativo = any(st.session_state.get(f"edit_mode_{r}", False) for r in range(1, 39))
if not modo_edicao_ativo:
    if st.button("📊 Ver Classificação e Tabelas", use_container_width=True):
        st.session_state.page = "tabelas"
        st.rerun()
    st.divider()

for r in range(1, 39):
    if r > rodada_atual + 2: continue
    
    titulo = f"📍 Rodada {r}"
    if r == rodada_atual: titulo = f"⚽ Rodada {r} (ATUAL)"
    
    is_editing = st.session_state.get(f"edit_mode_{r}", False)
    expanded = (r == rodada_atual) or is_editing
    
    with st.expander(titulo, expanded=expanded):
        if is_editing:
            foto = st.file_uploader("📸 Importar Foto", type=['jpg','png'], key=f"up_{r}", label_visibility="collapsed")
            if foto and st.button("🤖 Ler Foto", key=f"ia_{r}"):
                with st.spinner("Lendo..."):
                    lidos = processar_foto(foto, obter_jogos_rodada(r))
                    for j, p in lidos.items():
                        try:
                            m, v = p.lower().split('x')
                            st.session_state[f"gm_{r}_{j}"] = m.strip()
                            st.session_state[f"gv_{r}_{j}"] = v.strip()
                        except: pass
                    st.rerun()

        jogos = obter_jogos_rodada(r)
        salvos = db_carregar_rodada(usuario, r)
        palpites_save = {}
        
        for jogo in jogos:
            try: time_casa, time_fora = jogo.split(' x ')
            except: time_casa, time_fora = "Time A", "Time B"

            val_db = salvos.get(jogo, "x")
            g_m_db, g_v_db = val_db.split('x') if 'x' in val_db else ("", "")
            
            k_m, k_v = f"gm_{r}_{jogo}", f"gv_{r}_{jogo}"
            if k_m not in st.session_state: st.session_state[k_m] = g_m_db
            if k_v not in st.session_state: st.session_state[k_v] = g_v_db
            
            c1, c2, c3 = st.columns([1.5, 0.2, 1.5])
            with c1:
                st.markdown(f"<div style='text-align:center; font-size:14px; margin-bottom:2px;'>{time_casa}</div>", unsafe_allow_html=True)
                val_m = st.text_input("m", key=k_m, label_visibility="collapsed", disabled=not is_editing)
            with c2:
                st.markdown("<div style='text-align:center; padding-top:25px; font-weight:bold; color:#666;'>X</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='text-align:center; font-size:14px; margin-bottom:2px;'>{time_fora}</div>", unsafe_allow_html=True)
                val_v = st.text_input("v", key=k_v, label_visibility="collapsed", disabled=not is_editing)

            if val_m and val_v:
                palpites_save[jogo] = f"{val_m}x{val_v}"
            st.write("") 

        col_btn = st.columns(1)[0]
        if not is_editing:
            if col_btn.button("✏️ Editar Palpites", key=f"ed_{r}", use_container_width=True):
                st.session_state[f"edit_mode_{r}"] = True
                st.rerun()
        else:
            if col_btn.button("💾 Salvar Rodada", key=f"sv_{r}", type="primary", use_container_width=True):
                for j, p in palpites_save.items():
                    db_salvar(usuario, r, j, p)
                st.session_state[f"edit_mode_{r}"] = False
                st.toast("Salvo!", icon="✅")
                time.sleep(1)
                st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Sair"):
    del st.session_state["usuario"]
    st.session_state.page = "palpites"
    st.rerun()
