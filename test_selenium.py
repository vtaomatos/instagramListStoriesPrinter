from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

chrome_binary = "/snap/bin/chromium"
chromedriver_path = "/usr/bin/chromedriver"

options = Options()
options.binary_location = chrome_binary
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--headless=new")

service = Service(executable_path=chromedriver_path)

driver = webdriver.Chrome(service=service, options=options)

driver.get("https://www.google.com")
print("Título:", driver.title)

driver.quit()
