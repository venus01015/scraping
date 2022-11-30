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


homedir = path.expanduser("~")

def getChromeDriver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("start-maximized")
    # prefs = {'download.default_directory':'/downloads'}
    # chrome_options.add_experimental_option('prefs',prefs)
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

def goto_page(driver, blob_service_client, container_name, sql_connect):
    url = "https://www.pactiv.com/Pactiv/Resources/Marketing-Materials.htm"
    try:
        driver.get(url)
        driver.implicitly_wait(20)
        # elements = WebDriverWait(driver, 30).until(EC.visibility_of_all_elements_located((By.XPATH, "/html/body/form/div[4]/div[4]/div/div[1]/div[2]/div/div/fieldset[2]/div[2]/div/span")))
        elements = WebDriverWait(driver, 1).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#leftZone > div.Aggregation.New100.LeftZone.TitanBlock > div > div > fieldset.hideZero > div.inputs > div > span")))
        for element in elements :
            try:
                Master_Category = element.find_element_by_xpath("label").text
                Master_Category = Master_Category[:Master_Category.find(" (")]
                Web_Structure_ = "Pactiv/" + Master_Category
                input_element = element.find_element_by_xpath("input")
                input_element.click()
                WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CLASS_NAME, "AggregationResults")))
                items = driver.find_element_by_class_name("AggregationResults").find_elements_by_css_selector("div > div > div.item")
                for item in items:
                    try:
                        a_element = item.find_element_by_css_selector("div > h4 > a")
                        File_Link = a_element.get_attribute("href")
                        Title = a_element.text
                        strs = File_Link.split("/")
                        Original_Name = strs[len(strs)-1]
                        Content_Length = ""
                        ETag = ""
                        Last_Modified_by_Mfg = ""
                        Status = "Active"
                        Version = "V1"
                        Last_Modified_by_SETVI = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + " GMT"

                        urllib.request.urlretrieve(File_Link, Original_Name)
                        r = requests.get(File_Link)

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

                        Last_Verified = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()) + " GMT"
                        Create_Date = Last_Modified_by_SETVI
                        filename, File_Type = os.path.splitext(Original_Name)

                        File_Name = Title + "__" + Content_Length + File_Type
                        Blob_Link = "Pactiv/Current/" + File_Name

                        field = [Title, Original_Name, File_Link, File_Name, File_Type[1:], "", "", "", "", "", "", "", Content_Length, ETag, Last_Modified_by_Mfg, "", Version, Status, Blob_Link, Web_Structure_, Last_Verified, Create_Date]
                        #          0         1             2          3          4           5   6   7   8   9  10  11        12          13           14           15     16      17       18           19               20
                        strs = Web_Structure_.split("/")
                        for k in range(len(strs)) :
                            field[5+k] = strs[k]


                        sql_connect.execute("SELECT * FROM scrapingdata WHERE File_Link = '" + File_Link + "'AND ETag = '" + ETag + "';")
                        row = sql_connect.fetchone()

                        #########################################################
                        if Title == "" : ########### no Title
                            if row : ###### exist Link
                                sql_connect.execute("SELECT * FROM scrapingdata WHERE Status = 'Active' AND Web_Structure <> '" + Web_Structure_ + "' AND File_Link = '" + File_Link + "';")
                                row = sql_connect.fetchone()
                                if row :   ###### same link exist
                                    #update db(archived) only
                                    field[15] = Last_Modified_by_SETVI
                                    field[17] = "Archived"
                                    field[3] = row[1] + "__" + Content_Length + "_V1_Archived" + File_Type
                                    field[18] = "Pactiv/Archived/"+field[3]
                                    _query = "UPDATE scrapingdata SET Last_Verified = '"+ Last_Verified + "', status='Archived',Last_Modified_by_SETVI = '"+ field[15] +"',Blob_Link = '"+ field[18] +"',File_Name = '"+ field[3] +"' WHERE Web_Structure = '" + Web_Structure_ + "' AND File_Name = '" + File_Name + "';"
                                    sql_connect.execute(_query)
                                    sql_connect.commit()
                                else :  ####### another title ###### Same Web Link exist
                                    # update db(archived), update blob
                                    sql_connect.execute("SELECT * FROM scrapingdata WHERE Status = 'Archived' AND Web_Structure = '" + Web_Structure_ + "' AND File_Link = '" + File_Link + "';")
                                    row = sql_connect.fetchone()
                                    if row:
                                        continue
                                    field[17] = "Archived"
                                    field[3] = row[1] + "__" + row[13] + "_" + row[17] + "_Archived" + row[5]
                                    field[18] = "Pactiv/Archived/"+field[3]
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
                                    # run query
                                    _query = "UPDATE scrapingdata SET status='Archived',Last_Verified = '"+ Last_Verified + "', Last_Modified_by_SETVI = '"+ Last_Modified_by_SETVI +"',Blob_Link = '"+ field[18] +"', File_Name = '"+ field[3] +"' WHERE Web_Structure = '" + Web_Structure_ + "' AND File_Name = '" + File_Name + "';"
                                    sql_connect.execute(_query)
                                    sql_connect.commit()
                            
                            else : ########### no Exist Link
                                #insert db, upload blob(archived)
                                field[0] = filename
                                field[15] = Last_Modified_by_SETVI
                                field[17] = "Archived"
                                field[3] = filename + "__V1_Archived" + File_Type
                                field[18] = "Pactiv/Archived/"+field[3]
                                _query = "INSERT INTO scrapingdata( Title,Original_Name,File_Link,File_Name,File_Type,Manufacturer,Master_Category,Sub_Category1,Sub_Category2,Sub_Category3,Sub_Category4,Content_Type,Content_Length,ETag,Last_Modified_by_Mfg,Last_Modified_by_SETVI,Version,Status,Blob_Link,Web_Structure,  Last_Verified, Created_Date) VALUES ('"
                                for k in range(len(field)-1) :
                                    _query += field[k]   + "','"
                                _query += field[len(field)-1] + "');"
                                ###### insert record
                                try:
                                    sql_connect.execute(_query)
                                    sql_connect.commit()
                                except Exception as e:
                                    # print("sql error -> ", str(e))
                                    pass
                                ###### upload blob
                                blob_client = blob_service_client.get_blob_client(container=container_name, blob = field[18])
                                try:
                                    with open(Original_Name, "rb") as data:
                                        blob_client.upload_blob(data)
                                except Exception as e:
                                    pass
                        else : ######## have title
                            if row : ######### found title & exist Link
                                sql_connect.execute("SELECT * FROM scrapingdata WHERE Status = 'Active' AND Web_Structure <> '" + Web_Structure_ + "' AND File_Link = '" + File_Link + "';")
                                row = sql_connect.fetchone()
                                if row  :  ##### other ******
                                    # update db only
                                        # insert row, upload blob
                                    _query = "INSERT INTO scrapingdata( Title,Original_Name,File_Link,File_Name,File_Type,Manufacturer,Master_Category,Sub_Category1,Sub_Category2,Sub_Category3,Sub_Category4,Content_Type,Content_Length,ETag,Last_Modified_by_Mfg,Last_Modified_by_SETVI,Version,Status,Blob_Link,Web_Structure, Last_Verified, Created_Date) VALUES ('"
                                    for k in range(len(field)-1) :
                                        _query += field[k]   + "','"
                                    _query += field[len(field)-1] + "');"
                                    ###### insert record
                                    sql_connect.execute(_query)
                                    sql_connect.commit()
                                else :  ####### itself
                                    sql_connect.execute("SELECT * FROM scrapingdata WHERE Web_Structure = '" + Web_Structure_ + "' AND File_Link = '" + File_Link + "';")
                                    row = sql_connect.fetchone()
                                    if not(row):
                                        continue
                                    if ETag != row[14] or Last_Modified_by_Mfg != row[15] or Content_Length != row[13] :
                                        # update db only(archived), update blob(archived), upload new blob(active)
                                        # field[15] = Last_Modified_by_SETVI
                                        field[17] = "Archived"
                                        field[3] = row[1] + "__" + row[13] + "_" + row[17] + "_Archived" + row[5]
                                        field[18] = "Pactiv/Archived/"+field[3]
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
                                        # run query
                                        _query = "UPDATE scrapingdata SET status='Archived', Last_Verified = '"+ Last_Verified + "', Last_Modified_by_SETVI = '"+ Last_Modified_by_SETVI +"',Blob_Link = '"+ field[18] +"', File_Name = '"+ field[3] +"' WHERE Web_Structure = '" + Web_Structure_ + "' AND File_Name = '" + File_Name + "';"
                                        sql_connect.execute(_query)
                                        sql_connect.commit()
                                        ############ new add
                                        field[17] = "Active"
                                        field[3] = File_Name
                                        field[18] = "Pactiv/Current/"+field[3]
                                        field[16]="V"+str(int(row[17][1:])+1)
                                        _query = "INSERT INTO scrapingdata( Title,Original_Name,File_Link,File_Name,File_Type,Manufacturer,Master_Category,Sub_Category1,Sub_Category2,Sub_Category3,Sub_Category4,Content_Type,Content_Length,ETag,Last_Modified_by_Mfg,Last_Modified_by_SETVI,Version,Status,Blob_Link,Web_Structure,  Last_Verified, Created_Date) VALUES ('"
                                        for k in range(len(field)-1) :
                                            _query += field[k]   + "','"
                                        _query += field[len(field)-1] + "');"
                                        ###### insert record
                                        try:
                                            sql_connect.execute(_query)
                                            sql_connect.commit()
                                        except Exception as e:
                                            # print("sql error -> ", str(e))
                                            pass
                                        ###### upload blob
                                        blob_client = blob_service_client.get_blob_client(container=container_name,blob=field[18])
                                        try:
                                            with open(Original_Name, "rb") as data:
                                                blob_client.upload_blob(data)
                                        except Exception as e:
                                            pass
                                        pass
                                    _query = "UPDATE scrapingdata SET Last_Verified = '"+ Last_Verified + "' WHERE Status = 'Active' AND Manufacturer = 'Pactiv' AND Web_Structure = '" + Web_Structure_ + "' AND File_Link = '" + File_Link + "';"
                                    sql_connect.execute(_query)
                                    sql_connect.commit()
                            else : ########## title found & no exist Link
                                sql_connect.execute("SELECT * FROM scrapingdata WHERE Status = 'Active' AND Web_Structure = '" + Web_Structure_ + "' AND File_Name = '" + File_Name + "';")
                                row = sql_connect.fetchone()

                                if row : ###### itself  ************ have title, changed original file
                                    # update db(archived), update blob(archived)
                                    # field[15] = Last_Modified_by_SETVI
                                    field[17] = "Archived"
                                    field[3] = row[1] + "__" + row[13] + "_" + row[17] + "_Archived" + row[5]
                                    field[18] = "Pactiv/Archived/"+field[3]
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
                                    # run query
                                    _query = "UPDATE scrapingdata SET status='Archived' ,Last_Verified = '"+ Last_Verified + "', Last_Modified_by_SETVI = '"+ Last_Modified_by_SETVI +"',Blob_Link = '"+ field[18] +"', File_Name = '"+ field[3] +"' WHERE Web_Structure = '" + Web_Structure_ + "' AND File_Name = '" + File_Name + "';"
                                    sql_connect.execute(_query)
                                    sql_connect.commit()
                                    ############ new add
                                    field[17] = "Active"
                                    field[3] = File_Name
                                    field[18] = "Pactiv/Current/"+field[3]
                                    field[16]="V"+str(int(row[17][1:])+1)
                                    _query = "INSERT INTO scrapingdata( Title,Original_Name,File_Link,File_Name,File_Type,Manufacturer,Master_Category,Sub_Category1,Sub_Category2,Sub_Category3,Sub_Category4,Content_Type,Content_Length,ETag,Last_Modified_by_Mfg,Last_Modified_by_SETVI,Version,Status,Blob_Link,Web_Structure, Last_Verified, Created_Date) VALUES ('"
                                    for k in range(len(field)-1) :
                                        _query += field[k]   + "','"
                                    _query += field[len(field)-1] + "');"
                                    ###### insert record
                                    try:
                                        sql_connect.execute(_query)
                                        sql_connect.commit()
                                    except Exception as e:
                                        # print("sql error -> ", str(e))
                                        pass
                                    ###### upload blob
                                    blob_client = blob_service_client.get_blob_client(container=container_name,blob=field[18])
                                    try:
                                        with open(Original_Name, "rb") as data:
                                            blob_client.upload_blob(data)
                                    except Exception as e:
                                        pass
                                    pass
                                else :  ####### have title & no exist link & new add
                                    # insert row, upload blob
                                    _query = "INSERT INTO scrapingdata( Title,Original_Name,File_Link,File_Name,File_Type,Manufacturer,Master_Category,Sub_Category1,Sub_Category2,Sub_Category3,Sub_Category4,Content_Type,Content_Length,ETag,Last_Modified_by_Mfg,Last_Modified_by_SETVI,Version,Status,Blob_Link,Web_Structure, Last_Verified, Created_Date) VALUES ('"
                                    for k in range(len(field)-1) :
                                        _query += field[k]   + "','"
                                    _query += field[len(field)-1] + "');"
                                    ###### insert record
                                    try:
                                        sql_connect.execute(_query)
                                        sql_connect.commit()
                                    except Exception as e:
                                        print("sql error -> ", str(e))
                                        pass
                                    ###### upload blob
                                    blob_client = blob_service_client.get_blob_client(container=container_name,blob=Blob_Link)
                                    try:
                                        with open(Original_Name, "rb") as data:
                                            blob_client.upload_blob(data)
                                    except Exception as e:
                                        pass
                                    pass
                        ##########################################################
                        os.remove(Original_Name)
                    except Exception as err:
                        print("error -> ", str(err))
                        pass
                input_element.click()
            except Exception as err:
                print(str(err))
                pass


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
        create_sql = "CREATE TABLE scrapingdata(ID int IDENTITY(1,1), Title varchar(255) , Original_Name varchar(255), File_Link varchar(255), File_Name varchar(128), File_Type varchar(8), Manufacturer varchar(32), Master_Category varchar(255), Sub_Category1 varchar(255), Sub_Category2 varchar(255), Sub_Category3 varchar(255), Sub_Category4 varchar(255), Content_Type varchar(255), Content_Length VARCHAR(128), ETag VARCHAR(128), Last_Modified_by_Mfg VARCHAR(32), Last_Modified_by_SETVI VARCHAR(32), Version VARCHAR(32), Status VARCHAR(32), Blob_Link VARCHAR(255), Web_Structure VARCHAR(255), Last_Verified VARCHAR(255), Created_date VARCHAR(255), Image VARCHAR(255), Description TEXT, SDS VARCHAR(255));"
        try:
            cursor.execute(create_sql)
            cursor.commit()
        except Exception as ex:
            print('create table exception ->', str(ex))
            pass
        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_name = "scrapingdata" #+ str(uuid.uuid4())
        try:
            container_client = blob_service_client.create_container(container_name)
        except  Exception as ex:
            # print('Exception ->', str(ex))
            container_client = blob_service_client.get_container_client(container_name)
            pass
        driver = getChromeDriver()
        goto_page(driver, blob_service_client, container_name, cursor)
        driver.close()

    except Exception as ex:
        print('Exception ->', str(ex))