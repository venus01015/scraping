import json
from time import gmtime, strftime
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import requests
import urllib.request
from bs4 import BeautifulSoup
from os import path
import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pyodbc
import re

homedir = path.expanduser("~")

header_data = {
                'Host': 'www.pactiv.com',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'Dnt': '1',
            }

def getChromeDriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("start-maximized")
    return webdriver.Chrome(chrome_options=chrome_options)

def change_string(text):
    text = text.replace('<sup>','')
    text = text.replace('</sup>','') 
    text = text.replace('®','')              
    text = text.replace('&reg;','')
    text = text.replace('&trade;','')
    text = text.replace('<br> ','')
    text = text.replace('&amp; ','')
    text = text.replace('/','&')
    text = text.replace("'",'')
    text = text.replace('™','')
    return text

def data_storage(Mfg_ID, Category_ID, Product_Name, MPartNumber, UPC, Brand, Description, Details, Product_Image_urls, Files, Spec, Product_URL):
    try:
        Product_Name = Product_Name.replace("\"", "``").replace("'", "`")
        # Description = Description.replace("\"","``").replace("'","`")
        # Details = Details.replace("\"","`").replace("'","`")
        print("-- {} ---- Product_Name : '{}'".format(Category_ID, Product_Name))
        now = datetime.datetime.now()
        current_day= now.strftime("%m/%d/%Y")
        _odbc = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:tstdbset01.database.windows.net;PORT=1433;DATABASE=tstdb02;UID=sadminx;PWD=t*Te9qi?nk3'
        cnxn = pyodbc.connect(_odbc)
        cursor = cnxn.cursor()

        query = "SELECT top 1 * FROM items ORDER BY Item_ID DESC;"
        cursor.execute(query)
        row = cursor.fetchone()
        if row == None :
            query = "SET IDENTITY_INSERT items ON;"
            cursor.execute(query)
            cursor.commit()
            query = "INSERT INTO items(Item_ID, Name, URL, Mfg_ID, MPartNumber, UPC, Spec_ID, Description, Details, Category_ID, File_ID, Images, Created) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format("10001", Product_Name, Product_URL, Mfg_ID, MPartNumber, UPC, "", Description, Details, Category_ID, "", len(Product_Image_urls), current_day)
            cursor.execute(query)
            cursor.commit()
            query = "SET IDENTITY_INSERT items OFF;"
            cursor.execute(query)
            cursor.commit()
        elif row[0] < 10001 :
            query = "SET IDENTITY_INSERT items ON;"
            cursor.execute(query)
            cursor.commit()
            query = "INSERT INTO items(Item_ID, Name, URL, Mfg_ID, MPartNumber, UPC, Spec_ID, Description, Details, Category_ID, File_ID, Images, Created) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format("10001", Product_Name, Product_URL, Mfg_ID, MPartNumber, UPC, "", Description, Details, Category_ID, "", len(Product_Image_urls), current_day)
            cursor.execute(query)
            cursor.commit()
            query = "SET IDENTITY_INSERT items OFF;"
            cursor.execute(query)
            cursor.commit()
        else :
            query = "INSERT INTO items(Name, URL, Mfg_ID, MPartNumber, UPC, Spec_ID, Description, Details, Category_ID, File_ID, Images, Created) VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(Product_Name, Product_URL, Mfg_ID, MPartNumber, UPC, "", Description, Details, Category_ID, "", len(Product_Image_urls), current_day)
            cursor.execute(query)
            cursor.commit()

        query = "SELECT * FROM items WHERE URL LIKE '{}'".format(Product_URL)
        cursor.execute(query)
        row = cursor.fetchone()
        Item_ID = row[0]
        for i in range(len(Spec)):
            Spec[i] = Spec[i].replace("\"","``").replace("'","`")
        try:
            query = """INSERT INTO spec8pactiv(Item_ID, Material_Type , Color , Capacity , Dimensions , Case_Weight , Unit_Tier , Unit_Height , Cases_Per_Layer , Cases_Per_Pallet , Case_Pack , Case_Cube , Case_Length , Case_Width , Case_Height , Created)
                VALUES( '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')""".format(
                    Item_ID, Spec[0], Spec[1], Spec[2], Spec[3], Spec[4], Spec[5], Spec[6], Spec[7], Spec[8], Spec[9], Spec[10], Spec[11], Spec[12], Spec[13], current_day)
            cursor.execute(query)
            cursor.commit()
            query = "SELECT top 1 * FROM spec8pactiv ORDER BY Spec_ID DESC"
            cursor.execute(query)
            row = cursor.fetchone()
            Spec_ID = row[0]
        except Exception as err:
            print("spec8pactiv error ->", str(err))
            pass

        container_name = "portal"
        try:
            Product_Images =[]
            Str_Product_Images=""
            k = 0
            if len(Product_Image_urls) > 0 :
                for url in Product_Image_urls :
                    try:
                        k += 1
                        r = requests.get("https://www.pactiv.com" + url)
                        filename = url.split('/')[-1]
                        File_name, File_Type = os.path.splitext(filename)
                        new_name = "image{}{}".format(k, File_Type)
                        open(new_name, 'wb').write(r.content)
                        Product_Images.append(new_name)
                        Str_Product_Images = "{},{}".format(Str_Product_Images, new_name)
                    except:
                        pass
                Str_Product_Images=Str_Product_Images[1:]

            Resource_Files =[]
            Str_Files = ""
            k = 0
            if len(Files) > 0 :
                for url in Files:
                    try:
                        k += 1
                        r = requests.get("https://www.pactiv.com" + url, headers= header_data)
                        fname = re.findall("filename=(.+)", r.headers['content-disposition'])[0]
                        File_name, File_Type = os.path.splitext(fname)
                        new_name = "{}_{}{}".format(Product_Name, k, File_Type)
                        open(new_name, 'wb').write(r.content)
                        Resource_Files.append(new_name)
                    except:
                        pass

            try:
                if len(Product_Images)>0 :
                    for image in Product_Images :
                        url = "Pactiv/{}/{}".format(Item_ID, image)
                        blob_client = blob_service_client.get_blob_client(container=container_name,blob=url)
                        try:
                            with open(image, "rb") as data:
                                blob_client.upload_blob(data)
                        except :
                            pass

                if len(Resource_Files)>0 :
                    for filename in Resource_Files :
                        url = "Pactiv/{}/{}".format(Item_ID, filename)
                        blob_client = blob_service_client.get_blob_client(container=container_name,blob=url)
                        try:
                            with open(filename, "rb") as data:
                                blob_client.upload_blob(data)
                        except :
                            pass
                        query = "INSERT INTO files(File_Name, Item_ID, Created) VALUES( '{}', '{}', '{}')".format(filename, Item_ID, current_day)
                        cursor.execute(query)
                        cursor.commit()
                        query = "SELECT top 1 * FROM files ORDER BY File_ID DESC;"
                        cursor.execute(query)
                        row = cursor.fetchone()
                        File_ID = row[0]
                        Str_Files = "{},{}".format(Str_Files, File_ID)
                    Str_Files = Str_Files[1:]

            except Exception as err :
                print(" error -> ", str(err))
                pass
            query = "SELECT * FROM items WHERE URL LIKE '{}'".format(Product_URL)
            cursor.execute(query)
            row = cursor.fetchone()
            print(row[2])
            query = "UPDATE items SET File_ID = '{}', Spec_ID = '{}' where URL LIKE '{}'".format(Str_Files, Spec_ID, Product_URL)
            cursor.execute(query)
            cursor.commit()
            # ************************ remove files *********************

            if len(Product_Images)>0 :
                for filename in Product_Images :
                    try:
                        os.remove(filename)
                    except :
                        pass

            if len(Resource_Files)>0 :
                for filename in Resource_Files :
                    try:
                        os.remove(filename)
                    except :
                        pass
        except Exception as err :
            print(str(err))
            if len(Product_Images)>0 :
                for filename in Product_Images :
                    try:
                        os.remove(filename)
                    except :
                        pass

            if len(Resource_Files)>0 :
                for filename in Resource_Files :
                    try:
                        os.remove(filename)
                    except :
                        pass
    except Exception as err :
        print(str(err))

