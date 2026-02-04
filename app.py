import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# --- CONFIGURAÇÃO IA ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Configure a chave GEMINI_API_KEY nos Secrets do Streamlit!")

def analisar_com_gemini(imagem, lista_jogos):
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(imagem)
    
    prompt = f"""
    Analise esta imagem de palpites/resultados do Brasileirão.
    Esta é a lista oficial de jogos da rodada: {lista_jogos}
    
    Sua tarefa: Extraia os placares da imagem e associe aos jogos da lista acima.
    Retorne APENAS um JSON no formato: {{"Nome do Jogo": "Placar"}}.
    Exemplo: {{"Flamengo x Internacional": "2x0", "Santos x São Paulo": "1x2"}}
    Se não encontrar o placar de um jogo, não inclua no JSON. 
    Retorne apenas o JSON puro, sem markdown.
    """
    
    response = model.generate_content([prompt, img])
    txt = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(txt)

# --- CALENDÁRIO REAL CBF 2026 ---
# Dados baseados na tabela oficial da CBF para as primeiras rodadas
calendario = {
    1: [
        "Atlético-MG x Palmeiras", "Internacional x Athletico-PR", "Coritiba x RB Bragantino",
        "Vitória x Remo", "Fluminense x Grêmio", "Chapecoense x Santos", 
        "Corinthians x Bahia", "São Paulo x Flamengo", "Mirassol x Vasco", "Botafogo x Cruzeiro"
    ],
    2: [
        "Flamengo x Internacional", "RB Bragantino x Atlético-MG", "Santos x São Paulo",
        "Remo x Mirassol", "Palmeiras x Vitória", "Grêmio x Botafogo",
        "Bahia x Fluminense", "Vasco x Chapecoense", "Cruzeiro x Coritiba", "Athletico-PR x Corinthians"
    ],
    3: [
        "Mirassol x Cruzeiro", "Chapecoense x Coritiba", "Atlético-MG x Remo",
        "Vasco x Bahia", "São Paulo x Grêmio", "Athletico-PR x Santos",
        "Fluminense x Botafogo", "Corinthians x RB Bragantino", "Internacional x Palmeiras", "Vitória x Flamengo"
    ],
    4: [
        "Flamengo x Mirassol", "Botafogo x Vitória", "Santos x Vasco",
        "Palmeiras x Fluminense", "RB Bragantino x Athletico-PR", "Cruzeiro x Corinthians",
        "Grêmio x Atlético-MG", "Coritiba x São Paulo", "Bahia x Chapecoense", "Remo x Internacional"
    ]
}

# --- INTERFACE ---
st.set_page_config(page_title="Palpites Brasileirão 2026", layout="centered", page_icon="⚽")
st.title("🏆 Brasileirão 2026 - Maicon & Fabinho")

# Barra lateral para trocar de usuário
st.sidebar.header("Configuração")
usuario = st.sidebar.radio("Quem está editando?", ["Maicon", "Fabinho"])
rodada_atual = 2 # Conforme data de hoje 04/02/2026

# Tabs
tab_previsoes, tab_comparador = st.tabs(["📅 Palpites", "📊 Tabela Oficial"])

with tab_previsoes:
    st.write(f"### 📍 Editando como: **{usuario}**")
    
    for rodada in range(1, 39):
        # Exibe as rodadas passadas e as próximas 3 de forma clara
        is_relevant = (rodada <= rodada_atual + 3)
        label = f"Rodada {rodada}"
        if rodada == rodada_atual: label += " ⚽ (HOJE)"
        
        with st.expander(label, expanded=(rodada == rodada_atual)):
            
            # --- SEÇÃO UPLOAD (TOPO) ---
            st.markdown("#### 📸 1. Upload da Foto")
            foto = st.file_uploader(f"Subir print da Rodada {rodada}", type=['png', 'jpg', 'jpeg'], key=f"up_{rodada}")
            
            if foto:
                st.image(foto, caption="Foto para processamento", width=400)
                if st.button(f"🤖 Extrair com Gemini (Rodada {rodada})", key=f"btn_ia_{rodada}"):
                    with st.spinner("IA analisando a imagem..."):
                        try:
                            jogos_lista = calendario.get(rodada, [])
                            resultados_ia = analisar_com_gemini(foto, jogos_lista)
                            # Salva na memória do app
                            for jogo, placar in resultados_ia.items():
                                st.session_state[f"val_{usuario}_{rodada}_{jogo}"] = placar
                            st.success("Placares extraídos com sucesso! Confira abaixo.")
                        except Exception as e:
                            st.error(f"Erro ao ler imagem: {e}")

            st.divider()

            # --- SEÇÃO RESULTADOS (ABAIXO) ---
            st.markdown("#### 📝 2. Resultados / Palpites")
            jogos = calendario.get(rodada, [f"Jogo {x} (Aguardando CBF)" for x in range(1, 11)])
            
            for jogo in jogos:
                chave_input = f"val_{usuario}_{rodada}_{jogo}"
                # Busca valor da IA ou mantém vazio para preenchimento manual
                valor_atual = st.session_state.get(chave_input, "")
                
                st.text_input(f"➤ {jogo}", value=valor_atual, key=chave_input, placeholder="Ex: 2x0")

            if st.button("💾 Salvar Rodada", key=f"save_{rodada}"):
                st.balloons()
                st.success(f"Palpites de {usuario} para a rodada {rodada} salvos com sucesso!")

with tab_comparador:
    st.info("Aguardando script de atualização automática da CBF...")
    st.write("Aqui ficará a tabela oficial do Brasileirão 2026.")
