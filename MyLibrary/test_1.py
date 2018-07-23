import unittest
from selenium import webdriver

class FirstTest (unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
    
    def test_first_selenium_test(self):
        self.driver.get("http://www.swtestacademy.com")
    
    def tearDown(self):
        self.driver.quit()