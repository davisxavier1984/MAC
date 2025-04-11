import base64
import streamlit as st
import plotly.express as px
import pandas as pd
import json
import streamlit.components.v1 as components

# --- Carregamento dos dados ---
with open('evolucao_mac.json', 'r', encoding='utf-8') as file:
    dados_evolucao_mac_json = json.load(file)

def capturar_dados_evolucao_mac(json_data):
    sem_incentivos = []
    incentivos = []
    teto_financeiro_mac = []

    for entrada in json_data:
        for chave, valores in entrada.items():
            if chave == "Sem Incentivos":
                sem_incentivos = [float(valores[ano]) for ano in valores if ano.isdigit()]
                sem_incentivos.append(sem_incentivos[-1])  # Repetir 2023 em 2024
            elif chave == "Incentivos":
                incentivos = [float(valores[ano]) for ano in valores if ano.isdigit()]
                incentivos.append(incentivos[-1])  # Repetir 2023 em 2024
            elif chave == "Teto Financeiro MAC":
                teto_financeiro_mac = [float(valores[ano]) for ano in valores if ano.isdigit()]
                teto_financeiro_mac.append(teto_financeiro_mac[-1])  # Repetir 2023 em 2024

    return sem_incentivos, incentivos, teto_financeiro_mac

sem_incentivos, incentivos, teto_financeiro_mac = capturar_dados_evolucao_mac(dados_evolucao_mac_json)

# Listas fornecidas com os valores do JSON (usadas globalmente)
teto_total = teto_financeiro_mac
valores_sem_incentivo = sem_incentivos
valores_incentivos = incentivos

# Correção na extração dos anos
anos_str = sorted(
    {
        ano
        for entrada in dados_evolucao_mac_json
        for valores in entrada.values()
        for ano in valores
        if ano.isdigit()
    }
)
anos = [int(ano) for ano in anos_str]

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

# --- Conteúdo da página ---
def evolucao_teto_mac():
    
    st.title("Evolução do Teto MAC")

    data = []
    for ano in anos_str:
        
        if ano.isdigit():
            ano_int = int(ano)
            try:
                # Encontrar o índice do ano nas listas
                idx = anos.index(ano_int)
                data.append({"Ano": ano_int, "Valor (R$)": teto_total[idx], "Categoria": "Teto Total"})
                data.append({"Ano": ano_int, "Valor (R$)": valores_sem_incentivo[idx], "Categoria": "Valores Sem Incentivo"})
                data.append({"Ano": ano_int, "Valor (R$)": valores_incentivos[idx], "Categoria": "Valores Incentivos"})
            except ValueError:
                print(f"Ano {ano_int} não encontrado nas listas de valores.")

    df = pd.DataFrame(data)

    # Criando o gráfico
    fig = px.line(
        df,
        x="Ano",
        y="Valor (R$)",
        color="Categoria",
        labels={"value": "Valores", "variable": "Categorias"},
        markers=True,
    )
    fig.update_layout(
        title="Dados ao longo dos anos",
        xaxis_title="Ano",
        yaxis_title="Valores",
        legend_title_text="Categorias",
        legend=dict(itemsizing="constant", orientation="h"),
    )

    fig.update_traces(marker=dict(size=12))
    fig.update_xaxes(showgrid=True, gridwidth=0.1, gridcolor="LightGrey")
    fig.update_yaxes(showgrid=True, gridwidth=0.1, gridcolor="LightGrey")

    st.plotly_chart(fig)
    st.caption("Fonte: Sismac/MS")

    # Caminho do arquivo
    caminho_arquivo = "analise_mac_municipio.txt"

    # Lendo o conteúdo do arquivo
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        conteudo = arquivo.read()

    # Exibindo o conteúdo
    st.markdown(conteudo, unsafe_allow_html=True)
    
evolucao_teto_mac()