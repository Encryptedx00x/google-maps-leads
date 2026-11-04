from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import os

# Função para iniciar o navegador
def iniciar_navegador():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Se quiser rodar invisível, descomente esta linha
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Função para limpar e formatar o telefone
def formatar_telefone(telefone):
    telefone_limpo = re.sub(r'\D', '', telefone)
    if len(telefone_limpo) == 10:  # Exemplo para telefones com DDD
        return f"({telefone_limpo[:2]}) {telefone_limpo[2:6]}-{telefone_limpo[6:]}"
    elif len(telefone_limpo) == 11:  # Exemplo para celulares com DDD
        return f"({telefone_limpo[:2]}) {telefone_limpo[2:7]}-{telefone_limpo[7:]}"
    return telefone_limpo  # Retorna o número limpo se não corresponder aos padrões

# Função para buscar empresas
def buscar_empresas(cidade, termo_busca, driver):
    url = "https://www.google.com/maps"
    driver.get(url)

    # Localiza a barra de pesquisa e faz a busca
    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.clear()
    search_box.send_keys(f"{termo_busca} em {cidade}")
    search_box.send_keys(Keys.ENTER)

    # Aguarda a página carregar resultados
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Nv2PK")))

    empresas = []

    # Coleta os resultados
    resultados = driver.find_elements(By.CLASS_NAME, "Nv2PK")
    for resultado in resultados:
        try:
            nome = resultado.find_element(By.CLASS_NAME, "qBF1Pd").text
            
            # Tenta capturar o telefone
            telefone = "Telefone não encontrado"
            try:
                info_element = resultado.find_elements(By.XPATH, ".//span[contains(@class, 'UsdlK')]")
                for info in info_element:
                    texto_info = info.text
                    if re.search(r'\(?\d{2,3}\)?\s?\d{4,5}-?\d{4}', texto_info):
                        telefone = texto_info
                        break  # Para no primeiro telefone encontrado
            except Exception as e:
                print(f"Erro ao encontrar telefone: {e}")

            telefone_formatado = formatar_telefone(telefone)  # Formata o telefone

            # Captura tipo de empresa e endereço
            tipo_empresa = "Tipo não encontrado"
            endereco = "Endereço não encontrado"
            try:
                # Busca informações de tipo de empresa e endereço
                info_empresa = resultado.find_elements(By.XPATH, ".//div[contains(@class, 'W4Efsd') and not(./span[contains(@class, 'UY7F9')])]")

                if len(info_empresa) >= 2:  # Verifica se há pelo menos 2 elementos
                    tipo_empresa = info_empresa[0].text.strip()  # Primeiro elemento
                    endereco = info_empresa[1].text.strip()  # Segundo elemento
            except Exception as e:
                print(f"Erro ao encontrar tipo de empresa e endereço: {e}")

            empresas.append({
                "Nome": nome,
                "Telefone": telefone_formatado,
                "Tipo de Empresa": tipo_empresa,
                "Endereço": endereco,
                "Cidade": cidade
            })
        except Exception as e:
            print(f"Erro ao coletar dados: {e}")  # Exibe erro no console
            continue  # Ignora se não encontrar telefone ou nome

    return empresas

# Função para gerar um nome de arquivo único
def gerar_nome_arquivo(base_nome):
    contador = 1
    nome_arquivo = f"{base_nome}.xlsx"
    while os.path.exists(nome_arquivo):
        nome_arquivo = f"{base_nome}_{contador}.xlsx"
        contador += 1
    return nome_arquivo

# Função para obter cidades e palavras-chave do usuário
def obter_opcoes_usuario(cidades_padrao, termos_padrao):
    # Pergunta sobre as cidades
    cidades_usuario = input(f"Você deseja usar as cidades padrão {cidades_padrao}? (s/n): ").strip().lower()
    if cidades_usuario == 'n':
        cidades = input("Digite as cidades separadas por vírgula: ").split(',')
        cidades = [cidade.strip() for cidade in cidades]
    else:
        cidades = cidades_padrao

    # Pergunta sobre os termos de busca
    termos_usuario = input(f"Você deseja usar os termos padrão {termos_padrao}? (s/n): ").strip().lower()
    if termos_usuario == 'n':
        termos = input("Digite os termos de busca separados por vírgula: ").split(',')
        termos = [termo.strip() for termo in termos]
    else:
        termos = termos_padrao

    return cidades, termos

# Termos de busca e cidades
termos_busca_padrao = ["Transportadora", "CD", "Centro de Distribuição", "Logística", "Galpão", "Transportes", "Importação", "Exportação", "Express", "Armazéns gerais", "Distribuidora", "Armazenagem"]
cidades_padrao = ["Navegantes", "Itajaí", "Blumenau"]

# Obtém as opções do usuário
cidades, termos_busca = obter_opcoes_usuario(cidades_padrao, termos_busca_padrao)

# Inicia o navegador
driver = iniciar_navegador()
todas_empresas = []

# Realiza buscas para cada termo e cidade
for termo in termos_busca:
    for cidade in cidades:
        empresas_encontradas = buscar_empresas(cidade, termo, driver)
        todas_empresas.extend(empresas_encontradas)

driver.quit()  # Fecha o navegador

# Salva os resultados em um arquivo Excel
nome_arquivo = gerar_nome_arquivo("empresas_logistica")
df = pd.DataFrame(todas_empresas)
df.to_excel(nome_arquivo, index=False)

print(f"Busca concluída. Resultados salvos em '{nome_arquivo}'.")
