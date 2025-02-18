from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from dotenv import load_dotenv
import os
import re
import time

# Inicializar o WebDriver
driver = webdriver.Edge()

# Carregar variáveis do ambiente
load_dotenv("login.env")
email = os.getenv("MY_EMAIL")
password = os.getenv("MY_PASSWORD")
email_path = os.getenv("EMAIL")
password_path = os.getenv("PASSWORD")

# Configurar espera
wait = WebDriverWait(driver, 10)  # Tempo de espera ajustado para 10 segundos

# Acessar os sites necessários
driver.get("https://pathfinder.automationanywhere.com/challenges/salesorder-tracking.html")
driver.execute_script("window.open('https://pathfinder.automationanywhere.com/challenges/salesorder-applogin.html');")

# Trocar para a aba de login
abas = driver.window_handles
driver.switch_to.window(abas[1])
driver.maximize_window()

# Aceitar cookies se necessário (somente uma vez por sessão)
try:
    cookies_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
    cookies_button.click()
except Exception:
    print("Botão de cookies não encontrado ou já aceito.")

# Realizar login (somente uma vez por sessão)
try:
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "button_modal-login-btn__iPh6x")))
    login_button.click()
except Exception:
    print("Botão de login inicial não encontrado. Continuando...")

email_field = wait.until(EC.element_to_be_clickable((By.ID, "43:2;a")))
email_field.send_keys(email)
next_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "slds-button_brand")))
next_button.click()

password_field = wait.until(EC.element_to_be_clickable((By.ID, "10:152;a")))
password_field.send_keys(password)
login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "slds-button_brand")))
login_button.click()

# Preencher campos no Pathfinder
email_field_pathfinder = wait.until(EC.element_to_be_clickable((By.ID, "salesOrderInputEmail")))
email_field_pathfinder.send_keys(email_path)
password_field_pathfinder = wait.until(EC.element_to_be_clickable((By.ID, "salesOrderInputPassword")))
password_field_pathfinder.send_keys(password_path)

login_button_pathfinder = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-primary.btn-user.btn-block")))
login_button_pathfinder.click()

# Navegar para a tabela de pedidos
sales_order_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.nav-link[href='salesorder-applist.html']")))
sales_order_button.click()

# Configurar a tabela para mostrar 50 entradas
dropdown = wait.until(EC.presence_of_element_located((By.NAME, "salesOrderDataTable_length")))
select = Select(dropdown)
select.select_by_value("50")

# Capturar os itens de rastreamento
tabela = wait.until(EC.presence_of_element_located((By.ID, "salesOrderDataTable_wrapper")))
linhas = tabela.find_elements(By.CSS_SELECTOR, "tbody tr")

# Usar um conjunto para evitar repetir os números de rastreamento
rastreamentos_processados = set()

# Processar cada item de pedido
for linha in linhas:
    try:
        coluna_status = linha.find_element(By.XPATH, "./td[5]")
        status_texto = coluna_status.text

        # Verificar se o pedido pode ser expandido
        if status_texto in ["Confirmed", "Delivery Outstanding"]:
            botao_expandir = linha.find_element(By.CLASS_NAME, "fa-square-plus")
            botao_expandir.click()

            # Capturar itens expandidos
            itens_expandidos = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td table.sales-order-items tbody tr"))
            )

            # Armazenar números de rastreamento
            numeros_rastreamento = []
            for item in itens_expandidos:
                texto_item = item.text
                numero = re.findall(r"TR-\d{5}-\d{3}", texto_item)
                if numero:
                    numeros_rastreamento.append(numero[0])

            # Verificar status de cada número de rastreamento
            for numero_rastreamento in numeros_rastreamento:
                if numero_rastreamento in rastreamentos_processados:
                    print(f"Já processado o número {numero_rastreamento}, pulando...") 
                    continue  # Ignorar números já processados

                try:
                    print(f"Verificando status para o número: {numero_rastreamento}")
                    driver.switch_to.window(abas[0])  # Voltar para a aba de rastreamento

                    # Aceitar cookies novamente caso necessário
                    try:
                        cookies_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
                        cookies_button.click()
                    except Exception:
                        pass  # Cookies já aceitos

                    # Realizar login novamente caso necessário
                    try:
                        login_button = wait.until(EC.element_to_be_clickable((By.ID, "button_modal-login-btn__iPh6x")))
                        login_button.click()
                    except Exception:
                        pass  # Login já feito

                    # Inserir o número de rastreamento e clicar no botão de validação
                    campo_rastreamento = wait.until(EC.presence_of_element_located((By.ID, "inputTrackingNo")))
                    campo_rastreamento.clear()
                    campo_rastreamento.send_keys(numero_rastreamento)
                    track_button = wait.until(EC.element_to_be_clickable((By.ID, "btnCheckStatus")))
                    track_button.click()

                    # Esperar o status ser exibido e verificar
                    status_rastreamento = wait.until(
                        EC.presence_of_element_located((By.XPATH, "//*[@id='shipmentStatus']/tr[3]/td[2]"))
                    ).text
                    print(f"Status para {numero_rastreamento}: {status_rastreamento}")

                    # Se o número de rastreamento não for "Delivered", continue para o próximo item de pedido
                    if status_rastreamento.lower() != "delivered":
                        print(f"Status para {numero_rastreamento} não é 'Delivered'. Pulando para o próximo item de pedido.")
                        break  # Pula para o próximo item de pedido

                    # Marcar como processado
                    rastreamentos_processados.add(numero_rastreamento)

                except Exception as e:
                    print(f"Erro ao verificar número {numero_rastreamento}: {e}")
                    continue  # Ignora erros e continua para o próximo número

            # Se pelo menos um número de rastreamento for "Delivered", clicar em "Invoice" e ir para o próximo item
            if any(status_rastreamento.lower() == "delivered" for status_rastreamento in numeros_rastreamento):
                driver.switch_to.window(abas[1])  # Voltar para a aba de pedidos
                try:
                    # Clique no botão de gerar fatura
                    botao_invoice = linha.find_element(By.CLASS_NAME, "btn.btn-primary.mr-3")
                    botao_invoice.click()
                    print(f"Fatura gerada para o número {numeros_rastreamento[0]}")
                except Exception as e:
                    print(f"Erro ao clicar no botão de fatura para o número {numeros_rastreamento[0]}: {e}")

    except Exception as e:
        print(f"Erro ao processar linha: {e}")

# Finalizar apenas depois de concluir todos os processos
print("Processo concluído.")
driver.quit()
