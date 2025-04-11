import base64
import streamlit as st
import plotly.express as px
import json
import logging

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analise_correlacao.log'),
        logging.StreamHandler()
    ]
)

# --- Funções para cálculo de correlação ---

def pearson_correlation(x, y):
    n = len(x)
    if n != len(y) or n < 2:
        logging.warning(f"Não foi possível calcular a correlação: tamanhos diferentes ou dados insuficientes (mínimo 2 anos). Tamanho x: {len(x)}, Tamanho y: {len(y)}")
        return None

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi**2 for xi in x)
    sum_y2 = sum(yi**2 for yi in y)

    numerator = n * sum_xy - sum_x * sum_y
    denominator = ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))**0.5

    if denominator == 0:
        logging.warning("Denominador zero na correlação de Pearson. Verifique se os dados são constantes.")
        return None

    r = numerator / denominator
    return r

def calculate_correlations(teto_total, valores_sem_incentivo, valores_incentivos, sia_data, sih_data, anos):
    correlations = {}

    # Correlações com dados do MAC
    correlations["Teto Financeiro MAC"] = pearson_correlation(teto_total, list(teto_financeiro_mac.values()))
    correlations["Sem Incentivos"] = pearson_correlation(teto_total, list(valores_sem_incentivo.values()))
    correlations["Incentivos"] = pearson_correlation(teto_total, list(valores_incentivos.values()))

    # Correlações com dados do SIA
    if sia_data:
        correlations["Média Complexidade"] = pearson_correlation(teto_total, [sia_data['media_complexidade'].get(str(ano), 0) for ano in anos])
        correlations["Alta Complexidade"] = pearson_correlation(teto_total, [sia_data['alta_complexidade'].get(str(ano), 0) for ano in anos])
        correlations["Não se Aplica"] = pearson_correlation(teto_total, [sia_data['nao_se_aplica'].get(str(ano), 0) for ano in anos])

        # Verificação antes de calcular a correlação para "Total Ambulatorial"
        if any(sia_data['media_complexidade'].get(str(ano), 0) != 0 for ano in anos) and any(sia_data['alta_complexidade'].get(str(ano), 0) != 0 for ano in anos):
            correlations["Total Ambulatorial"] = pearson_correlation(teto_total, [sia_data['total_ambulatorial'].get(str(ano), 0) for ano in anos])
        else:
            correlations["Total Ambulatorial"] = None

    # Correlações com dados do SIH
    if sih_data:
        correlations["02 Procedimentos com finalidade diagnostica"] = pearson_correlation(teto_total, [sih_data.get("02 Procedimentos com finalidade diagnostica", {}).get(str(ano), 0) for ano in anos])
        correlations["03 Procedimentos clinicos"] = pearson_correlation(teto_total, [sih_data.get("03 Procedimentos clinicos", {}).get(str(ano), 0) for ano in anos])
        correlations["04 Procedimentos cirurgicos"] = pearson_correlation(teto_total, [sih_data.get("04 Procedimentos cirurgicos", {}).get(str(ano), 0) for ano in anos])
        correlations["05 Transplantes de orgaos, tecidos e celulas"] = pearson_correlation(teto_total, [sih_data.get("05 Transplantes de orgaos, tecidos e celulas", {}).get(str(ano), 0) for ano in anos])

    return correlations

# --- Carregamento dos dados ---
with open('SIA.json', 'r', encoding='utf-8') as file:
    dados_sia_json = json.load(file)

with open('SIH.json', 'r', encoding='utf-8') as file:
    dados_sih_json = json.load(file)

with open('evolucao_mac.json', 'r', encoding='utf-8') as file:
    dados_evolucao_mac_json = json.load(file)

# Carregar as análises prontas do JSON
with open('analise_correlacao.json', 'r', encoding='utf-8') as file:
    analise_correlacao = json.load(file)

