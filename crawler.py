from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import random
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

#Simulação de comportamento humano
def human_sleep(min_s: float = 1.0, max_s: float = 3.0):
    time.sleep(random.uniform(min_s, max_s))


def human_scroll(driver):
    total_height = driver.execute_script("return document.body.scrollHeight")
    current = 0
    step = random.randint(200, 400)

    while current < total_height:
        current += step
        driver.execute_script(f"window.scrollTo(0, {current});")
        time.sleep(random.uniform(0.05, 0.2))

    driver.execute_script(f"window.scrollTo(0, {current - random.randint(100, 300)});")
    human_sleep(0.5, 1.2)

#ABre a página da empresa e retorna o driver para interação
def open_company_page(target_company: str):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    url = f"https://www.reclameaqui.com.br/empresa/{target_company}/lista-reclamacoes/"
    driver.get(url)
    human_sleep(2.0, 4.0)

    return driver

#Coleta os dados de uma reclamação a partir da página individual

def get_complaint_data(driver, wait_seconds: int = 10) -> dict:
    data = {}
    try:
        title_elem = WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1[data-testid='complaint-title']"))
        )
        data['complaint-title'] = title_elem.text

        human_scroll(driver)

        try:
            date_elem = driver.find_element(By.CSS_SELECTOR, "span[data-testid='complaint-creation-date']")
            data['complaint-creation-date'] = date_elem.text
        except:
            data['complaint-creation-date'] = None

        try:
            desc_elem = driver.find_element(By.CSS_SELECTOR, "p[data-testid='complaint-description']")
            data['complaint-description'] = desc_elem.text
        except:
            data['complaint-description'] = None

    except TimeoutException:
        return None

    return data

#Padrão de seleção dos títulos das reclamações na página de listagem
H4_SELECTOR = "h4[data-testid='compain-title-link']"


#Abre cada reclamação em nova aba, coleta os dados e fecha a aba, retornando uma lista de reclamações
def open_h4_and_collect(driver, n: int = 1, wait_seconds: int = 10):
    complaints_list = []
    main_tab = driver.current_window_handle

    WebDriverWait(driver, wait_seconds).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, H4_SELECTOR))
    )
    human_scroll(driver)

    for i in range(n):
        try:
            h4_elements = WebDriverWait(driver, wait_seconds).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, H4_SELECTOR))
            )

            if i >= len(h4_elements):
                print(f"Apenas {len(h4_elements)} reclamações encontradas na página.")
                break

            # Tenta pegar o href do <a> , que é o botão de cada reclamação
            try:
                link_elem = h4_elements[i].find_element(By.XPATH, "ancestor::a")
            except:
                link_elem = None

            href = link_elem.get_attribute("href") if link_elem else h4_elements[i].get_attribute("href")

            if not href:
                print(f"[{i+1}/{n}] href não encontrado, pulando.")
                continue

            human_sleep(1.0, 2.5)

            # Abre nova aba com a reclamação
            driver.execute_script(f"window.open('{href}', '_blank');")
            new_tab = [t for t in driver.window_handles if t != main_tab][0]
            driver.switch_to.window(new_tab)

            # Lê a reclamação
            human_sleep(2.0, 4.0)
            complaint_data = get_complaint_data(driver, wait_seconds=wait_seconds)

            if complaint_data:
                human_sleep(2.0, 5.0)
                complaints_list.append(complaint_data)
                print(f"[{i+1}/{n}] Coletado: {complaint_data.get('complaint-title', 'sem título')}")

            # Fecha nova aba e volta 
            driver.close()
            driver.switch_to.window(main_tab)

            if random.random() < 0.3:
                print(f"[{i+1}/{n}] Pausa longa...")
                human_sleep(5.0, 10.0)
            else:
                human_sleep(1.5, 3.0)

        except (TimeoutException, StaleElementReferenceException) as e:
            print(f"[{i+1}/{n}] Erro, pulando: {e}")
            if driver.current_window_handle != main_tab:
                driver.close()
                driver.switch_to.window(main_tab)
            continue

    return complaints_list

#COleta as reclamações.
def collect_complaints(target_company, complaint_number=6, wait_seconds=10):
    driver = open_company_page(target_company)

    try:
        complaints_list = open_h4_and_collect(driver, complaint_number, wait_seconds)
    finally:
        driver.quit()

    return complaints_list