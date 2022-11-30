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
import csv

def change_string(text):
    text = text.replace('®','')
    text = text.replace('&reg;','')
    text = text.replace('&trade;','')
    text = text.replace('&amp; ','')
    text = text.replace('"',"`")
    text = text.replace("'","`")
    text = text.replace('™','')
    return text

def fix_string(string):
    change=[]
    k=0
    for a in string:
        k += 1
        if a==" " or (k < 4):
            continue
        if (a.isupper()) == True and string[k-2:k-1]!=" ":
            change.append(string[k-1:k+2])
    for cha in change:
        string=string.replace(cha," "+cha)
    return string

def getlogindriver():
    driver = getIncognitoChromeDriver()
    driver.get("https://wwwsc.ekeystone.com/Categories/Towing")
    time.sleep(2)
    driver.find_element_by_xpath("/html/body/form/div[10]/div[2]/div[1]/div/div[1]/div[2]/div[1]/table/tbody/tr[1]/td[3]/input").send_keys("145302")
    driver.find_element_by_xpath("/html/body/form/div[10]/div[2]/div[1]/div/div[1]/div[2]/div[1]/table/tbody/tr[3]/td[3]/input").send_keys("8cde1808")
    driver.find_element_by_xpath("/html/body/form/div[10]/div[2]/div[1]/div/div[1]/div[2]/div[1]/table/tbody/tr[5]/td[3]/input").click()
    time.sleep(2)
    return driver

