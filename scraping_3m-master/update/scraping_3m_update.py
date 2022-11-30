import json
import time
import datetime
import requests
import db_sqlite
from os import path
import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pyodbc
from bs4 import BeautifulSoup

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

def change_string(text):
    text = text.replace('®','')
    text = text.replace('&reg;','')
    text = text.replace('&trade;','')
    text = text.replace('™','')
    text = text.replace('<br>','')
    text = text.replace('&amp; ','')
    text = text.replace('/','_')
    text = text.replace("'","")
    return text

def data_storage(Mfg_ID, Category_ID, Product_Name, SKU, Brand, Description, Details, Product_Image_urls, Files, Spec, ProductURL):
    Product_Name = Product_Name.replace("\"", "``").replace("'", "`")
    Description = Description.replace("\"","``").replace("'","`")
    Details = Details.replace("\"","`").replace("'","`")
    print("Product_Name : '{}'".format(Product_Name))
    MPartNumber = ""
    UPC = ""
    SKUs =[]
    if SKU != "":
        if ", " in SKU:
            SKUs = SKU.split(", ")
        else :
            SKUs.append(SKU)
        for _sku in SKUs:
            if "ID" in _sku: MPartNumber = _sku.split(" ")[-1]
            if "UPC" in _sku: UPC = _sku.split(" ")[-1]

    now = datetime.datetime.now()
    current_day= now.strftime("%m/%d/%Y")
    DB_Name = "portal.db"
    conn = db_sqlite.connection(DB_Name)
    query = "SELECT * FROM items WHERE Name ='{}' and MPartNumber='{}' and UPC='{}'".format(Product_Name, MPartNumber, UPC)
    rows = db_sqlite.select_query(conn, query)
    if len(rows) == 0 :
        query = """INSERT INTO items(Name, URL, Mfg_ID, MPartNumber, UPC, Spec_ID, Description, Details, Category_ID, File_ID, Images, Created) VALUES("{}", "{}", "{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")""".format(Product_Name, ProductURL, Mfg_ID, MPartNumber, UPC, "", Description, Details, Category_ID, "", len(Product_Image_urls), current_day)
        db_sqlite.insert_query(conn,query)
    else:
        db_sqlite.close(conn)
        return

    query = "SELECT * FROM items WHERE Name ='{}' and MPartNumber='{}' and UPC='{}'".format(Product_Name, MPartNumber, UPC)
    rows = db_sqlite.select_query(conn, query)
    Item_ID = rows[0][0]
    for i in range(46):
        Spec[i] = Spec[i].replace("\"","``").replace("'","`")
    try:
        query = """INSERT INTO Specifications(Item_ID, Aggressiveness, Application, Brand, Center_Hole, Center_Hole_Diameter_Imperial, Center_Hole_Diameter_Metric, Cleaning_Area, Compatible_Dispensing_System, Concentrate_Dilution_Ratio, Disinfectant, Dispense_Rate, Dispensing_System, Color_Family, Function_Attachment_Style, Industries, Maximum_Speed, Machine_Speed, Commercial_Kitchen_Cleaning, Dishwasher_Safe, Overall_Diameter_Imperial, Overall_Diameter_Metric, Overall_Length_Imperial, Overall_Length_Metric, Overall_Width_Imperial, Overall_Width_Metric, Overall_Thickness_Imperial, Overall_Thickness_Metric, Net_Weight_Imperial, Net_Weight_Metric, Product_Color, Product_Form, Product_Type, Quantity, Recommended_Application, Recommended_Surfaces, Sheet_Size_Imperial, Sheet_Size_Metric, Shape, Size, Solution_Yield_Imperial, Solution_Yield_Metric, Surface_Type, Third_Party_Certification, Volume_Imperial, Volume_Metric, _Case, Created)
            VALUES("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}", "{}")""".format(
                Item_ID, Spec[0], Spec[1], Spec[2], Spec[3], Spec[4], Spec[5], Spec[6], Spec[7], Spec[8], Spec[9], Spec[10], Spec[11], Spec[12], Spec[13], Spec[14], Spec[15], Spec[16], Spec[17], Spec[18], Spec[19], Spec[20], Spec[21], Spec[22], Spec[23], Spec[24], Spec[25], Spec[26], Spec[27], Spec[28], Spec[29], Spec[30], Spec[31], Spec[32], Spec[33], Spec[34], Spec[35], Spec[36], Spec[37], Spec[38], Spec[39], Spec[40], Spec[41], Spec[42], Spec[43], Spec[44], Spec[45], current_day)
        db_sqlite.insert_query(conn,query)
        query = "SELECT * FROM Specifications ORDER BY Spec_ID DESC LIMIT 1"
        rows = db_sqlite.select_query(conn, query)
        Spec_ID = rows[0][0]
    except:
        pass

    container_name = "portal"
    try:
        Product_Images =[]
        Str_Product_Images=""
        k = 0
        if len(Product_Image_urls) > 0 :
            for url in Product_Image_urls :
                k += 1
                r = requests.get(url)
                filename = url.split('/')[-1]
                File_name, File_Type = os.path.splitext(filename)
                new_name = "image{}{}".format(k, File_Type)
                open(new_name, 'wb').write(r.content)
                Product_Images.append(new_name)
                Str_Product_Images = "{},{}".format(Str_Product_Images, new_name)
            Str_Product_Images=Str_Product_Images[1:]

        Resource_Files =[]
        Str_Files = ""
        k = 0
        if len(Files) > 0 :
            for file_title in Files.keys():
                k += 1
                url = Files[file_title]
                r = requests.get(url)
                filename = r.headers['Content-Disposition'].split('"')[1]
                File_name, File_Type = os.path.splitext(filename)
                new_name = "{}{}".format(file_title, File_Type)
                open(new_name, 'wb').write(r.content)
                Resource_Files.append(new_name)

        try:
            if len(Product_Images)>0 :
                for image in Product_Images :
                    url = "3M/{}/{}".format(Item_ID, image)
                    blob_client = blob_service_client.get_blob_client(container=container_name,blob=url)
                    try:
                        with open(image, "rb") as data:
                            blob_client.upload_blob(data)
                    except :
                        pass

            if len(Resource_Files)>0 :
                for filename in Resource_Files :
                    url = "3M/{}/{}".format(Item_ID, filename)
                    blob_client = blob_service_client.get_blob_client(container=container_name,blob=url)
                    try:
                        with open(filename, "rb") as data:
                            blob_client.upload_blob(data)
                    except :
                        pass
                    query = """INSERT INTO files(File_Name, Item_ID, Created) VALUES("{}","{}","{}")""".format(filename, Item_ID, current_day)
                    db_sqlite.insert_query(conn,query)
                    query = "SELECT * FROM files ORDER BY File_ID DESC LIMIT 1"
                    rows = db_sqlite.select_query(conn, query)
                    File_ID = rows[0][0]
                    Str_Files = "{},{}".format(Str_Files, File_ID)
                Str_Files = Str_Files[1:]

        except Exception as err :
            print(" error -> ", str(err))
            db_sqlite.close(conn)
            pass
        query = "UPDATE items SET File_ID = '{}', Spec_ID = '{}' where Name ='{}' and MPartNumber='{}' and UPC='{}'".format(Str_Files, Spec_ID, Product_Name, MPartNumber, UPC)
        db_sqlite.update_query(conn,query)
        db_sqlite.close(conn)
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
        db_sqlite.close(conn)
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

