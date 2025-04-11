import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import json
from babel.numbers import format_currency

# Função para carregar dados do JSON
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Carregar dados dos arquivos JSON
evolucao_mac = load_json('evolucao_mac.json')
dados_economicos = load_json('dados_economicos.json')

# Extrair dados do JSON
sem_incentivos = evolucao_mac[0]["Sem Incentivos"]
incentivos = evolucao_mac[1]["Incentivos"]
teto_financeiro = evolucao_mac[2]["Teto Financeiro MAC"]

# Obter anos e valores
anos = list(map(int, teto_financeiro.keys()))
valores_sem_incentivos = list(map(float, sem_incentivos.values()))
valores_incentivos = list(map(float, incentivos.values()))
valores_teto_total = list(map(float, teto_financeiro.values()))

# Criar dicionário de dados
dados_mac = {
    'Ano': anos,
    'Sem Incentivos (R$)': valores_sem_incentivos,
    'Incentivos (R$)': valores_incentivos,
    'Teto Total (R$)': valores_teto_total
}

# Identificar o último ano disponível
ultimo_ano = max(anos)

# Calcular o aumento de 15% para cada valor no próximo ano
valor_teto_ultimo_ano = dados_mac['Teto Total (R$)'][-1]
valor_sem_incentivos_ultimo_ano = dados_mac['Sem Incentivos (R$)'][-1]
valor_incentivos_ultimo_ano = dados_mac['Incentivos (R$)'][-1]

# Aplicar aumento de 15% a cada valor
aumento_teto = valor_teto_ultimo_ano * 0.25
aumento_sem_incentivos = valor_sem_incentivos_ultimo_ano * 0.25
aumento_incentivos = valor_incentivos_ultimo_ano * 0.25

# Valores projetados para o próximo ano
proximo_ano = ultimo_ano + 1
valor_teto_proximo_ano = valor_teto_ultimo_ano + aumento_teto
valor_sem_incentivos_proximo_ano = valor_sem_incentivos_ultimo_ano + aumento_sem_incentivos
valor_incentivos_proximo_ano = valor_incentivos_ultimo_ano + aumento_incentivos

# Adicionar previsão para o próximo ano
dados_mac['Ano'].append(proximo_ano)
dados_mac['Sem Incentivos (R$)'].append(valor_sem_incentivos_proximo_ano)
dados_mac['Incentivos (R$)'].append(valor_incentivos_proximo_ano)
dados_mac['Teto Total (R$)'].append(valor_teto_proximo_ano)

# Criar DataFrame
df = pd.DataFrame(dados_mac)

# Função para estilizar métricas com IDs únicos
def style_metric_card(
    element_id: str,
    background_color: str = "#FFF",
    border_size_px: int = 1,
    border_color: str = "#CCC",
    border_radius_px: int = 5,
    border_left_color: str = "red",
    box_shadow: bool = True,
) -> None:
    box_shadow_str = (
        "box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;"
        if box_shadow
        else "box-shadow: none !important;"
    )
    st.markdown(
        f"""
        <style>
            #{element_id} {{
                background-color: {background_color};
                border: {border_size_px}px solid {border_color};
                padding: 15px;
                border-radius: {border_radius_px}px;
                border-left: 0.5rem solid {border_left_color} !important;
                {box_shadow_str}
            }}
            #{element_id} .metric-label {{
                font-weight: bold;
                font-size: 1rem;
            }}
            #{element_id} .metric-value {{
                font-size: 1.2rem;
                font-weight: bold;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Calcular valores e formatar
recurso_atual_anual = format_currency(dados_mac['Teto Total (R$)'][-2], 'BRL', locale='pt_BR')  # Valor do último ano disponível
potencial_aumento_anual = format_currency(aumento_teto, 'BRL', locale='pt_BR')
soma_total = format_currency(valor_teto_proximo_ano, 'BRL', locale='pt_BR')

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

def obter_uf_por_ibge(codigo_ibge):
    """Retorna a UF com base nos dois primeiros dígitos do código IBGE."""
    uf_codigo = str(codigo_ibge)[:2]
    uf_map = {
        "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
        "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
        "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
        "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
        "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
        "52": "GO", "53": "DF"
    }
    return uf_map.get(uf_codigo, "UF desconhecida")

# Nome do município e UF
try:
    codigo_ibge = list(dados_economicos.keys())[0]  # Pega o primeiro código IBGE disponível
    uf = obter_uf_por_ibge(codigo_ibge)
    nome_municipio = dados_economicos[codigo_ibge]['nome_municipio']
except (KeyError, IndexError):
    nome_municipio = "Município Desconhecido"  # Valor padrão caso a chave não exista

st.title(f"Análise do Teto MAC - {nome_municipio} - {uf}")

# Placas de identificação do recurso atual e potenciais aumentos no início da página
st.subheader("Recurso Atual e Potencial de Aumento (MAC)")

col1, col2, col3 = st.columns(3)

# Card 1: Recurso Atual Anual
with col1:
    metric_id = "metric-red"
    st.markdown(
        f"""
        <div id="{metric_id}">
            <div class="metric-label">Teto MAC Atual</div>
            <div class="metric-value">{recurso_atual_anual}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    style_metric_card(element_id=metric_id, border_left_color="red")

# Card 2: Potencial de Aumento Anual
with col2:
    metric_id = "metric-yellow"
    st.markdown(
        f"""
        <div id="{metric_id}">
            <div class="metric-label">Potencial de Aumento</div>
            <div class="metric-value">{potencial_aumento_anual}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    style_metric_card(element_id=metric_id, border_left_color="yellow")

# Card 3: Soma dos Dois Anteriores
with col3:
    metric_id = "metric-green"
    st.markdown(
        f"""
        <div id="{metric_id}">
            <div class="metric-label">Novo Teto MAC</div>
            <div class="metric-value">{soma_total}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    style_metric_card(element_id=metric_id, border_left_color="green")

# Gráfico da evolução do teto MAC
fig1 = px.line(df, x='Ano', y=['Teto Total (R$)', 'Sem Incentivos (R$)', 'Incentivos (R$)'],
               title=f"Evolução do Teto MAC em {nome_municipio} - {uf} ({min(anos)}-{proximo_ano})")

# Destaque para projeção do último ano para o próximo ano
fig1.add_trace(go.Scatter(x=[ultimo_ano, proximo_ano], y=[dados_mac['Teto Total (R$)'][-2], dados_mac['Teto Total (R$)'][-1]],
                          mode='lines+markers+text',
                          name='Projeção',
                          line=dict(color='blue', width=4, dash='dash'),  # Linha tracejada
                          text=[str(ultimo_ano), str(proximo_ano)],
                          textposition="top center"))

st.plotly_chart(fig1)

# Fonte dos dados
st.markdown("Fonte: Sismac/MS")