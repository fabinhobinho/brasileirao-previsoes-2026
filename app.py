import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Previsões Brasileirão 2026", layout="wide")

st.title("🏆 Brasileirão 2026 - Maicon & Fabinho")

# --- BARRA LATERAL / SELEÇÃO DE USUÁRIO ---
st.sidebar.header("Configurações")
usuario = st.sidebar.radio("Quem está editando?", ["Maicon", "Fabinho"])
st.sidebar.write(f"Editando como: **{usuario}**")

# --- ABAS PRINCIPAIS ---
tab_previsoes, tab_comparador = st.tabs(["📅 Rodadas e Previsões", "📊 Comparador de Tabela"])

with tab_previsoes:
    st.info(f"Olá {usuario}, selecione uma rodada para subir sua foto ou editar os palpites.")
    
    # Criando as 38 rodadas dinamicamente
    for i in range(1, 39):
        with st.expander(f"📍 Rodada {i}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Upload de Palpites")
                foto = st.file_uploader(f"Subir foto da Rodada {i}", type=['png', 'jpg', 'jpeg'], key=f"foto_{i}")
                if foto:
                    st.image(foto, caption="Foto carregada", use_container_width=True)
                    if st.button(f"Processar com Gemini - R{i}", key=f"btn_ai_{i}"):
                        st.warning("IA em fase de implementação... (Próximo passo)")
            
            with col2:
                st.subheader("Edição Manual")
                # Aqui futuramente carregaremos os dados do banco
                st.text_area("Jogos e Resultados (Texto)", placeholder="Ex: Flamengo 2 x 0 Vasco", key=f"edit_{i}")
                st.button("Salvar Alterações", key=f"save_{i}")

with tab_comparador:
    st.header("Tabela Comparativa")
    st.write("Aguardando dados da CBF...")
    # Placeholder para a tabela
    df_exemplo = pd.DataFrame({
        'Posição': range(1, 21),
        'Time': ['-'] * 20,
        'Oficial': ['-'] * 20,
        'Maicon': ['-'] * 20,
        'Fabinho': ['-'] * 20
    })
    st.table(df_exemplo)