def get_product_details(Mfg_ID, Category_ID, my_page_source, ProductURL) :

    Product_Name = ""
    SKU =""
    Description = ""
    Details = ""
    Product_Image_urls=[]
    Files= json.loads('{}')
    Brand = ""
    Spec = ["","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","","",""]

    SKU = my_page_source.findAll(attrs={'class': 'MMM--contentDetailContain-bd'})[0].findAll('div')[0].text
    if SKU  != "" :
        SKU = SKU.replace("\n","").replace("\xa0"," ")
    Product_Name= my_page_source.findAll(attrs={'class' : 'MMM--hdg MMM--hdg_1 hdg_contentDetailTitle'})[0].text.replace("\n"," ").replace("'","`")
    if "case" in Product_Name.split(", ")[-1].lower():
        Spec[45] = Product_Name.split(", ")[-1].strip()
    elements = my_page_source.find(attrs={'id': 'js-carousel'}).findAll('noscript')
    for element in elements:
        img = element.find('img')
        Product_Image_urls.append(img['src'])
    elements = my_page_source.findAll(attrs={'class': 'MMM--tabSection clearfix 2'})
    for element in elements :
        part_title = element.find('div').text
        if "Specifications" in part_title or  "Typical Properties" in part_title :
            Specifications = element.findAll('div')[1].findAll('tr')
            k = 0
            for Specification in Specifications :
                k += 1
                if k == 1 : continue
                tds = Specification.findAll('td')
                if "Aggressiveness" in tds[0].text.strip():
                    Spec[0] = tds[1].text.strip()
                if "Application" in tds[0].text.strip():
                    Spec[1] = tds[1].text.strip()
                if "Brand" in tds[0].text.strip():
                    Spec[2] = tds[1].text.strip()
                if "Center Hole" in tds[0].text.strip():
                    Spec[3] = tds[1].text.strip()
                if "Center Hole Diameter (Imperial)" in tds[0].text.strip():
                    Spec[4] = tds[1].text.strip()
                if "Center Hole Diameter (Metric)" in tds[0].text.strip():
                    Spec[5] = tds[1].text.strip()
                if "Cleaning Area" in tds[0].text.strip():
                    Spec[6] = tds[1].text.strip()
                if "Compatible Dispensing System" in tds[0].text.strip():
                    Spec[7] = tds[1].text.strip()
                if "Concentrate Dilution Ratio" in tds[0].text.strip():
                    Spec[8] = tds[1].text.strip()
                if "Disinfectant" in tds[0].text.strip():
                    Spec[9] = tds[1].text.strip()
                if "Dispense Rate" in tds[0].text.strip():
                    Spec[10] = tds[1].text.strip()
                if "Dispensing System" in tds[0].text.strip():
                    Spec[11] = tds[1].text.strip()
                if "Color Family" in tds[0].text.strip():
                    Spec[12] = tds[1].text.strip()
                if "Function/Attachment Style" in tds[0].text.strip():
                    Spec[13] = tds[1].text.strip()
                if "Industries" in tds[0].text.strip():
                    Spec[14] = tds[1].text.strip()
                if "Maximum Speed" in tds[0].text.strip():
                    Spec[15] = tds[1].text.strip()
                if "Machine Speed" in tds[0].text.strip():
                    Spec[16] = tds[1].text.strip()
                if "Commercial Kitchen Cleaning" in tds[0].text.strip():
                    Spec[17] = tds[1].text.strip()
                if "Dishwasher Safe" in tds[0].text.strip():
                    Spec[18] = tds[1].text.strip()
                if "Overall Diameter (Imperial)" in tds[0].text.strip():
                    Spec[19] = tds[1].text.strip()
                if "Overall Diameter (Metric)" in tds[0].text.strip():
                    Spec[20] = tds[1].text.strip()
                if "Overall Length (Imperial)" in tds[0].text.strip():
                    Spec[21] = tds[1].text.strip()
                if "Overall Length (Metric)" in tds[0].text.strip():
                    Spec[22] = tds[1].text.strip()
                if "Overall Width (Imperial)" in tds[0].text.strip():
                    Spec[23] = tds[1].text.strip()
                if "Overall Width (Metric)" in tds[0].text.strip():
                    Spec[24] = tds[1].text.strip()
                if "Overall Thickness (Imperial)" in tds[0].text.strip():
                    Spec[25] = tds[1].text.strip()
                if "Overall Thickness (Metric)" in tds[0].text.strip():
                    Spec[26] = tds[1].text.strip()
                if "Net Weight (Imperial)" in tds[0].text.strip():
                    Spec[27] = tds[1].text.strip()
                if "Net Weight (Metric)" in tds[0].text.strip():
                    Spec[28] = tds[1].text.strip()
                if "Product Color" in tds[0].text.strip():
                    Spec[29] = tds[1].text.strip()
                if "Product Form" in tds[0].text.strip():
                    Spec[30] = tds[1].text.strip()
                if "Product Type" in tds[0].text.strip():
                    Spec[31] = tds[1].text.strip()
                if "Quantity" in tds[0].text.strip():
                    Spec[32] = tds[1].text.strip()
                if "Recommended Application" in tds[0].text.strip():
                    Spec[33] = tds[1].text.strip()
                if "Recommended Surfaces" in tds[0].text.strip():
                    Spec[34] = tds[1].text.strip()
                if "Sheet Size (Imperial)" in tds[0].text.strip():
                    Spec[35] = tds[1].text.strip()
                if "Sheet Size (Metric)" in tds[0].text.strip():
                    Spec[36] = tds[1].text.strip()
                if "Shape" in tds[0].text.strip():
                    Spec[37] = tds[1].text.strip()
                if "Size" in tds[0].text.strip():
                    Spec[38] = tds[1].text.strip()
                if "Solution Yield (Imperial)" in tds[0].text.strip():
                    Spec[39] = tds[1].text.strip()
                if "Solution Yield (Metric)" in tds[0].text.strip():
                    Spec[40] = tds[1].text.strip()
                if "Surface Type" in tds[0].text.strip():
                    Spec[41] = tds[1].text.strip()
                if "Third Party Certification" in tds[0].text.strip():
                    Spec[42] = tds[1].text.strip()
                if "Volume (Imperial)" in tds[0].text.strip():
                    Spec[43] = tds[1].text.strip()
                if "Volume (Metric)" in tds[0].text.strip():
                    Spec[44] = tds[1].text.strip()
        elif "Details" in part_title:
            D_elements = element.find(attrs={'class':'MMM--grids-col MMM--grids-col_pdpMain'}).find('ul').findAll('li')
            for D_element in D_elements :
                Details += " ∙ " + D_element.text.strip() + "\n"
            Description = element.find(attrs={'class':'MMM--grids-col MMM--grids-col_pdpMain'}).find('p').text.strip()
        elif "Resources" in part_title:
            #-----------------------------------
            divs = element.findAll(attrs={'class':'MMM--dataGroup MMM--columns-dataGroup SNAPS--Block'})
            for div in divs :
                try:
                    tag = div.find(attrs={'class':'MMM--hdg MMM--hdg_6'})
                    if tag.text == "Data Sheets" or tag.text =="Brochures" or tag.text=="" :
                        a_tags = div.findAll('a')
                        for a_tag in a_tags :
                            file_title = change_string(a_tag.text.strip().replace("\n",""))
                            if "(" in file_title:
                                key = file_title.split('(')[0].strip()
                            else :
                                key = file_title
                            _url = a_tag['href']
                            Files.update({key:_url})
                except:
                    pass
    data_storage(Mfg_ID, Category_ID, Product_Name, SKU, Brand, Description, Details, Product_Image_urls, Files, Spec, ProductURL)

