import base64
import streamlit as st
import plotly.graph_objs as go
import json

# --- Carregamento dos dados ---
# (Idêntico em todas as páginas, pois os dados são usados globalmente)
with open('SIA.json', 'r', encoding='utf-8') as file:
    dados_sia_json = json.load(file)

with open('evolucao_mac.json', 'r', encoding='utf-8') as file:
    dados_evolucao_mac_json = json.load(file)

def capturar_dados_sia(json_data):
    anos_disponiveis = sorted({int(chave) for entrada in json_data for chave in entrada.keys() if chave.isdigit()})
    media_complexidade = dict.fromkeys(map(str, anos_disponiveis), 0)
    alta_complexidade = dict.fromkeys(map(str, anos_disponiveis), 0)
    total_ambulatorial = dict.fromkeys(map(str, anos_disponiveis), 0)

    for entrada in json_data:
        try:
            complexidade = entrada["Complexidade"]
            for ano in anos_disponiveis:
                valor_str = entrada.get(str(ano), "0").replace('.', '')
                if valor_str.isdigit():  # Verifica se o valor é um número válido
                    valor_procedimento = int(valor_str)
                else:
                    valor_procedimento = 0  # Define um valor padrão caso o valor não seja numérico

                if complexidade in ["Média complexidade", "Alta complexidade"]:
                    total_ambulatorial[str(ano)] += valor_procedimento
                    if complexidade == "Média complexidade":
                        media_complexidade[str(ano)] += valor_procedimento
                    elif complexidade == "Alta complexidade":
                        alta_complexidade[str(ano)] += valor_procedimento

        except KeyError:
            print(f"Erro ao processar entrada: {entrada}")

    return anos_disponiveis, media_complexidade, alta_complexidade, total_ambulatorial

def capturar_dados_evolucao_mac(json_data):
    sem_incentivos = []
    incentivos = []
    teto_financeiro_mac = []

    for entrada in json_data:
        for chave, valores in entrada.items():
            if chave == "Sem Incentivos":
                sem_incentivos = [float(valores[ano]) for ano in valores]
                sem_incentivos.append(sem_incentivos[-1])
            elif chave == "Incentivos":
                incentivos = [float(valores[ano]) for ano in valores]
                incentivos.append(incentivos[-1])
            elif chave == "Teto Financeiro MAC":
                teto_financeiro_mac = [float(valores[ano]) for ano in valores]
                teto_financeiro_mac.append(teto_financeiro_mac[-1])

    return sem_incentivos, incentivos, teto_financeiro_mac

anos, media_complexidade, alta_complexidade, total_ambulatorial = capturar_dados_sia(dados_sia_json)
sem_incentivos, incentivos, teto_financeiro_mac = capturar_dados_evolucao_mac(dados_evolucao_mac_json)

# Listas fornecidas com os valores do JSON (usadas globalmente)
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

# --- Conteúdo da página ---
def mac_x_producao_ambulatorial():
    st.title("Produção Ambulatorial ao Longo dos Anos")

    # Criar figuras
    fig1 = go.Figure()

    # Produção ambulatorial ao longo dos anos
    fig1.add_trace(go.Scatter(x=anos, y=[media_complexidade[str(ano)] for ano in anos], mode='lines+markers', name='Média Complexidade'))
    fig1.add_trace(go.Scatter(x=anos, y=[alta_complexidade[str(ano)] for ano in anos], mode='lines+markers', name='Alta Complexidade'))
    fig1.add_trace(go.Scatter(x=anos, y=[total_ambulatorial[str(ano)] for ano in anos], mode='lines', name='Total de Procedimentos (Média e Alta)', line=dict(dash='dash')))

    fig1.update_layout(
        title='Produção Ambulatorial ao Longo dos Anos',
        xaxis_title='Anos',
        yaxis_title='Quantidade de Procedimentos',
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

    caminho_arquivo = "analise_mac_sia.txt"

    # Lendo o conteúdo do arquivo
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        conteudo = arquivo.read()  # Lê o conteúdo do arquivo

    # Exibindo o conteúdo com st.markdown
    st.markdown(conteudo)

mac_x_producao_ambulatorial()