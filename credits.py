from selenium.webdriver.support.ui import Select
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
import time

driver = webdriver.Chrome()
driver.get("""http://meaty.dfprofiler.com/marketplace.html""")

element = WebDriverWait(driver, 10).until(
	EC.presence_of_element_located((By.ID, "tradezone"))
)

select_zone = Select(driver.find_element_by_css_selector("select[id=tradezone]"))
select_category = Select(driver.find_element_by_css_selector("select[id=category]"))
submit = driver.find_element_by_css_selector("input[id=submitSearch]")

zones = {
	'4': "Nastya's Holdout",
	'10': "Dogg's Stockade",
	'11': "Precinct 13",
	'12': "Fort Pastor",
	'13': "Secronom Bunker"
}

for zone in zones:
	print('finding credit prices for zone:', zones[zone])
	print('----------------------')

	select_zone.select_by_value(zone)
	select_category.select_by_value('23')
	submit.click()

	# wait for results
	time.sleep(3)
	# element = WebDriverWait(driver, 10).until(
		# EC.presence_of_element_located((By.ID, "marketResults"))
	# )

	results = driver.find_element_by_css_selector("tbody[id=marketResults]")
	soup = bs(results.get_attribute('innerHTML'), features='lxml')

	for line in soup.select('tr'):
		cols = line.select('td')
		if int(cols[-1].text.replace(',','')) <= int(cols[4].text):
			print(' | '.join(cell.text for cell in cols))
	print('\n\n\n')

driver.quit()