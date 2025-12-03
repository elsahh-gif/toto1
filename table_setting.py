import pandas as pd
import numpy as np
import math
import xlsxwriter
import time
import copy
import sys

arr_final = []
unique_table = []

def print_to_excel():
    file_name = 'table_list.xlsx'
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter') # pylint: disable=abstract-class-instantiated
    
    arr_final_df = pd.DataFrame(arr_final)
    arr_final_df = arr_final_df.iloc[:,[0,1,2,3]]
    arr_final_df.columns = ['Table','FG','Cap','Time']
    arr_final_df.to_excel(writer,'Table_List')
    
    unique_table_df = pd.DataFrame(unique_table)
    unique_table_df.columns = ['Table','Capacity','#Employee/Table']
    unique_table_df.to_excel(writer,'Unique_Table')
    
    writer.close()
    
table_list = pd.read_excel ('table_setting.xlsx',sheet_name = 'Table_List').to_numpy()
table_size = pd.read_excel ('table_setting.xlsx',sheet_name = 'Table_Size').to_numpy()

for i in range(len(table_size)):
    table_size[i,0] = table_size[i,0].strip()

for i in range(len(table_size)):
    if (table_size[i,3]==1):
        for j in range(1,table_size[i,1]+1):
            for k in range(len(table_list)):
                if (table_list[k,0].upper()==table_size[i,0].upper()):
                    arr = []
                    table_name = table_list[k,0].upper() + 'C'
                    if (j<10):
                        table_name = table_name + '0'
                    table_name = table_name + str(j)
                    arr.append(table_name)
                    arr.append(table_list[k,1])
                    arr.append(table_size[i,2]*60/table_list[k,3])
                    arr.append(table_list[k,3])
                    arr.append(table_size[i,2])
                    arr.append(table_size[i,4])
                    arr_final.append(arr)
    else:
        for j in range(1,table_size[i,1]+1):
            for k in range(len(table_list)):
                if (table_list[k,0].upper()==table_size[i,0].upper()):
                    arr = []
                    table_name = table_list[k,0].upper() + 'R'
                    if (j<10):
                        table_name = table_name + '0'
                    table_name = table_name + str(j)
                    arr.append(table_name)
                    arr.append(table_list[k,1])
                    arr.append(table_size[i,2]*60/table_list[k,3])
                    arr.append(table_list[k,3])
                    arr.append(table_size[i,2])
                    arr.append(table_size[i,4])
                    arr_final.append(arr)
                
for i in range(len(arr_final)):
    found = 0
    for j in range(len(unique_table)):
        if (unique_table[j][0]==arr_final[i][0]):
            found=1
            break
    if (found==0):
        arr = []
        arr.append(arr_final[i][0])
        arr.append(arr_final[i][4])
        arr.append(arr_final[i][5])
        unique_table.append(arr)
        
print_to_excel()
print ('DONE!!!')
