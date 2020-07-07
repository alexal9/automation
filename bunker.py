from selenium.webdriver.support.ui import Select
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
import time
import sys

driver = webdriver.Chrome()
driver.get("""http://meaty.dfprofiler.com/marketplace.html""")

element = WebDriverWait(driver, 10).until(
	EC.presence_of_element_located((By.ID, "tradezone"))
)

select_zone = Select(driver.find_element_by_css_selector("select[id=tradezone]"))
text = driver.find_element_by_css_selector("input[id=item]")
submit = driver.find_element_by_css_selector("input[id=submitSearch]")

select_zone.select_by_value('13')
text.send_keys(sys.argv[1])
submit.click()

# wait for results
# time.sleep(3)
element = WebDriverWait(driver, 10).until(
	EC.presence_of_element_located((By.ID, "marketResults"))
)

results = driver.find_element_by_css_selector("tbody[id=marketResults]")
soup = bs(results.get_attribute('innerHTML'), features='lxml')

limit = int(sys.argv[2]) if len(sys.argv) == 3 else 20

for line in soup.select('tr')[:limit]:
	cols = line.select('td')
	print(' | '.join(cell.text for cell in cols))

driver.quit()