def capturar_dados_sia(json_data):
    anos_disponiveis = sorted({int(chave) for entrada in json_data for chave in entrada.keys() if chave.isdigit()})
    media_complexidade = dict.fromkeys(map(str, anos_disponiveis), 0)
    alta_complexidade = dict.fromkeys(map(str, anos_disponiveis), 0)
    nao_se_aplica = dict.fromkeys(map(str, anos_disponiveis), 0)
    total_ambulatorial = dict.fromkeys(map(str, anos_disponiveis), 0)

    for entrada in json_data:
        try:
            complexidade = entrada["Complexidade"]
            for ano in anos_disponiveis:
                valor_str = entrada.get(str(ano), "0")
                # Handle "-" before converting to int
                if valor_str == "-":
                    valor_procedimento = 0
                else:
                    valor_procedimento = int(valor_str.replace('.', ''))

                if complexidade in ["Média complexidade", "Alta complexidade", "Não se aplica"]:
                    total_ambulatorial[str(ano)] += valor_procedimento
                    if complexidade == "Média complexidade":
                        media_complexidade[str(ano)] += valor_procedimento
                    elif complexidade == "Alta complexidade":
                        alta_complexidade[str(ano)] += valor_procedimento
                    else:
                        nao_se_aplica[str(ano)] += valor_procedimento
        except KeyError:
            logging.error(f"Erro ao processar entrada: {entrada}")

    return anos_disponiveis, media_complexidade, alta_complexidade, nao_se_aplica, total_ambulatorial

def capturar_dados_sih(json_data, anos):
    grupos = {}
    total_procedimentos = {str(ano): 0 for ano in anos}

    for entrada in json_data:
        grupo = entrada.get("Grupo procedimento", "Outros")
        if grupo not in grupos:
            grupos[grupo] = {str(ano): 0 for ano in anos}

        for ano, valor in entrada.items():
            if ano.isdigit():
                try:
                    valor_formatado = (
                        int(valor.replace('.', '')) if isinstance(valor, str) and valor != "-" else int(valor)
                    )
                    grupos[grupo][ano] += valor_formatado
                    total_procedimentos[ano] += valor_formatado
                except (ValueError, TypeError):
                    logging.warning(f"Valor inválido encontrado para {ano} em {grupo}: {valor}. Tratando como 0.")
                    grupos[grupo][ano] += 0
                    total_procedimentos[ano] += 0

    return grupos, total_procedimentos

def capturar_dados_evolucao_mac(json_data):
    sem_incentivos = {}
    incentivos = {}
    teto_financeiro_mac = {}

    for entrada in json_data:
        for chave, valores in entrada.items():
            for ano, valor_str in valores.items():
                try:
                    valor = float(valor_str) if valor_str != '-' else 0.0
                except ValueError:
                    logging.warning(f"Valor inválido encontrado para {ano} em {chave}: {valor_str}. Tratando como 0.")
                    valor = 0.0

                if chave == "Sem Incentivos":
                    sem_incentivos[ano] = valor
                elif chave == "Incentivos":
                    incentivos[ano] = valor
                elif chave == "Teto Financeiro MAC":
                    teto_financeiro_mac[ano] = valor

    # Repetir o último ano para cada chave, se necessário
    def repetir_ultimo_ano(dados, chave):
        if dados:
            ultimo_ano = max(dados.keys(), key=int)
            ultimo_valor = dados[ultimo_ano]
            proximo_ano = str(int(ultimo_ano) + 1)
            if proximo_ano not in dados:
                dados[proximo_ano] = ultimo_valor
                logging.info(f"Último ano repetido para {chave}: {ultimo_ano} -> {proximo_ano}")
        return dados

    sem_incentivos = repetir_ultimo_ano(sem_incentivos, "Sem Incentivos")
    incentivos = repetir_ultimo_ano(incentivos, "Incentivos")
    teto_financeiro_mac = repetir_ultimo_ano(teto_financeiro_mac, "Teto Financeiro MAC")

    return sem_incentivos, incentivos, teto_financeiro_mac