def get_detail_products(Mfg_ID, urls_json):
    for category in urls_json.keys():
        now = datetime.datetime.now()
        current_day= now.strftime("%m/%d/%Y")
        _odbc = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:tstdbset01.database.windows.net;PORT=1433;DATABASE=tstdb02;UID=sadminx;PWD=t*Te9qi?nk3'
        cnxn = pyodbc.connect(_odbc)
        cursor = cnxn.cursor()
        query = "SELECT * FROM categories WHERE CONVERT(VARCHAR, Name) ='{}'".format(category)
        try:
            cursor.execute(query)
            row = cursor.fetchone()
        except Exception as e:
            print(str(e))
            pass

        if row == None :
            query = "INSERT INTO categories(Name, Created, Checked, URL, Category_Description, Category_URL, Parent_ID, Category_Mark) VALUES('{}','{}','{}','','','','','')".format(category, current_day, current_day)
            cursor.execute(query)
            cursor.commit()
        else:
            query = "UPDATE categories SET Checked = '{}' where CONVERT(VARCHAR, Name) ='{}'".format(current_day, category)
            cursor.execute(query)
            cursor.commit()
        query = "SELECT * FROM categories WHERE CONVERT(VARCHAR, Name) ='{}'".format(category)
        cursor.execute(query)
        row = cursor.fetchone()
        Category_ID = row[0]

        for product_url in urls_json[category] :
            query = "SELECT * FROM items WHERE URL LIKE '{}'".format(product_url)
            cursor.execute(query)
            row = cursor.fetchone()
            if row == None :
                response = requests.get(product_url, timeout=None)
                if response.status_code != 200 :
                    continue
                soup = BeautifulSoup(response.content, 'html.parser')
                Product_Name = ""
                MPartNumber =""
                UPC =""
                Description = ""
                Details = ""
                Product_Image_urls=[]
                Files= []
                Brand = ""
                Spec = ["","","","","","","","","","","","","",""]
                Product_Name = soup.find('h2').text.strip().replace("\"","``").replace("'","`")
                try:
                    element = soup.find(attrs={'class': 'productSpecs Float33'})
                    spans = element.findAll('span')
                except:
                    pass
                try:
                    element = soup.find(attrs={'class': 'productShipping Float33'})
                    spans.extend(element.findAll('span'))
                except:
                    pass
                Product_Image_urls.append(soup.find(attrs={'class':'Float50'}).find('a')['href'])
                for span in spans :
                    if "" == span.text.strip(): continue
                    if ":" == span.text.strip()[-1]: continue
                    if not ":" in span.text.strip(): continue
                    contents = span.text.strip().split(":")
                    _title = contents[0].strip()
                    _value = contents[1].strip().replace("\xa0"," ")
                    if "Product" in _title :
                        MPartNumber = _value
                    if "GTIN" in _title :
                        UPC = _value
                    if "Material Type" in _title :
                        Spec[0] = _value
                    if "Color" in _title :
                        Spec[1] = _value
                    if "Capacity" in _title :
                        Spec[2] = _value
                    if "Dimensions" in _title :
                        Spec[3] = _value
                    if "Case Weight" in _title :
                        Spec[4] = _value
                    if "Unit Tier" in _title :
                        Spec[5] = _value
                    if "Unit Height" in _title :
                        Spec[6] = _value
                    if "Cases Per Layer" in _title :
                        Spec[7] = _value
                    if "Cases Per Pallet" in _title :
                        Spec[8] = _value
                    if "Case Pack" in _title :
                        Spec[9] = _value
                    if "Case Cube" in _title :
                        Spec[10] = _value
                    if "Case Length" in _title :
                        Spec[11] = _value
                    if "Case Width" in _title :
                        Spec[12] = _value
                    if "Case Height" in _title :
                        Spec[13] = _value

                spans = soup.find(attrs={'class': 'productResources Float33'}).findAll('li')
                for span in spans :
                    a_tag = span.find('a')
                    Files.append(a_tag['href'])
                data_storage(Mfg_ID, Category_ID, Product_Name, MPartNumber, UPC, Brand, Description, Details, Product_Image_urls, Files, Spec, product_url)