def get_products():
    #####################################
    DB_Name = "portal.db"
    conn = db_sqlite.connection(DB_Name)
    query = "SELECT * FROM manufacturer WHERE Name='3M'"
    rows = db_sqlite.select_query(conn, query)
    now = datetime.datetime.now()
    # current_day= now.strftime("%m/%Y/%d %H:%M:%S")
    current_day= now.strftime("%m/%d/%Y")
    if len(rows) == 0 :
        query = """INSERT INTO manufacturer VALUES("1000","3M","{}","{}")""".format(current_day,current_day)
        db_sqlite.insert_query(conn,query)
    else:
        query = "UPDATE manufacturer SET Checked  = '{}' where Name ='3M'".format(current_day)
        db_sqlite.update_query(conn,query)
    query = "SELECT Mfg_ID FROM manufacturer WHERE Name='3M'"
    rows = db_sqlite.select_query(conn, query)
    Mfg_ID = rows[0][0]
    try:
        query = """INSERT INTO categories(Name, Created, Checked, URL, Category_Description, Category_URL, Parent_ID, Category_Mark) VALUES("{}","{}","{}","{}","","","","{}")""".format("All 3M Products", current_day, current_day, "https://www.3m.com/3M/en_US/company-us/all-3m-products/~/All-3M-Products/?N=5002385+8711017&rt=r3", "All 3M Products")
        db_sqlite.insert_query(conn,query)
    except:
        pass
    db_sqlite.close(conn)
    ##########################################
    page_urls =[
        # "https://www.3m.com/3M/en_US/company-us/all-3m-products/~/All-3M-Products/Cleaning-Supplies-Tools/?N=5002385+8710714+8711017+3294857497&rt=r3",
        # "https://www.3m.com/3M/en_US/company-us/all-3m-products/~/All-3M-Products/Chemicals/?N=5002385+8711017+8745514+3294857497&rt=r3",
        # "https://www.3m.com/3M/en_US/company-us/all-3m-products/~/All-3M-Products/Facility-Cleaning-Maintenance/?N=5002385+8710653+8711017+3294857497&rt=r3",
        "https://www.3m.com/3M/en_US/company-us/all-3m-products/~/All-3M-Products/Filtration/?N=5002385+8710655+8711017+3294857497&rt=r3",
        "https://www.3m.com/3M/en_US/company-us/all-3m-products/~/All-3M-Products/Food-Service-Hospitality/?N=5002385+8710657+8711017+3294857497&rt=r3",
        "https://www.3m.com/3M/en_US/company-us/all-3m-products/~/All-3M-Products/Home-Office-School-Supplies/?N=5002385+8710660+8711017+3294857497&rt=r3",
    ]
    all_product = 0
    cate_cou = 0
    for page_url in page_urls :
        cate_cou += 1
        try:
            response = requests.get(page_url, headers= header_data, timeout=None)
            if response.status_code != 200 :
                return
            soup = BeautifulSoup(response.content, 'html.parser')
            category_name = soup.find('title').text
            category_name = category_name[:category_name.find(' |')]
            #################################
            now = datetime.datetime.now()
            current_day= now.strftime("%m/%d/%Y")
            # DB_Name = "portal.db"
            # conn = db_sqlite.connection(DB_Name)
            # query = "SELECT * FROM categories WHERE URL ='{}'".format(page_url)
            # rows = db_sqlite.select_query(conn, query)
            # if len(rows) == 0 :
            #     query = """INSERT INTO categories(Name, Created, Checked, URL, Category_Description, Category_URL, Parent_ID) VALUES("{}","{}","{}","{}","","","{}")""".format(category_name, current_day, current_day, page_url, "0")
            #     db_sqlite.insert_query(conn,query)
            # else:
            #     query = "UPDATE categories SET Checked  = '{}' where URL ='{}'".format(current_day, page_url)
            #     db_sqlite.update_query(conn,query)
            # query = "SELECT * FROM categories WHERE URL ='{}'".format(page_url)
            # rows = db_sqlite.select_query(conn, query)
            # db_sqlite.close(conn)
            # Category_ID = rows[0][0]
            ###################################
            count = soup.findAll(attrs={'class':'SNAPS--CategoryCnt deskResultBar'})[1].text.split("\xa0")[0]
            All_Product_Count = int(count)
            page_count = int(All_Product_Count/24)
            Product_num = 0

            for page_number in range(page_count+1) :
                ajax_url = page_url
                show_page_num = 24 * page_number
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
                    Product_num += 1
                    conn = db_sqlite.connection(DB_Name)
                    query = "SELECT * FROM items WHERE URL ='{}'".format(pro_url)
                    rows = db_sqlite.select_query(conn, query)
                    db_sqlite.close(conn)
                    if len(rows) != 0 :
                        continue
                    try:
                        response = requests.get(pro_url, headers= header_data)
                        if response.status_code != 200 :
                            print(Product_num,"- Product requests fail")
                            continue
                        soup = BeautifulSoup(response.content, 'html.parser')
                        ##################################
                        element = soup.find(attrs={'id' : 'snapsBreadCrumb'})
                        cates = element.findAll('li')
                        DB_Name = "portal.db"
                        conn = db_sqlite.connection(DB_Name)
                        for k in range(1, len(cates)-1) :
                            category_url = cates[k].find('a')['href']
                            category_mark = cates[0].find('a').text.strip()
                            parent_mark = cates[0].find('a').text.strip()
                            for t in range (1,k+1) :
                                category_mark += ">" + cates[t].find('a').text.strip()
                                if t<k :
                                    parent_mark += ">" + cates[t].find('a').text.strip()
                            query = "SELECT * FROM categories WHERE URL ='{}'".format(category_url)
                            rows = db_sqlite.select_query(conn, query)
                            if len(rows) == 0 :
                                query = "SELECT * FROM categories WHERE Category_Mark ='{}'".format(parent_mark)
                                rows = db_sqlite.select_query(conn, query)
                                parent_id = rows[0][0]
                                parent_mark = rows[0][8]
                                category_response = requests.get(category_url, headers= header_data)
                                category_soup = BeautifulSoup(category_response.content, 'html.parser')
                                category_name = category_soup.find('title').text
                                if ' |' in category_name :
                                    category_name = category_name[:category_name.find(' |')]
                                if ':' in category_name :
                                    category_name = category_name[:category_name.find(':')]
                                query = """INSERT INTO categories(Name, Created, Checked, URL, Category_Description, Category_URL, Parent_ID, Category_Mark) VALUES("{}","{}","{}","{}","","","{}","{}")""".format(category_name, current_day, current_day, category_url, parent_id, category_mark)
                                db_sqlite.insert_query(conn,query)
                            else:
                                query = "UPDATE categories SET Checked  = '{}' where URL ='{}'".format(current_day, category_url)
                                db_sqlite.update_query(conn,query)
                            query = "SELECT * FROM categories WHERE URL ='{}'".format(category_url)
                            rows = db_sqlite.select_query(conn, query)
                            Category_ID = rows[0][0]
                        db_sqlite.close(conn)
                        ###########################
                        element = soup.find(attrs={'class':'MMM--dat MMM--pdpTabVr MMM--allModelSection MMM--isNotOnMobile js-allModelSection'})
                        if (element == None) :
                            all_product += 1
                            print("****** Category {} -> {} -> {} : {} ********".format(cate_cou, category_name, Product_num, all_product))
                            print(pro_url)
                            get_product_details(Mfg_ID, Category_ID, soup, pro_url)
                        else :
                            elements = element.findAll(attrs={'class':'MMM--dat-row js-row-results'})
                            select_urls =[]
                            for element in elements :
                                select_urls.append(element.find('a')['href'])
                            for select_url in select_urls :
                                conn = db_sqlite.connection(DB_Name)
                                query = "SELECT * FROM items WHERE URL ='{}'".format(select_url)
                                rows = db_sqlite.select_query(conn, query)
                                db_sqlite.close(conn)
                                if len(rows) != 0 :
                                    continue
                                try:
                                    all_product += 1
                                    response = requests.get(select_url, headers= header_data)
                                    if response.status_code != 200 :
                                        print(Product_num,"- Product option requests fail")
                                        continue
                                    print("****** Category {} -> {} -> {} : {} ********".format(cate_cou, category_name, Product_num, all_product))
                                    print(select_url)
                                    get_product_details(Mfg_ID, Category_ID, BeautifulSoup(response.content, 'html.parser'), select_url)
                                except:
                                    pass
                    except Exception as e:
                        print(str(e))
                        pass

        except Exception as e:
            print(page_url)
            print("error ->", str(e))
            pass

