import os
import requests
import sys
import time
import pandas as pd
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

# Configuração básica do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evolucao_mac.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def obter_nome_municipio(codigo_ibge):
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{codigo_ibge}"
    response = requests.get(url)
        
    if response.status_code == 200:
        dados = response.json()
        nome_municipio = dados['nome']
        uf = dados['microrregiao']['mesorregiao']['UF']['sigla']
        return f"{nome_municipio}/{uf}"
    else:
        logger.error("Código IBGE não encontrado.")
        return "Código IBGE não encontrado"

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode (no browser window)
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1366, 736)
    return driver

def main(municipio):
    driver = setup_driver()
    wait = WebDriverWait(driver, 30)  # Increased timeout to 30 seconds
    try:
        driver.get("https://sismac.saude.gov.br/teto_financeiro_anual")
        logger.info('Baixando Evolução do Teto MAC...')
        # Esperar até que o link "Município" esteja clicável
        logger.info("Waiting for 'Município' link...")
        municipio_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Município")))
        municipio_link.click()
        logger.info("'Município' link clicked!")

        # Re-locate the element after each interaction
        for _ in range(4):
            filtro_input = wait.until(EC.element_to_be_clickable((By.ID, "filtroPesquisaMunicipio_input")))
            if _ == 0:
                filtro_input.click()
                filtro_input.send_keys(municipio)  # Usando o município informado
            time.sleep(1)
            filtro_input.send_keys(Keys.ENTER)
            time.sleep(1)

        # Esperar até que o dropdown esteja disponível e selecionar a opção desejada
        logger.info("Waiting for dropdown...")
        dropdown = wait.until(EC.presence_of_element_located((By.ID, "tabelaConsolidadaEvolucaoTetoMAC_rppDD")))
        dropdown.find_element(By.XPATH, "//option[. = '80']").click()
        logger.info("Dropdown option '80' selected!")

        # Wait for the table to be fully loaded AFTER dropdown interaction
        logger.info("Waiting for table rows to load...")
        wait.until(EC.presence_of_element_located((By.XPATH, "//tbody[@id='tabelaConsolidadaEvolucaoTetoMAC_data']/tr[@data-ri]")))
        logger.info("Table rows loaded!")

        time.sleep(1)  # Wait for 5 seconds after initial row loading

        # Verifique novamente se as linhas da tabela estão presentes
        rows = driver.find_elements(By.XPATH, "//tbody[@id='tabelaConsolidadaEvolucaoTetoMAC_data']/tr[@data-ri]")
        if not rows:
            logger.warning("No rows found in the table.")
            return
        else:
            logger.info(f"Found {len(rows)} rows.")

        # Ajustar cabeçalhos para corresponder aos dados desejados
        headers = [
            'Referência', 
            'Sem Incentivos', 
            'Incentivos', 
            'Teto Financeiro MAC'
        ]
        logger.debug("Adjusted headers: %s", headers)

        # Extrair dados da tabela
        data = []
        try:
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                row_data = [
                    cols[0].text,  # Referência
                    cols[1].text,  # Sem Incentivos
                    cols[4].text,  # Incentivos
                    cols[7].text   # Teto Financeiro MAC
                ]
                data.append(row_data)
            logger.info("Table data extracted.")
        except Exception as e:
            logger.error(f"Erro ao extrair dados da tabela: {e}")
            return

        # Verificar e imprimir dados extraídos
        logger.debug("Rows data: %s", data)

        # Criar DataFrame do Pandas
        if headers and data:
            df = pd.DataFrame(data, columns=headers)
            logger.info("DataFrame created:")
            logger.info(df)

            # Reformatar os dados para o formato desejado
            reformatted_data = []
            for category in headers[1:]:
                category_data = {category: {}}
                for index, row in df.iterrows():
                    year = row['Referência']
                    value = row[category].replace(".", "").replace(",", ".")
                    category_data[category][year] = value
                reformatted_data.append(category_data)
                
                # Nome do arquivo JSON
                json_filename = 'evolucao_mac.json'

                def carregar_ou_criar_json():
                    """Carrega o arquivo JSON ou cria um novo se ele não existir."""
                    try:
                        # Verifica se o arquivo existe
                        if os.path.exists(json_filename):
                            # Tenta carregar o arquivo JSON
                            with open(json_filename, 'r', encoding='utf-8') as file:
                                return json.load(file)
                        else:
                            # Se o arquivo não existir, cria um novo arquivo JSON com um objeto vazio
                            logger.warning(f"Arquivo {json_filename} não encontrado. Criando um novo arquivo...")
                            with open(json_filename, 'w', encoding='utf-8') as file:
                                json.dump({}, file, ensure_ascii=False, indent=4)
                            return {}
                    except json.JSONDecodeError as e:
                        # Se o arquivo estiver corrompido, cria um novo arquivo JSON válido
                        logger.error(f"Erro ao decodificar o arquivo {json_filename}: {e}")
                        logger.info("Criando um novo arquivo JSON válido...")
                        with open(json_filename, 'w', encoding='utf-8') as file:
                            json.dump({}, file, ensure_ascii=False, indent=4)
                        return {}
                    except Exception as e:
                        # Captura outros erros inesperados
                        logger.error(f"Erro inesperado ao carregar/criar o arquivo JSON: {e}")
                        return {}

                try:
                    # Carrega ou cria o arquivo JSON
                    evolucao_mac_json = carregar_ou_criar_json()
                    logger.info(f"Dados carregados do arquivo {json_filename}.")

                    # Verifica se há dados para salvar
                    if reformatted_data:  # Supondo que `reformatted_data` já foi definido anteriormente
                        # Salvar dados reformatados em JSON
                        try:
                            with open(json_filename, 'w', encoding='utf-8') as file:
                                json.dump(reformatted_data, file, ensure_ascii=False, indent=4)
                            logger.info(f"Dados salvos no arquivo {json_filename}.")
                        except IOError as e:
                            logger.error(f"Falha ao salvar dados no arquivo JSON: {e}")
                    else:
                        logger.warning("Nenhum dado extraído para criar o DataFrame.")

                except (TimeoutException, StaleElementReferenceException) as e:
                    logger.error(f"Erro durante a extração de dados: {e}")
                except Exception as e:
                    logger.error(f"Erro inesperado: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    municipio_ibge = sys.argv[1]
    municipio = obter_nome_municipio(municipio_ibge)
    if municipio != "Código IBGE não encontrado":
        main(municipio)
    else:
        logger.error("Código IBGE não encontrado.")