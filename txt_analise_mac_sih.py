import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import sys

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Função para ler arquivo JSON
def ler_dados_json(caminho):
    """Lê dados de um arquivo JSON com codificação UTF-8 e retorna uma lista de dicionários."""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            if not isinstance(dados, list) and not isinstance(dados, dict):
                raise TypeError("O arquivo JSON deve conter uma lista ou um dicionário.")
            return dados
    except FileNotFoundError:
        logging.error(f"Arquivo não encontrado: {caminho}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar o JSON: {caminho}")
        return None
    except TypeError as e:
        logging.error(e)
        return None

# Lê os arquivos JSON
evolucao_mac = ler_dados_json('evolucao_mac.json')
sih = ler_dados_json('SIH.json')

# Verifica se os dados foram carregados corretamente
if evolucao_mac is None or sih is None:
    logging.error("Erro ao carregar os arquivos JSON. Encerrando a execução.")
    exit()

# Verifica se os dados são listas
if not isinstance(evolucao_mac, list) or not isinstance(sih, list):
    logging.error("Os dados carregados devem ser listas.")
    exit()

# --- Configuração do Modelo Gemini ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY is None:
    logging.error("Variável de ambiente GOOGLE_API_KEY não encontrada. Certifique-se de que o arquivo .env está configurado corretamente.")
    exit()

genai.configure(api_key=GOOGLE_API_KEY)

generation_config = {
  "temperature": 0.2,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
)

# --- Função para gerar o Markdown completo da análise ---
def gerar_markdown_analise(municipio, analise_correlacao, conclusao):
    """Gera o Markdown completo da análise."""
    markdown_completo = f"""
    # Análise de Correlação entre Produção Hospitalar (SIH) e Teto Financeiro MAC para {municipio}

    ## Análise de Correlação
    {analise_correlacao}

    ## Conclusão
    {conclusao}
    """
    return markdown_completo

