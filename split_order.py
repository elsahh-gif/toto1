import pandas as pd
import numpy as np
import math
import xlsxwriter
import time
import copy
import sys

order_1 = []
order_2 = []

def print_to_excel():
    file_name = 'order_list.xlsx'
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter') # pylint: disable=abstract-class-instantiated
    
    initial_order_df = pd.DataFrame(initial_order)
    initial_order_df.columns = ['Order_Number','Delivery_Time','Qty','FG_Type','Export/Local']
    initial_order_df.to_excel(writer,'Initial_Order')
    
    order_2_df = pd.DataFrame(order_2)
    order_2_df.columns = ['Order_Number','Delivery_Time','Qty','FG_Type','Export/Local']
    order_2_df.to_excel(writer,'Order_2')
    
    writer.close()
    
initial_order = pd.read_excel ('split_order.xlsx',sheet_name = 'Initial_Order').to_numpy()
FG_List = pd.read_excel ('split_order.xlsx',sheet_name = 'FG_List').to_numpy()

for i in range(len(FG_List)):
    for j in reversed(range(len(initial_order))):
        if (initial_order[j,3]==FG_List[i,0].strip()):
            if ((initial_order[j,4]==FG_List[i,2].strip())|(FG_List[i,2].strip()=='RANDOM')):
                if (initial_order[j,2]>=FG_List[i,1]):
                    initial_order[j,2]-=FG_List[i,1]
                    
                    arr = []
                    arr.append(initial_order[j,0])
                    arr.append(initial_order[j,1])
                    arr.append(FG_List[i,1])
                    arr.append(initial_order[j,3])
                    arr.append(initial_order[j,4])
                    
                    order_2.append(arr)
                    FG_List[i,1] = 0
                    break
                else:
                    arr = []
                    arr.append(initial_order[j,0])
                    arr.append(initial_order[j,1])
                    arr.append(initial_order[j,2])
                    arr.append(initial_order[j,3])
                    arr.append(initial_order[j,4])
                    
                    order_2.append(arr)
                    
                    FG_List[i,1] -= initial_order[j,2]
                    
                    initial_order[j,2] = 0
                
if (len(order_2)>0):
    print_to_excel()
    print ('DONE!!!')
