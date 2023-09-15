import os
import sys
from time import sleep

import requests
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()

assert (
    len(sys.argv) == 2
), "Enter a phone number after the script name i.e. python main.py 0123456789"

phone = sys.argv[1]


def get_captcha_solution(api_key, site_key, url):
    response = requests.post(
        "http://2captcha.com/in.php",
        {
            "key": api_key,
            "method": "hcaptcha",
            "sitekey": site_key,
            "pageurl": url,
            "json": 1,
        },
    ).json()

    request_result = response.get("request")

    if response.get("status") != 1:
        print("Failed to get captcha ID")
        return None

    for _ in range(30):
        sleep(5)
        solution = requests.get(
            f"http://2captcha.com/res.php?key={api_key}&action=get&id={request_result}&json=1"
        ).json()
        if solution.get("status") == 1:
            return solution.get("request")

    print("Failed to get captcha solution")
    return None


chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless")

driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()


print("Getting first page...")
driver.get("https://procedures.inpi.fr/?/")


locator = (
    By.CSS_SELECTOR,
    'img.franceConnectButton[alt="FranceConnect"][src="asset/img/franceconnect/franceconnect-plus-btn.svg"]',
)

wait = WebDriverWait(driver, 30)

button = wait.until(EC.presence_of_element_located(locator))
element = wait.until(EC.element_to_be_clickable(locator))
driver.execute_script("arguments[0].scrollIntoView();", button)
sleep(3)
print("Getting second page...")
button.click()

sleep(3)
button = driver.find_elements(By.TAG_NAME, "button")[0]
print("Getting last page...")
button.click()


sleep(3)
button = driver.find_elements(By.ID, "popin_tc_privacy_button_2")[0]
print("Accepting cookies...")
button.click()


confirm = False
while not confirm:
    sleep(3)
    form = driver.find_elements(By.ID, "kc-form-login")[0]
    action_url = form.get_attribute("action")

    input_ele = driver.find_elements(By.ID, "username")[0]
    input_ele.clear()
    print("Entering phone number...")
    input_ele.send_keys(phone)

    submit_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input.h-captcha.homepage-auth-btn[type="submit"]')
        )
    )

    site_key = submit_button.get_attribute("data-sitekey")
    print("Solving captcha...")
    captcha_solution = get_captcha_solution(
        os.environ["API_KEY_2CAPTCHA"],
        site_key,
        "authent.lidentitenumerique.laposte.fr",
    )

    if captcha_solution:
        driver.execute_script(
            f'document.getElementsByName("g-recaptcha-response")[0].value = "{captcha_solution}";'
        )
        driver.execute_script(
            f'document.getElementsByName("h-captcha-response")[0].value = "{captcha_solution}";'
        )
        print("Waiting for confirmation...")
        driver.execute_script('document.getElementById("kc-form-login").submit();')

        confirmation = driver.find_elements(By.CLASS_NAME, "confirmation-title")
        if confirmation:
            confirm = True
            print("Confirmed! Waiting 2 minutes for user...")
            sleep(120)
            break
        else:
            print("Failed! Trying again...")
    else:
        print("Failed! Trying again...")

driver.close()
