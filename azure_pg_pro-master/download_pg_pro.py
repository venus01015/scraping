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

cursor = None
download_path = path.expanduser("~") + "/Downloads/"
download_path = download_path.replace("\\","/")
print(download_path)

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
    options.add_experimental_option('useAutomationExtension', False)
    driver_path='chromedriver.exe'
    options.add_argument('--user-data-dir=' + path.expanduser("~") + '/AppData/Local/Google/Chrome/User Data')
    return webdriver.Chrome(options=options,executable_path=driver_path)

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

def getDownLoadedFileName(driver, waitTime):

    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[2])
    try:
        driver.get('chrome://downloads')
        endTime = time.time()+waitTime
        name = None
        while True:
            try:
                downloadStatus = driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#description').innerHTML")
                downloadStatus = downloadStatus.replace("\n","")
                downloadStatus = downloadStatus.replace(" ","")
                if downloadStatus == "" :
                    name = driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#file-link').innerHTML")
                    name = name.replace("&amp;","&")
                    break
            except Exception as e:
                print("downloaded file name error -> ", str(e))
                pass
            time.sleep(0.01)
            if time.time() > endTime:
                break
    except:
        pass

    driver.close()
    driver.switch_to.window(driver.window_handles[1])
    return name

def screenImage(driver, url, image_name) :
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[2])
    try:
        driver.get(url)
        img=driver.find_element_by_xpath("/html/body/img")
        location = img.location
        size = img.size
        driver.save_screenshot(image_name)
        x = location['x']
        y = location['y']
        width = location['x']+size['width']
        height = location['y']+size['height']
        im = Image.open(image_name)
        im = im.crop((int(x), int(y), int(width), int(height)))
        im.save(image_name)
    except :
        pass
    driver.close()
    driver.switch_to.window(driver.window_handles[1])

def update_blob_query(Manufacturer, field, row):
    global cursor
    global container_name
    global blob_service_client
    #[Product_Title, Original_Name, File_Link, File_Name, File_Type[1:], "", "", "", "", "", "", "", Content_Length, ETag, Last_Modified_by_Mfg, "", Version, Status, Blob_Link, Web_Structure, Last_Verified, Create_Date, Product_Image, Product_Description, Str_SDS_SHEETS, Str_Attachments, Category_Title, Category_Description, Category_Image]
    #        0             1             2          3           4         5   6   7   8   9  10  11        12          13           14           15     16      17       18           19               20            21           22               23                 24              25                26               27                  28
    field[17] = "Archived"
    field[3] = row[1] + "__" + row[13] + "_" + row[17] + "_Archived" + row[5]
    field[18] = Manufacturer + "/Archived/" + field[3]
    if row[4]!="" :
        blob_client = blob_service_client.get_blob_client(container=container_name,blob=row[19])
        # download blob
        with open(row[4], "wb") as my_blob:
            download_stream = blob_client.download_blob()
            my_blob.write(download_stream.readall())
        # delete blob
        blob_client.delete_blob()
        # upload Archived blob
        blob_client = blob_service_client.get_blob_client(container=container_name,blob=field[18])
        with open(row[4], "rb") as data:
            blob_client.upload_blob(data)
    str_allfiles = ""
    if row[25] != "" and row[26] == "" :
        str_allfiles = row[25]
    elif row[25] =="" and row[26] != "":
        str_allfiles = row[26]
    elif row[25]!= "" and row[26]!="":
        str_allfiles = row[25] + "," + row[26]

    if str_allfiles != "":
        allfiles = str_allfiles.split(",")
        for one_file in allfiles :
            # download blob
            blob_client = blob_service_client.get_blob_client(container=container_name,blob=one_file)
            with open("updateblobfile", "wb") as my_blob:
                download_stream = blob_client.download_blob()
                my_blob.write(download_stream.readall())
            # delete blob
            blob_client.delete_blob()
            # upload Archived blob
            blob_client = blob_service_client.get_blob_client(container=container_name,blob=one_file.replace("/Current/","/Archived/"))
            with open("updateblobfile", "rb") as data:
                blob_client.upload_blob(data)
    New_SDS = row[25].replace("/Current/","/Archived/")
    New_Attachments = row[26].replace("/Current/","/Archived/")
    os.remove("updateblobfile")
    # run query
    _query = "UPDATE scrapingdata SET status='Archived', Last_Verified = '"+ field[20] + "', SDS = '"+ New_SDS + "', Attachments = '"+ New_Attachments + "', Last_Modified_by_SETVI = '"+ field[15] +"',Blob_Link = '"+ field[18] +"', File_Name = '"+ field[3] +"' WHERE  Title = '" + field[1] + "' AND Web_Structure = '" + field[19] + "'AND File_Link = '" + field[2] + "';"
    cursor.execute(_query)
    cursor.commit()

