import json
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pyodbc
import csv


if  __name__ == "__main__":
    try:
        server = 'tcp:tstdbset01.database.windows.net'
        database = 'tstdb02'
        username = 'sadminx'
        password = 't*Te9qi?nk3'
        sql_driver= '{ODBC Driver 17 for SQL Server}'
        cnxn = pyodbc.connect('DRIVER='+sql_driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)
        cursor = cnxn.cursor()
        create_sql = "CREATE TABLE scraping3m(ID int IDENTITY(1,1), Product_Title varchar(255) ,SKU_SN varchar(255), Product_Description TEXT, Product_Images TEXT, Product_Specification TEXT, Resource_Files TEXT, Manufacture varchar(255), Category1 varchar(255), Category2 varchar(255), Category3 varchar(255), Category4 varchar(255), Category5 varchar(255), Category6 varchar(255), Web_Structure varchar(255));"
        try:
            cursor.execute(create_sql)
            cursor.commit()
        except :
            # cursor.execute("DROP TABLE scraping3m")
            # cursor.commit()
            # cursor.execute(create_sql)
            # cursor.commit()
            pass
        
        k = 0
        with open('ScrapingData.csv', 'rt') as f:
            reader = csv.reader(f) 
            for r, row in enumerate(reader):           
                fields=[]
                for c, col in enumerate(row):
                    fields.append(col)
                       
                _query = "Select * FROM scraping3m WHERE Product_Title = '" + fields[0] + "' AND CONVERT(NVARCHAR(MAX), Product_Description) = N'" + fields[2] + "' AND CONVERT(NVARCHAR(MAX), Product_Images) = N'" + fields[3] + "' AND CONVERT(NVARCHAR(MAX), Resource_Files) = N'" + fields[5] + "' AND CONVERT(NVARCHAR(MAX), Web_Structure) = N'" + fields[13] + "';"
                
                cursor.execute(_query)
                row = cursor.fetchone()
                if not row :

                    _query = "INSERT INTO scraping3m( Product_Title, SKU_SN, Product_Description, Product_Images, Product_Specification, Resource_Files, Manufacture, Category1, Category2, Category3, Category4, Category5, Category6, Web_Structure) VALUES ("
                    for field in fields :
                        _query += "'" + field + "',"
                    _query = _query[:len(_query)-1] + ");"
                    try:
                        cursor.execute(_query)
                        cursor.commit()
                    except:
                        pass

    except Exception as ex:
        print('Exception ->', str(ex))