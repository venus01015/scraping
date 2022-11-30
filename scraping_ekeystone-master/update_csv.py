import os
from tempfile import NamedTemporaryFile
import shutil
import csv

dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)
fields = ['Product itle', 'SKU', 'Short Description', 'Long Description', 'Features', 'Published', 'Is featured?', 'Visibility in catalog', 'Categories', 'Supplier', 'Product Cost', 'Sale Price', 'Regular Price', 'Color', 'Material', 'Style', 'Size', 'Quantity', 'ORDER QTY', 'Images', 'Purchase', 'Vehicle', 'Fits']

for f_name in os.listdir(dir_path):
    if f_name.endswith('.csv'):
        outfile="new_"+f_name
        with open(outfile, 'a', encoding="utf-8", newline='') as output_file:
            with open(f_name, 'r', encoding="utf-8") as file:
                reader = csv.reader(file,delimiter = ",")
                data = list(reader)
                k=-1
                for row in data:
                    k+=1
                    new_row = row
                    if k != 0 :
                        if row[13] : new_row[3]+="\nColor:"+row[13]
                        if row[14] : new_row[3]+="\nMaterial:"+row[14]
                        if row[15] : new_row[3]+="\nStyle:"+row[15]
                        if row[16] : new_row[3]+="\nSize:"+row[16]
                        if row[17] : new_row[3]+="\nQuantity:"+row[17]
                    writer = csv.writer(output_file)
                    writer.writerow(new_row)