def insert_blob_sql(Manufacturer, field, row, Original_Name, Product_Image_Name, Category_Image_Name, Attachments, SDS_SHEETS) :
    global cursor
    global container_name
    global blob_service_client
    #[Product_Title, Original_Name, File_Link, File_Name, File_Type[1:], "", "", "", "", "", "", "", Content_Length, ETag, Last_Modified_by_Mfg, "", Version, Status, Blob_Link, Web_Structure, Last_Verified, Create_Date, Product_Image, Product_Description, Str_SDS_SHEETS, Str_Attachments, Category_Title, Category_Description, Category_Image]
    #        0             1             2          3           4         5   6   7   8   9  10  11        12          13           14           15     16      17       18           19               20            21           22               23                 24              25                26               27                  28
    ############ new add product
    _query = "INSERT INTO scrapingdata( Title,Original_Name,File_Link,File_Name,File_Type,Manufacturer,Master_Category,Sub_Category1,Sub_Category2,Sub_Category3,Sub_Category4,Content_Type,Content_Length,ETag,Last_Modified_by_Mfg,Last_Modified_by_SETVI,Version,Status,Blob_Link,Web_Structure, Last_Verified, Created_Date, Image, Description, SDS, Attachments, CategoryTitle, CategoryDescription, CategoryImage) VALUES ('"
    for k in range(len(field)-1) :
        _query += field[k]   + "','"
    _query += field[len(field)-1] + "');"
    ###### insert record
    try:
        cursor.execute(_query)
        cursor.commit()
    except :
        pass
    #**************  upload blob start******************
    blob_client = blob_service_client.get_blob_client(container=container_name,blob=field[18])
    try:
        with open(  Original_Name, "rb") as data:
            blob_client.upload_blob(data)
    except :
        pass

    if field[22] !="" :
        blob_client = blob_service_client.get_blob_client(container=container_name,blob=field[22])
        try:
            with open(  Product_Image_Name, "rb") as data:
                blob_client.upload_blob(data)
        except :
            pass

    if field[28] !="" :
        blob_client = blob_service_client.get_blob_client(container=container_name,blob=field[28])
        try:
            with open(  Category_Image_Name, "rb") as data:
                blob_client.upload_blob(data)
        except :
            pass

    if len(Attachments)>0 :
        for attachment in Attachments :
            strs = attachment.split("/")
            Attachment_Name = strs[len(strs)-1]
            blob_client = blob_service_client.get_blob_client(container=container_name,blob=attachment)
            try:
                with open(  Attachment_Name, "rb") as data:
                    blob_client.upload_blob(data)
            except :
                pass
    if len(SDS_SHEETS)>0 :
        for SDS_SHEET in SDS_SHEETS :
            strs = SDS_SHEET.split("/")
            SDS_SHEET_Name = strs[len(strs)-1]
            blob_client = blob_service_client.get_blob_client(container=container_name,blob=SDS_SHEET)
            try:
                with open(  SDS_SHEET_Name, "rb") as data:
                    blob_client.upload_blob(data)
            except :
                pass

