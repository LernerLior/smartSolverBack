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

def get_complaint_data(driver, wait_seconds: int = 10) -> dict:
    data = {}
    try:
        title_elem = WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1[data-testid='complaint-title']"))
        )
        data['complaint_title'] = title_elem.text

        human_scroll(driver)

        try:
            date_container = driver.find_element(
                By.XPATH, "//p[.//*[contains(@class,'lucide-calendar')]]"
            )
            data['complaint_creation_date'] = driver.execute_script("""
                return Array.from(arguments[0].childNodes)
                    .filter(n => n.nodeType === Node.TEXT_NODE)
                    .map(n => n.textContent.trim())
                    .filter(t => t.length > 0)
                    .join('');
            """, date_container)
        except:
            data['complaint_creation_date'] = None

        try:
            desc_elem = driver.find_element(By.CSS_SELECTOR, "p[data-testid='complaint-description']")
            data['complaint_description'] = desc_elem.text
        except:
            data['complaint_description'] = None

    except TimeoutException:
        return None

    return data

COMPLAINT_LINK_SELECTOR = "a[data-testid='complaint-listagem-v2-title-link']"
NEXT_PAGE_SELECTOR = "button[data-testid='next-page-navigation-button']"


def go_to_next_page(driver, wait_seconds: int = 10) -> bool:
    """Clica no botão de próxima página, se disponível e habilitado. Retorna True se navegou."""
    try:
        next_btn = WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, NEXT_PAGE_SELECTOR))
        )
        if next_btn.is_enabled() and next_btn.is_displayed():
            driver.execute_script("arguments[0].click();", next_btn)
            human_sleep(2.0, 4.0)
            WebDriverWait(driver, wait_seconds).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, COMPLAINT_LINK_SELECTOR))
            )
            return True
        else:
            print("Botão de próxima página desabilitado. Fim das páginas.")
            return False
    except TimeoutException:
        print("Botão de próxima página não encontrado. Fim das páginas.")
        return False


def open_and_collect(driver, n: int = 1, wait_seconds: int = 10):
    complaints_list = []
    main_tab = driver.current_window_handle
    collected = 0
    page = 1

    WebDriverWait(driver, wait_seconds).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, COMPLAINT_LINK_SELECTOR))
    )
    human_scroll(driver)

    while collected < n:
        link_elements = WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, COMPLAINT_LINK_SELECTOR))
        )

        hrefs = [el.get_attribute("href") for el in link_elements if el.get_attribute("href")]

        if not hrefs:
            print(f"Nenhum link encontrado na página {page}.")
            break

        for href in hrefs:
            if collected >= n:
                break

            human_sleep(1.0, 2.5)

            try:
                driver.execute_script(f"window.open('{href}', '_blank');")
                new_tab = [t for t in driver.window_handles if t != main_tab][0]
                driver.switch_to.window(new_tab)

                human_sleep(2.0, 4.0)
                complaint_data = get_complaint_data(driver, wait_seconds=wait_seconds)

                if complaint_data:
                    human_sleep(2.0, 5.0)
                    complaints_list.append(complaint_data)
                    collected += 1
                    print(f"[{collected}/{n}] Coletado (pág. {page}): {complaint_data.get('complaint_title', 'sem título')}")

                driver.close()
                driver.switch_to.window(main_tab)

                if random.random() < 0.3:
                    print(f"[{collected}/{n}] Pausa longa...")
                    human_sleep(5.0, 10.0)
                else:
                    human_sleep(1.5, 3.0)

            except (TimeoutException, StaleElementReferenceException) as e:
                print(f"[{collected + 1}/{n}] Erro, pulando: {e}")
                if driver.current_window_handle != main_tab:
                    driver.close()
                    driver.switch_to.window(main_tab)
                continue

        # Se ainda não coletou o suficiente, tenta ir para a próxima página
        if collected < n:
            print(f"Página {page} esgotada. Tentando ir para a próxima...")
            if not go_to_next_page(driver, wait_seconds):
                print("Sem mais páginas disponíveis.")
                break
            page += 1
            human_scroll(driver)

    return complaints_list


def collect_complaints(target_company, complaint_number=6, wait_seconds=10):
    driver = open_company_page(target_company)

    try:
        complaints_list = open_and_collect(driver, complaint_number, wait_seconds)
    finally:
        driver.quit()

    return complaints_list