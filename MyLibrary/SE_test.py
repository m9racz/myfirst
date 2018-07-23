import time
from selenium import webdriver

driver = webdriver.Chrome()
driver.get('http://google.com')
elm = driver.find_element_by_name('btnI')
elm.click()
print(driver.current_url)
time.sleep(15)
driver.quit()