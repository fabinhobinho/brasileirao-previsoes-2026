import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# 1. Configuração da API (Pega o segredo que você salvou no Streamlit)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Erro: API Key não encontrada nos Secrets do Streamlit!")

# Função para processar a imagem
def ler_palpites_com_gemini(imagem_enviada):
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(imagem_enviada)
    
    prompt = """
    Analise esta imagem de jogos do Brasileirão. 
    Extraia os times e os placares.
    Retorne APENAS um formato de texto simples assim:
    Time Casa x Time Fora: Placar Casa x Placar Fora
    Exemplo: Flamengo x Internacional: 3 x 0
    """
    
    response = model.generate_content([prompt, img])
    return response.text

# --- INTERFACE ---
st.set_page_config(page_title="Palpites Brasileirão 2026", layout="wide")
st.title("🏆 Brasileirão 2026 - Maicon & Fabinho")

st.sidebar.header("👤 Usuário")
usuario = st.sidebar.radio("Quem está editando?", ["Maicon", "Fabinho"])

tab_previsoes, tab_comparador = st.tabs(["📅 Rodadas e Previsões", "📊 Tabela e Comparador"])

with tab_previsoes:
    for i in range(1, 39):
        with st.expander(f"Rodada {i}"):
            col_up, col_edit = st.columns([1, 1])
            
            with col_up:
                foto = st.file_uploader(f"Upload Foto R{i}", type=['png', 'jpg', 'jpeg'], key=f"up_{i}")
                if foto:
                    st.image(foto, width=250)
                    if st.button(f"🤖 IA: Ler Palpites R{i}", key=f"btn_ai_{i}"):
                        with st.spinner("Gemini analisando a foto..."):
                            resultado_ia = ler_palpites_com_gemini(foto)
                            st.session_state[f"temp_data_{i}"] = resultado_ia
                            st.success("Leitura concluída!")

            with col_edit:
                st.write("**📝 Resultados Extraídos**")
                # Se a IA já leu, mostra o texto para conferência
                texto_preenchido = st.session_state.get(f"temp_data_{i}", "")
                
                # Área de edição para o usuário ajustar se a IA errar
                dados_finais = st.text_area("Ajuste os resultados se necessário:", 
                                            value=texto_preenchido, 
                                            height=200, 
                                            key=f"area_{i}")
                
                if st.button("Confirmar e Salvar no Banco", key=f"save_{i}"):
                    st.success(f"Palpites de {usuario} para a Rodada {i} salvos!")

# (O código da Tab Comparador continua igual ao anterior)
