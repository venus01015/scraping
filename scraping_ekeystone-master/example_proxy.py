from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
from os import path
from selenium import webdriver
# req_proxy = RequestProxy() #you may get different number of proxy when  you run this at each time
# proxies = req_proxy.get_proxy_list() #this will create proxy list
# PROXY = proxies[0].get_address()
PROXY = "163.172.206.121:5836"
print(PROXY)
# print(path.expanduser("~"))
# exit()
webdriver.DesiredCapabilities.CHROME['proxy']={
    "httpProxy":PROXY,
    "ftpProxy":PROXY,
    "sslProxy":PROXY,
    "proxyType":"MANUAL",
}
# driver = webdriver.Chrome(executable_path= "chromedriver.exe")
url = 'https://wwwsc.ekeystone.com/'
url = 'https://www.w3schools.com/'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--proxy-server=%s' % PROXY)

driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get(url)
# def getChromeDriver():
#     options = Options()
#     # options.add_argument("--headless")
#     # options.add_argument("--no-sandbox")
#     # options.add_argument("--disable-dev-shm-usage")
#     # options.add_argument("--disable-gpu")
#     # options.add_argument("--window-size=1920,1080")
#     options.add_argument("--start-maximized")
#     # options.add_argument("download.default_directory=C:/Downloads")
#     # prefs = {'download.default_directory' : 'path/to/dir'}
#     # options.add_experimental_option('prefs', prefs)
#     # chromedriver = 'DESCTINATION_TO_YOUR_CHROME_DRIVER'
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
#     driver_path='chromedriver.exe'
#     options.add_argument('--user-data-dir=' + path.expanduser("~") + '/AppData/Local/Google/Chrome/User Data')
#     return webdriver.Chrome(options=options,executable_path=driver_path)