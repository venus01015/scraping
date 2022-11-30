import json
from time import gmtime, strftime
import time
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import requests
import urllib.request
from os import path
import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pyodbc
from PIL import Image
from fake_useragent import UserAgent

x = '{"MARKET SPECIALIZATION":"https://www.winwithgojo.com/selling-tools/category/2/", "PRODUCTS":"https://www.winwithgojo.com/selling-tools/category/1/"}'
# x = '{"PRODUCTS":"https://www.winwithgojo.com/selling-tools/category/1/","MARKET SPECIALIZATION":"https://www.winwithgojo.com/selling-tools/category/2/"}' 
Master_category_urls = json.loads(x)
info = {}
url_category = {}
with open('info_user.json') as f:
    info = json.load(f)  
homedir = path.expanduser("~")
cursor = None

def get_header() :
    ua=UserAgent()
    return {'User-Agent': ua.random,       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',      'Accept-Encoding': 'none',      'Accept-Language': 'en-US,en;q=0.8',      'Connection': 'keep-alive'}

def getChromeDriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    return webdriver.Chrome(chrome_options=chrome_options)

def loginProcess(driver,userinfo):
    driver.get("https://www.winwithgojo.com/login/")
    driver.implicitly_wait(3)
    user = driver.find_element_by_css_selector('body > div > div > div.form > form > div:nth-child(1) > label > input[type=text]')
    user.send_keys(userinfo["user"])
    password = driver.find_element_by_css_selector('body > div > div > div.form > form > div:nth-child(2) > label > input[type=password]')
    password.send_keys(userinfo["password"])
    submit_button = driver.find_element_by_css_selector('body > div > div > div.form > form > input[type=submit]')
    ActionChains(driver).move_to_element(submit_button).click(submit_button).perform()
    driver.get("https://www.winwithgojo.com/")
    driver.implicitly_wait(3)
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
    text = text.replace("'",'')
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
        if File_Link !="" :
            Original_Name = File_Link.split("/")[-1]
            # NOTE the stream=True parameter
            r = requests.get(File_Link, stream=True)
            with open(Original_Name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024): 
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
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

        if Web_Category_Image != "" :
            strs = Web_Category_Image.split("/")
            Category_Image_Name = "Category_IMG_" + strs[len(strs)-1]
            r = requests.get(Web_Category_Image, headers=get_header())
            open(Category_Image_Name, 'wb').write(r.content)
            Category_Image = Manufacturer + "/Current/" + Category_Image_Name
        if Web_Product_Image != "" :
            strs = Web_Product_Image.split("/")
            filename, File_Type = os.path.splitext( strs[len(strs)-1])
            Category_Last = Web_Structure.split("/")[-2]
            Product_Image_Name = Product_Title + "_IMG_" + Category_Last + "_" + Content_Length + ".png"
            r = requests.get(Web_Product_Image, headers=get_header())
            open(Product_Image_Name, 'wb').write(r.content)
            Product_Image = Manufacturer + "/Current/" + Product_Image_Name
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
        for k in range(len(strs)-1) :
            field[5+k] = strs[k]
        field[11] = strs[len(strs)-1]
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

def search_url(driver, url, Web_Structure, Product_Img):
    driver.get(url)
    driver.implicitly_wait(5)
    try:
        Sub_Category = WebDriverWait(driver,0.5).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR,"body > div.wrapper > div > div.content.page.module > div > div > div.category > a")))
        #   get urls of sub category *************************
        _sub_url=json.loads('{}')
        products_imgs=[]
        for _sub_cate in Sub_Category:
            title = change_string( _sub_cate.find_element_by_css_selector("span").get_attribute('innerHTML'))
            _url = _sub_cate.get_attribute("href")
            _sub_url.update({title:_url})
            _sub_url.update({title:_url})
            img = _sub_cate.value_of_css_property("background-image")
            products_imgs.append(img[5:len(img)-2])
        t = 0
        for key in _sub_url.keys():
            t += 1
            _Product_Image = products_imgs[t-1]
            search_url(driver, _sub_url[key], Web_Structure + '/' + key, _Product_Image )

        ##############################################################
    except:
        Product_Title = ""
        Product_Description =""
        Product_Image = Product_Img
        Category_Title =""
        Category_Description =""
        Category_Image =""
        SDS_SHEETS =[]
        File_Attached =""
        Attachments = []
        # Web_Structure
        try:
            try:
                Category_Image = driver.find_element_by_css_selector("body > div.wrapper > div.content-wrapper > div.content.page.module > div > img").get_attribute("src")
                Category_Description = driver.find_element_by_css_selector("body > div.wrapper > div.content-wrapper > div.content.page.module > aside > p").text
                Category_Description = change_string(Category_Description)
            except:
                pass
            Content_Types = WebDriverWait(driver,1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR,"body > div.wrapper > div > div.content.page.module > footer > div > div.hideshow.expandable-category.cf")))
            for Content_Type in Content_Types:
                try:
                    Content_Type_text = Content_Type.find_element_by_css_selector("h3").text
                    Content_Type_text = Content_Type_text[:Content_Type_text.find("( show )")]
                    Content_Type_text = Content_Type_text.replace('/','&')
                    Web_Structure_ = Web_Structure + '/' + Content_Type_text
                    element = Content_Type.find_element_by_css_selector("h3 > span")
                    element.click()
                    try:
                        articles = WebDriverWait(Content_Type,1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR,"div.content.module-list.resource-list > article.resource.open.resource.has-image")))
                        for article in articles:
                            try:
                                Product_Title = change_string( article.find_element_by_css_selector("div.resource-content > a").get_attribute("title"))
                                File_Attached = article.find_element_by_css_selector("div.resource-content > div > div.downloads > a").get_attribute("href")
                                data_storage(driver, "Gojo", Product_Title, Product_Description, Product_Image, Category_Title, Category_Description, Category_Image, SDS_SHEETS, File_Attached, Attachments, Web_Structure_ )
                            except :
                                pass
                    except :
                        pass
                except:
                    pass
        except:
            pass

def goto_page(driver):
    try:
        for key in Master_category_urls.keys():
            url = Master_category_urls[key] #   Master_Category_url
            driver.get(url)
            driver.implicitly_wait(3)
            Sub_Category1s = WebDriverWait(driver,3).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR,"body > div.wrapper > div > div.content.page.module > div > div > div.category > a")))
            #   get urls of sub category1 *************************
            _sub_url=json.loads('{}')
            try:
                products_imgs=[]
                for _sub_cate in Sub_Category1s:
                    title = change_string(_sub_cate.find_element_by_css_selector("span").get_attribute('innerHTML'))
                    _url = _sub_cate.get_attribute("href")
                    _sub_url.update({title:_url})
                    img = _sub_cate.value_of_css_property("background-image")
                    products_imgs.append(img[5:len(img)-2])
                t = 0
                for title in _sub_url.keys():
                    t += 1
                    if t <1: continue

                    _Product_Image = products_imgs[t-1]
                    search_url(driver, _sub_url[title], "Gojo/" + key + "/" + title, _Product_Image)
            except :
                time.sleep(0.01)
                pass

    except :
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
        goto_page(driver)
        driver.close()
        
    except Exception as ex:
        print('Exception ->', str(ex))
