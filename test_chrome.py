from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

opts = Options()
opts.binary_location = "/usr/bin/chromium"

opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-gpu")
opts.add_argument("--window-size=1920,1080")

service = Service("/usr/bin/chromedriver")

driver = webdriver.Chrome(
    service=service,
    options=opts
)

driver.get("https://www.google.com")
print(driver.title)

driver.quit()
