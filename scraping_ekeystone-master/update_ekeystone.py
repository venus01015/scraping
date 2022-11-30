import db_sqlite
import time

def change_string(text):
    text = text.replace('®','')
    text = text.replace('&reg;','')
    text = text.replace('&trade;','')
    text = text.replace('&amp; ','')
    text = text.replace('"',"`")
    text = text.replace("'","`")
    text = text.replace('™','')
    return text

def fix_string(string):
    change=[]
    k=0
    for a in string:
        k += 1
        if a==" " or (k < 4):
            continue
        if (a.isupper()) == True and string[k-2:k-1].islower()==True:
            change.append(string[k-1:k+2])
    for cha in change:
        string=string.replace(cha," "+cha)
    return string
#fields = ['Product itle', 'SKU', 'Short Description', 'Long Description', 'Features', 'Published', 'Is featured?', 'Visibility in catalog', 'Categories', 'Supplier', 'Product Cost', 'Sale Price', 'Regular Price', 'Color', 'Material', 'Style', 'Size', 'Quantity', 'ORDER QTY', 'Images', 'Purchase', 'Vehicle', 'Fits']
query = "create table if not exists scraping_data(Product_Title, SKU, Short_Description, Long_Description, Features, Published, Is_featured, Visibility_in_catalog, Categories, Supplier, Product_Cost, Sale_Price, Regular_Price, Color, Material, Style, Size, Quantity, ORDER_QTY, Images, Purchase, Vehicle, Fits)"
if __name__ == "__main__":
    DB_Name = "ekeystone.db"
    db_sqlite.create_db(DB_Name)
    conn = db_sqlite.connection(DB_Name)
    query = "SELECT Product_Title, SKU, Short_Description, Long_Description, Features, Categories, Images FROM scraping_data"
    rows = db_sqlite.select_query(conn, query)
    if len(rows) == 0 : exit()
    print(len(rows))
    cou = 0
    for row in rows :
        cou+=1
        if cou % 50 ==0:
            print(cou)
        # if cou == 42 :
        #     time.sleep(0.1)
        Short_Description = change_string(row[2])
        Long_Description = change_string(row[3])
        Features = change_string(row[4])
        Categories = fix_string(row[5])
        Images = row[6].replace("&maxheight=68&maxwidth=68","&maxheight=550&maxwidth=550").replace("&maxheight=250&maxwidth=400","&maxheight=550&maxwidth=550").replace(",","|")
        query = """UPDATE scraping_data SET Short_Description = "{}", Long_Description = "{}", Features = "{}", Categories = "{}", Images = "{}" where Product_Title="{}" and SKU="{}" and Short_Description="{}" and Categories="{}";""".format(
                Short_Description, Long_Description, Features, Categories, Images, row[0], row[1], row[2], row[5])
        db_sqlite.update_query(conn,query)
