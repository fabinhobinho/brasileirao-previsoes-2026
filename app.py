import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from supabase import create_client, Client
import json
import time

# --- CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira linha) ---
st.set_page_config(page_title="Brasileirão 2026", layout="centered", page_icon="⚽")

# --- CSS PERSONALIZADO (Para dar um visual de app) ---
st.markdown("""
<style>
    .stButton>button { border-radius: 20px; }
    .big-font { font-size: 20px !important; font-weight: bold; }
    div[data-testid="stExpander"] details summary p { font-size: 1.1rem; font-weight: 600; }
    .placar-input input { text-align: center; font-size: 18px; }
</style>
""", unsafe_allow_html=True)

# --- CONEXÕES ---
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- FUNÇÃO DE BUSCA DE JOGOS (MOCKUP) ---
@st.cache_data(ttl=3600)
def obter_jogos_cbf(rodada):
    # DICA: No futuro, substituir isso por um scraper real do GE ou CBF
    jogos_fixos = {
        1: ["Atlético-MG x Palmeiras", "Internacional x Athletico-PR", "Coritiba x RB Bragantino", "Vitória x Remo", "Fluminense x Grêmio", "Chapecoense x Santos", "Corinthians x Bahia", "São Paulo x Flamengo", "Mirassol x Vasco", "Botafogo x Cruzeiro"],
        2: ["Flamengo x Internacional", "RB Bragantino x Atlético-MG", "Santos x São Paulo", "Remo x Mirassol", "Palmeiras x Vitória", "Grêmio x Botafogo", "Bahia x Fluminense", "Vasco da Gama x Chapecoense", "Cruzeiro x Coritiba", "Athletico-PR x Corinthians"]
    }
    return jogos_fixos.get(rodada, [f"Time A {i} x Time B {i}" for i in range(1, 11)])

# --- IA GEMINI ---
def processar_foto(imagem, lista_jogos):
    model = genai.GenerativeModel('gemini-flash-latest')
    img = Image.open(imagem)
    # Prompt ajustado para garantir formato correto
    prompt = f"""
    Analise a imagem de palpites de futebol.
    Lista oficial de jogos desta rodada: {lista_jogos}.
    
    Tarefa: Identifique os placares na imagem que correspondem aos jogos da lista.
    Retorne APENAS um JSON válido. 
    Formato: {{'Nome do Jogo Exato da Lista': '2x0', 'Outro Jogo': '1x1'}}
    Se não achar o jogo, ignore. Use 'x' minúsculo como separador.
    """
    try:
        response = model.generate_content([prompt, img])
        txt = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(txt)
    except Exception as e:
        st.error(f"Erro na leitura da IA: {e}")
        return {}

# --- BANCO DE DADOS ---
def db_salvar(user, rod, jogo, placar):
    supabase.table("palpites").upsert({
        "usuario": user, "rodada": rod, "jogo": jogo, "placar": placar
    }, on_conflict="usuario,rodada,jogo").execute()

def db_carregar(user, rod):
    res = supabase.table("palpites").select("jogo, placar").eq("usuario", user).eq("rodada", rod).execute()
    return {item['jogo']: item['placar'] for item in res.data}

# --- TELA DE LOGIN (Fake) ---
if "usuario" not in st.session_state:
    st.title("⚽ Bolão Brasileirão 2026")
    st.subheader("Quem está acessando?")
    
    col_u1, col_u2 = st.columns(2)
    
    with col_u1:
        if st.button("🙋‍♂️ Fabinho", use_container_width=True):
            st.session_state["usuario"] = "Fabinho"
            st.rerun()
            
    with col_u2:
        if st.button("🤴 Maicolas", use_container_width=True):
            st.session_state["usuario"] = "Maicon"
            st.rerun()
    
    st.stop() # Para a execução aqui até escolher

# --- VARIÁVEIS DO APP ---
usuario = st.session_state["usuario"]
rodada_atual = 2 # Isso aqui depois podemos puxar do banco ou data

# --- HEADER E TABELAS ---
st.title(f"Olá, {usuario}! 🏆")

# Menu de Tabelas (A tal Pílula)
with st.expander("📊 Confira as Tabelas e Classificação", expanded=False):
    col_filter, _ = st.columns([2, 1])
    rodada_view = col_filter.selectbox("Visualizar classificação até a rodada:", range(1, 39), index=rodada_atual-1)
    
    tab1, tab2, tab3 = st.tabs(["Brasileirão Oficial", "Tabela Fabinho", "Tabela Maicolas"])
    
    # MOCKUP DE DADOS PARA VISUALIZAÇÃO (Substituir por lógica real depois)
    df_fake = pd.DataFrame({
        "Pos": [1, 2, 3, 4, 5],
        "Time": ["Flamengo", "Palmeiras", "São Paulo", "Corinthians", "Vasco"],
        "P": [45, 42, 40, 38, 35],
        "J": [20, 20, 20, 20, 20]
    }).set_index("Pos")

    with tab1: st.dataframe(df_fake, use_container_width=True)
    with tab2: st.info("Simulação baseada nos palpites do Fabinho"); st.dataframe(df_fake, use_container_width=True)
    with tab3: st.info("Simulação baseada nos palpites do Maicon"); st.dataframe(df_fake, use_container_width=True)

