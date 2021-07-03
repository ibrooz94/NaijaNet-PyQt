import requests
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import configparser
from pathlib import Path

class Naijanet():
    def __init__(self):
        self.config=configparser.ConfigParser()
        if Path('config.ini').is_file():
            self.config.read('config.ini')
        else:
            self.config['DRIVER'] = {'BROWSER':'FIREFOX' }
            self.config['LOCATION'] = {'PATH':Path.home()/'Downloads'}
            with open('config.ini', 'w') as configfile:
                self.config.write(configfile)
        
        self.path = self.config['DRIVER']['BROWSER']
        self.driver = None

    def get_search_result(self, search_item):
        # search for a movie
        search_url = "https://www.thenetnaija.com/search"
        params = {
            "t": search_item, "folder":"videos"
        }
        r = requests.get(search_url, params=params)
        search_result_html = BeautifulSoup(r.text, "html.parser")
        section = search_result_html.find("div", {"class": "search-results"})
        search_result = []
        try:
            for i in section.findAll("h3"):
                search_result.append({
                    "name": i.text,
                    "url": i.find("a")["href"]
                })
        except TypeError:
            pass
        return search_result

    def get_link(self, search_item):

        url = search_item
        r = requests.get(url)
        page_url_html = BeautifulSoup(r.text, "html.parser")
        section = page_url_html.find("div", {"class": "db-one"})
        pre_video_url = []
        if section is not None:
            for link in section.findAll("a", {"class": "btn"}):
                file_link = link.get("href")
                pre_video_url.append(file_link)
        return pre_video_url

    def sabi_share(self, search_item):
        # url=self.get_link(search_item)[1]
        urpl=self.get_link(search_item)[0]
        url ="https://www.thenetnaija.com" + urpl

        if self.path == "EDGE":
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from msedge.selenium_tools import Edge, EdgeOptions , EdgeService
            import os
            os.environ['WDM_LOG_LEVEL'] = '0'
            try:
                options = EdgeOptions()
                options.use_chromium = True
                # options.add_argument("headless")
                options.add_argument("disable-gpu")
                self.driver = Edge(options= options, executable_path = EdgeChromiumDriverManager(log_level=0).install())
            except Exception:
                raise 

        elif self.path == "FIREFOX":
            from webdriver_manager.firefox import GeckoDriverManager
            from selenium.webdriver.firefox.options import Options
            import os
            os.environ['WDM_LOG_LEVEL'] = '0'
            try:
                options = Options()
                options.add_argument('--disable-gpu')
                options.headless = False
                self.driver = webdriver.Firefox(options=options, executable_path=GeckoDriverManager(log_level=0).install())
            except Exception:
                raise 

        elif self.path == "CHROME":
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            import os
            os.environ['WDM_LOG_LEVEL'] = '0'

            try:
                options = Options()
                options.use_chromium = True
                # options.add_argument("headless")
                options.add_argument("disable-gpu")
                self.driver = webdriver.Chrome(options=options, executable_path=ChromeDriverManager(log_level=0).install())
            except Exception:
                raise 


        try: 
            self.driver.get(url)
            h1 = self.driver.find_element_by_css_selector('button.shadow-sm')
            h1.click()
            element = WebDriverWait(self.driver, 30).until( 
                EC.presence_of_element_located((By.CSS_SELECTOR, ".download-url")) 
            ) 
            URL = element.get_attribute('href')   
            return URL

        except selenium.common.exceptions.NoSuchElementException:
            self.driver.quit()
            return "ERROR_1"
        except selenium.common.exceptions.TimeoutException:
            self.driver.quit()
            return "ERROR_2"

        finally: 
            self.driver.quit()
            
    def destroy(self):
        if self.driver:
            self.driver.quit()
        else:
            pass

n = Naijanet()
def sabi_share(user_input):
    return n.sabi_share(user_input)
def get_search_result(user_input):
    return n.get_search_result(user_input)
def destroy():
    return n.destroy()


