import tkinter as tk
from tkinter import ttk
import threading
import queue
import subprocess
import logging
import requests
import json
import os
import sys

# Configuração básica do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('executa_scripts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Executa o script que baixa ou gera o arquivo evolucao_mac.json
subprocess.run(['python', 'evolucao_mac.py'])

# Fila para enviar atualizações de status
status_queue = queue.Queue()

# Função para obter municípios por UF
def obter_municipios_por_uf(uf):
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
    response = requests.get(url)

    if response.status_code == 200:
        dados = response.json()
        municipios = [municipio['nome'] for municipio in dados]
        return municipios
    else:
        logger.error(f"Erro ao obter municípios para a UF {uf}. Código de status: {response.status_code}")
        return []

# Função para obter o código IBGE de um município
def obter_codigo_ibge(nome_municipio, uf):
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
    response = requests.get(url)

    if response.status_code == 200:
        dados = response.json()
        for municipio in dados:
            if municipio['nome'].lower() == nome_municipio.lower():
                return municipio['id']
        logger.warning(f"Município {nome_municipio} não encontrado na UF {uf}.")
        return None
    else:
        logger.error(f"Erro ao obter código IBGE para o município {nome_municipio}. Código de status: {response.status_code}")
        return None

# Função para executar um script
def run_script(script_name, *params):
    script_mapping = {
        "analise_teto_mac": "analise_teto_mac.py",
        "BaixaSIA": "BaixaSIA.py",
        "BaixaSIH": "BaixaSIH.py",
        "evolucao_mac": "evolucao_mac.py",
        "evolucao_mac2": "evolucao_mac2.py",
        "MacUF": "MacUF.py",
        "Econo": "/home/davi/Python-Projetos/MAC/IBGE/economia.py",
        "Faixa": "/home/davi/Python-Projetos/MAC/IBGE/faixa_etaria.py",
        "Resumo_PT": "/home/davi/Python-Projetos/MAC/res_pt.py",
        "Analise MAC": "/home/davi/Python-Projetos/MAC/txt_analise_mac.py",
        "Analise MAC_SIH": "/home/davi/Python-Projetos/MAC/txt_analise_mac_sih.py",
        "Analise MAC_SIA": "/home/davi/Python-Projetos/MAC/txt_analise_mac_sia.py",
        "Analise Correlações": "/home/davi/Python-Projetos/MAC/analise_correlacao.py",
        "Conclusão": "/home/davi/Python-Projetos/MAC/conclusao.py",
    }
    script_path = script_mapping.get(script_name)

    if script_path:
        try:
            # Convert params to strings
            params = [str(param) for param in params]
            logger.info(f"Executando script {script_name} com parâmetros: {params}")
            status_queue.put((script_name, "Executando..."))  # Envia atualização de status
            # Executa o script
            subprocess.run(["python", script_path, *params], check=True)
            logger.info(f"Script {script_name} executado com sucesso!")
            status_queue.put((script_name, "Concluído"))  # Envia atualização de status

        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar o script {script_name}.")
            logger.error(f"Código de retorno: {e.returncode}")
            if e.output:
                logger.error(f"Saída:\n{e.output.decode()}")
            if e.stderr:
                logger.error(f"Erro padrão:\n{e.stderr.decode()}")
            status_queue.put((script_name, "Erro"))  # Envia atualização de status

    else:
        logger.error(f"Script {script_name} não encontrado.")
        status_queue.put((script_name, "Erro"))  # Envia atualização de status

# Função principal para executar todos os scripts
def executar_scripts(nome_municipio, uf, status_dict):
    logger.info(f"Iniciando execução de scripts para o município {nome_municipio}/{uf}...")
    codigo_ibge = obter_codigo_ibge(nome_municipio, uf)

    if not codigo_ibge:
        logger.error(f"Não foi possível encontrar o município {nome_municipio}/{uf}.")
        status_queue.put(("Erro", f"Não foi possível encontrar o município {nome_municipio}/{uf}."))
        return

    # Obtendo range de anos da evolução do MAC
    with open('evolucao_mac.json', 'r', encoding='utf-8') as file:
        evolucao_mac_json = json.load(file)

    # Função para obter os parâmetros
    def obter_params(json_data):
        anos = set()
        for item in json_data:
            for key, value in item.items():
                anos.update(value.keys())

        start_year = min(anos)
        end_year = str(int(max(anos)) + 1)
        start_month = 1  # Janeiro
        end_month = 12   # Dezembro

        return [start_year, start_month, end_year, str(end_month)]

    # Executa todos os scripts
    run_script("evolucao_mac", str(codigo_ibge))
    run_script("evolucao_mac2", str(codigo_ibge))
    params = [*obter_params(evolucao_mac_json), str(codigo_ibge)]
    logger.debug(f"Parâmetros obtidos: {params}")
    run_script("MacUF", str(codigo_ibge))
    run_script("analise_teto_mac", str(codigo_ibge))
    run_script("BaixaSIA", *params)
    run_script("BaixaSIH", *params)
    run_script("Faixa", str(codigo_ibge))
    run_script("Econo", str(codigo_ibge), nome_municipio)
    run_script("Resumo_PT")
    run_script("Analise MAC", nome_municipio)
    run_script("Analise MAC_SIH", nome_municipio)
    run_script("Analise MAC_SIA", nome_municipio)
    run_script("Analise Correlações")
    run_script("Conclusão")

    # Sinaliza o fim da execução de todos os scripts
    status_queue.put(("Fim", "Todos os scripts foram executados."))

