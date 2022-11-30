import json
import time
import datetime
import requests
import db_sqlite
import pyodbc

server = 'tcp:tstdbset01.database.windows.net'
database = 'tstdb02'
username = 'sadminx'
password = 't*Te9qi?nk3'
driver= '{ODBC Driver 17 for SQL Server}'
cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()
try:
    remove_sql = "DROP TABLE manufacturer; "
    cursor.execute(remove_sql)
    cursor.commit()
    create_sql = "CREATE TABLE manufacturer(Mfg_ID int IDENTITY(1,1), Name TEXT, Created TEXT, Checked TEXT)"
    cursor.execute(create_sql)
    cursor.commit()
except Exception as e:
    print(str(e))
    pass

try:
    remove_sql = "DROP TABLE categories; "
    cursor.execute(remove_sql)
    cursor.commit()
    create_sql = "create table categories(Category_ID int IDENTITY(1,1), Name TEXT, Created TEXT, Checked TEXT, URL TEXT, Category_Description TEXT, Category_URL TEXT, Parent_ID TEXT, Category_Mark TEXT)"
    cursor.execute(create_sql)
    cursor.commit()
except Exception as e:
    print(str(e))
    pass

try:
    remove_sql = "DROP TABLE items; "
    cursor.execute(remove_sql)
    cursor.commit()
    create_sql = "create table items(Item_ID int IDENTITY(1,1), Name TEXT, URL TEXT, Mfg_ID TEXT, MPartNumber TEXT, UPC TEXT, Spec_ID TEXT, Description TEXT, Details TEXT, Category_ID TEXT, File_ID TEXT, Images TEXT, Created TEXT)"
    cursor.execute(create_sql)
    cursor.commit()
except Exception as e:
    print(str(e))
    pass

try:
    remove_sql = "DROP TABLE specifications; "
    cursor.execute(remove_sql)
    cursor.commit()
    create_sql = "create table specifications(Spec_ID int IDENTITY(1,1), Item_ID int, Aggressiveness TEXT, Application TEXT, Brand TEXT, Center_Hole TEXT, Center_Hole_Diameter_Imperial TEXT, Center_Hole_Diameter_Metric TEXT, Cleaning_Area TEXT, Compatible_Dispensing_System TEXT, Concentrate_Dilution_Ratio TEXT, Disinfectant TEXT, Dispense_Rate TEXT, Dispensing_System TEXT, Color_Family TEXT, Function_Attachment_Style TEXT, Industries TEXT, Maximum_Speed TEXT, Machine_Speed TEXT, Commercial_Kitchen_Cleaning TEXT, Dishwasher_Safe TEXT, Overall_Diameter_Imperial TEXT, Overall_Diameter_Metric TEXT, Overall_Length_Imperial TEXT, Overall_Length_Metric TEXT, Overall_Width_Imperial TEXT, Overall_Width_Metric TEXT, Overall_Thickness_Imperial TEXT, Overall_Thickness_Metric TEXT, Net_Weight_Imperial TEXT, Net_Weight_Metric TEXT, Product_Color TEXT, Product_Form TEXT, Product_Type TEXT, Quantity TEXT, Recommended_Application TEXT, Recommended_Surfaces TEXT, Sheet_Size_Imperial TEXT, Sheet_Size_Metric TEXT, Shape TEXT, Size TEXT, Solution_Yield_Imperial TEXT, Solution_Yield_Metric TEXT, Surface_Type TEXT, Third_Party_Certification TEXT, Volume_Imperial TEXT, Volume_Metric TEXT, _Case text, Created TEXT)"
    cursor.execute(create_sql)
    cursor.commit()
except Exception as e:
    print(str(e))
    pass

try:
    remove_sql = "DROP TABLE files; "
    cursor.execute(remove_sql)
    cursor.commit()
    create_sql = "create table files(File_ID int IDENTITY(1,1), File_Name TEXT, Item_ID TEXT, Created TEXT)"
    cursor.execute(create_sql)
    cursor.commit()
except Exception as e:
    print(str(e))
    pass


DB_Name = "portal.db"
conn = db_sqlite.connection(DB_Name)
####################################
query = "select * from manufacturer"
rows = db_sqlite.select_query(conn, query)
sql_query = "SET IDENTITY_INSERT manufacturer ON;"
cursor.execute(sql_query)
cursor.commit()
for row in rows :
    try:
        sql_query = "INSERT INTO manufacturer(Mfg_ID, Name, Created, Checked) VALUES {};".format(row)
        cursor.execute(sql_query)
        cursor.commit()
    except Exception as e:
        print(str(e))
