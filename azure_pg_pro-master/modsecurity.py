import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
ua=UserAgent()
hdr = {'User-Agent': ua.random,
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
      'Accept-Encoding': 'none',
      'Accept-Language': 'en-US,en;q=0.8',
      'Connection': 'keep-alive'}
# urllib.request.urlretrieve(Web_Category_Image, download_path + Category_Image_Name)
url = "https://istudio.pgpro.com/Assets/DownloadMSDS/95H2AGDNMWHM33YD"
# url = "https://istudio.pgpro.com/QuickView/ShowAsset/?id=e68dfec2-9768-4f0f-929d-a5b3ea7bab95"
# url = "https://istudio.pgpro.com/di/prod/dadf8c23-5b0e-4837-ae02-7dbeaa3f6b74/s/640x418/jq/90/o/th.jpg"
r = requests.get(url, headers=hdr)
# r = requests.get(url, allow_redirects=True)
# r = requests.get(url)

try:
    Content_Length = r.headers['Content-Length']
    print("Content_Length : ", Content_Length)
except:
    pass
try:
    ETag = r.headers['ETag']
    ETag = ETag[1:len(ETag)-1]
    print("ETag : ", ETag)
except:
    pass
try:
    Last_Modified_by_Mfg = r.headers['Last-Modified']
    print("Last_Modified_by_Mfg : ", Last_Modified_by_Mfg)
except:
    pass
print (r.headers)
# r = requests.get(url, allow_redirects=True)

file_name =  r.headers['Content-Disposition'].split('"')[1]

print(file_name)
open('download.pdf', 'wb').write(r.content)