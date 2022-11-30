import json
from time import gmtime, strftime
import time
import requests
import urllib.parse
import urllib.request
from os import path
import os, uuid
from PIL import Image
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

def get_header() :
    ua=UserAgent()
    return {'User-Agent': ua.random,       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',      'Accept-Encoding': 'none',      'Accept-Language': 'en-US,en;q=0.8',      'Connection': 'keep-alive'}

url = 'https://www.3m.com/3M/en_US/company-us/all-3m-products/~/3M-Novec-Electronic-Degreaser-12-oz-Can-6-Case/?N=5002385+3292076371&rt=rud'

print(url)
for i in range(1) :
      try :
            start_time= time.time()
            headers = {
                  'Host': 'www.3m.com',
                  'Connection': 'keep-alive',
                  'Cache-Control': 'max-age=0',
                  'Upgrade-Insecure-Requests': '1',
                  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
                  'Accept-Encoding': 'gzip, deflate',
                  'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                  'Dnt': '1'
            }
            # response = requests.get(url, headers= header_data, timeout=2)
            # print ('count :', i, response,'Content-Length:', response.headers['Content-Length'], response.elapsed.total_seconds(), time.time()-start_time)
            # if response.status_code == 200 : print(response.status_code, "OK")
            req = urllib.request.Request(url, headers)
            print(req)
            with urllib.request.urlopen(req) as response:
                  the_page = response.read()


      except Exception as e :
            print(str(e))
            pass

