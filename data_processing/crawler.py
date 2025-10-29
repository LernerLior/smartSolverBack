from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import time
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def open_company_page(target_company: str):
    """
    Abre a página de reclamações da empresa no Reclame Aqui.
    
    Args:
        target_company (str): Nome da empresa usado na URL do Reclame Aqui.
    
    Returns:
        webdriver.Chrome: Instância do navegador aberta na página da empresa.
    """
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--log-level=3")  

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    url = f"https://www.reclameaqui.com.br/empresa/{target_company}/lista-reclamacoes/"
    driver.get(url)

    return driver

def get_complaint_data(driver, wait_seconds: int = 3) -> dict:
    """
    Coleta dados da reclamação na página atual usando os nomes originais do data-testid.
    """
    data = {}
    try:
        # Título
        title_elem = WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1[data-testid='complaint-title']"))
        )
        data['complaint-title'] = title_elem.text

        # Data
        try:
            date_elem = driver.find_element(By.CSS_SELECTOR, "span[data-testid='complaint-creation-date']")
            data['complaint-creation-date'] = date_elem.text
        except:
            data['complaint-creation-date'] = None

        # Descrição
        try:
            desc_elem = driver.find_element(By.CSS_SELECTOR, "p[data-testid='complaint-description']")
            data['complaint-description'] = desc_elem.text
        except:
            data['complaint-description'] = None

    except TimeoutException:
        return None

    return data


def open_h4_and_collect(driver, n: int = 1, wait_seconds: int = 3):
    """
    Coleta as reclamações clicando nos elementos h4 e retorna uma lista de dicionários.
    """
    complaints_list = []

    for i in range(n):
        h4_elements = driver.find_elements(By.CSS_SELECTOR, "h4[data-testid='compain-title-link']")
        if i >= len(h4_elements):
            break

        h4 = h4_elements[i]
        driver.execute_script("arguments[0].click();", h4)
        time.sleep(wait_seconds)

        complaint_data = get_complaint_data(driver, wait_seconds=wait_seconds)
        if complaint_data:
            complaints_list.append(complaint_data)

        driver.back()
        time.sleep(1)

    return complaints_list



def collect_complaints(target_company, complaint_number=6, wait_seconds=10):
    driver = open_company_page(target_company)

    try:
        complaints_list = open_h4_and_collect(driver, complaint_number, wait_seconds)
    finally:
        driver.quit()

    return complaints_list
