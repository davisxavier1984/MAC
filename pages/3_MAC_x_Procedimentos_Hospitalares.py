import base64
import streamlit as st
import plotly.graph_objs as go
import json
import pandas as pd  # Importe o pandas (mesmo que não seja usado imediatamente, é uma boa prática)

# --- Carregamento dos Dados ---
try:
    with open('SIH.json', 'r', encoding='utf-8') as arquivo:
        dados_sih_json = json.load(arquivo)
except FileNotFoundError:
    st.error("SIH.json não encontrado. Por favor, carregue o arquivo.")
    st.stop()
except json.JSONDecodeError:
    st.error("Erro ao decodificar SIH.json. Por favor, verifique o formato do arquivo.")
    st.stop()

try:
    with open('evolucao_mac.json', 'r', encoding='utf-8') as arquivo:
        dados_evolucao_mac_json = json.load(arquivo)
except FileNotFoundError:
    st.error("evolucao_mac.json não encontrado. Por favor, carregue o arquivo.")
    st.stop()
except json.JSONDecodeError:
    st.error("Erro ao decodificar evolucao_mac.json. Por favor, verifique o formato do arquivo.")
    st.stop()


def capturar_dados_sih(dados_json, anos):
    grupos = {}
    total_procedimentos = {str(ano): 0 for ano in anos}

    for entrada in dados_json:
        grupo = entrada.get("Grupo procedimento", "Outros")
        if grupo not in grupos:
            grupos[grupo] = {str(ano): 0 for ano in anos}

        for ano_str, valor in entrada.items():
            if ano_str.isdigit():
                ano = int(ano_str)
                if ano in anos:
                    try:
                        valor_formatado = int(valor.replace('.', '')) if isinstance(valor, str) and valor != "-" else int(valor)
                    except (ValueError, TypeError):
                        valor_formatado = 0

                    grupos[grupo][str(ano)] += valor_formatado
                    total_procedimentos[str(ano)] += valor_formatado

    return grupos, total_procedimentos


def capturar_dados_evolucao_mac(json_data, anos):
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


# --- Determina os anos disponíveis em ambos os arquivos JSON ---
anos_sih = set()
for entrada in dados_sih_json:
    for chave in entrada:
        if chave.isdigit():
            anos_sih.add(int(chave))
anos_sih = sorted(list(anos_sih))

anos_mac = sorted({int(chave) for entrada in dados_evolucao_mac_json for chave in entrada.keys() if chave.isdigit()})
anos = sorted(list(set(anos_sih).union(anos_mac)))
grupos, total_procedimentos = capturar_dados_sih(dados_sih_json, anos)
sem_incentivos, incentivos, teto_financeiro_mac = capturar_dados_evolucao_mac(dados_evolucao_mac_json, anos) # Pass 'anos' to the function

teto_total = teto_financeiro_mac
valores_sem_incentivo = sem_incentivos
valores_incentivos = incentivos

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

# --- Conteúdo da Página ---
def mac_x_procedimentos_hospitalares():
    st.title("Procedimentos Hospitalares e Recursos ao Longo dos Anos")

    # Criando o gráfico dinamicamente
    fig1 = go.Figure()

    # Adicionando os dados de cada grupo ao gráfico
    for grupo, dados in grupos.items():
        valores = [dados[str(ano)] for ano in anos]
        if any(valores):  # Apenas adiciona se houver dados
            fig1.add_trace(go.Scatter(x=anos, y=valores, mode='lines+markers', name=grupo))

    # Adicionando os dados totais ao gráfico
    valores_totais = [total_procedimentos[str(ano)] for ano in anos]
    fig1.add_trace(go.Scatter(x=anos, y=valores_totais, mode='lines+markers', name='Total de Procedimentos', line=dict(dash='dash')))

    # Personalizando o layout do gráfico
    fig1.update_layout(
        title='Procedimentos Hospitalares ao Longo dos Anos',
        xaxis_title='Anos',
        yaxis_title='Número de Procedimentos',
        legend_title='Tipo de Procedimento',
        legend=dict(orientation='h', y=-0.2, x=0)
    )

    fig1.update_traces(marker=dict(size=12))
    fig1.update_xaxes(showgrid=True, gridwidth=0.1, gridcolor='LightGrey')
    fig1.update_yaxes(showgrid=True, gridwidth=0.1, gridcolor='LightGrey')

    fig2 = go.Figure()

    # Recursos ao longo dos anos
    fig2.add_trace(go.Scatter(x=anos, y=teto_total, mode='lines+markers', name='Teto Total'))
    fig2.add_trace(go.Scatter(x=anos, y=valores_sem_incentivo, mode='lines+markers', name='Valores Sem Incentivo'))
    fig2.add_trace(go.Scatter(x=anos, y=valores_incentivos, mode='lines+markers', name='Valores com Incentivos'))

    fig2.update_traces(marker=dict(size=12))
    fig2.update_xaxes(showgrid=True, gridwidth=0.1, gridcolor='LightGrey')
    fig2.update_yaxes(showgrid=True, gridwidth=0.1, gridcolor='LightGrey')

    fig2.update_layout(
    title='Recursos ao Longo dos Anos',
    xaxis_title='Anos',
    yaxis_title='Valores (R$)',
    legend_title='Tipo de Recurso',
    legend=dict(orientation='h', y=-0.2, x=0)
    )

    # Exibir os gráficos no Streamlit
    st.plotly_chart(fig1)
    st.plotly_chart(fig2)
    st.caption('Fonte: Tabnet/Datasus/MS')

    # Texto da Análise

    caminho_arquivo = "analise_mac_sih.txt"

    # Lendo o conteúdo do arquivo
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        conteudo = arquivo.read()  # Lê o conteúdo do arquivo

    # Exibindo o conteúdo com st.markdown
    st.markdown(conteudo)

mac_x_procedimentos_hospitalares()