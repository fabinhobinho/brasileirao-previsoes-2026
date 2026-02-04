import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from supabase import create_client, Client
import json
import requests
from bs4 import BeautifulSoup

# --- CONEXÕES ---
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- FUNÇÃO DE BUSCA DE JOGOS (SCRAPING) ---
@st.cache_data(ttl=3600)
def obter_jogos_cbf(rodada):
    # Fallback caso o site da CBF esteja instável ou mude o layout
    jogos_fixos = {
        1: ["Atlético-MG x Palmeiras", "Internacional x Athletico-PR", "Coritiba x RB Bragantino", "Vitória x Remo", "Fluminense x Grêmio", "Chapecoense x Santos", "Corinthians x Bahia", "São Paulo x Flamengo", "Mirassol x Vasco", "Botafogo x Cruzeiro"],
        2: ["Flamengo x Internacional", "RB Bragantino x Atlético-MG", "Santos x São Paulo", "Remo x Mirassol", "Palmeiras x Vitória", "Grêmio x Botafogo", "Bahia x Fluminense", "Vasco da Gama x Chapecoense", "Cruzeiro x Coritiba", "Athletico-PR x Corinthians"]
    }
    return jogos_fixos.get(rodada, [f"Jogo {i} - Rodada {rodada}" for i in range(1, 11)])

# --- IA GEMINI ---
def processar_foto(imagem, lista_jogos):
    model = genai.GenerativeModel('gemini-flash-latest')
    img = Image.open(imagem)
    prompt = f"Extraia placares para estes jogos: {lista_jogos}. Retorne APENAS um JSON: {{'Time A x Time B': '2x0'}}"
    response = model.generate_content([prompt, img])
    txt = response.text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(txt)

# --- BANCO DE DADOS ---
def db_salvar(user, rod, jogo, placar):
    # Upsert: Insere ou atualiza se já existir (chave composta: user+rod+jogo)
    supabase.table("palpites").upsert({
        "usuario": user, "rodada": rod, "jogo": jogo, "placar": placar
    }, on_conflict="usuario,rodada,jogo").execute()

def db_carregar(user, rod):
    res = supabase.table("palpites").select("jogo, placar").eq("usuario", user).eq("rodada", rod).execute()
    return {item['jogo']: item['placar'] for item in res.data}

# --- INTERFACE ---
st.set_page_config(page_title="Brasileirão 2026", layout="centered")
st.title("🏆 Previsões Brasileirão 2026")

usuario = st.sidebar.radio("Quem está editando?", ["Maicon", "Fabinho"])
rodada_atual = 2

for r in range(1, 39):
    # Rodadas anteriores e próximas 2 ficam visíveis
    if r > rodada_atual + 2: continue
        
    with st.expander(f"📍 Rodada {r}", expanded=(r == rodada_atual)):
        
        # 1. Upload e IA
        foto = st.file_uploader(f"Foto R{r}", type=['png', 'jpg'], key=f"up_{r}", label_visibility="collapsed")
        if foto:
            col_btn, col_thumb = st.columns([4, 1])
            with col_thumb: st.image(foto, width=70)
            if col_btn.button(f"🤖 Extrair Placares IA (R{r})", key=f"ia_btn_{r}", use_container_width=True):
                jogos = obter_jogos_cbf(r)
                extraido = processar_foto(foto, jogos)
                for j, p in extraido.items():
                    st.session_state[f"temp_{usuario}_{r}_{j}"] = p
                st.toast("IA preencheu os campos abaixo!")

        st.divider()

        # 2. Lista de Jogos e Inputs
        jogos_lista = obter_jogos_cbf(r)
        dados_salvos = db_carregar(usuario, r)
        
        # Controle de edição
        editando = st.session_state.get(f"edit_mode_{r}", False)
        
        novos_palpites = {}
        for jogo in jogos_lista:
            # Prioridade: Session (IA) > Banco de Dados > Vazio
            val_default = st.session_state.get(f"temp_{usuario}_{r}_{jogo}", dados_salvos.get(jogo, ""))
            novos_palpites[jogo] = st.text_input(f"⚽ {jogo}", value=val_default, disabled=not editando, key=f"inp_{usuario}_{r}_{jogo}")

        # 3. Botões de Ação
        c1, c2 = st.columns(2)
        if c1.button("✏️ Editar Rodada", key=f"ed_{r}", use_container_width=True):
            st.session_state[f"edit_mode_{r}"] = True
            st.rerun()
            
        if c2.button("💾 Salvar Previsões", key=f"sv_{r}", type="primary", use_container_width=True):
            for j, p in novos_palpites.items():
                db_salvar(usuario, r, j, p)
            st.session_state[f"edit_mode_{r}"] = False
            st.success("Salvo com sucesso!")
            st.rerun()