def main(municipio):
    # --- Prompt para Análise de Correlação ---
    prompt_analise_correlacao = f"""
    ## Análise de Correlação entre Produção Hospitalar (SIH) e Teto Financeiro MAC para {municipio}

    Você é um assistente de análise de dados na área da saúde pública. Sua tarefa é analisar a correlação entre a produção hospitalar, representada pelos dados do SIH, e o Teto Financeiro MAC para o município de {municipio}.

    ## Objetivo:

    Identificar a relação entre a variação do Teto Financeiro MAC e a quantidade de procedimentos hospitalares realizados, por grupo de procedimento, conforme os dados do SIH, **de forma a evidenciar a necessidade de ampliação do Teto MAC, mesmo considerando as limitações dos dados disponíveis.**

    ## Instruções:

    - Gere uma **análise de correlação** entre a produção hospitalar (SIH) e o Teto Financeiro MAC, em formato **Markdown**.
    - **Divida a análise em SEÇÕES CLARAMENTE SEPARADAS POR PARÁGRAFOS DISTINTOS. CADA PARÁGRAFO DEVE TRATAR DE UM ASPECTO ESPECÍFICO DA ANÁLISE. USE SUBTÍTULOS (EM NÍVEL H2 OU H3) PARA ORGANIZAR AS SEÇÕES: "Evolução do Teto MAC e da Produção Hospitalar", "Correlação e Complexidade do Sistema", "Necessidade de Ampliação do Teto MAC" e "Eficiência na Gestão dos Recursos".**
    - Analise os dados do SIH e do Teto MAC para identificar padrões ou tendências, **enfatizando aspectos que indiquem a importância do aumento do Teto MAC para o atendimento das demandas de saúde do município.**
    - Reconheça que a correlação pode não ser linear ou proporcional, mas **interprete essa não linearidade como uma evidência da complexidade do sistema de saúde e da necessidade de um financiamento robusto para atender às demandas variáveis.**
    - Mencione que outros fatores podem influenciar a produção hospitalar, mas **sugira que um Teto MAC maior pode oferecer a flexibilidade necessária para lidar com essas variáveis.**
    - Não cite os arquivos, mas use seus dados para a análise.
    - Sua missão é gerar a **análise de correlação**, em **Markdown**, para ser inserida posteriormente em um documento.
    - **Utilize formatação Markdown para melhorar a legibilidade do texto (negrito, itálico, etc.).**
    - **Quando for se referir a valores monetários, use sempre R\\$ e não R$ para evitar erros de formatação.**
    - **Cite números e dados específicos da análise para embasar os argumentos. Mencione a variação percentual do Teto MAC e da produção hospitalar em determinados períodos.**
    - **Explore os fatores que contribuem para a complexidade do sistema de saúde, como o envelhecimento da população, o aumento da prevalência de doenças crônicas e a incorporação de novas tecnologias.**
    - **Mencione a importância da eficiência na gestão dos recursos, como forma de otimizar o uso do financiamento disponível.**
    - :red[**Use destaques e cores:**] :blue[Colored text and background colors for text, using the syntax :color[text to be colored] and :color-background[text to be colored], respectively.] :green[color must be replaced with any of the following supported colors: blue, green, orange, red, violet, gray/grey, rainbow, or primary.] :violet[For example, you can use :orange[your text here] or :blue-background[your text here].] :gray[If you use "primary" for color, Streamlit will use the default primary accent color unless you set the theme.primaryColor configuration option.]

    ## Dados:

    **Evolução do Teto MAC:**
    ```json
    {json.dumps(evolucao_mac, ensure_ascii=False)}
    ```

    **Produção hospitalar (SIH):**
    ```json
    {json.dumps(sih, ensure_ascii=False)}
    ```

    Gere a análise, em Markdown, com parágrafos e justificada, conforme as instruções acima.
    """

    # --- Prompt para a Conclusão ---
    prompt_conclusao = f"""
    ## Conclusão

    Com base na análise de correlação entre o Teto MAC e a produção hospitalar (SIH), elabore uma conclusão que sintetize os principais achados e suas implicações para o planejamento e gestão de recursos em saúde para o município de {municipio}, reforçando a necessidade de aumento do Teto MAC.

    ## Objetivo:
    Concluir o documento de forma a justificar um pleito para solicitação de ajuste do teto MAC para o ano seguinte, enfatizando que, apesar das limitações dos dados e da complexidade do sistema, um financiamento maior é crucial.

    ## Instruções:
    - Gere uma conclusão para a análise de correlação entre a produção hospitalar (SIH) e o Teto Financeiro MAC, em formato Markdown.
    - **Divida a conclusão em parágrafos, utilizando subtítulos para organizar as seções.**
    - Sintetize os principais achados da análise e suas implicações para o planejamento e gestão de recursos em saúde para o município de {municipio}, reforçando a necessidade de aumento do Teto MAC.
    - Reconheça que a correlação pode não ser linear ou proporcional, mas interprete essa não linearidade como uma evidência da complexidade do sistema de saúde e da necessidade de um financiamento robusto para atender às demandas variáveis.
    - Mencione que outros fatores podem influenciar a produção hospitalar, mas sugira que um Teto MAC maior pode oferecer a flexibilidade necessária para lidar com essas variáveis.
    - Não cite os arquivos, mas use seus dados para a análise.
    - Sua missão é gerar a conclusão, em Markdown, para ser inserida posteriormente em um documento.
    - **Utilize formatação Markdown para melhorar a legibilidade do texto (negrito, itálico, etc.).**
    - **Quando for se referir a valores monetários, use sempre R\\$ e não R$ para evitar erros de formatação.**
    - **Cite números e dados específicos da análise para embasar os argumentos. Mencione a variação percentual do Teto MAC e da produção hospitalar em determinados períodos.**
    - **Explore os fatores que contribuem para a complexidade do sistema de saúde, como o envelhecimento da população, o aumento da prevalência de doenças crônicas e a incorporação de novas tecnologias.**
    - **Mencione a importância da eficiência na gestão dos recursos, como forma de otimizar o uso do financiamento disponível.**
    - :red[**Use destaques e cores:**] :blue[Colored text and background colors for text, using the syntax :color[text to be colored] and :color-background[text to be colored], respectively.] :green[color must be replaced with any of the following supported colors: blue, green, orange, red, violet, gray/grey, rainbow, or primary.] :violet[For example, you can use :orange[your text here] or :blue-background[your text here].] :gray[If you use "primary" for color, Streamlit will use the default primary accent color unless you set the theme.primaryColor configuration option.]

    ## Dados:

    **Evolução do Teto MAC:**
    ```json
    {json.dumps(evolucao_mac, ensure_ascii=False)}
    ```

    **Produção Hospitalar (SIH):**
    ```json
    {json.dumps(sih, ensure_ascii=False)}
    ```

    Gere a conclusão, em Markdown, com parágrafos e justificada, conforme as instruções acima.
    """
    
    # --- Execução da Análise de Correlação ---
    logging.info("Iniciando a análise de correlação com o Gemini 1.5 flash...")
    response_correlacao = model.generate_content(prompt_analise_correlacao)
    analise_correlacao_texto = response_correlacao.text
    logging.info("Análise de correlação concluída.")

    # --- Execução da Conclusão ---
    logging.info("Iniciando a geração da conclusão com o Gemini 1.5 flash...")
    response_conclusao = model.generate_content(prompt_conclusao)
    conclusao_texto = response_conclusao.text
    logging.info("Conclusão gerada.")

    # --- Gerar o Markdown completo da análise ---
    markdown_completo = gerar_markdown_analise(municipio, analise_correlacao_texto, conclusao_texto)

    # --- Salvar o Resultado em um Arquivo Markdown ---
    nome_arquivo_saida = f'analise_mac_sih.txt'
    try:
        with open(nome_arquivo_saida, 'w', encoding='utf-8') as f:
            f.write(markdown_completo)
        logging.info(f"Análise salva em {nome_arquivo_saida}")
    except IOError as e:
        logging.error(f"Erro ao salvar o arquivo: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Por favor, forneça o nome do município como argumento.")
        exit()
    municipio = sys.argv[1]
    main(municipio)