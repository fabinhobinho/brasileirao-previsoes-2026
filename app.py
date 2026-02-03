import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Palpites Brasileirão 2026", layout="wide", page_icon="⚽")

# --- DADOS OFICIAIS (SIMULANDO CONSULTA API/SITE) ---
# Aqui listamos os jogos que a IA buscou para as próximas rodadas
jogos_oficiais = {
    2: [
        "Flamengo x Internacional", "RB Bragantino x Atlético-MG", "Santos x São Paulo",
        "Remo x Mirassol", "Palmeiras x Vitória", "Grêmio x Botafogo",
        "Bahia x Fluminense", "Vasco x Chapecoense", "Cruzeiro x Coritiba", "Athletico-PR x Corinthians"
    ],
    3: [
        "Vitória x Flamengo", "Mirassol x Cruzeiro", "Chapecoense x Coritiba",
        "Atlético-MG x Remo", "Vasco x Bahia", "São Paulo x Grêmio",
        "Fluminense x Botafogo", "Corinthians x RB Bragantino", "Internacional x Palmeiras", "Athletico-PR x Santos"
    ],
    4: [
        "Flamengo x Mirassol", "Botafogo x Vitória", "Santos x Vasco",
        "Palmeiras x Fluminense", "RB Bragantino x Athletico-PR", "Cruzeiro x Corinthians",
        "Grêmio x Atlético-MG", "Coritiba x São Paulo", "Bahia x Chapecoense", "Remo x Internacional"
    ]
}

# Tabela Oficial após a Rodada 1
classificacao_real = [
    {"Pos": 1, "Time": "Botafogo", "Pts": 3, "SG": 4},
    {"Pos": 2, "Time": "Chapecoense", "Pts": 3, "SG": 2},
    {"Pos": 3, "Time": "Vitória", "Pts": 3, "SG": 2},
    {"Pos": 4, "Time": "São Paulo", "Pts": 3, "SG": 1},
    {"Pos": 5, "Time": "Fluminense", "Pts": 3, "SG": 1},
    {"Pos": 6, "Time": "Mirassol", "Pts": 3, "SG": 1},
    {"Pos": 7, "Time": "Bahia", "Pts": 3, "SG": 1},
    {"Pos": 8, "Time": "Athletico-PR", "Pts": 3, "SG": 1},
    {"Pos": 9, "Time": "RB Bragantino", "Pts": 3, "SG": 1},
    {"Pos": 10, "Time": "Palmeiras", "Pts": 1, "SG": 0},
    {"Pos": 11, "Time": "Atlético-MG", "Pts": 1, "SG": 0},
    {"Pos": 12, "Time": "Vasco", "Pts": 0, "SG": -1},
    {"Pos": 13, "Time": "Grêmio", "Pts": 0, "SG": -1},
    {"Pos": 14, "Time": "Corinthians", "Pts": 0, "SG": -1},
    {"Pos": 15, "Time": "Flamengo", "Pts": 0, "SG": -1},
    {"Pos": 16, "Time": "Internacional", "Pts": 0, "SG": -1},
    {"Pos": 17, "Time": "Coritiba", "Pts": 0, "SG": -1},
    {"Pos": 18, "Time": "Santos", "Pts": 0, "SG": -2},
    {"Pos": 19, "Time": "Remo", "Pts": 0, "SG": -2},
    {"Pos": 20, "Time": "Cruzeiro", "Pts": 0, "SG": -4},
]

# --- INTERFACE ---
st.title("🏆 Brasileirão 2026 - Maicon & Fabinho")

# Seletor de usuário na lateral
st.sidebar.header("👤 Usuário")
usuario = st.sidebar.radio("Quem está editando?", ["Maicon", "Fabinho"])
rodada_atual = 2  # Definimos a 2 como atual pois começa amanhã

tab_previsoes, tab_comparador = st.tabs(["📅 Rodadas e Previsões", "📊 Tabela e Comparador"])

with tab_previsoes:
    st.markdown(f"### 📍 Editando como: **{usuario}**")
    
    for i in range(1, 39):
        # Destaca a rodada atual com um emoji
        label = f"Rodada {i} {'⚽ (Atual)' if i == rodada_atual else ''}"
        
        with st.expander(label, expanded=(i == rodada_atual)):
            col_up, col_edit = st.columns([1, 1])
            
            with col_up:
                st.write("**📸 Subir Foto dos Palpites**")
                foto = st.file_uploader(f"Upload R{i}", type=['png', 'jpg'], key=f"up_{i}")
                if foto:
                    st.image(foto, width=300)
                    if st.button(f"Mandar para o Gemini 🚀", key=f"gemini_{i}"):
                        st.info("Conectando com a API... Aguarde.")

            with col_edit:
                st.write("**📝 Lista de Jogos**")
                # Se tivermos os jogos no nosso dicionário, listamos eles
                if i in jogos_oficiais:
                    for jogo in jogos_oficiais[i]:
                        st.text_input(jogo, placeholder="0 x 0", key=f"input_{i}_{jogo}")
                else:
                    st.info("Jogos ainda não liberados pela CBF para esta rodada.")
                
                st.button("Salvar Palpites", key=f"save_{i}")

with tab_comparador:
    st.header("📈 Classificação Oficial (CBF)")
    df_oficial = pd.DataFrame(classificacao_real)
    
    # Exemplo de visualização da tabela
    st.dataframe(df_oficial, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("🎯 Comparativo de Acertos")
    st.write("Aqui aparecerá a comparação entre Maicon, Fabinho e a Tabela Real.")
