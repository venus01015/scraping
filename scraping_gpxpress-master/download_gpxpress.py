import json
from time import gmtime, strftime
import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from os import path
import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pyodbc
from PIL import Image
from fake_useragent import UserAgent
from pynput.keyboard import Key, Controller
from pathlib import Path
from zipfile import ZipFile

with open('info_user.json') as f:
    info = json.load(f)  
download_folder = path.expanduser("~").replace("\\","/") + "/Downloads/"
download_sheet_name = download_folder + "pdfversion.pdf"
download_file_attachments = download_folder + "imagedownload.zip"
download_file_attach = ""
download_product_image = ""
try:
    os.remove(download_sheet_name)
except:
    pass
try:
    os.remove(download_file_attachments)
except:
    pass
try:
    os.remove(download_product_image)
except:
    pass
cursor = None
keyboard = None

def get_header() :
    ua=UserAgent()
    return {'User-Agent': ua.random,       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',      'Accept-Encoding': 'none',      'Accept-Language': 'en-US,en;q=0.8',      'Connection': 'keep-alive'}

def getDownLoadedFileName(driver, waitTime):

    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    try:
        driver.get('chrome://downloads')
        endTime = time.time()+waitTime
        name = None
        while True:
            try:
                downloadStatus = driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('#description').innerHTML")
                if ('-' in downloadStatus) or (',' in downloadStatus) :
                    continue
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
    driver.switch_to.window(driver.window_handles[0])
    return name

def screenImage(driver, image_name) :
    try:
        img = driver.find_element_by_css_selector("#pagecontentcontainer > section:nth-child(12) > div.c-detailAsset > div")
        location = img.location
        size = img.size
        driver.save_screenshot(image_name)
        x = location['x']
        y = location['y']
        width = location['x']+size['width']
        height = location['y']+size['height']
        im = Image.open(image_name)
        im = im.crop((int(x)+30, int(y), int(width)-35, int(height)-70))
        im.save(image_name)
    except :
        pass

def getChromeDriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # chrome_options.add_experimental_option('useAutomationExtension', False)
    return webdriver.Chrome(chrome_options=chrome_options)

def loginProcess(driver,userinfo):
    driver.implicitly_wait(20)
    driver.get("https://gpxpr.es/")
    time.sleep(3)
    driver.find_element_by_css_selector('#inputEmail').send_keys(userinfo["user"])
    driver.find_element_by_css_selector('#inputPassword').send_keys(userinfo["password"])
    submit_button = driver.find_element_by_css_selector('#submitBtn')
    ActionChains(driver).move_to_element(submit_button).click(submit_button).perform()
    time.sleep(1)
    return driver
 
def change_string(text):
    text = text.replace('<sup>','')
    text = text.replace('</sup>','')
    text = text.replace('®','')              
    text = text.replace('&reg;','')
    text = text.replace('&trade;','')
    text = text.replace('<br> ','')
    text = text.replace('&amp; ','')
    text = text.replace('/','&')
    text = text.replace(',','_')
    text = text.replace("'",'`')
    text = text.replace('"','inch')
    text = text.replace('™','')
    return text

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
    global download_product_image
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
    except Exception as e:
        print(str(e))
        pass
    #**************  upload blob start******************
    blob_client = blob_service_client.get_blob_client(container=container_name,blob=field[18])
    try:
        with open( download_folder + Original_Name, "rb") as data:
            blob_client.upload_blob(data)
    except Exception as e:
        print(str(e))
        pass

    if field[22] !="" :
        blob_client = blob_service_client.get_blob_client(container=container_name,blob=field[22])
        try:
            with open( download_product_image, "rb") as data:
                blob_client.upload_blob(data)
        except :
            pass

    if field[28] !="" :
        blob_client = blob_service_client.get_blob_client(container=container_name,blob=field[28])
        try:
            with open( download_folder + Category_Image_Name, "rb") as data:
                blob_client.upload_blob(data)
        except :
            pass

    if len(Attachments)>0 :
        for attachment in Attachments :
            # strs = attachment.split("/")
            # Attachment_Name = strs[len(strs)-1]
            blob_client = blob_service_client.get_blob_client(container=container_name,blob=attachment)
            try:
                with open( download_file_attachments, "rb") as data:
                    blob_client.upload_blob(data)
            except :
                pass
    if len(SDS_SHEETS)>0 :
        for SDS_SHEET in SDS_SHEETS :
            # strs = SDS_SHEET.split("/")
            # SDS_SHEET_Name = strs[len(strs)-1]
            blob_client = blob_service_client.get_blob_client(container=container_name,blob=SDS_SHEET)
            try:
                with open( download_sheet_name, "rb") as data:
                    blob_client.upload_blob(data)
            except :
                pass

def data_storage(driver, Manufacturer, Product_Title, Product_Description, Web_Product_Image, Category_Title, Category_Description, Web_Category_Image, Web_SDS_SHEETS, File_Attached,download_file_attach, Web_Attachments, Web_Structure ) :
    ##############################
    global cursor
    global container_name
    global download_product_image
    Content_Length = ""
    ETag = ""
    Last_Modified_by_Mfg = ""
    Status = "Active"
    Version = "V1"
    Last_Modified_by_SETVI = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + " GMT"
    File_Link = File_Attached
    Category_Image = ""
    Category_Image_Name = ""
    Product_Image = ""
    Product_Image_Name = ""
    Str_SDS_SHEETS = ""
    SDS_SHEETS =[]
    Str_Attachments = ""
    Attachments = []
    Last_Verified = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + " GMT"
    Create_Date = Last_Modified_by_SETVI
    Original_Name = ""
    try:
        #********************* download images and link file, sds file, attachments file ***********************
        if download_file_attach !="" :
            Original_Name = download_file_attach.split("/")[-1]
            my_stat = Path(download_file_attach).stat()
        try:
            Content_Length = str(my_stat.st_size)
        except:
            pass
        try:
            ETag = str(my_stat.st_dev)
        except:
            pass
        try:
            Last_Modified_by_Mfg = ""
        except:
            pass
        if Web_Category_Image != "" :
            strs = Web_Category_Image.split("/")[-1]
            Category_Image_Name = "Category_IMG_" + strs
            Category_Image = Manufacturer + "/Current/" + Category_Image_Name
        if Web_Product_Image != "" :
            strs = Web_Product_Image.split("/")[-1]
            filename, File_Type = os.path.splitext(strs)
            Product_Image_Name = Product_Title.replace(",","").replace("#","") + '_IMG_' + Web_Structure.split("/")[-1] + "_" + Content_Length + File_Type
            Product_Image = Manufacturer + "/Current/" + Product_Image_Name
        k = 0
        if len(Web_SDS_SHEETS) > 0 :
            for Web_SDS in Web_SDS_SHEETS :
                k += 1
                filename, File_Type = os.path.splitext(Web_SDS)
                SDS_Name = Product_Title.replace(",","").replace("#","") + "_SDS" + str(k) + "_" + Web_Structure.split("/")[-1] + "_" + Content_Length + File_Type
                SDS_SHEETS.append(Manufacturer + "/Current/" + SDS_Name)
                Str_SDS_SHEETS += "," + Manufacturer + "/Current/" + SDS_Name
            Str_SDS_SHEETS = Str_SDS_SHEETS[1:]
        k = 0
        if len(Web_Attachments) >0 :
            for attachment in Web_Attachments :
                k += 1
                filename, File_Type = os.path.splitext(attachment)
                Attachment_Name = Product_Title.replace(",","").replace("#","") + "_ADD" + str(k) + "_" + Web_Structure.split("/")[-1] + "_" + Content_Length + File_Type
                Attachments.append(Manufacturer + "/Current/" + Attachment_Name)
                Str_Attachments += "," + Manufacturer + "/Current/" + Attachment_Name
            Str_Attachments = Str_Attachments[1:]
        #********************* End (download images and link file, sds file, attachments file) ***********************
        if Original_Name !="" :
            filename, File_Type = os.path.splitext(Original_Name)
            File_Name = Product_Title.replace(",","").replace("#","") + "_" + Content_Length + File_Type
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
            if Product_Title != "" : # if Product Title exist
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
            else : # if Product Title not exist
                if not(row) : ######### if not exist product
                    filename, File_Type = os.path.splitext(Original_Name)
                    field[0] = filename
                    field[15] = Last_Modified_by_SETVI
                    field[17] = "Archived"
                    field[3] = filename + "__V1_Archived" + File_Type
                    field[18] = Manufacturer + "/Archived/" + field[3]
                    field[24]= field[24].replace("/Current/", "/Archived/")
                    field[25]= field[25].replace("/Current/", "/Archived/")
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
    except Exception as err :
        print("Add Product error ->", str(err))

        time.sleep(0.01)
        pass
    # ************************ remove files start*********************
    try:
        os.remove(download_folder + Original_Name)
    except :
        pass
    try:
        os.remove(download_product_image)
    except :
        pass
    if Category_Image !="" :
        try:
            os.remove( download_folder +  Category_Image_Name)
        except :
            pass
    try:
        os.remove( download_file_attachments)
    except :
        pass
    try:
        os.remove( download_sheet_name)
    except :
        pass
    # ************************ remove files end *********************
    return

def search_url(driver, url, Web_Structure):
    global download_product_image
    global keyboard
    driver.get(url)
    time.sleep(1)
    try:
        Sub_Categorys = WebDriverWait(driver,0.5).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR,"#pagecontentcontainer > section.c-contentWrap > ul.c-catList > li > a")))
        #   get urls of sub category *************************
        _sub_url=json.loads('{}')
        for Sub_Category in Sub_Categorys:
            title = change_string( Sub_Category.get_attribute('title'))
            _url = Sub_Category.get_attribute("href")
            _sub_url.update({title:_url})
        for key in _sub_url.keys():
            if key == "Paper Towels & Dispensers" or key == "Toilet Paper_ Facial Tissue & Dispensers" or key=="Skin Care & Dispensers" or key == "Cups_Lids_& Straws" or key == "Cutlery & Dispensers" or key == "Wipers & Dispensers" or key == "Air Care & Dispensers":
                continue
            search_url(driver, _sub_url[key], Web_Structure + '/' + key )
        ##############################################################
    except:
        Product_Title = ""
        Product_Description =""
        Product_Image = ""
        Category_Title =""
        Category_Description =""
        Category_Image =""
        File_Attached =""
        SDS_SHEETS =[]
        Attachments = []
        # Web_Structure
        try:
            Content_Types = WebDriverWait(driver,1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR,"#pagecontentcontainer > section.c-contentWrap--full > div > ul > li > div.c-objectInfo > h2 > a")))
            Product_URLS =[]
            for Product in Content_Types :
                Product_URLS.append(Product.get_attribute('href'))
            for url in Product_URLS :
                try:
                    driver.implicitly_wait(20)
                    driver.get(url)
                    Product_Title = change_string(driver.find_element_by_css_selector("#pagecontentcontainer > section:nth-child(12) > div.c-detailInfo > h2").text)
                    Product_Description = change_string(driver.find_element_by_css_selector("#pagecontentcontainer > section:nth-child(12) > div.c-detailInfo > div.c-productMeta.c-panel__showhide.js-panel-showhide > section > p.js-detailDesc.c-detailDesc").text)
                    driver.find_element_by_css_selector("#pagecontentcontainer > section:nth-child(13) > section > ul > li:nth-child(4)").click()
                    time.sleep(0.1)
                    try:
                        element = driver.find_element_by_css_selector("#prod > div > div > div.gp-resource-title > div.gp-resource-viewshare > span.view > a")
                        File_Attached = element.get_attribute('href')
                        ActionChains(driver).click(element).perform()
                        time.sleep(0.1)
                        try:
                            driver.switch_to.window(window_name=driver.window_handles[1])
                            time.sleep(0.1)
                            driver.close()
                            driver.switch_to.window(window_name=driver.window_handles[0])
                        except:
                            driver.switch_to.window(window_name=driver.window_handles[0])
                            pass
                        filename = getDownLoadedFileName(driver,20)
                        if(filename == 'imagedownload.zip') :
                            continue
                        download_file_attach = download_folder + filename
                    except:
                        continue
                    # ******************************** Product PDF Link *******************************
                    driver.find_element_by_css_selector("#pagecontentcontainer > section:nth-child(12) > div.c-detailInfo > div.c-productMeta.c-panel__showhide.js-panel-showhide > ul > li:nth-child(3) > a").click()
                    WebDriverWait(driver,1).until(EC.visibility_of_element_located((By.CSS_SELECTOR,"#js-scroll-top > div.mfp-wrap.mfp-auto-cursor.mfp-ready")))
                    element = driver.find_element_by_css_selector("#pdf-generate-form > div.c-btngroup--center > button.c-btn--positive")
                    driver.implicitly_wait(20)
                    element.send_keys(Keys.CONTROL + Keys.RETURN)
                    driver.switch_to.window(window_name=driver.window_handles[1])
                    time.sleep(3)
                    keyboard.press(Key.ctrl)
                    keyboard.press('s')
                    keyboard.release('s')
                    keyboard.release(Key.ctrl)
                    time.sleep(0.5)
                    keyboard.press(Key.enter)
                    keyboard.release(Key.enter)
                    time.sleep(0.5)
                    driver.close()
                    driver.switch_to.window(window_name=driver.window_handles[0])
                    download_sheet_name = download_folder +getDownLoadedFileName(driver,20)
                    driver.find_element_by_css_selector("#js-scroll-top > div.mfp-wrap.mfp-auto-cursor.mfp-ready > div > div.mfp-content > div > button").click()
                    # ---------------------------------------------------------------------------------------
                    # ******************************** Image Download Link *******************************
                    driver.find_element_by_css_selector("#pagecontentcontainer > section:nth-child(12) > div.c-detailInfo > div.c-productMeta.c-panel__showhide.js-panel-showhide > ul > li:nth-child(4) > a").click()
                    WebDriverWait(driver,1).until(EC.visibility_of_element_located((By.CSS_SELECTOR,"#js-scroll-top > div.mfp-wrap.mfp-auto-cursor.mfp-ready")))
                    driver.find_element_by_css_selector("#imagedowloadform > div.c-btngroup--center > button.c-btn--positive").click()
                    time.sleep(0.1)
                    download_file_attachments = download_folder + getDownLoadedFileName(driver,20)
                    time.sleep(0.5)
                    driver.find_element_by_css_selector("#js-scroll-top > div.mfp-wrap.mfp-auto-cursor.mfp-ready > div > div.mfp-content > div > button").click()
                    Product_Image = ""
                    try:
                        with ZipFile(download_file_attachments, 'r') as zipObj:
                            listOfFileNames = zipObj.namelist()
                            for fileName in listOfFileNames:
                                zipObj.extract(fileName, download_folder)
                                Product_Image = download_folder + fileName
                                download_product_image = Product_Image
                                break
                    except:
                        pass
                    SDS_SHEETS =[]
                    Attachments = []
                    SDS_SHEETS.append(download_sheet_name)
                    Attachments.append(download_file_attachments)
                    # ---------------------------------------------------------------------------------------
                    data_storage(driver, "GPXpress", Product_Title, Product_Description, Product_Image, Category_Title, Category_Description, Category_Image, SDS_SHEETS, File_Attached,download_file_attach, Attachments, Web_Structure )
                except Exception as e:
                    pass
        except:
            pass

def find_Products(driver):
    driver.get("https://mygp.gp.com/,DanaInfo=gpxpress.srv.gapac.com,SSL+SMHomepage.aspx")
    time.sleep(3)
    try:
        driver.find_element_by_id("MainNavid").find_element_by_css_selector("div > ul.nav > li:nth-child(2) > a").click()
        time.sleep(0.3)
        driver.find_element_by_id("MainNavid").find_element_by_css_selector("div > ul.nav > li:nth-child(2) > ul > li:nth-child(1) > a").click()
        time.sleep(0.3)
        url = "https://mygp.gp.com/,DanaInfo=productcatalog.srv.gapac.com,SSL+"
        search_url(driver, url, "GPXpress/Products")
    except Exception as e:
        print(str(e))
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
            # print('create table exception ->', str(ex))
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
        driver = loginProcess(driver,info)
        keyboard = Controller()
        find_Products(driver)
        driver.close()

    except Exception as ex:
        print('Exception ->', str(ex))
