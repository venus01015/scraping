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

####################################
sql_query = "SELECT * From items;"
rows = cursor.execute(sql_query)
for row in rows:
    print("-------------------")
    print( row[8])

####################################