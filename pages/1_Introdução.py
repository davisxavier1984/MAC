import json
import base64
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards
import logging
from babel.numbers import format_currency, format_decimal

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def carregar_dados(caminho_arquivo):
    """Carrega dados de um arquivo JSON."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON no arquivo: {caminho_arquivo}")
        return {}

def extrair_codigo_ibge(dados_economicos):
    """Extrai o código IBGE da primeira chave do dicionário de dados econômicos."""
    if dados_economicos and isinstance(dados_economicos, dict):
        return next(iter(dados_economicos.keys()), None)
    return None

def criar_dataframe_populacao(dados_populacao):
    """Cria um DataFrame pandas a partir dos dados de população."""
    df = pd.DataFrame.from_dict(dados_populacao, orient='index')
    df.index.name = 'Faixa Etária'
    return df

def obter_dados_economicos(dados_economicos, codigo_ibge):
    """Retorna os dados econômicos para um código IBGE específico."""
    return dados_economicos.get(codigo_ibge)

def grafico_piramide_etaria(df_populacao):
    """Gera um gráfico de pirâmide etária usando plotly."""
    y = df_populacao.index
    x_men = df_populacao['Homens'] * -1
    x_women = df_populacao['Mulheres']

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=y,
        x=x_men,
        name='Homens',
        orientation='h',
        marker=dict(color='#6C9BCF')  # Azul suave
    ))

    fig.add_trace(go.Bar(
        y=y,
        x=x_women,
        name='Mulheres',
        orientation='h',
        marker=dict(color='#E88BB3')  # Rosa suave
    ))

    fig.update_layout(
        title='Pirâmide Etária',
        title_x=0.5,
        yaxis_title='Faixa Etária',
        xaxis_title='População',
        barmode='relative',
        bargap=0.0,
        bargroupgap=0,
        xaxis=dict(
            tickvals=[-100000, -75000, -50000, -25000, 0, 25000, 50000, 75000, 100000],
            ticktext=['100 mil', '75 mil', '50 mil', '25 mil', '0', '25 mil', '50 mil', '75 mil', '100 mil'],
            tickformat=',.0f'
        ),
        plot_bgcolor='#FFFFFF',  # Fundo branco
        paper_bgcolor='#FFFFFF'  # Fundo branco
    )

    return fig

def grafico_populacao_total(df):
    """Cria um gráfico de barras da população total por faixa etária."""
    fig = go.Figure(go.Bar(
        x=df.index,
        y=df['Total'],
        marker_color='#7FB77E'  # Verde suave
    ))
    fig.update_layout(title='População Total por Faixa Etária',
                      xaxis_title='Faixa Etária',
                      yaxis_title='População Total',
                      plot_bgcolor='#FFFFFF',  # Fundo branco
                      paper_bgcolor='#FFFFFF')  # Fundo branco
    return fig

def exibir_dados_economicos(dados_eco_municipio):
    """Exibe os dados econômicos de forma mais amigável usando metric cards."""
    st.subheader(":bar_chart: Dados Econômicos")

    # Cores para os cards
    cores = ["#6C9BCF", "#E88BB3", "#7FB77E", "#FFB6B9", "#A8D8EA", "#FFD3B6", "#B6E880", "#FF97FF", "#FECB52"]

    # Indicadores em destaque
    col1, col2, col3 = st.columns(3)

    # Card 1: População Residente
    with col1:
        populacao_residente = dados_eco_municipio.get("populacao_area_densidade", {}).get("populacao_residente", "N/A")
        if populacao_residente != "N/A":
            populacao_residente = format_decimal(populacao_residente, format="#,###", locale='pt_BR')
        st.markdown(f"""
            <div style='background-color: #FFF; border-left: 0.5rem solid {cores[0]}; padding: 15px; border-radius: 5px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);'>
                <p style='font-weight: bold; font-size: 1rem; color: #495057;'>👥 População Residente</p>
                <p style='font-size: 1.2rem; font-weight: bold; color: #262730;'>{populacao_residente}</p>
            </div>
        """, unsafe_allow_html=True)

    # Card 2: Taxa de Alfabetização
    with col2:
        taxa_alfabetizacao = dados_eco_municipio.get("taxa_alfabetizacao", {}).get("taxa_alfabetizacao_15_anos_ou_mais", "N/A")
        if taxa_alfabetizacao != "N/A":
            taxa_alfabetizacao = format_decimal(taxa_alfabetizacao, format="#,##0.00", locale='pt_BR')
        st.markdown(f"""
            <div style='background-color: #FFF; border-left: 0.5rem solid {cores[1]}; padding: 15px; border-radius: 5px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);'>
                <p style='font-weight: bold; font-size: 1rem; color: #495057;'>📚 Taxa de Alfabetização (15 anos ou mais)</p>
                <p style='font-size: 1.2rem; font-weight: bold; color: #262730;'>{taxa_alfabetizacao}%</p>
            </div>
        """, unsafe_allow_html=True)

    # Card 3: Rendimento Médio Mensal
    with col3:
        rendimento_medio = dados_eco_municipio.get("rendimento_medio", {}).get("rendimento_medio_mensal_real", "N/A")
        if rendimento_medio != "N/A":
            rendimento_medio = format_currency(rendimento_medio, 'BRL', locale='pt_BR')
        st.markdown(f"""
            <div style='background-color: #FFF; border-left: 0.5rem solid {cores[2]}; padding: 15px; border-radius: 5px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);'>
                <p style='font-weight: bold; font-size: 1rem; color: #495057;'>💰 Rendimento Médio Mensal</p>
                <p style='font-size: 1.2rem; font-weight: bold; color: #262730;'>{rendimento_medio}</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Outros dados econômicos em cards
    st.subheader("🏠 Domicílios")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_domicilios = dados_eco_municipio.get("domicilios_especie", {}).get("total", "N/A")
        if total_domicilios != "N/A":
            total_domicilios = format_decimal(total_domicilios, format="#,###", locale='pt_BR')
        st.markdown(f"""
            <div style='background-color: #FFF; border-left: 0.5rem solid {cores[3]}; padding: 15px; border-radius: 5px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);'>
                <p style='font-weight: bold; font-size: 1rem; color: #495057;'>Total de Domicílios</p>
                <p style='font-size: 1.2rem; font-weight: bold; color: #262730;'>{total_domicilios}</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        domicilios_ocupados = dados_eco_municipio.get("domicilios_moradores", {}).get("domicilios_particulares_permanentes_ocupados", "N/A")
        if domicilios_ocupados != "N/A":
            domicilios_ocupados = format_decimal(domicilios_ocupados, format="#,###", locale='pt_BR')
        st.markdown(f"""
            <div style='background-color: #FFF; border-left: 0.5rem solid {cores[4]}; padding: 15px; border-radius: 5px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);'>
                <p style='font-weight: bold; font-size: 1rem; color: #495057;'>Domicílios Ocupados</p>
                <p style='font-size: 1.2rem; font-weight: bold; color: #262730;'>{domicilios_ocupados}</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        media_moradores = dados_eco_municipio.get("domicilios_moradores", {}).get("media_de_moradores_em_domicilios_particulares_permanentes_ocupados", "N/A")
        if media_moradores != "N/A":
            media_moradores = format_decimal(media_moradores, format="#,##0.0", locale='pt_BR')
        st.markdown(f"""
            <div style='background-color: #FFF; border-left: 0.5rem solid {cores[5]}; padding: 15px; border-radius: 5px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);'>
                <p style='font-weight: bold; font-size: 1rem; color: #495057;'>Média de Moradores</p>
                <p style='font-size: 1.2rem; font-weight: bold; color: #262730;'>{media_moradores}</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.subheader("🗺️ Área e Densidade")
    col1, col2 = st.columns(2)
    with col1:
        area_territorial = dados_eco_municipio.get("populacao_area_densidade", {}).get("area_da_unidade_territorial", "N/A")
        if area_territorial != "N/A":
            area_territorial = format_decimal(area_territorial, format="#,##0.000", locale='pt_BR')
        st.markdown(f"""
            <div style='background-color: #FFF; border-left: 0.5rem solid {cores[6]}; padding: 15px; border-radius: 5px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);'>
                <p style='font-weight: bold; font-size: 1rem; color: #495057;'>Área da Unidade Territorial</p>
                <p style='font-size: 1.2rem; font-weight: bold; color: #262730;'>{area_territorial} km²</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        densidade_demografica = dados_eco_municipio.get("populacao_area_densidade", {}).get("densidade_demografica", "N/A")
        if densidade_demografica != "N/A":
            densidade_demografica = format_decimal(densidade_demografica, format="#,##0.0", locale='pt_BR')
        st.markdown(f"""
            <div style='background-color: #FFF; border-left: 0.5rem solid {cores[7]}; padding: 15px; border-radius: 5px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);'>
                <p style='font-weight: bold; font-size: 1rem; color: #495057;'>Densidade Demográfica</p>
                <p style='font-size: 1.2rem; font-weight: bold; color: #262730;'>{densidade_demografica} hab/km²</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

def exibir_analise_demografica(dados_eco_municipio, codigo_ibge, df_populacao):
    """Exibe a análise do Gemini dividida em seções."""
    analise_gemini = dados_eco_municipio.get(codigo_ibge, {}).get("analise_gemini")
    if not analise_gemini:
        st.write("Análise não disponível para este município.")
        return

    st.markdown("### Introdução")
    st.markdown(analise_gemini.get("introducao", "Introdução não disponível."))

    # Gráfico de Pirâmide Etária
    st.markdown("### Pirâmide Etária")
    st.write(
        """
        A pirâmide etária é uma representação gráfica da distribuição da população por idade e sexo.
        Ela nos permite visualizar a estrutura etária de uma população e entender tendências demográficas.
        """
    )
    st.plotly_chart(grafico_piramide_etaria(df_populacao))

    st.markdown(analise_gemini.get("analise_piramide_etaria", "Análise da pirâmide etária não disponível."))

    # Gráfico de População Total por Faixa Etária
    st.markdown("### População Total por Faixa Etária")
    st.write(
        """
        Este gráfico mostra a população total para cada faixa etária, independentemente do sexo.
        Ele complementa a pirâmide etária, fornecendo uma visão geral da distribuição etária da população.
        """
    )
    st.plotly_chart(grafico_populacao_total(df_populacao))

    st.markdown(analise_gemini.get("analise_populacao_faixa_etaria", "Análise da população por faixa etária não disponível."))

    st.markdown(analise_gemini.get("conclusao", "Conclusão não disponível."))

def main():
    # Definindo as cores principais
    st.markdown("""
    <style>
    body {
        color: #495057;
        background-color: #FFFFFF;
    }
    .sidebar .sidebar-content {
        background-color: #343a40;
        color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

    # Carrega os dados
    try:
        dados_populacao = carregar_dados('tabela_populacao_completa.json')
        dados_economicos = carregar_dados('dados_economicos.json')
    except FileNotFoundError as e:
        logger.error(f"Erro ao carregar os dados: {e}")
        st.error("Erro ao carregar os arquivos de dados. Verifique se os arquivos 'tabela_populacao_completa.json' e 'dados_economicos.json' existem e estão no formato correto.")
        return

    # Extrai o código IBGE da primeira chave do dicionário de dados econômicos
    codigo_ibge = extrair_codigo_ibge(dados_economicos)
    if not codigo_ibge:
        st.error("Não foi possível extrair o código IBGE dos dados econômicos.")
        return

    # Obtém os dados econômicos
    dados_eco_municipio = obter_dados_economicos(dados_economicos, codigo_ibge)

    if dados_eco_municipio:
        # Exibe o nome do município
        nome_municipio = dados_eco_municipio.get('nome_municipio', 'Nome do Município Não Encontrado')
        
        # Dicionário que mapeia os dois primeiros dígitos do código IBGE para as siglas das UFs
        uf_por_codigo = {
            '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA',
            '16': 'AP', '17': 'TO', '21': 'MA', '22': 'PI', '23': 'CE',
            '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE',
            '29': 'BA', '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
            '41': 'PR', '42': 'SC', '43': 'RS', '50': 'MS', '51': 'MT',
            '52': 'GO', '53': 'DF'
        }

        # Extrai os dois primeiros dígitos do código IBGE
        codigo_uf = codigo_ibge[:2]

        # Obtém a sigla da UF usando o dicionário
        uf = uf_por_codigo.get(codigo_uf, 'UF desconhecida')
        
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
        
        st.title(f"Análise Populacional e Econômica: {nome_municipio} - {uf}")
                
        # Exibe os dados econômicos de forma amigável
        exibir_dados_economicos(dados_eco_municipio)

        st.header("Dados Populacionais")
        # Cria o DataFrame de população
        df_populacao = criar_dataframe_populacao(dados_populacao)

        # Exibe a tabela de população
        st.markdown("### Tabela de População por Faixa Etária e Gênero")
        st.dataframe(df_populacao)

        # Exibe a análise do Gemini dividida em seções
        st.header("Análise Demográfica e Econômica")
        exibir_analise_demografica(dados_economicos, codigo_ibge, df_populacao)  # Passando df_populacao
    else:
        st.error(f"Dados não encontrados para o código IBGE: {codigo_ibge}")

if __name__ == "__main__":
    main()