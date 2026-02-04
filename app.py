import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from supabase import create_client, Client
import json
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Brasileirão 2026", layout="centered", page_icon="⚽")

# --- CSS PERSONALIZADO (A MÁGICA DO VISUAL) ---
st.markdown("""
<style>
    /* Centralizar o texto dentro do input */
    .stTextInput input {
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        padding: 5px;
    }
    
    /* Forçar o input a ficar pequeno (bloquinho) e centralizado na coluna */
    div[data-testid="stTextInput"] {
        width: 60px !important;
        margin: 0 auto !important;
    }
    
    /* Centralizar textos das colunas (Nomes dos times) */
    div[data-testid="column"] {
        text-align: center !important;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    /* Estilo do botão de tabela (parece um pop-up/pílula) */
    .btn-tabela {
        width: 100%;
        border-radius: 25px;
        font-weight: bold;
        background-color: #2e2e2e;
        border: 1px solid #444;
    }
    
    /* Esconder decoração padrão do Streamlit */
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

# --- FUNÇÕES ---
@st.cache_data(ttl=3600)
def obter_jogos_cbf(rodada):
    jogos_fixos = {
        1: ["Atlético-MG x Palmeiras", "Internacional x Athletico-PR", "Coritiba x RB Bragantino", "Vitória x Remo", "Fluminense x Grêmio", "Chapecoense x Santos", "Corinthians x Bahia", "São Paulo x Flamengo", "Mirassol x Vasco", "Botafogo x Cruzeiro"],
        2: ["Flamengo x Internacional", "RB Bragantino x Atlético-MG", "Santos x São Paulo", "Remo x Mirassol", "Palmeiras x Vitória", "Grêmio x Botafogo", "Bahia x Fluminense", "Vasco da Gama x Chapecoense", "Cruzeiro x Coritiba", "Athletico-PR x Corinthians"]
    }
    return jogos_fixos.get(rodada, [f"Time A {i} x Time B {i}" for i in range(1, 11)])

def processar_foto(imagem, lista_jogos):
    model = genai.GenerativeModel('gemini-flash-latest')
    img = Image.open(imagem)
    prompt = f"""
    Analise a imagem de palpites. Lista oficial: {lista_jogos}.
    Retorne JSON: {{'Nome do Jogo Exato': '2x0'}}. 
    Separe mandante x visitante com 'x' minusculo.
    """
    try:
        response = model.generate_content([prompt, img])
        txt = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(txt)
    except:
        return {}

def db_salvar(user, rod, jogo, placar):
    supabase.table("palpites").upsert({
        "usuario": user, "rodada": rod, "jogo": jogo, "placar": placar
    }, on_conflict="usuario,rodada,jogo").execute()

def db_carregar(user, rod):
    res = supabase.table("palpites").select("jogo, placar").eq("usuario", user).eq("rodada", rod).execute()
    return {item['jogo']: item['placar'] for item in res.data}

# --- GERENCIAMENTO DE ESTADO (NAVEGAÇÃO) ---
if "page" not in st.session_state:
    st.session_state.page = "palpites"

# --- TELA DE LOGIN ---
if "usuario" not in st.session_state:
    st.title("⚽ Bolão 2026")
    c1, c2 = st.columns(2)
    if c1.button("🙋‍♂️ Fabinho", use_container_width=True):
        st.session_state["usuario"] = "Fabinho"
        st.rerun()
    if c2.button("🤴 Maicolas", use_container_width=True):
        st.session_state["usuario"] = "Maicon"
        st.rerun()
    st.stop()

usuario = st.session_state["usuario"]
rodada_atual = 2

# =========================================================
# TELA 1: TABELAS E CLASSIFICAÇÃO (TELA À PARTE)
# =========================================================
if st.session_state.page == "tabelas":
    st.button("⬅️ Voltar para Palpites", on_click=lambda: st.session_state.update(page="palpites"))
    st.title("📊 Tabelas e Classificação")
    
    # Simulação de dados
    df_fake = pd.DataFrame({
        "Pos": [1, 2, 3, 4, 5],
        "Time": ["Flamengo", "Palmeiras", "São Paulo", "Corinthians", "Vasco"],
        "P": [45, 42, 40, 38, 35],
        "J": [20, 20, 20, 20, 20]
    }).set_index("Pos")

    t1, t2, t3 = st.tabs(["Oficial", "Fabinho", "Maicolas"])
    with t1: st.dataframe(df_fake, use_container_width=True)
    with t2: st.warning("Tabela simulada Fabinho"); st.dataframe(df_fake, use_container_width=True)
    with t3: st.warning("Tabela simulada Maicon"); st.dataframe(df_fake, use_container_width=True)
    
    st.stop() # Para o script aqui para não carregar o resto

# =========================================================
# TELA 2: PALPITES (PRINCIPAL)
# =========================================================

st.subheader(f"Olá, {usuario}! 🏆")

# Verifica se tem alguma rodada em modo de edição
modo_edicao_ativo = any(st.session_state.get(f"edit_mode_{r}", False) for r in range(1, 39))

# Só mostra o botão de tabelas se NÃO estiver editando
if not modo_edicao_ativo:
    if st.button("📊 Confira as Tabelas e Classificação", use_container_width=True):
        st.session_state.page = "tabelas"
        st.rerun()
    st.divider()

# Loop das Rodadas
for r in range(1, 39):
    if r > rodada_atual + 2: continue
    
    titulo = f"📍 Rodada {r}"
    if r == rodada_atual: titulo = f"⚽ Rodada {r} (ATUAL)"
    
    # Se estiver editando ESSA rodada, mantém expandido
    is_editing = st.session_state.get(f"edit_mode_{r}", False)
    expanded = (r == rodada_atual) or is_editing
    
    with st.expander(titulo, expanded=expanded):
        
        # Upload de Foto (Só aparece se estiver editando)
        if is_editing:
            foto = st.file_uploader("📸 Importar Foto", type=['jpg','png'], key=f"up_{r}", label_visibility="collapsed")
            if foto and st.button("🤖 Ler Foto", key=f"ia_{r}"):
                with st.spinner("Lendo..."):
                    lidos = processar_foto(foto, obter_jogos_cbf(r))
                    for j, p in lidos.items():
                        try:
                            m, v = p.lower().split('x')
                            st.session_state[f"gm_{r}_{j}"] = m.strip()
                            st.session_state[f"gv_{r}_{j}"] = v.strip()
                        except: pass
                    st.rerun()

        # Lista de Jogos
        jogos = obter_jogos_cbf(r)
        salvos = db_carregar(usuario, r)
        palpites_save = {}
        
        for jogo in jogos:
            # Separar nomes dos times
            try:
                time_casa, time_fora = jogo.split(' x ')
            except:
                time_casa, time_fora = "Time A", "Time B"

            # Recuperar valores
            val_db = salvos.get(jogo, "x")
            g_m_db, g_v_db = val_db.split('x') if 'x' in val_db else ("", "")
            
            k_m, k_v = f"gm_{r}_{jogo}", f"gv_{r}_{jogo}"
            if k_m not in st.session_state: st.session_state[k_m] = g_m_db
            if k_v not in st.session_state: st.session_state[k_v] = g_v_db
            
            # --- NOVO LAYOUT DOS INPUTS ---
            # Colunas: [Time Casa] [X] [Time Fora]
            # Pesos ajustados para centralizar visualmente
            c1, c2, c3 = st.columns([1.5, 0.2, 1.5])
            
            with c1:
                # Nome em cima, input em baixo centralizado
                st.markdown(f"<div style='text-align:center; font-size:14px; margin-bottom:2px;'>{time_casa}</div>", unsafe_allow_html=True)
                val_m = st.text_input("m", key=k_m, label_visibility="collapsed", disabled=not is_editing)
            
            with c2:
                # O X centralizado verticalmente (gambiarra visual com padding)
                st.markdown("<div style='text-align:center; padding-top:25px; font-weight:bold; color:#666;'>X</div>", unsafe_allow_html=True)
                
            with c3:
                st.markdown(f"<div style='text-align:center; font-size:14px; margin-bottom:2px;'>{time_fora}</div>", unsafe_allow_html=True)
                val_v = st.text_input("v", key=k_v, label_visibility="collapsed", disabled=not is_editing)

            if val_m and val_v:
                palpites_save[jogo] = f"{val_m}x{val_v}"
            
            st.write("") # Espaçamento entre jogos

        # Botões Editar/Salvar
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