def get_link_of_all_products(driver):
    now = datetime.datetime.now()
    current_day= now.strftime("%m/%d/%Y")
    _odbc = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:tstdbset01.database.windows.net;PORT=1433;DATABASE=tstdb02;UID=sadminx;PWD=t*Te9qi?nk3'
    cnxn = pyodbc.connect(_odbc)
    cursor = cnxn.cursor()
    query = "SELECT * FROM manufacturer WHERE CONVERT(VARCHAR, Name)='Pactiv'"

    try:
        cursor.execute(query)
        row = cursor.fetchone()
    except Exception as e:
        print(str(e))
        pass

    if row == None :
        query = "INSERT INTO manufacturer(Name, Created, Checked) VALUES('Pactiv','{}','{}')".format(current_day,current_day)
        cursor.execute(query)
        cursor.commit()
    else:
        query = "UPDATE manufacturer SET Checked = '{}' where CONVERT(VARCHAR, Name) ='Pactiv'".format(current_day)
        cursor.execute(query)
        cursor.commit()
    query = "SELECT * FROM manufacturer WHERE CONVERT(VARCHAR, Name)='Pactiv'"
    cursor.execute(query)
    row = cursor.fetchone()
    Mfg_ID = row[0]

    try:
        driver.get("https://www.pactiv.com/Pactiv/Products/All-Products.htm#")
        driver.implicitly_wait(3)
        try:
            element = driver.find_element_by_css_selector("#F541_C24_fieldset > div.head > a")
            element.click()
            print("Clear")
            time.sleep(1)
        except:
            pass
        # elements = WebDriverWait(driver, 3).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#F541_C24_div > div")))
        elements = driver.find_elements_by_css_selector("#F541_C24_div > div")
        count = len(elements)
        urls_json= json.loads('{}')
        for No in range(count) :
            print("-----{}-----".format(No))
            driver.get("https://www.pactiv.com/Pactiv/Products/All-Products.htm#")
            driver.implicitly_wait(3)
            try:
                element = driver.find_element_by_css_selector("#F541_C24_fieldset > div.head > a")
                element.click()
                time.sleep(1)
            except:
                pass
            try:
                print("No -----", No)
                elements = driver.find_elements_by_css_selector("#F541_C24_div > div")
                Master_Category = elements[No].find_element_by_css_selector("span > label").text
                Master_Category = Master_Category[:Master_Category.find(" (")].strip()
                input_element = elements[No].find_element_by_css_selector("span > input")
                input_element.click()
                driver.implicitly_wait(5)
                time.sleep(1)
                urls = []
                while True:
                    try:
                        result = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "F541_ResultsDiv")))
                        product_elements = result.find_elements_by_css_selector("div.item")
                        for product_element in product_elements:
                            url = product_element.find_element_by_css_selector("div.otherStuff > h4 > a").get_attribute("href")
                            urls.append(url)
                        pages = result.find_element_by_class_name("paginationFooter").find_elements_by_css_selector("li")
                        pagenumbers = pages[1].text.strip().split(" ")
                        print(pagenumbers)
                        if pagenumbers[1] ==pagenumbers[3] :
                            time.sleep(1)
                            break
                        if pagenumbers[1] == 3 :
                            time.sleep(1)
                            break
                        pages[2].click()
                        time.sleep(2)
                    except:
                        pass
                urls_json.update({Master_Category:urls})
                print(len(urls))

            except Exception as err:
                print(str(err))
                pass
            # if No > 1 :
            #     break
        get_detail_products(Mfg_ID, urls_json)
    except Exception as e:
        print("err->",str(e))
        pass