def data_storage(driver, Manufacturer, Product_Title, Product_Description, Web_Product_Image, Category_Title, Category_Description, Web_Category_Image, Web_SDS_SHEETS, File_Attached, Web_Attachments, Web_Structure ) :
    ##############################
    global cursor
    global container_name
    Content_Length = ""
    ETag = ""
    Last_Modified_by_Mfg = ""
    Status = "Active"
    Version = "V1"
    Last_Modified_by_SETVI = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + " GMT"
    File_Link = File_Attached
    try:
        #********************* download images and link file, sds file, attachments file ***********************
        Original_Name = ""
        if File_Link !="" :
            r = requests.get(File_Link, headers=get_header())
            Original_Name =  r.headers['Content-Disposition'].split('"')[1]
            open(Original_Name, 'wb').write(r.content)
        r = requests.get(Web_Product_Image, headers=get_header())

        try:
            Content_Length = r.headers['Content-Length']
        except:
            pass
        try:
            ETag = r.headers['ETag']
            ETag = ETag[1:len(ETag)-1]
        except:
            pass
        try:
            Last_Modified_by_Mfg = r.headers['Last-Modified']
        except:
            pass

        Category_Image = ""
        if Web_Category_Image != "" :
            strs = Web_Category_Image.split("/")
            Category_Image_Name = "Category_IMG_" + strs[len(strs)-1]
            r = requests.get(Web_Category_Image, headers=get_header())
            open(Category_Image_Name, 'wb').write(r.content)
            Category_Image = Manufacturer + "/Current/" + Category_Image_Name

        Product_Image = ""
        if Web_Product_Image != "" :
            strs = Web_Product_Image.split("/")
            filename, File_Type = os.path.splitext( strs[len(strs)-1])
            Product_Image_Name = Product_Title + "_IMG" + "_" + Content_Length + ".png"
            r = requests.get(Web_Product_Image, headers=get_header())
            open(Product_Image_Name, 'wb').write(r.content)
            Product_Image = Manufacturer + "/Current/" + Product_Image_Name

        Str_SDS_SHEETS = ""
        SDS_SHEETS =[]
        k = 0
        if len(Web_SDS_SHEETS) > 0 :
            for Web_SDS in Web_SDS_SHEETS :
                k += 1
                r = requests.get(Web_SDS, headers=get_header())
                OriginFile =  r.headers['Content-Disposition'].split('"')[1]
                filename, File_Type = os.path.splitext(OriginFile)
                SDS_Name = Product_Title + "_SDS" + str(k) + "_" + Content_Length + "_" + File_Type
                open(SDS_Name, 'wb').write(r.content)
                SDS_SHEETS.append(Manufacturer + "/Current/" + SDS_Name)
                Str_SDS_SHEETS += "," + Manufacturer + "/Current/" + SDS_Name
            Str_SDS_SHEETS = Str_SDS_SHEETS[1:]

        Str_Attachments = ""
        Attachments = []
        k = 0
        if len(Web_Attachments) >0 :
            for attachment in Web_Attachments :
                k += 1
                r = requests.get(attachment, headers=get_header())
                OriginFile =  r.headers['Content-Disposition'].split('"')[1]
                filename, File_Type = os.path.splitext(OriginFile)
                Attachment_Name = Product_Title + "_ADD" + str(k) + "_" + Content_Length + "_" + File_Type
                open(Attachment_Name, 'wb').write(r.content)
                Attachments.append(Manufacturer + "/Current/" + Attachment_Name)
                Str_Attachments += "," + Manufacturer + "/Current/" + Attachment_Name
            Str_Attachments = Str_Attachments[1:]
        #********************* End (download images and link file, sds file, attachments file) ***********************
        Last_Verified = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + " GMT"
        Create_Date = Last_Modified_by_SETVI
        if Original_Name !="" :
            filename, File_Type = os.path.splitext(Original_Name)
            File_Name = Product_Title + "__" + Content_Length + File_Type
            Blob_Link = Manufacturer + "/Current/" + File_Name
        else :
            File_Name = ""
            Blob_Link = ""

        field = [Product_Title, Original_Name, File_Link, File_Name, File_Type[1:], "", "", "", "", "", "", "", Content_Length, ETag, Last_Modified_by_Mfg, "", Version, Status, Blob_Link, Web_Structure, Last_Verified, Create_Date, Product_Image, Product_Description, Str_SDS_SHEETS, Str_Attachments, Category_Title, Category_Description, Category_Image]
        #               0             1             2          3           4         5   6   7   8   9  10  11        12          13           14           15     16      17       18           19               20            21           22               23                 24              25                26               27                  28
        strs = Web_Structure.split("/")
        for k in range(len(strs)) :
            field[5+k] = strs[k]
        try:
            cursor.execute("SELECT * FROM scrapingdata WHERE Title = '" + Product_Title + "' AND Web_Structure = '" + Web_Structure + "'AND File_Link = '" + File_Link + "';")
            row = cursor.fetchone()
            if Product_Title != "" :
                if row : ######### if already exist product
                    ######## if change ETag, ContentLength, Last_Modified_by_Mfg of product inforamtion
                    if Content_Length != row[13] or ETag != row[14] or Last_Modified_by_Mfg != row[15] :
                        cursor.execute("SELECT * FROM scrapingdata WHERE Title = '" + Product_Title + "' AND Web_Structure <> '" + Web_Structure + "'AND File_Link = '" + File_Link + "';")
                        row_another = cursor.fetchone()
                        if row_another : # if there is another product with same file link
                            _query = "UPDATE scrapingdata SET status='Archived', Last_Verified = '"+ Last_Verified + "', Last_Modified_by_SETVI = '"+ Last_Modified_by_SETVI +"' WHERE Title = '" + Product_Title + "' AND Web_Structure = '" + Web_Structure + "'AND File_Link = '" + File_Link + "';"
                            cursor.execute(_query)
                            cursor.commit()
                        else : # if no exist another product with same file link
                            field[19] = Last_Modified_by_SETVI
                            update_blob_query(Manufacturer, field, row)
                            ############ new add
                            field[16]="V"+str(int(row[17][1:])+1)
                            insert_blob_sql(Manufacturer, field, row, Original_Name, Product_Image_Name, Category_Image_Name, Attachments,SDS_SHEETS)
                    ######## if not change ETag, ContentLength, Last_Modified_by_Mfg of product inforamtion
                    elif row[18] == 'Active':
                        _query = "UPDATE scrapingdata SET Last_Verified = '"+ Last_Verified + "' WHERE Status = 'Active' AND Title = '" + Product_Title + "' AND Web_Structure = '" + Web_Structure + "' AND File_Link = '" + File_Link + "';"
                        cursor.execute(_query)
                        cursor.commit()
                else : ########## if not exist product
                    insert_blob_sql( Manufacturer, field, row, Original_Name, Product_Image_Name, Category_Image_Name, Attachments,SDS_SHEETS)
        except Exception as err :
            print(" error -> ", str(err))
            server = 'tcp:tstdbset01.database.windows.net'
            database = 'tstdb02'
            username = 'sadminx'
            password = 't*Te9qi?nk3'
            driver= '{ODBC Driver 17 for SQL Server}'
            cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
            cursor = cnxn.cursor()
            pass
        # ************************ remove files start*********************
        try:
            os.remove(  Original_Name)
        except :
            pass

        if Product_Image !="" :
            try:
                os.remove(  Product_Image_Name)
            except :
                pass

        if Category_Image !="" :
            try:
                os.remove(  Category_Image_Name)
            except :
                pass

        if len(Attachments)>0 :
            for attachment in Attachments :
                strs = attachment.split("/")
                Attachment_Name = strs[len(strs)-1]
                try:
                    os.remove(  Attachment_Name)
                except :
                    pass
        if len(SDS_SHEETS)>0 :
            for SDS_SHEET in SDS_SHEETS :
                strs = SDS_SHEET.split("/")
                SDS_SHEET_Name = strs[len(strs)-1]
                try:
                    os.remove(  SDS_SHEET_Name)
                except :
                    pass
        # ************************ remove files end *********************
    except Exception as err :
        #print("Add Product error ->", str(err))
        time.sleep(0.01)
        pass
    ##############################
    return

