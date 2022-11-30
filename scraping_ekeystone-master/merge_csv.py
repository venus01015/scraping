import os
from tempfile import NamedTemporaryFile
import shutil
import csv

dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)
fields = ['Product itle', 'SKU', 'Short Description', 'Long Description', 'Features', 'Published', 'Is featured?', 'Visibility in catalog', 'Categories', 'Supplier', 'Product Cost', 'Sale Price', 'Regular Price', 'Color', 'Material', 'Style', 'Size', 'Quantity', 'ORDER QTY', 'Images', 'Purchase', 'Vehicle', 'Fits']
outfile = "all_product.csv"
with open(outfile, 'a', encoding="utf-8", newline='') as output_file:
    writer = csv.writer(output_file)
    writer.writerow(fields)
    for f_name in os.listdir(dir_path):
        if f_name.endswith('.csv'):
            # print(f_name)
            # continue
            with open(f_name, 'r', encoding="utf-8") as file:
                reader = csv.reader(file,delimiter = ",")
                data = list(reader)
                k=-1
                for row in data:
                    k+=1
                    if k==0: continue
                    writer = csv.writer(output_file)
                    writer.writerow(row)