if  __name__ == "__main__":
    try:
        server = 'tcp:tstdbset01.database.windows.net'
        database = 'tstdb02'
        username = 'sadminx'
        password = 't*Te9qi?nk3'
        driver= '{ODBC Driver 17 for SQL Server}'
        # cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
        _odbc = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:tstdbset01.database.windows.net;PORT=1433;DATABASE=tstdb02;UID=sadminx;PWD=t*Te9qi?nk3'
        cnxn = pyodbc.connect(_odbc)
        cursor = cnxn.cursor()        

        try:
            create_sql = "CREATE TABLE manufacturer(Mfg_ID int IDENTITY(1,1), Name TEXT, Created TEXT, Checked TEXT)"
            cursor.execute(create_sql)
            cursor.commit()
        except Exception as e:
            # print(str(e))
            pass
        try:
            create_sql = "create table categories(Category_ID int IDENTITY(1,1), Name TEXT, Created TEXT, Checked TEXT, URL TEXT, Category_Description TEXT, Category_URL TEXT, Parent_ID TEXT)"
            cursor.execute(create_sql)
            cursor.commit()
        except Exception as e:
            # print(str(e))
            pass

        try:
            create_sql = "create table items(Item_ID int IDENTITY(1,1), Name TEXT, URL TEXT, Mfg_ID TEXT, MPartNumber TEXT, UPC TEXT, Spec_ID TEXT, Description TEXT, Details TEXT, Category_ID TEXT, File_ID TEXT, Images TEXT, Created TEXT)"
            cursor.execute(create_sql)
            cursor.commit()
        except Exception as e:
            # print(str(e))
            pass

        try:
            create_sql = "create table spec8pactiv(Spec_ID int IDENTITY(1,1), Item_ID int, Material_Type TEXT, Color TEXT, Capacity TEXT, Dimensions TEXT, Case_Weight TEXT, Unit_Tier TEXT, Unit_Height TEXT, Cases_Per_Layer TEXT, Cases_Per_Pallet TEXT, Case_Pack TEXT, Case_Cube TEXT, Case_Length TEXT, Case_Width TEXT, Case_Height TEXT, Created TEXT)"
            cursor.execute(create_sql)
            cursor.commit()
        except Exception as e:
            print(str(e))
            pass

        try:
            create_sql = "create table files(File_ID int IDENTITY(1,1), File_Name TEXT, Item_ID TEXT, Created TEXT)"
            cursor.execute(create_sql)
            cursor.commit()
        except Exception as e:
            # print(str(e))
            pass


        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_name = "portal"
        try:
            container_client = blob_service_client.create_container(container_name)
        except  Exception as ex:
            # print('Exception ->', str(ex))
            container_client = blob_service_client.get_container_client(container_name)
            pass
        driver = getChromeDriver()
        get_link_of_all_products(driver)
        driver.close()

    except Exception as ex:
        print('Exception ->', str(ex))