anos, media_complexidade, alta_complexidade, nao_se_aplica, total_ambulatorial = capturar_dados_sia(dados_sia_json)
grupos, total_procedimentos = capturar_dados_sih(dados_sih_json, anos)
sem_incentivos, incentivos, teto_financeiro_mac = capturar_dados_evolucao_mac(dados_evolucao_mac_json)

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
def correlacao_producao_recursos():
    # Introdução às correlações
    st.title('Correlação entre os Recursos e a Produção')
    st.markdown("""
        As correlações entre os valores recebidos (Teto Total, Valores Sem Incentivo, Valores com Incentivos) e a produção ambulatorial foram calculadas usando o coeficiente de correlação de _Pearson_. Este coeficiente mede a força e a direção da associação linear entre duas variáveis. Valores próximos de 1 ou -1 indicam uma correlação forte, enquanto valores próximos de 0 indicam pouca ou nenhuma correlação.
        """)

    with st.expander('Como foram calculadas as correlações'):
        st.subheader("Exemplo de cálculo")

        st.latex(r'''
        r = \frac{n(\sum xy) - (\sum x)(\sum y)}{\sqrt{[n\sum x^2 - (\sum x)^2][n\sum y^2 - (\sum y)^2]}}
        ''')

        # Explicação dos componentes da fórmula
        st.markdown("Onde:")
        st.latex(r'''
        \begin{align*}
        r & \text{ é o coeficiente de correlação de Pearson} \\
        n & \text{ é o número de pares de valores} \\
        \sum xy & \text{ é a soma do produto de cada par de valores} \\
        \sum x & \text{ é a soma dos valores da variável } x \\
        \sum y & \text{ é a soma dos valores da variável } y \\
        \sum x^2 & \text{ é a soma dos quadrados dos valores da variável } x \\
        \sum y^2 & \text{ é a soma dos quadrados dos valores da variável } y \\
        \end{align*}
        ''')

        # Valores hipotéticos para as variáveis x e y
        x = [10, 20, 30, 40, 50]
        y = [5, 10, 15, 20, 25]

        # Soma dos Produtos
        sum_xy = sum([a * b for a, b in zip(x, y)])

        # Mostrando o cálculo na aplicação Streamlit
        st.markdown("1. **Soma dos Produtos**")
        st.latex(r'''
        \sum xy = (10 \times 5) + (20 \times 10) + (30 \times 15) + (40 \times 20) + (50 \times 25) = 50 + 200 + 450 + 800 + 1250 = 2750
        ''')
        # Somatório das Variáveis
        sum_x = sum(x)
        sum_y = sum(y)

        # Mostrando o cálculo na aplicação Streamlit
        st.markdown("2. **Somatório das Variáveis**")
        st.latex(r'\sum x = 10 + 20 + 30 + 40 + 50 = 150')
        st.latex(r'\sum y = 5 + 10 + 15 + 20 + 25 = 75')

        # Soma dos Quadrados
        sum_x2 = sum([a**2 for a in x])
        sum_y2 = sum([b**2 for b in y])

        # Mostrando o cálculo na aplicação Streamlit
        st.markdown("3. **Soma dos Quadrados**")
        st.latex(r'\sum x^2 = 10^2 + 20^2 + 30^2 + 40^2 + 50^2 = 100 + 400 + 900 + 1600 + 2500 = 5500')
        st.latex(r'\sum y^2 = 5^2 + 10^2 + 15^2 + 20^2 + 25^2 = 25 + 100 + 225 + 400 + 625 = 1375')

        # Número de pares
        n = len(x)

        # Mostrando o cálculo na aplicação Streamlit
        st.markdown("4. **Número de Pares**")
        st.latex(r'n = \text{Número de pares de valores} = 5')

        # Aplicação da Fórmula
        r = (n * sum_xy - sum_x * sum_y) / ((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))**0.5

        # Mostrando o cálculo na aplicação Streamlit
        st.markdown("5. **Aplicação da Fórmula**")
        st.latex(r'''
        r = \frac{n(\sum xy) - (\sum x)(\sum y)}{\sqrt{[n\sum x^2 - (\sum x)^2][n\sum y^2 - (\sum y)^2]}}
        ''')
        st.latex(r'''
        r = \frac{5 \times 2750 - 150 \times 75}{\sqrt{[5 \times 5500 - 150^2][5 \times 1375 - 75^2]}}
        ''')
        st.latex(r'''
        r = \frac{13750 - 11250}{\sqrt{[27500 - 22500][6875 - 5625]}}
        ''')
        st.latex(r'''
        r = \frac{2500}{\sqrt{5000 \times 1250}}
        ''')
        st.latex(r'''
        r = \frac{2500}{2500}
        ''')
        st.latex(r'''
        r = 1
        ''')
        st.write(f"Coeficiente de Correlação de Pearson ( r = {r} )")

    # --- CÁLCULO E EXIBIÇÃO DAS CORRELAÇÕES ---

    # Função para criar gráficos de correlação
    def plot_correlacao(x, y, xlabel, ylabel, title):
        fig = px.scatter(x=x, y=y, trendline='ols', labels={'x': xlabel, 'y': ylabel}, title=title)
        return fig

    # Apresentação das correlações calculadas
    def verificar_e_plotar(teto_total, variavel, nome_variavel, titulo):
        # Verifica se a variável possui dados não nulos
        if variavel and any(valor != 0 for valor in variavel.values()):
            # Verificação específica para "Total Ambulatorial"
            if nome_variavel == "Total Ambulatorial":
                if not media_complexidade or not alta_complexidade:
                    st.warning(f"Não é possível analisar 'Total Ambulatorial' sem dados de 'Média Complexidade' e 'Alta Complexidade'.")
                    return
                elif all(valor == 0 for valor in media_complexidade.values()) or all(valor == 0 for valor in alta_complexidade.values()):
                    st.warning(f"Não é possível analisar 'Total Ambulatorial' se apenas um dos valores ('Média Complexidade' ou 'Alta Complexidade') estiver disponível.")
                    return

            # Alinhar os dados: garantir que x e y tenham o mesmo comprimento
            anos_teto = set(teto_financeiro_mac.keys())
            anos_variavel = set(variavel.keys())
            anos_comuns = sorted(anos_teto.intersection(anos_variavel))

            if not anos_comuns:
                st.warning(f"Não há anos comuns entre 'Teto Total' e '{nome_variavel}'. Não é possível plotar o gráfico.")
                return

            teto_total_alinhado = [teto_financeiro_mac[str(ano)] for ano in anos_comuns]
            variavel_alinhado = [variavel[str(ano)] for ano in anos_comuns]

            st.subheader(titulo)
            fig = plot_correlacao(teto_total_alinhado, variavel_alinhado, 'Teto Total', nome_variavel, titulo)
            st.plotly_chart(fig)
            # Recupera o comentário do arquivo JSON
            analysis_text = analise_correlacao.get(nome_variavel, "Análise não disponível.")
            st.write(analysis_text)

    # Correlações e gráficos

    # Restante das correlações
    verificar_e_plotar(list(teto_financeiro_mac.values()), media_complexidade, 'Média Complexidade', 'Correlação: Teto Total vs Média Complexidade')
    verificar_e_plotar(list(teto_financeiro_mac.values()), alta_complexidade, 'Alta Complexidade', 'Correlação: Teto Total vs Alta Complexidade')
    verificar_e_plotar(list(teto_financeiro_mac.values()), nao_se_aplica, 'Não se Aplica', 'Correlação: Teto Total vs Não se Aplica')
    verificar_e_plotar(list(teto_financeiro_mac.values()), total_ambulatorial, 'Total Ambulatorial', 'Correlação: Teto Total vs Total Ambulatorial')
    verificar_e_plotar(list(teto_financeiro_mac.values()), grupos.get("02 Procedimentos com finalidade diagnostica", {}), '02 Procedimentos com finalidade diagnostica', 'Correlação: Teto Total vs Procedimentos Diagnósticos')
    verificar_e_plotar(list(teto_financeiro_mac.values()), grupos.get("03 Procedimentos clinicos", {}), '03 Procedimentos clinicos', 'Correlação: Teto Total vs Procedimentos Clínicos')
    verificar_e_plotar(list(teto_financeiro_mac.values()), grupos.get("04 Procedimentos cirurgicos", {}), '04 Procedimentos cirurgicos', 'Correlação: Teto Total vs Procedimentos Cirúrgicos')
    verificar_e_plotar(list(teto_financeiro_mac.values()), grupos.get("05 Transplantes de orgaos, tecidos e celulas", {}), '05 Transplantes de orgaos, tecidos e celulas', 'Correlação: Teto Total vs Transplantes de Órgãos')

correlacao_producao_recursos()