if  __name__ == "__main__":
    Main_Categories=[
        # '/Categories/Suspension',
        # '/Categories/WheelTire',
        # '/Categories/Exterior',
        # '/Categories/Cargo',
        # '/Categories/Towing',
        # '/Categories/LightingElectronics',
        '/Categories/Interior',
        '/Categories/DrivetrainBrakes',
        '/Categories/Exhaust',
        '/Categories/Engine',
        '/Categories/ChemicalTool',
        '/Categories/Marine',
        '/Categories/RV'
    ]
    driver = getlogindriver()
    for Main_Categorie in Main_Categories:
        csv_file = "keystone_{}.csv".format(Main_Categorie.split("/")[2])
        new_file = True
        try:
            with open(csv_file, 'r', encoding="utf-8") as file:
                reader = csv.reader(file,delimiter = ",")
                data = list(reader)
                if len(data)>0 :
                    new_file = False
        except:
            pass
        if new_file :
            with open(csv_file, 'a', encoding="utf-8", newline='') as file:
                fields = ['Product itle', 'SKU', 'Short Description', 'Long Description', 'Features', 'Published', 'Is featured?', 'Visibility in catalog', 'Categories', 'Supplier', 'Product Cost', 'Sale Price', 'Regular Price', 'Color', 'Material', 'Style', 'Size', 'Quantity', 'ORDER QTY', 'Images', 'Purchase', 'Vehicle', 'Fits']
                writer = csv.writer(file)
                writer.writerow(fields)

        DB_Name = "ekeystone.db"
        db_sqlite.create_db(DB_Name)
        conn = db_sqlite.connection(DB_Name)
        query = "create table if not exists scraping_data(Product_Title, SKU, Short_Description, Long_Description, Features, Published, Is_featured, Visibility_in_catalog, Categories, Supplier, Product_Cost, Sale_Price, Regular_Price, Color, Material, Style, Size, Quantity, ORDER_QTY, Images, Purchase, Vehicle, Fits)"
        db_sqlite.create_table(conn,query)
        query = "SELECT DISTINCT category, product_url FROM product_url WHERE complete='no' and category LIKE '%{}%'".format(Main_Categorie)# ORDER BY category ASC
        rows = db_sqlite.select_query(conn, query)
        if len(rows) == 0 :
            continue
        WebDriverWait(driver, 4).until(EC.visibility_of_element_located((By.ID, 'bodyContainer')))
        print(len(rows))

        for row in rows :
            time.sleep(random.uniform(1,3))
            try:
                Product_Title = ""
                Short_Description = ""
                Published = '1'
                Is_featured = '0'
                Visibility_in_catalog = 'visible'
                Color = ""
                Material = ""
                Style = ""
                Size = ""
                Quantity = ""
                Purchase = ""
                Vehicle = ""
                Images=""
                ORDER_QTY = ""
                Supplier = ""
                SKU =""
                Product_Cost = ""
                Sale_Price = ""
                Reqular_Price = ""
                Long_Description = ""
                Features = ""
                Categories = ""
                Fits = ""

                print(row[1])
                start_time = time.time()
                driver.implicitly_wait(4)
                driver.get(row[1])
                WebDriverWait(driver, 4).until(EC.visibility_of_element_located((By.ID, 'partTabs')))
                page = driver.find_element_by_id("bodyContainer")
                soup = BeautifulSoup(page.get_attribute('innerHTML'), 'lxml')
                if "No result found." in soup.text :
                    continue
                Product_Title = soup.find(attrs={'class':'partHeader'}).find('span').text
                Short_Description = change_string(soup.find(attrs={'class':'partDescription'}).find('span').text)
                spans = soup.find(attrs={'class':'checkoutTbl'}).findAll('span')

                INVENTORY_STATUS = soup.find(attrs={'id':'webcontent_0_row2_0_productDetailBasicInfo_tdInventory'}).text
                for span in spans :
                    try:
                        if "lblSupplierCode" in span['id']:
                            Supplier += "({})".format(span.text)
                            continue
                        if "lblSupplier" in span['id']:
                            Supplier = span.text
                            continue
                        if "lblSecondaryPartId" in span['id']:
                            SKU = span.text
                            continue
                        if "lblMyPrice" in span['id']:
                            Product_Cost = span.text
                            continue
                        if "lblJobberPrice" in span['id']:
                            Sale_Price = span.text
                            continue
                        if "lblRetailPrice" in span['id']:
                            Regular_Price = span.text
                            continue
                    except:
                        pass
                try:
                    element = soup.find(attrs={'id':'webcontent_0_row2_0_aZoomImage'}).find('img')
                    Images = element['src'].replace("&maxheight=250&maxwidth=400","&maxheight=550&maxwidth=550")
                except:
                    pass
                try:
                    elements = soup.find(attrs={'id':'item_detail_nav'}).findAll('img')
                    for element in elements:
                        Images += "|" + element['src'].replace("&maxheight=68&maxwidth=68","&maxheight=550&maxwidth=550")
                except:
                    pass
                try:
                    element = soup.find('div', attrs={'id':'webcontent_0_row2_0_productDetailTabs_upAdditionalInfoTab'})
                    Long_Description = change_string(element.find('div').find('div').find('span').text)
                    elements = soup.find(attrs={'class':'features'}).findAll('li')
                    for element in elements :
                        Features += element.text + "\n"
                    Features = change_string(Features)
                    try:
                        element = soup.find(attrs={'id':'webcontent_0_row2_0_productDetailBasicInfo_addToOrder_txtQuantity'})
                        ORDER_QTY= element['value']
                    except:
                        pass
                    elements = soup.findAll(attrs={'class':'productAttribute'})
                    for element in elements :
                        attribute_name = element.findAll('span')[0].text
                        attribute_value = element.findAll('span')[1].text
                        if ("Width" in attribute_name) or ("Size" in attribute_name):
                            Size = attribute_value
                        if ("Style" in attribute_name) :
                            Style = attribute_value
                        if ("Color" in attribute_name) :
                            Color = attribute_value
                        if ("Material" in attribute_name) :
                            Material = attribute_value
                        if ("Quantity" in attribute_name) :
                            Quantity = attribute_value

                except:
                    pass
                if random.uniform(0, 2) < 1 :
                    try:
                        element = driver.find_element_by_id("PartTabContainerScroll").find_element_by_css_selector(" div:nth-child(2) > a")
                        element.click()
                        element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, 'webcontent_0_row2_0_productDetailTabs_upThisFitsTab')))
                        elements = element.find_elements_by_css_selector("div")
                        k = 0
                        for element in elements:
                            k += 1
                            if k==1 : continue
                            Fits += element.text + "\n"
                        Fits = change_string(Fits)
                        time.sleep(random.uniform(0.5,2))
                    except:
                        pass
                Categories = "{} > {} > {}".format(row[0].split('/')[2], row[0].split('/')[3], row[0].split('/')[4])
                Categories = fix_string(Categories)
                fields = [Product_Title, SKU, Short_Description, Long_Description, Features, Published, Is_featured, Visibility_in_catalog, Categories, Supplier, Product_Cost, Sale_Price, Regular_Price, Color, Material, Style, Size, Quantity, ORDER_QTY, Images, Purchase, Vehicle, Fits]
                query = """INSERT INTO scraping_data VALUES("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")""".format(Product_Title, SKU, Short_Description, Long_Description, Features, Published, Is_featured, Visibility_in_catalog, Categories, Supplier, Product_Cost, Sale_Price, Regular_Price, Color, Material, Style, Size, Quantity, ORDER_QTY, Images, Purchase, Vehicle, Fits)
                if db_sqlite.insert_query(conn,query) == False :
                    time
                    continue
                with open(csv_file, 'a', encoding="utf-8", newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(fields)
                query = "UPDATE product_url SET complete = 'okay' where product_url='{}'".format(row[1])
                db_sqlite.update_query(conn,query)
                print("--- %s ---" % (time.time() - start_time))
            except Exception as e:
                print(str(e))
                pass

        db_sqlite.close(conn)

    driver.close()