if  __name__ == "__main__":
    DB_Name = "portal.db"
    db_sqlite.create_db(DB_Name)
    conn = db_sqlite.connection(DB_Name)
    query = "create table if not exists manufacturer(Mfg_ID integer PRIMARY KEY AUTOINCREMENT, Name text, Created text, Checked text)"
    db_sqlite.create_table(conn,query)
    query = "create table if not exists categories(Category_ID integer PRIMARY KEY AUTOINCREMENT, Name text, Created text, Checked text, URL text, Category_Description text, Category_URL text, Parent_ID text, Category_Mark text)"
    db_sqlite.create_table(conn,query)
    query = "create table if not exists items(Item_ID integer PRIMARY KEY AUTOINCREMENT, Name text, URL text, Mfg_ID integer, MPartNumber text, UPC text, Spec_ID integer, Description text, Details text, Category_ID integer, File_ID text, Images text, Created text)"
    db_sqlite.create_table(conn,query)
    query = "create table if not exists specifications(Spec_ID integer PRIMARY KEY AUTOINCREMENT, Item_ID integer, Aggressiveness text, Application text, Brand text, Center_Hole text, Center_Hole_Diameter_Imperial text, Center_Hole_Diameter_Metric text, Cleaning_Area text, Compatible_Dispensing_System text, Concentrate_Dilution_Ratio text, Disinfectant text, Dispense_Rate text, Dispensing_System text, Color_Family text, Function_Attachment_Style text, Industries text, Maximum_Speed text, Machine_Speed text, Commercial_Kitchen_Cleaning text, Dishwasher_Safe text, Overall_Diameter_Imperial text, Overall_Diameter_Metric text, Overall_Length_Imperial text, Overall_Length_Metric text, Overall_Width_Imperial text, Overall_Width_Metric text, Overall_Thickness_Imperial text, Overall_Thickness_Metric text, Net_Weight_Imperial text, Net_Weight_Metric text, Product_Color text, Product_Form text, Product_Type text, Quantity text, Recommended_Application text, Recommended_Surfaces text, Sheet_Size_Imperial text, Sheet_Size_Metric text, Shape text, Size text, Solution_Yield_Imperial text, Solution_Yield_Metric text, Surface_Type text, Third_Party_Certification text, Volume_Imperial text, Volume_Metric text, _Case text, Created text)"
    db_sqlite.create_table(conn,query)
    query = "create table if not exists files(File_ID integer PRIMARY KEY AUTOINCREMENT, File_Name text, Item_ID text, Created text)"
    db_sqlite.create_table(conn,query)
    db_sqlite.close(conn)

    try:
        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_name = "portal"
        try:
            container_client = blob_service_client.create_container(container_name)
        except  Exception as ex:
            container_client = blob_service_client.get_container_client(container_name)
            pass
        get_products()

    except Exception as ex:
        print('Exception ->', str(ex))