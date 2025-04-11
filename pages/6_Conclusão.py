import streamlit as st
import json
import base64

# --- Conteúdo da página ---

# Função para converter imagem em base64
def img_to_base64(file_path):
    with open(file_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# Caminhos das imagens
logo_maisgestor = 'logo_colorida_mg.png'
logo = 'bombinhas.png'

# Converter imagens para base64
logo_maisgestor_base64 = img_to_base64(logo_maisgestor)
logo_base64 = img_to_base64(logo)

# Adicionar logos na sidebar
st.sidebar.markdown(
    f"""
    <div style="display: flex; flex-direction: column; align-items: center;">
        <img src='data:image/png;base64,{logo_maisgestor_base64}' style='height: 100px; margin-bottom: 20px;'>
        <img src='data:image/png;base64,{logo_base64}' style='height: 100px; margin-bottom: 20px;'>
        
    </div>
    """,
    unsafe_allow_html=True,
)

def conclusao():
    # Caminho do arquivo
    caminho_arquivo = "conclusao_final.txt"

    # Lendo o conteúdo do arquivo TXT
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        conteudo = arquivo.read()

    # Exibindo o conteúdo no Streamlit
    st.markdown(conteudo)

conclusao()