def get_elements_solution(driver):
    try:
        driver.get("https://pgpro.com/")
        Product_Title = ""
        Product_Description =""
        Product_Image =""
        Category_Title =""
        Category_Description =""
        Category_Image =""
        SDS_SHEETS =[]
        File_Attached =""
        Attachments = []
        Web_Structure = ""
        driver.implicitly_wait(20)                                                                      #site_navigation_wrapper > div.container.desktop > nav > ul:nth-child(1) > li.parent.solution.split_menu > a
        menu_item = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#site_navigation_wrapper > div.container.desktop > nav > ul:nth-child(1) > li.parent.solution.split_menu > a")))
        menu_item.click()
        time.sleep(1)
        sections = WebDriverWait(driver, 1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#site_navigation_wrapper > div.container.desktop > nav > ul:nth-child(1) > li.parent.solution.split_menu > nav > section")))
        Category1_all= []
        for section in sections :
            try:
                Category1s = WebDriverWait(section, 1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "ul > li > a")))
                for Category1 in Category1s :
                    try:
                        Category1_all.append(Category1.text + "->" + Category1.get_attribute("href"))
                    except Exception as e:
                        print("err->",str(e))
                        pass
            except Exception as e:
                print("Category1 find err->",str(e))
                pass
        time.sleep(5)
        Cat1 =0
        for Category1 in Category1_all :
            Cat1+=1
            if(Cat1<1) :
                continue
            Category1_text = Category1.split("->")[0]
            Category1_text = change_string(Category1_text)
            Category1_url = Category1.split("->")[1]
            driver.get(Category1_url)
            driver.implicitly_wait(10)
            try:
                Category_Image = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div:nth-child(5) > div > div > figure > img").get_attribute("src")
            except:
                try:
                    Category_Image = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div:nth-child(5) > div > div > img.full_image_large").get_attribute("src")
                except:
                    continue
            driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
            time.sleep(0.3)
            try:
                Category2s = WebDriverWait(driver, 1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#pg_main > div.primary_wrapper > div.container.margin_section > div > header.inline > ul > li > a")))
                num = 0
                for Category2 in Category2s :
                    try :
                        Category2_text = Category2.get_attribute("Title")
                        Category2_text = change_string(Category2_text)
                        num += 1
                        if num < 1:
                            continue
                        if num>1 :
                            Category2.click()
                            time.sleep(0.5)
                        Category_Title = ""
                        Category_Description = ""
                        try:
                            Category_Title = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.container.margin_section > div > div > section:nth-child(" + str(num) + ") > div:nth-child(1) > div > div > strong").text
                            Category_Description = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.container.margin_section > div > div > section:nth-child(" + str(num) + ") > div:nth-child(1) > div > div > p").text
                        except :
                            pass
                        Category_Title = change_string(Category_Title)
                        Category_Description = change_string(Category_Description)
                        elements = WebDriverWait(driver, 2).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#pg_main > div.primary_wrapper > div.container.margin_section > div > div > section:nth-child(" + str(num) + ")  > div > div > section > ul > li > div.details > a.image")))
                        k = 0 
                        for element in elements :
                            k+=1
                            if k<1:
                                continue                            
                            element.send_keys(Keys.CONTROL + Keys.RETURN)
                            driver.switch_to.window(window_name=driver.window_handles[1])
                            driver.implicitly_wait(10)
                            Web_Structure = "PG_Pro/Solutions/" + Category1_text + "/" + Category2_text + "/"
                            try:
                                Product_Title = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.product_page_header.margin_headline.margin_section > div > div.main_details > div > h1").text
                                Product_Image = driver.find_element_by_css_selector("#productSlider > div > div > div > img.slider_content").get_attribute("src")
                                Product_Description = ""
                                try:
                                    Product_Description = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.product_page_header.margin_headline.margin_section > div > div.main_details > div > div.no_container > div").text
                                except:
                                    pass
                                Product_Title = change_string(Product_Title)
                                Product_Description = change_string(Product_Description)
                                ################   File Sheet   ######################
                                SDS_SHEETS = []
                                try:
                                    sheets = WebDriverWait(driver, 1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#pg_main > div.primary_wrapper > div:nth-child(7) > div > section > ul > li > div.actions > div > a")))
                                    for sheet in sheets :
                                        sheet.send_keys(Keys.CONTROL + Keys.RETURN)
                                        driver.switch_to.window(window_name=driver.window_handles[2])
                                        try:
                                            sheet_link = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "body > div.sku_modal > div > a:nth-child(2)")))
                                            SDS_SHEETS.append(sheet_link.get_attribute("href"))
                                        except Exception as e:
                                            print("get sheet error -> ", str(e))
                                            pass
                                        driver.close()
                                        driver.switch_to.window(window_name=driver.window_handles[1])
                                except:
                                    pass
                                ################   File Attached   ######################
                                try:
                                    element = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.container.pg_margin_section > div > div > div.primary > a")
                                    element.send_keys(Keys.CONTROL + Keys.RETURN)
                                    driver.switch_to.window(window_name=driver.window_handles[2])
                                    File_Attached = ""
                                    try:
                                        File_Attached = driver.find_element_by_css_selector("body > article > div > div.details.span10.pull-left > div > table > tbody > tr:nth-child(1) > td.last.actions > a").get_attribute("href")
                                    except Exception as e:
                                        print("get attache file error -> ", str(e))
                                        File_Attached = ""
                                        pass
                                    driver.close()
                                    driver.switch_to.window(window_name=driver.window_handles[1])
                                except:
                                    pass
                            except Exception as e:
                                # print("switch tab err->",str(e))
                                time.sleep(0.01)
                                pass
                            driver.close()
                            driver.switch_to.window(window_name=driver.window_handles[0])
                            data_storage(driver, "PG_Pro", Product_Title, Product_Description, Product_Image, Category_Title, Category_Description, Category_Image, SDS_SHEETS, File_Attached, Attachments, Web_Structure )
                            time.sleep(0.01)
                    except Exception as e:
                        # print("Product find err->",str(e))
                        time.sleep(0.01)
                        pass
            except Exception as e :
                try:
                    Category_Title = ""
                    Category_Description = ""
                    try:
                        Category_Title = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div:nth-child(8) > h3").text
                        Category_Description = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div:nth-child(8) > p").text
                    except :
                        pass
                    Category_Title = change_string(Category_Title)
                    Category_Description = change_string(Category_Description)
                    elements = WebDriverWait(driver, 2).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#pg_main > div.primary_wrapper > div:nth-child(12) > div > div.totalfs__prods-items > div > div.totalfs__prods-item > p > a")))
                    k = 0
                    for element in elements :
                        k+=1
                        if k<1:
                            continue                            
                        element.send_keys(Keys.CONTROL + Keys.RETURN)
                        driver.switch_to.window(window_name=driver.window_handles[1])
                        driver.implicitly_wait(10)
                        Web_Structure = "PG_Pro/Solutions/" + Category1_text + "/"
                        try:
                            Product_Title = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.product_page_header.margin_headline.margin_section > div > div.main_details > div > h1").text
                            Product_Image = driver.find_element_by_css_selector("#productSlider > div > div > div > img.slider_content").get_attribute("src")
                            Product_Description = ""
                            try:
                                Product_Description = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.product_page_header.margin_headline.margin_section > div > div.main_details > div > div.no_container > div").text
                            except:
                                pass

                            Product_Title = change_string(Product_Title)
                            Product_Description = change_string(Product_Description)
                            ################   File Sheet   ######################
                            SDS_SHEETS = []
                            try:
                                sheets = WebDriverWait(driver, 1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#pg_main > div.primary_wrapper > div:nth-child(7) > div > section > ul > li > div.actions > div > a")))
                                for sheet in sheets :
                                    sheet.send_keys(Keys.CONTROL + Keys.RETURN)
                                    driver.switch_to.window(window_name=driver.window_handles[2])
                                    try:
                                        sheet_link = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "body > div.sku_modal > div > a:nth-child(2)")))
                                        SDS_SHEETS.append(sheet_link.get_attribute("href"))
                                    except Exception as e:
                                        print("get sheet error -> ", str(e))
                                        pass
                                    driver.close()
                                    driver.switch_to.window(window_name=driver.window_handles[1])
                            except:
                                pass
                            ################   File Attached   ######################
                            try:
                                element = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.container.pg_margin_section > div > div > div.primary > a")
                                element.send_keys(Keys.CONTROL + Keys.RETURN)
                                driver.switch_to.window(window_name=driver.window_handles[2])
                                File_Attached = ""
                                try:
                                    File_Attached = driver.find_element_by_css_selector("body > article > div > div.details.span10.pull-left > div > table > tbody > tr:nth-child(1) > td.last.actions > a").get_attribute("href")
                                except Exception as e:
                                    print("get attache file error -> ", str(e))
                                    File_Attached = ""
                                    pass
                                driver.close()
                                driver.switch_to.window(window_name=driver.window_handles[1])
                            except:
                                pass
                        except Exception as e:
                            # print("switch tab err->",str(e))
                            time.sleep(0.01)
                            pass
                        driver.close()
                        driver.switch_to.window(window_name=driver.window_handles[0])
                        data_storage(driver, "PG_Pro", Product_Title, Product_Description, Product_Image, Category_Title, Category_Description, Category_Image, SDS_SHEETS, File_Attached, Attachments, Web_Structure )
                        time.sleep(0.01)

                except:
                    pass
                continue
            time.sleep(1)


    except Exception as e:
        print("err->",str(e))
        pass