st.divider()

# --- LOOP DE RODADAS ---
for r in range(1, 39):
    # Regra: Mostra todas as anteriores, a atual e as próximas 2
    if r > rodada_atual + 2:
        continue
    
    # Define o título visual
    titulo_rodada = f"📍 Rodada {r}"
    if r == rodada_atual:
        titulo_rodada = f"⚽ Rodada {r} (ATUAL)"
    
    # Expandido se for a rodada atual
    start_expanded = (r == rodada_atual)
    
    with st.expander(titulo_rodada, expanded=start_expanded):
        
        # --- ÁREA DA IA ---
        with st.container():
            foto = st.file_uploader(f"📸 Foto Palpites R{r}", type=['png', 'jpg'], key=f"up_{r}")
            
            if foto:
                if st.button(f"🤖 Ler Foto e Preencher (R{r})", key=f"btn_ia_{r}"):
                    with st.spinner("A IA está lendo seus garranchos..."):
                        jogos_ref = obter_jogos_cbf(r)
                        extraido = processar_foto(foto, jogos_ref)
                        
                        if extraido:
                            for jogo_nome, placar_full in extraido.items():
                                # A mágica: quebra "2x1" em "2" e "1"
                                try:
                                    gols_m, gols_v = placar_full.lower().split('x')
                                    st.session_state[f"gols_m_{usuario}_{r}_{jogo_nome}"] = gols_m.strip()
                                    st.session_state[f"gols_v_{usuario}_{r}_{jogo_nome}"] = gols_v.strip()
                                except:
                                    pass # Se falhar o split, ignora
                            st.success("Campos preenchidos! Confira e salve.")
                        else:
                            st.warning("Não consegui ler nada. Tente uma foto mais clara.")

        st.markdown("---")

        # --- LISTA DE JOGOS E INPUTS ---
        jogos_lista = obter_jogos_cbf(r)
        dados_salvos_bd = db_carregar(usuario, r) # Retorna dict {'Jogo': '2x1'}
        
        editando = st.session_state.get(f"edit_mode_{r}", False)
        
        # Dicionário temporário para salvar depois
        palpites_para_salvar = {} 

        for jogo in jogos_lista:
            st.markdown(f"**{jogo}**")
            
            # Recupera valor: Session (IA/Edição) > Banco > Vazio
            valor_bd = dados_salvos_bd.get(jogo, "x") # "2x1" ou "x"
            g_m_bd, g_v_bd = valor_bd.split('x') if 'x' in valor_bd else ("", "")
            
            # Chaves únicas para os widgets
            k_m = f"gols_m_{usuario}_{r}_{jogo}"
            k_v = f"gols_v_{usuario}_{r}_{jogo}"
            
            # Inicializa session state se não existir
            if k_m not in st.session_state: st.session_state[k_m] = g_m_bd
            if k_v not in st.session_state: st.session_state[k_v] = g_v_bd
            
            # Layout: [Input] X [Input]
            c_m, c_x, c_v = st.columns([2, 0.5, 2])
            
            with c_m:
                val_m = st.text_input("M", key=k_m, label_visibility="collapsed", disabled=not editando, placeholder="0")
            with c_x:
                st.markdown("<div style='text-align: center; padding-top: 5px;'>X</div>", unsafe_allow_html=True)
            with c_v:
                val_v = st.text_input("V", key=k_v, label_visibility="collapsed", disabled=not editando, placeholder="0")
            
            # Monta string pro save (se tiver preenchido)
            if val_m and val_v:
                palpites_para_salvar[jogo] = f"{val_m}x{val_v}"

            st.write("") # Espacinho

        # --- BOTÕES DE AÇÃO ---
        col_b1, col_b2 = st.columns(2)
        
        if col_b1.button("✏️ Editar", key=f"bt_edit_{r}", use_container_width=True):
            st.session_state[f"edit_mode_{r}"] = True
            st.rerun()
            
        if col_b2.button("💾 Salvar", key=f"bt_save_{r}", type="primary", use_container_width=True):
            if not palpites_para_salvar:
                st.warning("Preencha os placares antes de salvar!")
            else:
                for j, p in palpites_para_salvar.items():
                    db_salvar(usuario, r, j, p)
                st.session_state[f"edit_mode_{r}"] = False
                st.toast(f"Rodada {r} salva com sucesso!", icon="✅")
                time.sleep(1)
                st.rerun()

# Botão de Sair (Resetar usuário)
st.sidebar.markdown("---")
if st.sidebar.button("Sair / Trocar Usuário"):
    del st.session_state["usuario"]
    st.rerun()
