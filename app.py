import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# --- CONFIGURAÇÃO IA ---
try:
    # Usando o modelo latest que funcionou para você
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    MODELO_ESCOLHIDO = 'gemini-1.5-flash-latest'
except Exception as e:
    st.error(f"Erro na configuração da API Key: {e}")

def analisar_com_gemini(imagem, lista_jogos):
    model = genai.GenerativeModel(MODELO_ESCOLHIDO)
    img = Image.open(imagem)
    
    prompt = f"""
    Analise esta imagem de palpites/resultados do Brasileirão.
    Esta é a lista oficial de jogos da rodada: {lista_jogos}
    
    Sua tarefa: Extraia os placares da imagem e associe aos jogos da lista acima.
    Retorne APENAS um JSON no formato: {{"Nome do Jogo": "Placar"}}.
    Exemplo: {{"Flamengo x Internacional": "3x0", "Santos x São Paulo": "3x1"}}
    Se não encontrar o placar de um jogo, não inclua no JSON. 
    ATENÇÃO: Retorne apenas o JSON puro, sem blocos de código markdown (```json ... ```).
    """
    
    response = model.generate_content([prompt, img])
    # Limpeza extra para garantir que venha só o JSON
    txt = response.text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(txt)

# --- CALENDÁRIO REAL CBF 2026 (Primeiras Rodadas) ---
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

st.sidebar.header("Configuração")
usuario = st.sidebar.radio("Quem está editando?", ["Maicon", "Fabinho"])
rodada_atual = 2 # Data de hoje 04/02/2026

tab_previsoes, tab_comparador = st.tabs(["📅 Palpites", "📊 Tabela Oficial"])

with tab_previsoes:
    st.write(f"### 📍 Editando como: **{usuario}**")
    
    for rodada in range(1, 39):
        is_relevant = (rodada <= rodada_atual + 3)
        label = f"Rodada {rodada}"
        if rodada == rodada_atual: label += " ⚽ (HOJE)"
        
        with st.expander(label, expanded=(rodada == rodada_atual)):
            
            # --- SEÇÃO UPLOAD (TOPO) ---
            st.markdown("#### 📸 1. Upload da Foto")
            foto = st.file_uploader(f"Subir print da Rodada {rodada}", type=['png', 'jpg', 'jpeg'], key=f"up_{rodada}", label_visibility="collapsed")
            
            if foto:
                # --- MUDANÇA AQUI: Layout em colunas para miniatura ---
                col_btn, col_thumb = st.columns([4, 1]) # Coluna do botão maior, da imagem menor
                
                with col_thumb:
                    # Exibe a imagem bem pequena (width=80 pixels)
                    st.image(foto, width=80, use_container_width=False)

                with col_btn:
                    # O botão ocupa a largura da coluna dele
                    processar = st.button(f"🤖 Extrair Placar com IA", key=f"btn_ia_{rodada}", use_container_width=True)

                if processar:
                    with st.spinner("Gemini lendo a imagem..."):
                        try:
                            jogos_lista = calendario.get(rodada, [])
                            resultados_ia = analisar_com_gemini(foto, jogos_lista)
                            # Salva na memória temporária
                            for jogo, placar in resultados_ia.items():
                                st.session_state[f"val_{usuario}_{rodada}_{jogo}"] = placar
                            st.toast("Placares extraídos! Verifique abaixo.", icon="✅")
                        except Exception as e:
                            st.error(f"Erro na leitura: {e}")
            
            st.divider()

            # --- SEÇÃO RESULTADOS (ABAIXO) ---
            st.markdown("#### 📝 2. Resultados / Palpites")
            jogos = calendario.get(rodada, [f"Jogo {x} (Aguardando CBF)" for x in range(1, 11)])
            
            for jogo in jogos:
                chave_input = f"val_{usuario}_{rodada}_{jogo}"
                valor_atual = st.session_state.get(chave_input, "")
                st.text_input(f"➤ {jogo}", value=valor_atual, key=chave_input, placeholder="Ex: 2x0")

            # Botão de salvar (ainda sem banco de dados)
            st.button("💾 Salvar Rodada (Temporário)", key=f"save_{rodada}", use_container_width=True)

with tab_comparador:
    st.info("Aguardando script de atualização automática da CBF...")
