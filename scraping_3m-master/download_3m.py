import json
from time import gmtime, strftime
import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import requests
import urllib.request
from os import path
import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pyodbc
from PIL import Image
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

cursor = None
download_path = path.expanduser("~") + "/Downloads/"
download_path = download_path.replace("\\","/")
print(download_path)
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Dnt": "1",
    "Host": "httpbin.org",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
}
def get_header() :
    ua=UserAgent()
    return {'User-Agent': ua.random,       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',      'Accept-Encoding': 'none',      'Accept-Language': 'en-US,en;q=0.8',      'Connection': 'keep-alive'}

def getChromeDriver():
    options = Options()
    # options.add_argument("--headless")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    # options.add_argument("download.default_directory=C:/Downloads")
    # prefs = {'download.default_directory' : 'path/to/dir'}
    # options.add_experimental_option('prefs', prefs)
    # chromedriver = 'DESCTINATION_TO_YOUR_CHROME_DRIVER'
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option('useAutomationExtension', False)
    driver_path='chromedriver.exe'
    options.add_argument('--user-data-dir=' + path.expanduser("~").replace("\\","/") + '/AppData/Local/Google/Chrome/User Data')
    return webdriver.Chrome(options=options,executable_path=driver_path)

def change_string(text):
    text = text.replace('®','')
    text = text.replace('&reg;','')
    text = text.replace('&trade;','')
    text = text.replace('<br> ','')
    text = text.replace('&amp; ','')
    text = text.replace('/','&')
    text = text.replace("'",'`')
    text = text.replace('™','')
    text = text.replace('\n\n','')
    # text = text.replace('"','``')
    return text

def data_storage( Product_Title, Sku_SN, Product_Description, Product_Image_urls, Resources_urls, Product_Specification, Categorys):
    global cursor
    # global container_name
    Web_Structure =""
    try:
        Product_Images =[]
        Str_Product_Images=""
        k = 0
        if len(Product_Image_urls) > 0 :
            for url in Product_Image_urls :
                k += 1
                r = requests.get(url, headers=headers)
                filename = url.split('/')[-1]
                open(filename, 'wb').write(r.content)
                Product_Images.append(Categorys[0] + "/Current/" + filename)
                Str_Product_Images += "," + Categorys[0] + "/Current/" + filename
        Str_Product_Images = Str_Product_Images[1:]

        Resource_Files =[]
        Str_Resource_Files = ""
        k = 0
        if len(Resources_urls) > 0 :
            for url in Resources_urls :
                k += 1
                r = requests.get(url, headers=headers)
                filename = url.split('/')[-1]
                open(filename, 'wb').write(r.content)
                Resource_Files.append(Categorys[0] + "/Current/" + filename)
                Str_Resource_Files += "," + Categorys[0] + "/Current/" + filename
        Str_Resource_Files = Str_Resource_Files[1:]

        for cate in Categorys :
            Web_Structure += "/"+cate
        Web_Structure=Web_Structure[1:]
        fields = [Product_Title, Sku_SN, Product_Description, Str_Product_Images, Product_Specification, Str_Resource_Files, "", "", "", "", "", "", "", Web_Structure]
        k = 5
        for cate in Categorys :
            k+=1
            fields[k] = cate
        _query = "INSERT INTO scraping3m( Product_Title, SKU_SN, Product_Description, Product_Images, Product_Specification, Resource_Files, Manufacture, Category1, Category2, Category3, Category4, Category5, Category6, Web_Structure) VALUES ("
        for field in fields :
            _query += "'" + field + "',"
        _query = _query[:len(_query)-1] + ");"
        # print(_query)
        try:
            # cursor.execute(_query)
            # cursor.commit()
            if len(Product_Images)>0 :
                for url in Product_Images :
                    filename = url.split("/")[-1]
                    # blob_client = blob_service_client.get_blob_client(container=container_name,blob=url)
                    # try:
                    #     with open(  filename, "rb") as data:
                    #         blob_client.upload_blob(data)
                    # except :
                    #     pass

            if len(Resource_Files)>0 :
                for url in Resource_Files :
                    filename = url.split("/")[-1]
                    # blob_client = blob_service_client.get_blob_client(container=container_name,blob=url)
                    # try:
                    #     with open(  filename, "rb") as data:
                    #         blob_client.upload_blob(data)
                    # except :
                    #     pass

        except Exception as err :
            print(" error -> ", str(err))
            # server = 'tcp:tstdbset01.database.windows.net'
            # database = 'tstdb02'
            # username = 'sadminx'
            # password = 't*Te9qi?nk3'
            # sql_driver= '{ODBC Driver 17 for SQL Server}'
            # cnxn = pyodbc.connect('DRIVER='+sql_driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
            # cursor = cnxn.cursor()
            pass
        # ************************ remove files *********************

        if len(Product_Images)>0 :
            for url in Product_Images :
                filename = url.split("/")[-1]
                try:
                    os.remove(filename)
                except :
                    pass

        if len(Resource_Files)>0 :
            for url in Resource_Files :
                filename = url.split("/")[-1]
                try:
                    os.remove(filename)
                except :
                    pass
    except Exception as err :
        print(str(err))
        if len(Product_Images)>0 :
            for url in Product_Images :
                filename = url.split("/")[-1]
                try:
                    os.remove(filename)
                except :
                    pass

        if len(Resource_Files)>0 :
            for url in Resource_Files :
                filename = url.split("/")[-1]
                try:
                    os.remove(filename)
                except :
                    pass
        pass
    return


def get_product_details(my_page_source) :
    Product_Title = ""
    Sku_SN =""
    Product_Description =""
    Product_Specification= ""
    Product_Image_urls=[]
    Resources_urls=[]
    Categorys=['3M']

    Sku_SN = my_page_source.findAll(attrs={'class': 'MMM--contentDetailContain-bd'})[0].findAll('div')[0].text
    if Sku_SN  == "" :
        return
    Sku_SN = Sku_SN.replace("\n","").replace("\xa0"," ")
    cates = my_page_source.find(attrs={'class' : 'MMM--breadcrumbs-list'}).findAll('li')
    k = 0
    for cate in cates :
        k+=1
        if k<3 or k==len(cates) : continue
        Categorys.append(cate.text.replace('\n', ''))
    Product_Title= my_page_source.findAll(attrs={'class' : 'MMM--hdg MMM--hdg_1 hdg_contentDetailTitle'})[0].text.replace("\n","")
    elements = my_page_source.findAll(attrs={'class': 'MMM--variationsList js-thumbList MMM--isNotOnMobile'})[0].findAll('li')
    for li in elements :
        img = li.find('img')
        Product_Image_urls.append(img['src'])
    elements = my_page_source.findAll(attrs={'class': 'MMM--tabSection clearfix 2'})
    for element in elements :
        part_title = element.find('div').text
        if "Specifications" in part_title :
            Specifications = element.findAll('div')[1].findAll('tr')
            k = 0
            for Specification in Specifications :
                k += 1
                if k == 1 : continue
                tds = Specification.findAll('td')
                Product_Specification += '[' + tds[0].text.replace('\n','') + ':' + tds[1].text.replace('\n','') + ']'
        elif "Details" in part_title:
            Product_Description = element.find(attrs={'class':'MMM--grids-col MMM--grids-col_pdpMain'}).text
        elif "Resources" in part_title:
            a_tags = element.findAll('div')[1].findAll('a')
            for a_tag in a_tags :
                Resources_urls.append(a_tag['href'])
    data_storage(change_string(Product_Title), Sku_SN,  change_string(Product_Description), Product_Image_urls, Resources_urls,  change_string(Product_Specification), Categorys)


def get_products(driver):
    try:
        driver.get("https://www.3m.com/3M/en_US/company-us/all-3m-products/?N=5002385+8709314+8710653+8710714+8711017+8718925+3294857497&rt=r3")
        time.sleep(1)
        while True:
            try:
                elements = driver.find_elements_by_css_selector("#pageContent > div.MMM--grids > div.component-container.MMM--grids-col.MMM--grids-col_single.ibmDndColumn.id-Z7_U00M8B1A0O3R40AQU5O6CFGOE2 > div > div > div.snaps--overflow.SNAPS--filtered_content_ajax.SNAPS--clear > div.MMM--grids-col.MMM--grids-col_main.SNAPS--beforeResponse_right > div > div.MMM--contentWrapper-bd > div.MMM--pagination")
                k = False
                for element in elements :
                    if element.value_of_css_property('display')=='block' and ('SHOW' in element.text):
                        k = True
                        element.click()
                        driver.implicitly_wait(20)
                        time.sleep(2)
                        break
                if k == False :
                    break
            except Exception as e:
                print("err->",str(e))
                pass
        elements = driver.find_element_by_id("comparisonForm").find_element_by_id("js-ajax-target").find_elements_by_css_selector("li > div > div > div > div > a")
        print(len(elements))
        product_urls = []
        for element in elements :
            product_urls.append(element.get_attribute('href'))
        for pro_url in product_urls :
            driver.get(pro_url)
            page = driver.find_element_by_tag_name('body')
            product_details = BeautifulSoup(page.get_attribute('innerHTML'), 'lxml')
            try:
                elements= page.find_elements_by_class_name("SNAPS--SelBxOpts")
                if (len(elements)>0) :
                    select_urls =[]
                    for element in elements :
                        if element.get_attribute('value') == 'default' : continue
                        select_urls.append(element.get_attribute('value'))
                    print("**** select options count: ", len(select_urls))
                    for select_url in select_urls :
                        print("select_url :", select_url )
                        driver.get(select_url)
                        page = driver.find_element_by_tag_name('body')
                        get_product_details(BeautifulSoup(page.get_attribute('innerHTML'), 'lxml'))
                else :
                    get_product_details(product_details)

            except Exception as e:
                print(str(e))
                pass

            time.sleep(1)

        # print(len(items))
    except Exception as e:
        print("error ->", str(e))
        pass

if  __name__ == "__main__":
    try:
        # server = 'tcp:tstdbset01.database.windows.net'
        # database = 'tstdb02'
        # username = 'sadminx'
        # password = 't*Te9qi?nk3'
        # sql_driver= '{ODBC Driver 17 for SQL Server}'
        # cnxn = pyodbc.connect('DRIVER='+sql_driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
        # cursor = cnxn.cursor()
        # create_sql = "CREATE TABLE scraping3m(ID int IDENTITY(1,1), Product_Title varchar(255) ,SKU_SN varchar(255), Product_Description TEXT, Product_Images TEXT, Product_Specification TEXT, Resource_Files TEXT, Manufacture varchar(255), Category1 varchar(255), Category2 varchar(255), Category3 varchar(255), Category4 varchar(255), Category5 varchar(255), Category6 varchar(255), Web_Structure varchar(255));"
        # try:
        #     cursor.execute(create_sql)
        #     cursor.commit()
        # except Exception as ex:
        #     pass
        # connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        # blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        # container_name = "scrapingdata"
        # try:
        #     container_client = blob_service_client.create_container(container_name)
        # except  Exception as ex:
        #     container_client = blob_service_client.get_container_client(container_name)
        #     pass

        driver = getChromeDriver()
        get_products(driver)
        driver.close()

    except Exception as ex:
        print('Exception ->', str(ex))