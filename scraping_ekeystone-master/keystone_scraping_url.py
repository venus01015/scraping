import json
from time import gmtime, strftime
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests
import urllib.request
import os, uuid
from getStyleDriver import getNormalChromeDriver, getIncognitoChromeDriver
import db_sqlite
from fake_useragent import UserAgent
from os import path
import random

download_path = path.expanduser("~") + "/Downloads/"
download_path = download_path.replace("\\","/")

def get_header() :
    ua=UserAgent()
    return {'User-Agent':ua.random,'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.3', 'Accept-Encoding':'none', 'Accept-Language':'en-US,en;q=0.8', 'Connection':'keep-alive'}

def getlogindriver():
    driver = getIncognitoChromeDriver()
    driver.implicitly_wait(20)
    driver.get("https://wwwsc.ekeystone.com/Categories/Suspension")
    time.sleep(2)
    driver.find_element_by_xpath("/html/body/form/div[10]/div[2]/div[1]/div/div[1]/div[2]/div[1]/table/tbody/tr[1]/td[3]/input").send_keys("145302")
    driver.find_element_by_xpath("/html/body/form/div[10]/div[2]/div[1]/div/div[1]/div[2]/div[1]/table/tbody/tr[3]/td[3]/input").send_keys("8cde1808")
    driver.find_element_by_xpath("/html/body/form/div[10]/div[2]/div[1]/div/div[1]/div[2]/div[1]/table/tbody/tr[5]/td[3]/input").click()
    time.sleep(2)
    return driver

def find_sub_categories(driver, main_sub) :
    global DB_Name
    driver.get(main_sub)
    time.sleep(2)
    try:
        page = driver.find_element_by_id("bodyContainer")
        soup = BeautifulSoup(page.get_attribute('innerHTML'), 'lxml')
        elements= soup.findAll('span',attrs={'valign':'top'})
        category_urls=json.loads('{}')
        for element in elements :
            try:
                a_tag = element.find('a')
                category_urls.update({a_tag.text:a_tag['href']})
            except:
                pass
        cou = 0
        for node in category_urls.keys():
            node_url = category_urls[node]
            if not 'browse=sub' in node_url :
                pattern_category = node_url
                continue
            cou += 1
            web_category = pattern_category + "/" + node
            # print(web_category,":::",node_url)
            category_url = "https://wwwsc.ekeystone.com" + node_url
            conn = db_sqlite.connection(DB_Name)
            if db_sqlite.exist_check_query(conn,"Select * FROM category_url WHERE category_url='{}'".format(category_url)) :
                continue
            driver.get(category_url)
            try:
                element = WebDriverWait(driver, 4).until(EC.visibility_of_element_located((By.ID, 'results')))
            except:
                continue
            if element == None :
                continue
            no = False
            while True:
                try:
                    results = driver.find_element_by_id("results")
                    soup = BeautifulSoup(results.get_attribute('innerHTML'), 'lxml')
                    elements = soup.findAll('div',attrs={'class':'resultsContentArea'})
                    for element in elements :
                        a_tag = element.find('a')
                        product_url = 'https://wwwsc.ekeystone.com' + a_tag['href']
                        query = "Select * FROM product_url WHERE product_url='{}'".format(product_url)
                        if db_sqlite.exist_check_query(conn,query) :
                            continue
                        query = "INSERT INTO product_url VALUES('{}','{}','{}')".format(web_category, 'no', product_url)
                        db_sqlite.insert_query(conn,query)
                    count_status = soup.find('div',attrs={'class':'resultsItemsPerPage'}).text.replace('\n', '').replace(' ', '').replace('\r', '')
                    all_cou = count_status.split('of')[-1]
                    current_cou = count_status.split('of')[-2].split('-')[-1]
                    if all_cou == current_cou :
                        break
                    if int(all_cou) > 2500 and int(current_cou) > 100 :
                        break
                    if int(all_cou) > 1000 and int(current_cou) > 100 :
                        break
                    if int(all_cou) > 300 and int(current_cou) > 100 :
                        break
                    pages_id = soup.find('div',attrs={'class':'resultsPages'}).find('div')['id']
                    element = driver.find_element_by_id(pages_id)
                    elements = element.find_elements_by_css_selector('a')
                    start_time = time.time()
                    for element in elements :
                        if "Next" in element.text:
                            element.click()
                            break
                    try:
                        WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.ID, 'webcontent_0_row2_0_upSearchProgress')))
                        WebDriverWait(driver, 4).until(EC.invisibility_of_element_located((By.ID, 'webcontent_0_row2_0_upSearchProgress')))
                        print(current_cou, all_cou, "--- %s ---" % (time.time() - start_time))
                    except Exception as err:
                        print("WebDriverWait:error->", str(err))
                        pass
                    time.sleep(random.uniform(0.5,3))
                except Exception as err:
                    print("error in while :", str(err))
                    pass
            if not no :
                query = "INSERT INTO category_url VALUES('{}','{}','{}')".format(web_category, 'ok', category_url)
                db_sqlite.insert_query(conn,query)
                db_sqlite.close(conn)

    except Exception as e:
        print(str(e))
        pass

if  __name__ == "__main__":
    DB_Name = "ekeystone.db"
    db_sqlite.create_db(DB_Name)
    conn = db_sqlite.connection(DB_Name)
    query = "create table if not exists category_url(category text, complete text, category_url text )"
    db_sqlite.create_table(conn,query)
    query = "create table if not exists product_url(category text, complete text, product_url text )"
    db_sqlite.create_table(conn,query)
    db_sqlite.close(conn)
    # exit()
    Main_Categories=[
        # 'https://wwwsc.ekeystone.com/Categories/Suspension',
        # 'https://wwwsc.ekeystone.com/Categories/WheelTire',
        # 'https://wwwsc.ekeystone.com/Categories/Exterior',
        # 'https://wwwsc.ekeystone.com/Categories/Cargo',
        # 'https://wwwsc.ekeystone.com/Categories/Towing',
        # 'https://wwwsc.ekeystone.com/Categories/LightingElectronics',
        # 'https://wwwsc.ekeystone.com/Categories/Interior',
        # 'https://wwwsc.ekeystone.com/Categories/DrivetrainBrakes',
        # 'https://wwwsc.ekeystone.com/Categories/Exhaust',
        # 'https://wwwsc.ekeystone.com/Categories/Engine',
        # 'https://wwwsc.ekeystone.com/Categories/ChemicalTool',
        # 'https://wwwsc.ekeystone.com/Categories/Marine',
        'https://wwwsc.ekeystone.com/Categories/RV'
    ]
    driver = getlogindriver()
    for main_cate in Main_Categories :
        time.sleep(random.uniform(1,4))
        print(main_cate)
        find_sub_categories(driver, main_cate)
        # break

    driver.close()
