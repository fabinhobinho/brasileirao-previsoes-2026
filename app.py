import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# --- CONFIGURAÇÃO IA ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Configure a GEMINI_API_KEY nos Secrets do Streamlit!")

def analisar_com_gemini(imagem, lista_jogos):
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(imagem)
    
    # Prompt pedindo JSON para facilitar o preenchimento automático
    prompt = f"""
    Analise esta imagem de palpites do Brasileirão.
    Aqui está a lista de jogos esperada: {lista_jogos}
    Retorne um JSON onde a chave é o nome exato do jogo da lista e o valor é o placar encontrado (ex: "2x0").
    Se não encontrar um jogo, ignore-o.
    Retorne APENAS o JSON, sem textos adicionais.
    """
    
    response = model.generate_content([prompt, img])
    # Limpeza simples caso a IA coloque blocos de código markdown
    txt = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(txt)

# --- DADOS DOS JOGOS (Exemplo das primeiras rodadas) ---
calendario = {
    1: ["Botafogo x Cruzeiro", "Chapecoense x Santos", "Vitória x Remo", "São Paulo x Flamengo"], # Adicione os 10 aqui
    2: ["Flamengo x Internacional", "Bragantino x Atlético-MG", "Santos x São Paulo", 
        "Remo x Mirassol", "Grêmio x Botafogo", "Bahia x Fluminense", 
        "Vasco da Gama x Chapecoense", "Cruzeiro x Coritiba"],
    3: ["Vitória x Flamengo", "Mirassol x Cruzeiro", "Chapecoense x Coritiba", "Atlético-MG x Remo"] # E assim por diante
}

# --- INTERFACE ---
st.set_page_config(page_title="Brasileirão 2026", layout="wide")
st.title("🏆 Previsões Brasileirão 2026")

usuario = st.sidebar.radio("Quem está editando?", ["Maicon", "Fabinho"])

for rodada in range(1, 39):
    with st.expander(f"📍 Rodada {rodada}", expanded=(rodada == 2)):
        
        # 1. ÁREA DE UPLOAD (Topo)
        st.subheader("📸 Upload da Foto")
        foto = st.file_uploader(f"Arraste a foto da R{rodada} aqui", type=['png', 'jpg', 'jpeg'], key=f"up_{rodada}")
        
        if foto:
            st.image(foto, width=300)
            if st.button(f"🤖 Ler com IA e Preencher Rodada {rodada}", key=f"btn_ai_{rodada}"):
                with st.spinner("IA lendo placares..."):
                    try:
                        jogos_da_rodada = calendario.get(rodada, [])
                        dados_extraidos = analisar_com_gemini(foto, jogos_da_rodada)
                        
                        # Salva na "memória" do navegador para preencher os inputs abaixo
                        for jogo, placar in dados_extraidos.items():
                            st.session_state[f"input_{usuario}_{rodada}_{jogo}"] = placar
                        st.success("Campos atualizados abaixo!")
                    except Exception as e:
                        st.error(f"Erro na leitura: {e}")

        st.divider()

        # 2. LISTA DE JOGOS (Abaixo)
        st.subheader("📝 Resultados / Palpites")
        jogos = calendario.get(rodada, [f"Jogo {x} (Aguardando CBF)" for x in range(1, 11)])
        
        # Criar os campos para cada jogo
        for jogo in jogos:
            # Chave única para cada input baseada no usuário, rodada e jogo
            key = f"input_{usuario}_{rodada}_{jogo}"
            
            # Se a IA já preencheu, o valor estará no session_state
            valor_padrao = st.session_state.get(key, "")
            
            st.text_input(f"⚽ {jogo}", value=valor_padrao, key=key)

        if st.button("💾 Salvar Tudo desta Rodada", key=f"save_final_{rodada}"):
            st.success(f"Palpites de {usuario} para a Rodada {rodada} foram registrados!")