# Função para atualizar o status na interface
def atualizar_status():
    while True:  # Loop infinito para monitorar a fila continuamente
        try:
            script_name, status = status_queue.get(timeout=1)  # Timeout para não travar o loop

            if script_name == "Fim":
                # Verifica se todos os scripts foram executados com sucesso
                if all(status == "Concluído" for status in status_dict.values()):
                    logger.info("Todos os scripts foram executados com sucesso!")
                    status_queue.put(("Sucesso", "Todos os scripts foram executados com sucesso!"))

                    # Fecha a janela do Tkinter
                    root.after(0, root.destroy)

                else:
                    logger.error("Alguns scripts falharam. Verifique os logs para mais detalhes.")
                    status_queue.put(("Erro", "Alguns scripts falharam. Verifique os logs para mais detalhes."))
                break  # Sai do loop após processar o sinal de "Fim"

            elif script_name in status_labels:
                status_dict[script_name] = status
                if status == "Concluído":
                    status_labels[script_name].config(text=f"{script_name}: {status}", background="green")
                elif status == "Executando...":
                    status_labels[script_name].config(text=f"{script_name}: {status}", background="yellow")
                elif status == "Erro":
                    status_labels[script_name].config(text=f"{script_name}: {status}", background="red")
                else:
                    status_labels[script_name].config(text=f"{script_name}: {status}", background="white")

        except queue.Empty:
            pass  # Continua o loop se a fila estiver vazia

# Função para abrir um novo terminal e executar o comando
def abrir_terminal_e_executar_streamlit():
    comando = f'streamlit run "Inicio.py"'
    
    if sys.platform.startswith('win'):  # Windows
        subprocess.Popen(['start', 'cmd', '/k', comando], shell=True)
    elif sys.platform.startswith('darwin'):  # macOS
        subprocess.Popen(['open', '-a', 'Terminal', '-n', '--args', comando])
    elif sys.platform.startswith('linux'):  # Linux
        try:
            # Tenta usar gnome-terminal
            subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', comando + '; exec bash'])
        except FileNotFoundError:
            try:
                # Tenta usar xterm se gnome-terminal não estiver disponível
                subprocess.Popen(['xterm', '-e', comando + '; exec bash'])
            except FileNotFoundError:
                logger.error("Não foi possível encontrar um emulador de terminal compatível.")
    else:
        logger.error("Sistema operacional não suportado.")

# Cria a janela principal
root = tk.Tk()
root.title("Executar Scripts do Teto MAC")

# Dicionário para armazenar os status dos scripts
status_dict = {
    "analise_teto_mac": "Aguardando",
    "BaixaSIA": "Aguardando",
    "BaixaSIH": "Aguardando",
    "evolucao_mac": "Aguardando",
    "evolucao_mac2": "Aguardando",
    "MacUF": "Aguardando",
    "Econo": "Aguardando",
    "Faixa": "Aguardando",
    "Resumo_PT": "Aguardando",
    "Analise MAC": "Aguardando",
    "Analise MAC_SIH": "Aguardando",
    "Analise MAC_SIA": "Aguardando",
    "Analise Correlações": "Aguardando",
    "Conclusão": "Aguardando",
}

# Dicionário para armazenar os labels de status
status_labels = {}

# Cria os labels para exibir o status dos scripts
for i, (script, status) in enumerate(status_dict.items()):
    label = tk.Label(root, text=f"{script}: {status}", background="white")
    label.grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=5)
    status_labels[script] = label

# Lista de UFs
ufs = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]

# Seleção de UF
uf_label = tk.Label(root, text="Selecione a UF:")
uf_label.grid(row=len(status_dict) // 2 + 1, column=0, sticky="w", padx=10, pady=5)
uf_var = tk.StringVar(value=ufs[0])
uf_dropdown = ttk.Combobox(root, textvariable=uf_var, values=ufs)
uf_dropdown.grid(row=len(status_dict) // 2 + 1, column=1, sticky="w", padx=10, pady=5)

# Seleção de município
municipio_label = tk.Label(root, text="Selecione o município:")
municipio_label.grid(row=len(status_dict) // 2 + 2, column=0, sticky="w", padx=10, pady=5)
municipio_var = tk.StringVar()
municipio_dropdown = ttk.Combobox(root, textvariable=municipio_var)
municipio_dropdown.grid(row=len(status_dict) // 2 + 2, column=1, sticky="w", padx=10, pady=5)

# Atualiza a lista de municípios com base na UF selecionada
def atualizar_municipios(event=None):
    uf = uf_var.get()
    municipios = obter_municipios_por_uf(uf)
    municipio_dropdown['values'] = municipios
    if municipios:
        municipio_var.set(municipios[0])

uf_dropdown.bind("<<ComboboxSelected>>", atualizar_municipios)
atualizar_municipios()  # Atualiza inicialmente

# Botão para executar scripts
def iniciar_execucao():
    nome_municipio = municipio_var.get()
    uf = uf_var.get()
    threading.Thread(target=executar_scripts, args=(nome_municipio, uf, status_dict), daemon=True).start()

executar_button = tk.Button(root, text="Executar Scripts", command=iniciar_execucao)
executar_button.grid(row=len(status_dict) // 2 + 3, column=0, columnspan=2, pady=10)

# Inicia a atualização do status em uma thread separada
threading.Thread(target=atualizar_status, daemon=True).start()

# Inicia o loop principal da interface
root.mainloop()

# Abre um novo terminal e executa o Streamlit após o Tkinter fechar
abrir_terminal_e_executar_streamlit()