def get_elements_Product(driver):
    try:
        driver.get("https://pgpro.com/")
        Product_Title = ""
        Product_Description =""
        Product_Image =""
        Category_Title =""
        Category_Description =""
        Category_Image =""
        SDS_SHEETS =[]
        File_Attached =""
        Attachments = []
        Web_Structure = ""
        driver.implicitly_wait(20)
        menu_item = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#site_navigation_wrapper > div.container.desktop > nav > ul:nth-child(1) > li.parent.product.split_menu > a")))
        menu_item.click()
        time.sleep(1)
        sections = WebDriverWait(driver, 1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#site_navigation_wrapper > div.container.desktop > nav > ul:nth-child(1) > li.parent.product.split_menu > nav > section.categories > ul > li > span > a")))
        Category1_all= []
        for section in sections :
            try:
                Category1_all.append(section.text + "->" + section.get_attribute("href"))
            except Exception as e:
                # print("Category1 find err->",str(e))
                pass
        time.sleep(5)
        Cat1 =0
        for Category1 in Category1_all :
            Cat1+=1
            if(Cat1<1) :
                continue
            Category1_text = Category1.split("->")[0]
            Category1_text = change_string(Category1_text)
            Category1_url = Category1.split("->")[1]
            driver.get(Category1_url)
            driver.implicitly_wait(10)
            try:
                Category_Image = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div:nth-child(5) > div > div > figure > img").get_attribute("src")
            except:
                try:
                    Category_Image = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div:nth-child(5) > div > div > img.full_image_large").get_attribute("src")
                except:
                    pass
            driver.find_element_by_tag_name('body').send_keys(Keys.PAGE_DOWN)
            time.sleep(0.3)
            try:
                Category_Title = ""
                Category_Description = ""
                try:
                    Category_Title = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div:nth-child(5) > div > div > div > h1").text
                    # Category_Description = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div:nth-child(8) > p").text
                except :
                    pass
                Category_Title = change_string(Category_Title)
                elements = WebDriverWait(driver, 2).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#pg_main > div.primary_wrapper > div.container > div > section > ul > li > div.details > a.image")))
                k = 0
                for element in elements :
                    k+=1
                    if k<1:
                        continue
                    element.send_keys(Keys.CONTROL + Keys.RETURN)
                    driver.switch_to.window(window_name=driver.window_handles[1])
                    driver.implicitly_wait(10)
                    Web_Structure = "PG_Pro/Products/" + Category1_text + "/"
                    try:
                        Product_Title = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.product_page_header.margin_headline.margin_section > div > div.main_details > div > h1").text
                        Product_Image = driver.find_element_by_css_selector("#productSlider > div > div > div > img.slider_content").get_attribute("src")
                        Product_Description = ""
                        try:
                            Product_Description = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.product_page_header.margin_headline.margin_section > div > div.main_details > div > div.no_container > div").text
                        except:
                            pass
                        Product_Title = change_string(Product_Title)
                        Product_Description = change_string(Product_Description)
                        ################   File Sheet   ######################
                        SDS_SHEETS = []
                        try:
                            sheets = WebDriverWait(driver, 1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#pg_main > div.primary_wrapper > div:nth-child(7) > div > section > ul > li > div.actions > div > a")))
                            for sheet in sheets :
                                sheet.send_keys(Keys.CONTROL + Keys.RETURN)
                                driver.switch_to.window(window_name=driver.window_handles[2])
                                try:
                                    sheet_link = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "body > div.sku_modal > div > a:nth-child(2)")))
                                    SDS_SHEETS.append(sheet_link.get_attribute("href"))
                                except Exception as e:
                                    print("get sheet error -> ", str(e))
                                    pass
                                driver.close()
                                driver.switch_to.window(window_name=driver.window_handles[1])
                        except:
                            pass
                        ################   File Attached   ######################
                        try:
                            element = driver.find_element_by_css_selector("#pg_main > div.primary_wrapper > div.container.pg_margin_section > div > div > div.primary > a")
                            element.send_keys(Keys.CONTROL + Keys.RETURN)
                            driver.switch_to.window(window_name=driver.window_handles[2])
                            File_Attached = ""
                            try:
                                File_Attached = driver.find_element_by_css_selector("body > article > div > div.details.span10.pull-left > div > table > tbody > tr:nth-child(1) > td.last.actions > a").get_attribute("href")
                            except Exception as e:
                                print("get attache file error -> ", str(e))
                                File_Attached = ""
                                pass
                            driver.close()
                            driver.switch_to.window(window_name=driver.window_handles[1])
                        except:
                            pass
                    except Exception as e:
                        # print("switch tab err->",str(e))
                        time.sleep(0.01)
                        pass
                    driver.close()
                    driver.switch_to.window(window_name=driver.window_handles[0])
                    data_storage(driver, "PG_Pro", Product_Title, Product_Description, Product_Image, Category_Title, Category_Description, Category_Image, SDS_SHEETS, File_Attached, Attachments, Web_Structure )
                    time.sleep(0.01)
            except:
                pass
            time.sleep(1)
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
        cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
        cursor = cnxn.cursor()
        create_sql = "CREATE TABLE scrapingdata(ID int IDENTITY(1,1), Title varchar(255) , Original_Name varchar(255), File_Link varchar(255), File_Name varchar(128), File_Type varchar(8), Manufacturer varchar(32), Master_Category varchar(255), Sub_Category1 varchar(255), Sub_Category2 varchar(255), Sub_Category3 varchar(255), Sub_Category4 varchar(255), Content_Type varchar(255), Content_Length VARCHAR(128), ETag VARCHAR(128), Last_Modified_by_Mfg VARCHAR(32), Last_Modified_by_SETVI VARCHAR(32), Version VARCHAR(32), Status VARCHAR(32), Blob_Link VARCHAR(255), Web_Structure VARCHAR(255), Last_Verified VARCHAR(255), Created_date VARCHAR(255), Image VARCHAR(255), Description TEXT, SDS TEXT, Attachments TEXT, CategoryTitle VARCHAR(255), CategoryDescription TEXT, CategoryImage VARCHAR(255));"
        try:
            cursor.execute(create_sql)
            cursor.commit()
        except Exception as ex:
            pass
        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_name = "scrapingdata"
        try:
            container_client = blob_service_client.create_container(container_name)
        except  Exception as ex:
            container_client = blob_service_client.get_container_client(container_name)
            pass

        driver = getChromeDriver()
        get_elements_Product(driver)
        get_elements_solution(driver)
        driver.close()

    except Exception as ex:
        print('Exception ->', str(ex))