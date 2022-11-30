import unittest
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import xlwt 
from xlwt import Workbook 
from xlrd import open_workbook
import os

inputName = "BankAccount.xls"
outputName = "Result.xls"
sheetName = "Sheet1"
f = open("user.txt", "r")
_user = f.readline()
_pass = f.readline()

##########################################################      
class PythonOrgSearch(unittest.TestCase):
    def setUp(self):
        PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")
        self.driver = webdriver.Chrome(executable_path = DRIVER_BIN)
    def test_search_in_python_org(self):
        driver = self.driver     
        driver.get("http://proveedoreco.infonavit.org.mx/proveedoresEcoWeb")
        elem = driver.find_element_by_name("usuario")
        elem.send_keys(_user)
        elem = driver.find_element_by_name("password")
        elem.send_keys(_pass) 
        elem.send_keys(Keys.RETURN)
        my_read_obj = open_workbook(inputName,on_demand=True)   #---------------xls read obj       
        my_read_sheet = my_read_obj.sheet_by_index(0) 
        my_write_obj = Workbook()                               #---------------xls write obj
        my_write_sheet = my_write_obj.add_sheet('Sheet1')         
        #-----------------------------
        record = 0 
        invalue = 0
        for cell_col in my_read_sheet.col(0): 
            cells = my_read_sheet.row(record)
            for cell in cells:
                invalue = int(cell.value)
            my_write_sheet.write(record, 0,invalue) 
            elem = driver.find_element_by_name('numeroCredito')
            elem.clear_field()
            elem.send_keys(invalue)
            elem.send_keys(Keys.RETURN)
            try:
                elem = driver.find_element_by_xpath("//form[@name='proveedoresForm']/fieldset/div/div[2]/ul/li").text
                my_write_sheet.write(record, 2,elem) 
                try:
                    elem = driver.find_element_by_xpath("//form[@name='proveedoresForm']/fieldset[2]/div/div[5]/span").text
                    my_write_sheet.write(record, 1,elem)
                except NoSuchElementException:
                    pass
            except NoSuchElementException:
                pass
                elem = driver.find_element_by_xpath("//form[@name='proveedoresForm']/fieldset[2]/div/div[5]/span").text
                my_write_sheet.write(record, 1,elem)
            record = record+1
        my_write_obj.save(outputName)  
        ###################################################### 
    def tearDown(self):
        self.driver.close()
#########################################
if __name__ == "__main__":
    unittest.main()