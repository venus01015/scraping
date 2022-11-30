import db_sqlite
import csv

if  __name__ == "__main__":
    DB_Name = "ekeystone.db"
    conn = db_sqlite.connection(DB_Name)
    query = "SELECT * FROM scraping_data"
    rows = db_sqlite.select_query(conn, query)
    db_sqlite.close(conn)
    no = 1
    cou = 0
    for row in rows :
        cou += 1
        if cou == 1:
            csv_file = "keystone_{}.csv".format(no)
            with open(csv_file, 'a', encoding="utf-8", newline='') as file:
                fields = ['Product itle', 'SKU', 'Short Description', 'Long Description', 'Features', 'Published', 'Is featured?', 'Visibility in catalog', 'Categories', 'Supplier', 'Product Cost', 'Sale Price', 'Regular Price', 'Color', 'Material', 'Style', 'Size', 'Quantity', 'ORDER QTY', 'Images', 'Purchase', 'Vehicle', 'Fits']
                writer = csv.writer(file)
                writer.writerow(fields)
        with open(csv_file, 'a', encoding="utf-8", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)
        if cou == 4000 :
            cou = 0
            no += 1
        if no >5 :break