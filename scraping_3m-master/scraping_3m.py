import json
from time import gmtime, strftime
import time
import requests
from requests import Request, Session

from os import path
import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pyodbc
from PIL import Image
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import csv

cursor = None
download_path = path.expanduser("~") + "/Downloads/"
download_path = download_path.replace("\\","/")

header_data = {
                  'Host': 'www.3m.com',
                  'Connection': 'keep-alive',
                  'Cache-Control': 'max-age=0',
                  'Upgrade-Insecure-Requests': '1',
                  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
                  'Accept-Encoding': 'gzip, deflate',
                  'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                  'Dnt': '1',
            }
def get_header() :
    ua=UserAgent()
    return {'User-Agent': ua.random,       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',      'Accept-Encoding': 'none',      'Accept-Language': 'en-US,en;q=0.8',      'Connection': 'keep-alive'}

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
    return text

def data_storage( Product_Title, Sku_SN, Product_Description, Product_Image_urls, Resources_urls, Product_Specification, Categorys):
    print( "*-*-*-*-----------\n",Product_Title,"\n", Sku_SN,"\n", Categorys,"\n", Product_Image_urls,"\n", Resources_urls,"\n-----------*-*-*-*" )
    global cursor
    global container_name
    Web_Structure =""
    try:
        Product_Images =[]
        Str_Product_Images=""
        k = 0
        if len(Product_Image_urls) > 0 :
            for url in Product_Image_urls :
                k += 1
                r = requests.get(url)
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
                r = requests.get(url)
                filename = r.headers['Content-Disposition'].split('"')[1]
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
        _query = "Select * FROM scraping3m WHERE Product_Title = '" + Product_Title + "' AND CONVERT(NVARCHAR(MAX), Product_Description) = N'" + Product_Description + "' AND CONVERT(NVARCHAR(MAX), Product_Images) = N'" + Str_Product_Images + "' AND CONVERT(NVARCHAR(MAX), Resource_Files) = N'" + Str_Resource_Files + "' AND CONVERT(NVARCHAR(MAX), Web_Structure) = N'" + Web_Structure + "';"
        with open("ScrapingData.csv", 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(fields)
        # cursor.execute(_query)
        # row = cursor.fetchone()
        row = None
        if not row :
            _query = "INSERT INTO scraping3m( Product_Title, SKU_SN, Product_Description, Product_Images, Product_Specification, Resource_Files, Manufacture, Category1, Category2, Category3, Category4, Category5, Category6, Web_Structure) VALUES ("
            for field in fields :
                _query += "'" + field + "',"
            _query = _query[:len(_query)-1] + ");"
            try:
                # cursor.execute(_query)
                # cursor.commit()
                if len(Product_Images)>0 :
                    for url in Product_Images :
                        filename = url.split("/")[-1]
                        blob_client = blob_service_client.get_blob_client(container=container_name,blob=url)
                        try:
                            with open(  filename, "rb") as data:
                                blob_client.upload_blob(data)
                        except :
                            pass

                if len(Resource_Files)>0 :
                    for url in Resource_Files :
                        filename = url.split("/")[-1]
                        blob_client = blob_service_client.get_blob_client(container=container_name,blob=url)
                        try:
                            with open(  filename, "rb") as data:
                                blob_client.upload_blob(data)
                        except :
                            pass

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


def get_product_details(Categorys, my_page_source) :
    Product_Title = ""
    Sku_SN =""
    Product_Description =""
    Product_Specification= ""
    Product_Image_urls=[]
    Resources_urls=[]

    Sku_SN = my_page_source.findAll(attrs={'class': 'MMM--contentDetailContain-bd'})[0].findAll('div')[0].text
    if Sku_SN  == "" :
        return
    Sku_SN = Sku_SN.replace("\n","").replace("\xa0"," ")
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
            #### all attachment ######
            # a_tags = element.findAll('div')[1].findAll('a')
            # for a_tag in a_tags :
            #     Resources_urls.append(a_tag['href'])
            #-----------------------------------
            divs = element.findAll(attrs={'class':'MMM--dataGroup MMM--columns-dataGroup SNAPS--Block'})
            for div in divs :
                try:
                    tag = div.find(attrs={'class':'MMM--hdg MMM--hdg_6'})
                    if tag.text == "Data Sheets" or tag.text =="Brochures" or tag.text=="" :
                        a_tags = div.findAll('a')
                        for a_tag in a_tags :
                            Resources_urls.append(a_tag['href'])
                except:
                    pass

    data_storage(change_string(Product_Title), Sku_SN,  change_string(Product_Description), Product_Image_urls, Resources_urls,  change_string(Product_Specification), Categorys)

def get_products():
    try:
        page_url = "https://www.3m.com/3M/en_US/company-us/all-3m-products/~/All-3M-Products/?N=5002385+8711017+3294857497&rt=r3"
        response = requests.get(page_url, headers= header_data)
        if response.status_code != 200 :
            return
        soup = BeautifulSoup(response.content, 'html.parser')
        count = soup.findAll(attrs={'class':'SNAPS--CategoryCnt deskResultBar'})[1].text.split("\xa0")[0]
        All_Product_Count = int(count)
        page_count = int(All_Product_Count/24)
        Product_num = 0

        for page_number in range(page_count+2) :
            ajax_url = page_url
            show_page_num = 24*page_number
            if show_page_num > All_Product_Count : show_page_num = All_Product_Count
            if page_number>0 :
                ajax_url += "&Nrpp={}&No={}".format(24,show_page_num)
            response = requests.get(ajax_url, headers= header_data)
            if response.status_code != 200 :
                print(page_number,"- Page requests fail")
                continue
            soup = BeautifulSoup(response.content, 'html.parser')
            elements = soup.findAll(attrs={'class':'SNAPS--hideBdrBottom js--preselect'})
            product_urls = []
            for element in elements :
                product_urls.append(element['href'])
            for pro_url in product_urls :
                try:
                    response = requests.get(pro_url, headers= header_data)
                    if response.status_code != 200 :
                        print(Product_num,"- Product requests fail")
                        continue
                    soup = BeautifulSoup(response.content, 'html.parser')
                    ###########################
                    Categorys=['3M']
                    element = soup.find(attrs={'id' : 'snapsBreadCrumb'})
                    cates = element.findAll('li')
                    k = 0
                    for cate in cates :
                        k+=1
                        if k==len(cates) : continue
                        Categorys.append(cate.text.replace('\n', ''))
                    #################################
                    element = soup.find(attrs={'class':'MMM--dat MMM--pdpTabVr MMM--allModelSection MMM--isNotOnMobile js-allModelSection'})
                    if (element==None) :
                        Product_num += 1
                        print("******---------- Product", Product_num, "-----------***********")
                        if(Product_num<1024) : continue
                        print(pro_url)
                        get_product_details(Categorys, soup)
                    else :
                        elements = element.findAll(attrs={'class':'MMM--dat-row js-row-results'})
                        select_urls =[]
                        for element in elements :
                            select_urls.append(element.find('a')['href'])
                        for select_url in select_urls :
                            try:
                                Product_num += 1
                                if(Product_num<1024) : continue
                                response = requests.get(select_url, headers= header_data)
                                if response.status_code != 200 :
                                    print(Product_num,"- Product option requests fail")
                                    continue
                                print("******---------- Product", Product_num, "-----------***********")
                                print(select_url)
                                get_product_details(Categorys,BeautifulSoup(response.content, 'html.parser'))
                            except:
                                pass
                except:
                    pass

    except Exception as e:
        print("error ->", str(e))
        pass

if  __name__ == "__main__":
    try:
        server = 'tcp:tstdbset01.database.windows.net'
        database = 'tstdb02'
        username = 'sadminx'
        password = 't*Te9qi?nk3'
        sql_driver= '{ODBC Driver 17 for SQL Server}'
        # cnxn = pyodbc.connect('DRIVER='+sql_driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
        # cursor = cnxn.cursor()
        # create_sql = "CREATE TABLE scraping3m(ID int IDENTITY(1,1), Product_Title varchar(255) ,SKU_SN varchar(255), Product_Description TEXT, Product_Images TEXT, Product_Specification TEXT, Resource_Files TEXT, Manufacture varchar(255), Category1 varchar(255), Category2 varchar(255), Category3 varchar(255), Category4 varchar(255), Category5 varchar(255), Category6 varchar(255), Web_Structure varchar(255));"
        # try:
        #     cursor.execute(create_sql)
        #     cursor.commit()
        # except Exception as ex:
        #     pass
        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_name = "scrapingdata"
        try:
            container_client = blob_service_client.create_container(container_name)
        except  Exception as ex:
            container_client = blob_service_client.get_container_client(container_name)
            pass

        get_products()

    except Exception as ex:
        print('Exception ->', str(ex))