sql_query = "SET IDENTITY_INSERT manufacturer OFF;"
cursor.execute(sql_query)
cursor.commit()
####################################
####################################
query = "select * from categories"
rows = db_sqlite.select_query(conn, query)
sql_query = "SET IDENTITY_INSERT categories ON;"
cursor.execute(sql_query)
cursor.commit()
for row in rows :
    try:
        sql_query = "INSERT INTO categories(Category_ID, Name, Created, Checked, URL, Category_Description, Category_URL, Parent_ID, Category_Mark) VALUES {};".format(row)
        cursor.execute(sql_query)
        cursor.commit()
    except Exception as e:
        print(str(e))
sql_query = "SET IDENTITY_INSERT categories OFF;"
cursor.execute(sql_query)
cursor.commit()
####################################
####################################
query = "select * from items"
rows = db_sqlite.select_query(conn, query)
sql_query = "SET IDENTITY_INSERT items ON;"
cursor.execute(sql_query)
cursor.commit()
for row in rows :
    try:
        sql_query = "INSERT INTO items(Item_ID, Name, URL, Mfg_ID, MPartNumber, UPC, Spec_ID, Description, Details, Category_ID, File_ID, Images, Created) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}') ;".format(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7].replace("'", "`"),row[8].replace("'", "`"),row[9],row[10],row[11],row[12])
        # sql_query = "INSERT INTO items(Item_ID, Name, URL, Mfg_ID, MPartNumber, UPC, Spec_ID, Description, Details, Category_ID, File_ID, Images) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}') ;".format(row[0],row[1],row[1],row[1],row[1],row[1],row[1],row[1],row[1],row[1],row[1],row[1])
        cursor.execute(sql_query)
        cursor.commit()
    except Exception as e:
        print(str(e))
sql_query = "SET IDENTITY_INSERT items OFF;"
cursor.execute(sql_query)
cursor.commit()
####################################
####################################
query = "select * from specifications"
rows = db_sqlite.select_query(conn, query)
sql_query = "SET IDENTITY_INSERT specifications ON;"
cursor.execute(sql_query)
cursor.commit()
for row in rows :
    try:
        sql_query = "INSERT INTO specifications(Spec_ID, Item_ID, Aggressiveness, Application, Brand, Center_Hole, Center_Hole_Diameter_Imperial, Center_Hole_Diameter_Metric, Cleaning_Area, Compatible_Dispensing_System, Concentrate_Dilution_Ratio, Disinfectant, Dispense_Rate, Dispensing_System, Color_Family, Function_Attachment_Style, Industries, Maximum_Speed, Machine_Speed, Commercial_Kitchen_Cleaning, Dishwasher_Safe, Overall_Diameter_Imperial, Overall_Diameter_Metric, Overall_Length_Imperial, Overall_Length_Metric, Overall_Width_Imperial, Overall_Width_Metric, Overall_Thickness_Imperial, Overall_Thickness_Metric, Net_Weight_Imperial, Net_Weight_Metric, Product_Color, Product_Form, Product_Type, Quantity, Recommended_Application, Recommended_Surfaces, Sheet_Size_Imperial, Sheet_Size_Metric, Shape, Size, Solution_Yield_Imperial, Solution_Yield_Metric, Surface_Type, Third_Party_Certification, Volume_Imperial, Volume_Metric, _Case, Created) VALUES {};".format(row)
        cursor.execute(sql_query)
        cursor.commit()
    except Exception as e:
        print(str(e))
sql_query = "SET IDENTITY_INSERT specifications OFF;"
cursor.execute(sql_query)
cursor.commit()
####################################
####################################
query = "select * from files"
rows = db_sqlite.select_query(conn, query)
sql_query = "SET IDENTITY_INSERT files ON;"
cursor.execute(sql_query)
cursor.commit()
for row in rows :
    try:
        sql_query = "INSERT INTO files(File_ID, File_Name, Item_ID, Created) VALUES {};".format(row)
        cursor.execute(sql_query)
        cursor.commit()
    except Exception as e:
        print(str(e))
sql_query = "SET IDENTITY_INSERT files OFF;"
cursor.execute(sql_query)
cursor.commit()
####################################
db_sqlite.close(conn)