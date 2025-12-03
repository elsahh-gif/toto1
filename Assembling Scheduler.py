import pandas as pd
import numpy as np
import math
import xlsxwriter
import time
import copy
import sys

sys.setrecursionlimit(10_000)
set_up_time = 10*60
Monday = 1

Additional_order_day = 15
day_off_before_additional = 1 #1 means yes, 0 means no

##############################################################################

operation_mode = 2 #1 for table list, 2 for run the scheduler
sort_mode = 1
target_day = 14 #can be changed by adding workload
target_day_2 = target_day #never change
print_comb = 5
sub_divider = 5 #if qty order 1000, j will be a multiplier of 50. if 1, it will be a multiplier of box size

deviation_mult_0 = 0.9 #deviation mult if there is no load in a day (the lower, the most likely to stack loads in a day rather than distribute it)
deviation_mult_OT = 1.2 #the higher, the most likely to avoid OT 

arr_ex = ['EXPORT-01','EXPORT-02','EXPORT-03','EXPORT-04','EXPORT-05','EXPORT-06','EXPORT-07','EXPORT-08','EXPORT-09','EXPORT-10']
arr_loc = ['LOCAL-01','LOCAL-02','LOCAL-03','LOCAL-04','LOCAL-05','LOCAL-06','LOCAL-07','LOCAL-08','LOCAL-09','LOCAL-10']
arr_add_ex = ['ADD_EXPORT-01','ADD_EXPORT-02','ADD_EXPORT-03','ADD_EXPORT-04','ADD_EXPORT-05']
arr_add_loc = ['ADD_LOCAL-01','ADD_LOCAL-02','ADD_LOCAL-03','ADD_LOCAL-04','ADD_LOCAL-05']
arr_ex_loc = arr_ex+arr_loc+arr_add_ex+arr_add_loc

order = []
table_cap = []
stock_fg = []
calendar = []
order_capacity = []
workload = []
wl = []
row_names = []
row_names_2 = []
row_names_fg = []
row_names_jig = []
column_names = []
fg_produced = []
fg_need_OT = []
fg_BOM = []
stock_part = []
deviation_sum = []
fail_of_lack_order = []
calendar_stock_part = []
calendar_stock_part_prod = []
table_list = []
fg_calendar = []
BOM_set_id = []
part_test_production = []
box_fg = []
additional_fg = []
additional_table_fg = []
table_calendar_box = []
table_calendar_load_box = []
table_calendar_time = []
max_cap = []
fg_need_part = []
stock_part_edit = []
is_set = []
fg_lack_of_part = []
arr_need_part = []
arr_need_OT = []
arr_production_item = []
calendar_prod_summary = []
fg_jig = []
jig_qty = []
jig_schedule = []

temporary_part_list = []
temporary_fg_need_part = []

draft_order = []
draft_stock_fg = []

saved_calendar = []
saved_table_calendar_box = []
saved_table_calendar_load_box = []
saved_fg_calendar = []
saved_fg_produced = []
saved_stock_part_edit = []
saved_stock_fg = []
saved_temporary_part_list = []
saved_jig_qty = []

break_all_ops = 0
attempt = 0
max_attempt = 0
start_day = 0
deviation_workload = 0
deviation_qty = 0
deviation_temp = 0
need_OT = 0
need_part = 0
OT_min = 0

def printX(a):
    for row in a:
        for col in row:
            print("{:8.0f}".format(col), end=" ")
        print("")
        
def printX3(a):
    for row in a:
        for col in row:
            print('{:15}'.format('{}'.format(col)), end="\t")      
        print("")
        
def printXP(a):
    for row in a:
        for col in row:
            print("{:8.2%}".format(col), end=" ")
        print("")
        
def round_up(n, decimals=0): 
    multiplier = 10 ** decimals 
    return math.ceil(n * multiplier) / multiplier

def round_up_box(j, box):
    return math.ceil(j/box)*box
    
def round_down_box(j,box):
    return math.floor(j/box)*box
                       
def find_capacity(capacity_list, item):
    rows = np.where(capacity_list[:,2] == item)
    return capacity_list[rows]
    
def find_stock_fg(stock_fg, item):
    rows = np.where(stock_fg[:,0] == item)
    return int(stock_fg[rows,1])

def change_stock_fg(item, number):
    global stock_fg
    
    rows = np.where(stock_fg[:,0] == item)
    stock_fg[rows,1] = int(stock_fg[rows,1])
    if (number<0):
        stock_fg[rows,1] += number
    elif (number==0):
        stock_fg[rows,1] = 0

def make_fg_need_part(part):
    global fg_need_part
    rows_fg = np.where(BOM[:,1] == part)
    if(len(rows_fg[0])>0):
        for j in range(len(BOM[rows_fg])):
            rows_set = np.where(BOM_set[:,1] == BOM[rows_fg[0][j]][0])
            if (len(rows_set[0])>0):
                make_fg_need_part(BOM[rows_fg[0][j]][0])
            
            rows = np.where(stock_fg[:,0] == BOM[rows_fg[0][j]][0])
            if (len(rows[0])>0):
                fg_need_part[int(rows[0])][0] = 1
    
def change_stock_part(z,order_idx_new, qty, day):
    global stock_part
    global calendar_stock_part
    global stock_part_edit
    
    item = new_order[z][order_idx_new][8]
    order_idx_old= new_order[z][order_idx_new][0]
    for i in range(len(fg_BOM[item])):
        qty_temp = qty
        qty_part = qty_temp*fg_BOM[item][i][1]
        arr_1 = []
        for j in reversed(range(day+1)):
            if(int(float(stock_part_edit[fg_BOM[item][i][0]][j+1]))>0):
                if (int(float(stock_part_edit[fg_BOM[item][i][0]][j+1]))>=qty_part):
                    arr_2 = []
                    arr_2.append(j)
                    arr_2.append(fg_BOM[item][i][0])
                    arr_2.append(qty_part)
                    arr_1.append(arr_2)
                    var_temp = int(float(stock_part_edit[fg_BOM[item][i][0]][j+1]))-qty_part
                    stock_part_edit[fg_BOM[item][i][0]][j+1] = var_temp
                    for k in range(target_day_2-j):
                        stock_part[fg_BOM[item][i][0]][k+j]-=qty_part
                    qty_part = 0
                    break
                else:
                    arr_2 = []
                    arr_2.append(j)
                    arr_2.append(fg_BOM[item][i][0])
                    arr_2.append(stock_part_edit[fg_BOM[item][i][0]][j+1])
                    arr_1.append(arr_2)
                    for k in range(target_day_2-j):
                        stock_part[fg_BOM[item][i][0]][k+j]-=stock_part_edit[fg_BOM[item][i][0]][j+1]
                    qty_part -= stock_part_edit[fg_BOM[item][i][0]][j+1]
                    stock_part_edit[fg_BOM[item][i][0]][j+1]=0
        calendar_stock_part[order_idx_old][day].append(arr_1)

def return_stock_part(z,order_idx_new,day):
    global stock_part
    global calendar_stock_part
    global stock_part_edit
    
    order_idx = new_order[z][order_idx_new][0]
    for i in range(len(calendar_stock_part[order_idx][day])):
        for j in range (len(calendar_stock_part[order_idx][day][i])):
            stock_part_edit[calendar_stock_part[order_idx][day][i][j][1]][calendar_stock_part[order_idx][day][i][j][0]+1]+=calendar_stock_part[order_idx][day][i][j][2]
            for k in range(target_day_2-calendar_stock_part[order_idx][day][i][j][0]):
                stock_part[calendar_stock_part[order_idx][day][i][j][1]][k+calendar_stock_part[order_idx][day][i][j][0]]+=calendar_stock_part[order_idx][day][i][j][2]
    calendar_stock_part[order_idx][day].clear()
            
def check_stock_part(item, qty, day):   
    result=False
    
    stock_arr = []
    for i in range(len(fg_BOM[item])):
        stock_arr += [0]
        
    for i in range(len(fg_BOM[item])):
        stock_arr[i]+=stock_part[fg_BOM[item][i][0]][day]
    
    qty_ready = 2147483647
    
    for i in range(len(fg_BOM[item])):
        if (stock_arr[i]/fg_BOM[item][i][1] < qty_ready):
            qty_ready = int(stock_arr[i]/fg_BOM[item][i][1])
        
    if ((qty!=2147483647)&(qty_ready>=qty)):
        result =True
    
    return result

def amount_ready(item, day):
    arr = []
    for i in range(2):
        arr += [0]
        
    stock_arr = []
    for i in range(len(fg_BOM[item])):
        stock_arr += [0]
        
    for i in range(len(fg_BOM[item])):
        stock_arr[i]+=stock_part[fg_BOM[item][i][0]][day]
    
    qty_ready = 2147483647
    
    for i in range(len(fg_BOM[item])):
        if (stock_arr[i]/fg_BOM[item][i][1] < qty_ready):
            qty_ready = int(stock_arr[i]/fg_BOM[item][i][1])
            arr[0] = fg_BOM[item][i][0]
            arr[1] = qty_ready
            
    return arr

def calculate_stock_part_additional():
    global calendar_stock_part
    global Additional_order_day
    global stock_part_edit_2
    
    Additional_order_day-=1
    if (Additional_order_day>target_day):
        Additional_order_day=target_day

    for i in range(len(calendar_stock_part)):
        for j in range(Additional_order_day):
            for k in range(len(calendar_stock_part[i][j])):
                if (calendar_stock_part[i][j][k][0][1]<len(stock_part_edit_2)):
                    stock_part_edit_2[calendar_stock_part[i][j][k][0][1]][calendar_stock_part[i][j][k][0][0]+1]-=calendar_stock_part[i][j][k][0][2]

def print_to_excel(stock_part_p, stock_fg_p, table_calendar_p, table_calendar_load_p, order_capacity):
    global row_names
    global row_names_2
    global column_names
    global stock_part_edit_2
    global stock_fg
    
    file_name = 'calendar.xlsx'
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter') # pylint: disable=abstract-class-instantiated
    workbook  = writer.book
    
    format_percent = workbook.add_format({'num_format': '0.00%'})
    format_qty = workbook.add_format({'num_format': '###,###,###,###,##0'})
    format_price = workbook.add_format({'num_format': '###,###,###,###,##0.00'})
    
    order_temp = []
    for i in range(len(new_order)):
        order_temp += new_order[i]
    order_df = pd.DataFrame(order_temp)
    order_df = order_df.iloc[:,[4,5,6]]
    order_df.columns = ['FG Type','EXPORT/LOCAL','Qty Assy']
    
    draft_order_df = pd.DataFrame(draft_order)
    draft_order_df = draft_order_df.iloc[:,[4,5,6]]
    draft_order_df.columns = ['FG Type','EXPORT/LOCAL','Order Qty']
    
    draft_stock_fg_df = pd.DataFrame(draft_stock_fg)
    draft_stock_fg_df.columns = ['FG Type','EXPORT/LOCAL','Stock Qty']
    
    cogm_df = pd.DataFrame(cogm)
    cogm_df.columns = ['FG Type', 'COGM']
    
    order_df_merge = pd.merge(order_df, draft_order_df, on=['FG Type', 'EXPORT/LOCAL'], how='right')
    order_df_merge['Qty Assy'] = order_df_merge['Qty Assy'].fillna(0)
    order_df_merge = pd.merge(order_df_merge, draft_stock_fg_df, on=['FG Type', 'EXPORT/LOCAL'], how='inner')
    order_df_merge['Stock Qty'] = pd.to_numeric(order_df_merge['Stock Qty'])
    
    if (len(arr_need_OT)==0):
        arr = []
        for i in range(4):
            arr.append('')
        arr_need_OT.append(arr)
    arr_need_OT_df = pd.DataFrame(arr_need_OT)
    arr_need_OT_df.columns = ['FG Type', 'Cancel Assy Qty','EXPORT/LOCAL','Reason']
    order_df_merge = pd.merge(order_df_merge, arr_need_OT_df, on=['FG Type', 'EXPORT/LOCAL'], how='left')
    order_df_merge = order_df_merge.drop('Reason', axis = 1)
    order_df_merge['Cancel Assy Qty'] = order_df_merge['Cancel Assy Qty'].fillna(0)
    order_df_merge['Qty Assy'] -= order_df_merge['Cancel Assy Qty']
    
    order_df_merge['Over Production Qty']=order_df_merge['Stock Qty']+order_df_merge['Qty Assy']-order_df_merge['Order Qty']+order_df_merge['Cancel Assy Qty']
    
    order_df_merge = pd.merge(order_df_merge, cogm_df, on=['FG Type'], how='left')
    order_df_merge['COGM'] = order_df_merge['COGM'].fillna(0)
    order_df_merge['TOTAL COGM']=order_df_merge['COGM']*(order_df_merge['Order Qty']-order_df_merge['Cancel Assy Qty'])
    
    order_df_merge.sort_values(['FG Type','EXPORT/LOCAL'], ascending=[True, True], inplace=True)
    order_df_merge.to_excel(writer,'Order Summary', index=False)
    
    sheet_order = writer.sheets['Order Summary']
    sheet_order.set_column('A:A', 18, None)
    sheet_order.set_column('B:B', 15, None)
    sheet_order.set_column('C:E', 9, format_qty)
    sheet_order.set_column('F:G', 17, format_qty)
    sheet_order.set_column('H:I', 15, format_price)
        
    fg_calendar_df = pd.DataFrame(fg_calendar,row_names_fg,column_names)
    fg_calendar_df = fg_calendar_df[fg_calendar_df.ne(0).any(axis = 1)]
    fg_calendar_df.to_excel(writer,'FG Calendar')
        
    for i in range (len(table_calendar_p)):
        for j in range (len(table_calendar_p[i])):
            if (len(table_calendar_p[i][j])>0):
                for k in range(len(table_calendar_p[i][j])):
                    table_calendar_p[i][j][k].pop(2)
    
    table_calendar_df = pd.DataFrame(table_calendar_p,row_names_2,column_names)
    table_calendar_df.to_excel(writer,'Table')
                
    table_calendar_load_df = pd.DataFrame(table_calendar_load_p,row_names_2,column_names)
    table_calendar_load_df.to_excel(writer,'Table Load')
    
    table_calendar_time_df = pd.DataFrame(table_calendar_time,row_names_2,column_names)
    table_calendar_time_df.to_excel(writer,'Table Time')
    
    for i in range(len(jig_schedule)):
        for j in range(len(jig_schedule[i])):
            amount_pop = 0
            for k in range(len(jig_schedule[i][j])):
                if (len(jig_schedule[i][j][k-amount_pop])==0):
                    jig_schedule[i][j].pop(k-amount_pop)
                    amount_pop+=1
                        
    jig_schedule_df = pd.DataFrame(jig_schedule,row_names_jig)
    jig_schedule_df.to_excel(writer,'Jig Schedule')
    
    column_names.insert(0,'Part')
              
    stock_fg_order = order_df_merge.groupby('FG Type')['Over Production Qty'].sum().reset_index()
    stock_fg_order_np = stock_fg_order.to_numpy()
    
    for i in range(len(stock_fg)):
        for j in range (len(stock_fg_order)):
            if (stock_fg_order_np[j,0] == stock_fg[i][0]):
                stock_fg[i][1] += stock_fg_order_np[j,1]
                break
        
    stock_fg_df = pd.DataFrame(stock_fg)
    stock_fg_df.columns = ['FG Type','Qty']
    stock_fg_df.to_excel(writer,'Stock FG', index = False)
    
    calculate_stock_part_additional()
    stock_part_df = pd.DataFrame(stock_part_edit_2)
    stock_part_df.columns = column_names
    stock_part_df.to_excel(writer,'Stock Part', index = False)
    
    sheet_table_load = writer.sheets['Table Load']
    str_percent_formatting = 'B:'+chr(ord('@')+target_day+1)
    sheet_table_load.set_column(str_percent_formatting, None, format_percent)
    
    writer.close()
    
def save_data():
    global saved_calendar
    global saved_table_calendar_box 
    global saved_table_calendar_load_box
    global saved_fg_calendar
    global saved_fg_produced
    global saved_stock_part_edit
    global saved_stock_fg
    global saved_temporary_part_list
    global saved_jig_qty
    global saved_calendar_stock_part
    
    saved_calendar = copy.deepcopy(calendar)
    saved_table_calendar_box = copy.deepcopy(table_calendar_box)
    saved_table_calendar_load_box = copy.deepcopy(table_calendar_load_box)
    saved_fg_calendar = copy.deepcopy(fg_calendar)
    saved_fg_produced = copy.deepcopy(fg_produced)
    saved_stock_part_edit = copy.deepcopy(stock_part_edit)
    saved_stock_fg = copy.deepcopy(stock_fg)
    saved_temporary_part_list = copy.deepcopy(temporary_part_list)
    saved_jig_qty = copy.deepcopy(jig_qty)
    saved_calendar_stock_part = copy.deepcopy(calendar_stock_part)
    
def load_saved_data():
    global calendar
    global table_calendar_box 
    global table_calendar_load_box
    global fg_calendar
    global fg_produced
    global stock_part_edit
    global stock_fg
    global temporary_part_list
    global jig_qty
    global calendar_stock_part
    
    calendar = copy.deepcopy(saved_calendar)
    table_calendar_box = copy.deepcopy(saved_table_calendar_box)
    table_calendar_load_box = copy.deepcopy(saved_table_calendar_load_box)
    fg_calendar = copy.deepcopy(saved_fg_calendar)
    fg_produced = copy.deepcopy(saved_fg_produced)
    stock_part_edit = copy.deepcopy(saved_stock_part_edit)
    stock_fg = copy.deepcopy(saved_stock_fg)
    temporary_part_list = copy.deepcopy(saved_temporary_part_list)
    jig_qty = copy.deepcopy(saved_jig_qty)
    calendar_stock_part = copy.deepcopy(saved_calendar_stock_part)
    
def make_table_calendar(table_calendar_p,part,capacity,idx,part_idx):
    if (capacity == 0):
        table_calendar_p.pop(idx)
    else:
        table_calendar_p[idx][0]=part
        table_calendar_p[idx][1]=capacity
        table_calendar_p[idx][2]=part_idx

def make_table_calendar_load_box(table_id,day,table_calendar_load_box_p,load):
    table_calendar_load_box_p[table_id][day] += load

def while_subtractor(j,qty,box_size):
    if (qty/box_size<sub_divider):
        if(j%box_size>0):
            return j-(j%box_size)
        elif((j>0)&(j-box_size<0)):
            return 0
        else:
            return j-box_size
    else:
        if(j%box_size>0):
            return j-(j%box_size)
        elif((j>0)&(j-math.floor((qty/sub_divider)/box_size)*box_size<0)):
            return 0
        else:
            return j-math.floor((qty/sub_divider)/box_size)*box_size
        
def return_stock_part_prod(order_num,t_day):
    global calendar_stock_part_prod
    global calendar_prod_summary
    global calendar_production
    global calendar_production_load
    global stock_part
    global stock_part_edit
    
    for i in range(len(calendar_stock_part_prod[order_num][t_day])):
        s_day = calendar_stock_part_prod[order_num][t_day][i][2]
        stock_part_edit[calendar_stock_part_prod[order_num][t_day][i][0]][s_day+2]-=calendar_stock_part_prod[order_num][t_day][i][1]
        for j in range(target_day_2-s_day-1):
            stock_part[calendar_stock_part_prod[order_num][t_day][i][0]][s_day+1+j]-=calendar_stock_part_prod[order_num][t_day][i][1]
    
    calendar_stock_part_prod[order_num][t_day].clear()
    
    for i in range(len(calendar_prod_summary[order_num][t_day])):
        part_idx = calendar_prod_summary[order_num][t_day][i][0]
        part_qty = calendar_prod_summary[order_num][t_day][i][1]
        prod_table = calendar_prod_summary[order_num][t_day][i][2]
        prod_load = calendar_prod_summary[order_num][t_day][i][3]
        p_day = calendar_prod_summary[order_num][t_day][i][4]
        
        calendar_production_load[prod_table][p_day+1]-=prod_load
        
        for j in range(len(calendar_production[prod_table][p_day+1])):
            if (calendar_production[prod_table][p_day+1][j][0] == arr_part_routing[part_idx][0]):
                if (calendar_production[prod_table][p_day+1][j][1]==part_qty):
                    calendar_production[prod_table][p_day+1][j].clear
                else:
                    calendar_production[prod_table][p_day+1][j][1]-=part_qty
        
def make_production(order_num, fg_idx, fg_qty, t_day):
    global calendar_stock_part_prod
    global calendar_prod_summary
    global calendar_production
    global calendar_production_load
    global stock_part
    global stock_part_edit
    
    calendar_origin = copy.deepcopy(calendar_production)
    calendar_load_origin = copy.deepcopy(calendar_production_load)
    stock_part_origin = copy.deepcopy(stock_part)
    stock_part_edit_origin = copy.deepcopy(stock_part_edit)
    
    stock_added = []
    
    def fail_schedule(calendar_origin, calendar_load_origin, stock_part_origin, stock_part_edit_origin):
        calendar_production = copy.deepcopy(calendar_origin)
        calendar_production_load = copy.deepcopy(calendar_load_origin)
        stock_part = copy.deepcopy(stock_part_origin)
        stock_part_edit = copy.deepcopy(stock_part_edit_origin)
        
        del calendar_origin
        del calendar_load_origin
        del stock_part_origin
        del stock_part_edit_origin
        return False
        
    for x in range(len(fg_BOM[fg_idx])):
        part_idx = fg_BOM[fg_idx][x][0]
        part_qty = fg_qty*fg_BOM[fg_idx][x][1]-stock_part[fg_BOM[fg_idx][x][0]][t_day]
        
        previous_step_success = 1
        start_day = 0
        for i in range(len(arr_part_routing[part_idx])-1):
            if (previous_step_success==0):
                fail_schedule(calendar_origin, calendar_load_origin, stock_part_origin, stock_part_edit_origin)
            else:
                previous_step_success = 0
            produced_qty = 0
            while produced_qty<part_qty:
                max_prod = math.floor(production_table_cap[arr_part_routing[part_idx][i+1][1]][4]/arr_part_routing[part_idx][i+1][5])*arr_part_routing[part_idx][i+1][5]
                for day in range(start_day,t_day+13):
                    j = math.ceil((part_qty-produced_qty)/arr_part_routing[part_idx][i+1][5])*arr_part_routing[part_idx][i+1][5]
                    if (j>max_prod):
                        j = max_prod
                    while j>=0:
                        time_required_box = j*arr_part_routing[part_idx][i+1][4]
                        setup_time_prod = arr_part_routing[part_idx][i+1][3]
                        for k in range(len(calendar_production[arr_part_routing[part_idx][i+1][1]][day+1])):
                            if (calendar_production[arr_part_routing[part_idx][i+1][1]][day+1][k][0]==arr_part_routing[part_idx][0]):
                                setup_time_prod = 0
                                break
                        time_required = setup_time_prod+time_required_box
                        load_required = time_required/(production_table_cap[arr_part_routing[part_idx][i+1][1]][4]*3600)
                        
                        if (calendar_production_load[arr_part_routing[part_idx][i+1][1]][day+1]+load_required<=1):
                            found = 0
                            for k in range(len(calendar_production[arr_part_routing[part_idx][i+1][1]][day+1])):
                                if (calendar_production[arr_part_routing[part_idx][i+1][1]][day+1][k][0]==arr_part_routing[part_idx][0]):
                                    calendar_production[arr_part_routing[part_idx][i+1][1]][day+1][k][1]+=j
                                    found = 1
                                    break
                                    
                            if (found==0):
                                arr = []
                                arr.append(arr_part_routing[part_idx][0])
                                arr.append(j)
                                calendar_production[arr_part_routing[part_idx][i+1][1]][day+1].append(arr)
                                
                            calendar_production_load[arr_part_routing[part_idx][i+1][1]][day+1] += load_required
                            
                            arr=[]
                            arr.append(part_idx)
                            arr.append(j)
                            arr.append(arr_part_routing[part_idx][i+1][1])
                            arr.append(load_required)
                            arr.append(day)
                            calendar_prod_summary[order_num][t_day].append(arr)
                            
                            produced_qty+=j
                            j=0
                            
                            if (produced_qty>=part_qty):
                                previous_step_success = 1
                                start_day = day+1
                                break
                        
                        j -= arr_part_routing[part_idx][i+1][5]
                    if (produced_qty>=part_qty):
                        break
            if (previous_step_success==1):
                arr = []
                arr.append(order_num)
                arr_2 = []
                arr_2.append(part_idx)
                arr_2.append(part_qty)
                arr_2.append(day)
                
                arr_3 = []
                arr_3.append(arr)
                arr_3.append(arr_2)
                
                stock_added.append(arr_3)
            else:
                fail_schedule(calendar_origin, calendar_load_origin, stock_part_origin, stock_part_edit_origin)
    
    for i in range(len(stock_added)):
        order_add = stock_added[i][0][0]
        part_add = stock_added[i][1][0]
        qty_add = stock_added[i][1][1]
        day_add = stock_added[i][1][2]
        
        calendar_stock_part_prod[order_add][t_day].append(stock_added[i][1])
        stock_part_edit[part_add][day_add+2]=float(stock_part_edit[part_add][day_add+2]) + qty_add
        for j_p in range(target_day_2-day_add-1):
            stock_part[part_add][day_add+1+j_p]+=qty_add
    
    return True
        
def temporary_check_part(item, qty, day):
    result=False
    
    stock_arr = []
    for i in range(len(fg_BOM[item])):
        stock_arr += [0]
        
    for i in range(len(fg_BOM[item])):
        if (len(temporary_part_list[fg_BOM[item][i][0]])==0):
            stock_arr[i]=0
        else:
            stock_arr[i]+=temporary_part_list[fg_BOM[item][i][0]][day+1]
    
    qty_ready = 2147483647
    
    for i in range(len(fg_BOM[item])):
        if (len(temporary_part_list[fg_BOM[item][i][0]])!=0):
            if (stock_arr[i]/fg_BOM[item][i][1] < qty_ready):
                qty_ready = int(stock_arr[i]/fg_BOM[item][i][1])
        
    if (qty_ready>=qty):
        result =True

    return result

def temporary_change_part(item, qty, day):
    global temporary_part_list
    
    for i in range(len(fg_BOM[item])):
        if (len(temporary_part_list[fg_BOM[item][i][0]])!=0):
            temporary_part_list[fg_BOM[item][i][0]][day+1]+=fg_BOM[item][i][1]*qty

def temporary_amount_ready(item, day):
    arr = []
    for i in range(2):
        arr += [0]
        
    stock_arr = []
    for i in range(len(fg_BOM[item])):
        stock_arr += [0]
        
    for i in range(len(fg_BOM[item])):
        if (len(temporary_part_list[fg_BOM[item][i][0]])>0):
            stock_arr[i]+=temporary_part_list[fg_BOM[item][i][0]][day+1]
        else:
            stock_arr[i]=0
            
    qty_ready = 2147483647
    
    for i in range(len(fg_BOM[item])):
        if (len(temporary_part_list[fg_BOM[item][i][0]])>0):
            if (stock_arr[i]/fg_BOM[item][i][1] < qty_ready):
                qty_ready = int(stock_arr[i]/fg_BOM[item][i][1])
                arr[0] = fg_BOM[item][i][0]
                arr[1] = qty_ready
            
    return arr

def temporary_make_fg_need_part(part):
    global temporary_fg_need_part
    rows_fg = np.where(BOM[:,1] == part)
    if(len(rows_fg[0])>0):
        for j in range(len(BOM[rows_fg])):
            rows_set = np.where(BOM_set[:,1] == BOM[rows_fg[0][j]][0])
            if (len(rows_set[0])>0):
                temporary_make_fg_need_part(BOM[rows_fg[0][j]][0])
            
            rows = np.where(stock_fg[:,0] == BOM[rows_fg[0][j]][0])
            if (len(rows[0])>0):
                temporary_fg_need_part[int(rows[0])] = 1
                
def make_table_calendar_time(table_calendar_p,table,fg,capacity):
    idx = -1
    for i in range(len(table_calendar_p)):
        if (table_calendar_p[i][2]==fg):
            idx = i
            break
        
    result = []
    result.append(table_calendar_p[idx][0])
    result.append(table_calendar_p[idx][1])
    
    if (table_calendar_p[idx][3]-capacity == 0):
        table_calendar_p.pop(idx)
    else:
        duration_cut = capacity*table[4]/set_up_table[table[0]][2]
        table_calendar_p[idx][1]-=duration_cut
        table_calendar_p[idx][3]-=capacity
        
        result.append(table_calendar_p[idx][1])
        result.append(table_calendar_p[idx][3])
        
    return result
        
def make_jig_schedule(jig_schedule_p,day,start_end):
    idx_jig = -1
    idx_order = -1
    found = False
    for i in range(len(jig_schedule_p)):
        for j in range(len(jig_schedule_p[i][day])):
            if ((jig_schedule_p[i][day][j][0]==start_end[0])&(jig_schedule_p[i][day][j][1]==start_end[1])):
                idx_jig = i
                idx_order = j
                found = True
                break
        if (found):
            break
           
    if (found==True):
        if (len(start_end)==2):
            jig_schedule_p[idx_jig][day].pop(idx_order)
        else:
            jig_schedule_p[idx_jig][day][idx_order][1]=start_end[2]
            jig_schedule_p[idx_jig][day][idx_order][3]=start_end[3]
        
def return_all_assy(z,i,day,j_before,j_after,k,m_2):
    global stock_part_edit
    global stock_part
    global calendar
    global fg_produced
    global fg_calendar
    global jig_qty
    
    j = j_before-j_after
    i_old = new_order[z][i][0]
    
    start_end_time = []
    
    if (j>0):
        load = round(j/order_capacity[i_old][k][3],3)
        if (len(table_calendar_box[order_capacity[i_old][k][0]][day])>1):
            load += set_up_time/(set_up_table[order_capacity[i_old][k][0]][1]*60)
        
        make_table_calendar(table_calendar_box[order_capacity[i_old][k][0]][day],order_capacity[i_old][k][2],table_calendar_box[order_capacity[i_old][k][0]][day][m_2][1]-j,m_2,new_order[z][i][8])
        
        start_end_time = make_table_calendar_time(table_calendar_time[order_capacity[i_old][k][0]][day],order_capacity[i_old][k],new_order[z][i][4],j)
        
        make_table_calendar_load_box(order_capacity[i_old][k][0],day,table_calendar_load_box,0-load)
        
        if (int(fg_need_part[new_order[z][i][8]][0])==1):
            return_stock_part(z,i,day)
    
            if (int(fg_need_part[new_order[z][i][8]][1])!=-1):
                if (day<target_day-1):
                    stock_part_edit[fg_need_part[new_order[z][i][8]][1]][day+2]-=j_before
                    for j_p in range(target_day_2-day-1):
                        stock_part[fg_need_part[new_order[z][i][8]][1]][day+1+j_p]-=j_before
                        
            if (int(fg_need_part[new_order[z][i][8]][0])==1):
                if (int(fg_need_part[new_order[z][i][8]][1])!=-1):
                    if (day<target_day-1):
                        stock_part_edit[fg_need_part[new_order[z][i][8]][1]][day+2]= int(stock_part_edit[fg_need_part[new_order[z][i][8]][1]][day+2])+j_after
                        for j_p in range(target_day_2-day-1):
                            stock_part[fg_need_part[new_order[z][i][8]][1]][day+1+j_p]+=j_after
                    
                change_stock_part(z,i,j_after,day)
            
    calendar[i_old][day]-=j
    fg_produced[i_old]-=j
    fg_calendar[new_order[z][i][8]][day]-=j
    
    if (temporary_fg_need_part[new_order[z][i][8]]==1):
        temporary_change_part(new_order[z][i][8],j,day)
    
    if (fg_jig[new_order[z][i][8]]>=0):
        jig_qty[fg_jig[new_order[z][i][8]]][day+1]+=load_jig
        make_jig_schedule(jig_schedule[fg_jig[new_order[z][i][8]]],day,start_end)
        
def is_intersect(start_jig, end_jig, start_other, end_other):
    if ((start_other>=start_jig)&(start_other<end_jig)):
        return True
    elif ((end_other>start_jig)&(end_other<=end_jig)):
        return True
    elif ((start_other<=start_jig)&(end_other>=end_jig)):
        return True
    
    return False

def check_jig(start_time_fix,end_time_fix,duration,day,z,idx,idx_table,booked_jig):
    idx_fg = new_order[z][idx][8]
    i_old = new_order[z][idx][0]
    
    saved_jig_schedule_temp = copy.deepcopy(jig_schedule[fg_jig[idx_fg]])
    
    if ((fg_jig[idx_fg]<0)|(table_list[idx_table][0][2]=='C')):
        return(start_time_fix,0)
        
    for i in range(len(booked_jig)):
        if (booked_jig[i][2]==day):
            arr = []
            arr.append(booked_jig[i][0])
            arr.append(booked_jig[i][1])
            jig_schedule[fg_jig[idx_fg]][booked_jig[i][3]][booked_jig[i][2]].append(arr)
    
    for i in range(len(jig_schedule[fg_jig[idx_fg]])):
        if(len(jig_schedule[fg_jig[idx_fg]][i][day])>1):
            jig_schedule[fg_jig[idx_fg]][i][day] = sorted(jig_schedule[fg_jig[idx_fg]][i][day], key=lambda x: x[0], reverse=False)
           
    start_time = []
    for i in range(len(jig_schedule[fg_jig[idx_fg]])):
        arr = []
        arr.append(start_time_fix)
        arr.append(False)
        start_time.append(arr)

    for i in range(len(jig_schedule[fg_jig[idx_fg]])):
        for j in range(len(jig_schedule[fg_jig[idx_fg]][i][day])):
            if (jig_schedule[fg_jig[idx_fg]][i][day][j][0]-start_time[i][0]>=duration):
                if (len(table_calendar_time[idx_table][day])==0):
                    start_time[i][0] = jig_schedule[fg_jig[idx_fg]][i][day][j][0]
                    start_time[i][1] = True
                else:
                    success = True
                    for k in range(len(table_calendar_time[idx_table][day])):
                        if (is_intersect(table_calendar_time[idx_table][day][k][0],table_calendar_time[idx_table][day][k][1],start_time[i][0],duration+start_time[i][0])):
                            success = False
                            if (jig_schedule[fg_jig[idx_fg]][i][day][j][0]-table_calendar_time[idx_table][day][k][1]>=duration):
                                start_time[i][0] = table_calendar_time[idx_table][day][k][1]
                                success = True
                            else:
                                break
                    if (success):
                        start_time[i][1] = True
                            
                if (start_time[i][1]):
                    break
            else:
                if (jig_schedule[fg_jig[idx_fg]][i][day][j][1]>start_time[i][0]):
                    start_time[i][0] = jig_schedule[fg_jig[idx_fg]][i][day][j][1]
                    start_time[i][1] = False
                
        if (start_time[i][1]==False):
            if (len(table_calendar_time[idx_table][day])==0):
                if (end_time_fix-start_time[i][0]>=duration):
                    start_time[i][1] = True
            else:
                success = True
                for k in range(len(table_calendar_time[idx_table][day])):
                    if (is_intersect(table_calendar_time[idx_table][day][k][0],table_calendar_time[idx_table][day][k][1],start_time[i][0],duration+start_time[i][0])):
                        success = False
                        if (end_time_fix-table_calendar_time[idx_table][day][k][1]>=duration):
                            start_time[i][0] = table_calendar_time[idx_table][day][k][1]
                            success = True
                        else:
                            break
                if (success):
                    if (end_time_fix-start_time[i][0]>=duration):
                        start_time[i][1] = True
    
    result = []
    result.append(0)
    result.append(-1)
    
    for i in range(len(start_time)):
        if (start_time[i][1]==True):
            if (result[1]==-1):
                result[0] = start_time[i][0]
                result[1] = i
            else:
                if (result[0]>start_time[i][0]):
                    result[0] = start_time[i][0]
                    result[1] = i
    
    jig_schedule[fg_jig[idx_fg]] = copy.deepcopy(saved_jig_schedule_temp)
    return(result)
                
def for_2(arr_table,idx_table,x,day,z,i,stable_can_pass):
    global order
    global table_cap
    global calendar
    global order_capacity
    global deviation_sum 
    global fail_of_lack_order
    global break_all_ops
    global start_day
    global workload
    global max_attempt
    global deviation_workload
    global fg_calendar
    global additional_fg
    global additional_table_fg
    global table_calendar_box
    global table_calendar_load_box
    global deviation_temp
    global OT_min
    global jig_qty
    global fg_need_OT
        
    i_old = new_order[z][i][0]
    j = x-calendar[i_old][day]
    
    if (len(arr_table)>0):
        k = arr_table[idx_table][0]
    else:
        k = 0
    
    set_up_time_temp = 0

    if (j>0):
        if (len(table_calendar_box[order_capacity[i_old][k][0]][day])>=1):
            set_up_time_temp = set_up_time/(set_up_table[order_capacity[i_old][k][0]][1]*60)
        
    max_qty_prod_2 = math.floor((wl[order_capacity[i_old][k][0]][day+1]-table_calendar_load_box[order_capacity[i_old][k][0]][day]-set_up_time_temp)*order_capacity[i_old][k][3]/box_fg[new_order[z][i][8]])*box_fg[new_order[z][i][8]]
    if (max_qty_prod_2<0):
        max_qty_prod_2 = 0
    
    if (len(arr_table)>0):
        if (max_qty_prod_2>arr_table[idx_table][1]):
            max_qty_prod_2=arr_table[idx_table][1]
    
    if (j>max_qty_prod_2):
        j = max_qty_prod_2
    
    max_qty_prod_2 = None
        
    if (break_all_ops==0):
        if (((j+calendar[i_old][day]<=x)&(idx_table<len(arr_table)-1))|((j+calendar[i_old][day]==x)&(idx_table==len(arr_table)-1))|(len(arr_table)==0)):
            fail_below_bot_percentage = 0
            load_jig = 0
            if (j>0):
                fail_below_bot_percentage = 1
                if(round_up(j/order_capacity[i_old][k][3],3)+table_calendar_load_box[order_capacity[i_old][k][0]][day]<=wl[order_capacity[i_old][k][0]][day+1]):
                    fail_below_bot_percentage = 0
                    load = round(j/order_capacity[i_old][k][3],3)
                    if (len(table_calendar_box[order_capacity[i_old][k][0]][day])>1):
                        load += set_up_time/(set_up_table[order_capacity[i_old][k][0]][1]*60)
                    load_jig = load
                    make_table_calendar_load_box(order_capacity[i_old][k][0],day,table_calendar_load_box,load)
                                
            if(fail_below_bot_percentage==0):
                m_2 = -1
                if (j>0):
                    if (m_2==-1):
                        m_2 = len(table_calendar_box[order_capacity[i_old][k][0]][day])
                        arr_temp = []
                        arr_temp.append(order_capacity[i_old][k][2])
                        arr_temp.append(j)
                        arr_temp.append(new_order[z][i][8])
                        table_calendar_box[order_capacity[i_old][k][0]][day].append(arr_temp)
                        
                        idx_input = 0
                        arr_temp = []
                        arr_temp.append(arr_table[idx_table][3][0])
                        set_up_time_temp = 0
                        if (len(table_calendar_box[order_capacity[i_old][k][0]][day])>1):
                            set_up_time_temp = set_up_time
                            for i_p in range (len(table_calendar_time[order_capacity[i_old][k][0]][day])):
                                if (arr_table[idx_table][3][0]>=table_calendar_time[order_capacity[i_old][k][0]][day][i_p][1]):
                                    idx_input=i_p+1
                                    if (table_calendar_time[order_capacity[i_old][k][0]][day][i_p][1]==arr_temp[0]):
                                        if (table_calendar_time[order_capacity[i_old][k][0]][day][i_p][2]==new_order[z][i][4]):
                                            set_up_time_temp = 0
                                        break

                        arr_temp.append(j*order_capacity[i_old][k][4]/set_up_table[order_capacity[i_old][k][0]][2]+set_up_time_temp+arr_table[idx_table][3][0])
                        arr_temp.append(new_order[z][i][4])
                        arr_temp.append(j)
                        table_calendar_time[order_capacity[i_old][k][0]][day] = table_calendar_time[order_capacity[i_old][k][0]][day][0:idx_input] + [arr_temp] + table_calendar_time[order_capacity[i_old][k][0]][day][idx_input:]
                    
                    calendar[i_old][day]+=j
                    fg_produced[i_old]+=j
                    fg_calendar[new_order[z][i][8]][day]+=j
                    
                    if ((fg_jig[new_order[z][i][8]]>=0)&(order_capacity[i_old][k][1][2]!='C')):
                        arr_temp = []
                        for i_p in range(len(table_calendar_time[order_capacity[i_old][k][0]][day])):
                            if (table_calendar_time[order_capacity[i_old][k][0]][day][i_p][0]==arr_table[idx_table][3][0]):
                                arr_temp.append(table_calendar_time[order_capacity[i_old][k][0]][day][i_p][0])
                                arr_temp.append(table_calendar_time[order_capacity[i_old][k][0]][day][i_p][1])
                                arr_temp.append(order_capacity[i_old][k][1])
                                arr_temp.append('day: '+str(day))
                                break
                        idx_jig = arr_table[idx_table][4]
                        idx_input = 0
                        
                        for i_p in range(len(jig_schedule[fg_jig[new_order[z][i][8]]][idx_jig][day])):
                            if (arr_temp[0]>=jig_schedule[fg_jig[new_order[z][i][8]]][idx_jig][day][i_p][0]):
                                idx_input=i_p+1
                                if (jig_schedule[fg_jig[new_order[z][i][8]]][idx_jig][day][i_p][1]==arr_temp[0]):
                                    break

                        jig_schedule[fg_jig[new_order[z][i][8]]][idx_jig][day] = jig_schedule[fg_jig[new_order[z][i][8]]][idx_jig][day][0:idx_input] + [arr_temp] + jig_schedule[fg_jig[new_order[z][i][8]]][idx_jig][day][idx_input:]
                        jig_qty[fg_jig[new_order[z][i][8]]][day+1]-=load_jig

                    if (temporary_fg_need_part[new_order[z][i][8]]==1):
                        if (stable_can_pass==False):
                            temporary_change_part(new_order[z][i][8],-j,day)
                        
                    if (int(fg_need_part[new_order[z][i][8]][0])==1):
                        if (int(fg_need_part[new_order[z][i][8]][1])!=-1):
                            if (day<target_day-1):
                                stock_part_edit[fg_need_part[new_order[z][i][8]][1]][day+2]= int(stock_part_edit[fg_need_part[new_order[z][i][8]][1]][day+2])+j
                                for j_p in range(target_day_2-day-1):
                                    stock_part[fg_need_part[new_order[z][i][8]][1]][day+1+j_p]+=j
                        
                        if (stable_can_pass==False):        
                            change_stock_part(z,i,j,day)
                
                if (x!=calendar[i_old][day]): #split order by K
                    fail_below_bot_percentage = None
                    if (idx_table+1<len(arr_table)):
                        for_2(arr_table,idx_table+1,x,day,z,i,stable_can_pass)
                if (x==calendar[i_old][day]):
                    if ((new_order[z][i][6]-fg_produced[i_old]==0)|((fg_need_OT[i_old][0]>0)|(fg_need_OT[i_old][1]>0)|(fg_need_OT[i_old][2]>0))|(fg_lack_of_part[i_old]>0)):
                        if (i==len(new_order[z])-1):
                            if (fail_below_bot_percentage==0):
                                global attempt
                                if (attempt==2147483647):
                                    attempt = 0
                                    
                                attempt += 1
                                
                                print ('attempt: ', attempt)
                                        
                                if(operation_mode==1):
                                    break_all_ops = 1
                                if (attempt>max_attempt-1):
                                    break_all_ops = 1
                                
                                save_data()
                                    
                        if (i<len(new_order[z])-1) :
                            fail_below_bot_percentage = None
                            make_schedule(start_day,z, i+1)
                    else:
                        fail_below_bot_percentage = None
                        nextday = day+1
                        if (nextday<=target_day-1):
                            while (workload[nextday]==-1):
                                nextday+=1
                            if (nextday<=target_day-1):
                                make_schedule(nextday,z, i)
        
def make_schedule(day,z, i):
    global order
    global table_cap
    global calendar
    global order_capacity
    global deviation_sum 
    global fail_of_lack_order
    global break_all_ops
    global start_day
    global workload
    global wl
    global fg_need_part
    global need_OT
    global need_part
    global fg_lack_of_part
    global arr_need_part
    global arr_need_OT
    
    i_old = new_order[z][i][0]
    j=int(new_order[z][i][6])-fg_produced[i_old]
    
    max_qty_prod = 0
        
    no_prod_reason = ''
    
    jig_avail = len(order_capacity[i_old])  
    if (fg_jig[new_order[z][i][8]]>0):
        jig_avail = jig_qty[fg_jig[new_order[z][i][8]]][day+1]
    
    arr_table = []
        
    for i_p in range(len(order_capacity[i_old])):
        set_up_time_temp = 0
        if (len(table_calendar_box[order_capacity[i_old][i_p][0]][day])>0):
            found = False
            for j_p in range(len(table_calendar_box[order_capacity[i_old][i_p][0]][day])):
                if (table_calendar_box[order_capacity[i_old][i_p][0]][day][j_p][0]==new_order[z][i][4]):
                    found = True
            if (found==False):
                set_up_time_temp = set_up_time/(set_up_table[order_capacity[i_old][i_p][0]][1]*60)
        
        load_add = math.floor(((wl[order_capacity[i_old][i_p][0]][day+1]-table_calendar_load_box[order_capacity[i_old][i_p][0]][day]-set_up_time_temp)*order_capacity[i_old][i_p][3])/box_fg[new_order[z][i][8]])*box_fg[new_order[z][i][8]]
        
        if (load_add<0):
            load_add = 0
        
        if (load_add>0):
            temp = load_add/order_capacity[i_old][i_p][3]
            
            if (is_stable[i_old]==1):
                for j_p in range(len(stable_qty_prod)):
                    if (stable_qty_prod[j_p][0]==new_order[z][i][4]):
                        load_add = stable_qty_prod[j_p][day+1]
                        break
                
            arr = []
            arr.append(i_p)
            arr.append(load_add)
            arr.append(load_add/order_capacity[i_old][i_p][3])
            arr_table.append(arr)
            
    arr_table = sorted(arr_table, key=lambda x: x[1], reverse=True)
        
    booked_jig = []
    
    for i_q in range(len(arr_table)):
        idx_jig = -1
        booked_jig_idx = -1
        i_p = arr_table[i_q][0]
        start_time = 8*3600 #jam 8 dalam satuan second, akan berubah mengikuti jadwal terakhir
        start_time_fix = 8*3600 #jam 8 dalam satuan second tidak pernah berubah
        work_dur = 0
        for j_p in range(len(set_up_table)):
            if (order_capacity[i_old][i_p][1]==set_up_table[j_p,0]):
                work_dur = set_up_table[j_p,1]*60/set_up_table[j_p,2]
                break
        end_time_fix = work_dur+start_time_fix
        
        set_up_time_temp_2 = None
        
        arr_time = []
        arr_time.append([]) #start
        arr_time.append([]) #end
        arr_time.append(-1) #max_capacity
            
        if (len(table_calendar_time[order_capacity[i_old][i_p][0]][day])==0):
            set_up_time_temp_2 = 0
            max_capacity_temp = math.floor(((end_time_fix-start_time_fix)*wl[order_capacity[i_old][i_p][0]][day+1]-set_up_time_temp_2)/(order_capacity[i_old][i_p][4]/set_up_table[order_capacity[i_old][i_p][0]][2]*box_fg[new_order[z][i][8]]))*box_fg[new_order[z][i][8]]
            duration = max_capacity_temp*order_capacity[i_old][i_p][4]/set_up_table[order_capacity[i_old][i_p][0]][2]+set_up_time_temp_2
            start_time_jig = check_jig(start_time,(end_time_fix-start_time_fix)*wl[order_capacity[i_old][i_p][0]][day+1]+start_time_fix,duration,day,z,i,order_capacity[i_old][i_p][0],booked_jig)

            if (start_time_jig[1]!=-1):
                arr_time[0]=start_time_jig[0] 
                arr_time[1]=duration+start_time_jig[0]
                arr_time[2]=max_capacity_temp
                
                if ((fg_jig[new_order[z][i][8]]>0)&(order_capacity[i_old][i_p][1][2]!='C')):
                    if (booked_jig_idx!=-1):
                        booked_jig.pop(booked_jig_idx)
                    booked_jig_idx = len(booked_jig)
                    
                    idx_jig = start_time_jig[1]
                    arr_booked_jig = []
                    arr_booked_jig.append(start_time_jig[0])
                    arr_booked_jig.append(duration+start_time_jig[0])
                    arr_booked_jig.append(day)
                    arr_booked_jig.append(start_time_jig[1])
                    booked_jig.append(arr_booked_jig)
            else:
                if (max_capacity_temp>0):
                    no_prod_reason = 'INSUFFICIENT JIG'
                arr_time[2]=0
        else:
            for j_p in range(len(table_calendar_time[order_capacity[i_old][i_p][0]][day])):
                if (set_up_time_temp_2==None):
                    set_up_time_temp_2 = set_up_time
                if (table_calendar_time[order_capacity[i_old][i_p][0]][day][j_p][0]-start_time>=order_capacity[i_old][i_p][4]/set_up_table[order_capacity[i_old][i_p][0]][2]*box_fg[new_order[z][i][8]]+set_up_time_temp_2):
                    max_capacity_temp = math.floor((table_calendar_time[order_capacity[i_old][i_p][0]][day][j_p][0]-start_time-set_up_time_temp_2)/(order_capacity[i_old][i_p][4]/set_up_table[order_capacity[i_old][i_p][0]][2]*box_fg[new_order[z][i][8]]))*box_fg[new_order[z][i][8]]
                    duration = max_capacity_temp*order_capacity[i_old][i_p][4]/set_up_table[order_capacity[i_old][i_p][0]][2]+set_up_time_temp_2
                    start_time_jig = check_jig(start_time,(end_time_fix-start_time_fix)*wl[order_capacity[i_old][i_p][0]][day+1]+start_time_fix,duration,day,z,i,order_capacity[i_old][i_p][0],booked_jig)
                    if (start_time_jig[1]!=-1):
                        if ((max_capacity_temp>arr_time[2])&(max_capacity_temp>0)):
                            arr_time[0]=start_time_jig[0]
                            arr_time[1]=duration+start_time_jig[0]
                            arr_time[2]=max_capacity_temp
                            start_time = table_calendar_time[order_capacity[i_old][i_p][0]][day][j_p][1]
                            
                            if ((fg_jig[new_order[z][i][8]]>0)&(order_capacity[i_old][i_p][1][2]!='C')):
                                if (booked_jig_idx!=-1):
                                    booked_jig.pop(booked_jig_idx)
                                
                                booked_jig_idx = len(booked_jig)
                                idx_jig = start_time_jig[1]
                                arr_booked_jig = []
                                arr_booked_jig.append(start_time_jig[0])
                                arr_booked_jig.append(duration+start_time_jig[0])
                                arr_booked_jig.append(day)
                                arr_booked_jig.append(start_time_jig[1])
                                booked_jig.append(arr_booked_jig)
                    else:
                        if (max_capacity_temp>0):
                            no_prod_reason = 'INSUFFICIENT JIG'
                        arr_time[2]=0
                else:
                    start_time = table_calendar_time[order_capacity[i_old][i_p][0]][day][j_p][1]
                    if (table_calendar_time[order_capacity[i_old][i_p][0]][day][j_p][2]==new_order[z][i][4]):
                        set_up_time_temp_2 = 0
                    else:
                        set_up_time_temp_2 = set_up_time
                        
            max_capacity_temp= math.floor(((end_time_fix-start_time_fix)*wl[order_capacity[i_old][i_p][0]][day+1]+start_time_fix-start_time-set_up_time_temp_2)/(order_capacity[i_old][i_p][4]/set_up_table[order_capacity[i_old][i_p][0]][2]*box_fg[new_order[z][i][8]]))*box_fg[new_order[z][i][8]]
            if ((arr_time[2]==-1)|(max_capacity_temp>arr_time[2])):
                if (max_capacity_temp<0):
                    max_capacity_temp = 0
                duration = max_capacity_temp*order_capacity[i_old][i_p][4]/set_up_table[order_capacity[i_old][i_p][0]][2]+set_up_time_temp_2
                start_time_jig = check_jig(start_time,(end_time_fix-start_time_fix)*wl[order_capacity[i_old][i_p][0]][day+1]+start_time_fix,duration,day,z,i,order_capacity[i_old][i_p][0],booked_jig)
                if (start_time_jig[1]!=-1):
                    arr_time[0]=start_time_jig[0]
                    if (max_capacity_temp>0):
                        arr_time[1]=duration+start_time_jig[0]
                        arr_time[2]=max_capacity_temp
                        
                        if ((fg_jig[new_order[z][i][8]]>0)&(order_capacity[i_old][i_p][1][2]!='C')):
                            if (booked_jig_idx!=-1):
                                booked_jig.pop(booked_jig_idx)
                            
                            booked_jig_idx = len(booked_jig)
                            idx_jig = start_time_jig[1]
                            arr_booked_jig = []
                            arr_booked_jig.append(start_time_jig[0])
                            arr_booked_jig.append(duration+start_time_jig[0])
                            arr_booked_jig.append(day)
                            arr_booked_jig.append(start_time_jig[1])
                            booked_jig.append(arr_booked_jig)
                    else:
                        arr_time[1]=start_time
                        arr_time[2]=0
                else:
                    if (max_capacity_temp>0):
                        no_prod_reason = 'INSUFFICIENT JIG'
                    arr_time[2]=0
        
        if (arr_table[i_q][1]<arr_time[2]):
            duration = arr_table[i_q][1]*order_capacity[i_old][i_p][4]/set_up_table[order_capacity[i_old][i_p][0]][2]+set_up_time_temp_2
            arr_time[1] = arr_time[0]+duration
            arr_time[2] = arr_table[i_q][1]
            
        arr_table[i_q].append(arr_time)
        arr_table[i_q].append(idx_jig)
            
        if (arr_time[2]==0):
            arr_table[i_q][1]=0
        else:
            arr_table[i_q][1]=arr_time[2]
        
    i_q = 0
    while i_q < len(arr_table):
        if (arr_table[i_q][1]==0):
            arr_table.pop(i_q)
        else:
            i_q+=1
        
    for i_p in range(len(arr_table)):
        max_qty_prod += arr_table[i_p][1]
        
    if ((is_set[i_old]==1) & (day == target_day-1) & (is_stable[i_old]==0)):
        max_qty_prod = 0
    
    stable_can_pass = False
    if (is_stable[i_old]==1):
        for j_p in range(len(stable_qty_prod)):
            if (stable_qty_prod[j_p][0]==new_order[z][i][4]):
                if (stable_qty_prod[j_p][len(stable_qty_prod[j_p])-1]==day):
                    stable_can_pass = True
                break

    if (check_stock_part(new_order[z][i][8],j,day)==False):
        if (stable_can_pass==False):
            no_part = amount_ready(new_order[z][i][8],day)
            if (day == target_day - 1):
                row_part = np.where(stock_part_edit_2[:,0] == stock_part_edit[no_part[0]][0])
                if (len(row_part[0])>0):
                    print ('\nNOT ENOUGH IMPORTED PART | i:',i,'\tno part: ',stock_part_edit[no_part[0]][0],'\tqty: ',no_part[1],'/',j,'\titem: ',new_order[z][i][4])
                    need_part = 1
                    found = 0
                    for q in range(len(arr_need_part)):
                        if (arr_need_part[q][0]==stock_part_edit[no_part[0]][0]):
                            if (arr_need_part[q][2]==new_order[z][i][5]):
                                found = 1
                                arr_need_part[q][1]+=j-no_part[1]
                                break
                    if (found==0):
                        arr = []
                        arr.append(stock_part_edit[no_part[0]][0])
                        arr.append(j-no_part[1])
                        arr.append(new_order[z][i][5])
                        arr_need_part.append(arr)
                    no_prod_reason = 'INSUFFICIENT IMPORTED PART'
                else:
                    print ('\nNOT ENOUGH SET PART | i:',i,'\tno part: ',stock_part_edit[no_part[0]][0],'\tqty: ',no_part[1],'/',j,'\titem: ',new_order[z][i][4])
                    idx_q = -1
                    for q in range(len(new_order[z])):
                        if (new_order[z][q][4]==stock_part_edit[no_part[0]][0]):
                            idx_q = new_order[z][q][0]
                            break
                    need_OT = 1
                    if (no_prod_reason == ''):
                        no_prod_reason = 'INSUFFICIENT SET PART'
                    
                fg_lack_of_part[i_old]+=1
            if (max_qty_prod>round_down_box(no_part[1],box_fg[new_order[z][i][8]])):
                max_qty_prod=round_down_box(no_part[1],box_fg[new_order[z][i][8]])
    
    if (temporary_check_part(new_order[z][i][8],j,day)==False):
        if (stable_can_pass==False):
            no_part = temporary_amount_ready(new_order[z][i][8],day)
            if (day == target_day - 1):
                print ('\nNOT ENOUGH PART FROM PRODUCTION: ',new_order[z][i][4])
                need_part = 1
                found = 0
                for q in range(len(arr_need_part)):
                    if (arr_need_part[q][0]==stock_part_edit[no_part[0]][0]):
                        if (arr_need_part[q][2]==new_order[z][i][5]):
                            found = 1
                            arr_need_part[q][1]+=j-no_part[1]
                            break
                if (found==0):
                    arr = []
                    arr.append(stock_part_edit[no_part[0]][0])
                    arr.append(j-no_part[1])
                    arr.append(new_order[z][i][5])
                    arr_need_part.append(arr)
                fg_lack_of_part[i_old]+=1
                if (no_prod_reason!='INSUFFICIENT IMPORTED PART'):
                    no_prod_reason = 'INSUFFICIENT PART FROM PRODUCTION'
            
            if (max_qty_prod>round_down_box(no_part[1],box_fg[new_order[z][i][8]])):
                max_qty_prod=round_down_box(no_part[1],box_fg[new_order[z][i][8]])
        
    if (j>max_qty_prod):
        if (attempt==0):
            if (day==target_day-1):
                if ((fg_jig[new_order[z][i][8]]>=0)&(no_prod_reason == '')):
                    load_temp = j/order_capacity[i_old][0][3]
                    avail_jig_temp = 0
                    for k in range(len(jig_qty[fg_jig[new_order[z][i][8]]])-1):
                        avail_jig_temp+=jig_qty[fg_jig[new_order[z][i][8]]][k+1]
                    if (avail_jig_temp<load_temp):
                        no_prod_reason = 'INSUFFICIENT JIG'
                print ('order_ID: ',new_order[z][i][0],'\tFG: ',new_order[z][i][4],'\tqty: ',j,'\tmax: ',max_qty_prod, ' | target: ',new_order[z][i][6],' - produced: ',fg_produced[i_old])
                if ((no_prod_reason == 'INSUFFICIENT PART FROM PRODUCTION')|(no_prod_reason =='INSUFFICIENT IMPORTED PART')):
                    fg_need_OT[i_old][0]+=(j-max_qty_prod)
                elif (no_prod_reason == 'INSUFFICIENT JIG'):
                    fg_need_OT[i_old][1]+=(j-max_qty_prod) 
                else:
                    fg_need_OT[i_old][2]+=(j-max_qty_prod)
                need_OT = 1
                
                if (no_prod_reason == ''):
                    no_prod_reason = 'INSUFFICIENT TABLE'
                
                rows_1 = np.where(BOM_set[:,0] == new_order[z][i][4])
                if ((len(rows_1[0])>0)&(is_stable[i_old]==0)):
                    #RETURN ALL SET PART PROD
                    for j_p in range(len(rows_1[0])):
                        done_this_part = 0                        
                        rows_2 = np.where((BOM[:,0] == new_order[z][i][4])&(BOM[:,1] == BOM_set[rows_1[0][j_p]][1]))
                        qty_mult = BOM[rows_2][0][2]
                        for i_p in reversed(range(i)):
                            if ((new_order[z][i][1]==new_order[z][i_p][1])&(BOM_set[rows_1[0][j_p]][1]==new_order[z][i_p][4])):
                                remain_qty = fg_produced[new_order[z][i_p][0]]-(fg_produced[new_order[z][i][0]]+max_qty_prod)*qty_mult
                                if (remain_qty>0):
                                    for day_p in reversed(range(target_day)):
                                        if (calendar[new_order[z][i_p][0]][day_p]>0):
                                            for k_p in range(len(order_capacity[new_order[z][i_p][0]])):
                                                for m_p in range(len(table_calendar_box[order_capacity[new_order[z][i_p][0]][k_p][0]][day_p])):
                                                    if (table_calendar_box[order_capacity[new_order[z][i_p][0]][k_p][0]][day_p][m_p][2]==new_order[z][i_p][8]):
                                                        j_before = table_calendar_box[order_capacity[new_order[z][i_p][0]][k_p][0]][day_p][m_p][1]
                                                        print('>>>',new_order[z][i_p][4],' day: ',day_p,' table: ',k_p,' qty: ',remain_qty,'-',j_before)
                                                        if (remain_qty<=j_before):
                                                            return_all_assy(z,i_p,day_p,j_before,j_before-remain_qty,k_p,m_p)
                                                            done_this_part = 1
                                                        else:
                                                            remain_qty-=j_before
                                                            return_all_assy(z,i_p,day_p,j_before,0,k_p,m_p)
                                                        break
                                                if (done_this_part==1):
                                                    break
                                        if (done_this_part==1):
                                            break
                                    break    
                    
                found = 0
                for q in range(len(arr_need_OT)):
                    if (arr_need_OT[q][0]==new_order[z][i][4]):
                        if (arr_need_OT[q][2]==new_order[z][i][5]):
                            if (no_prod_reason == arr_need_OT[q][3]):
                                found = 1
                                arr_need_OT[q][1]+=j-max_qty_prod
                                break
                if (found==0):
                    arr = []
                    arr.append(new_order[z][i][4])
                    arr.append(j-max_qty_prod)
                    arr.append(new_order[z][i][5])
                    arr.append(no_prod_reason)
                    arr_need_OT.append(arr)
                    
        j=max_qty_prod
        
    max_qty_prod = None
    
    while j>=0:
        if (break_all_ops==0):
            next_idx = 1
            if (j==0): 
                nextday = day+1
                if (nextday<=target_day-1):
                    while (workload[nextday]==-1):
                        nextday+=1
                    
                    if (nextday<=target_day-1):
                        next_idx = 0
                        make_schedule(nextday,z, i)
                    else:
                        next_idx = 1
            
            if (next_idx==1):
                if (len(arr_table)>=0):
                    if ((check_stock_part(new_order[z][i][8],j,day))|(stable_can_pass==True)):
                        if ((temporary_check_part(new_order[z][i][8],j,day))|(stable_can_pass==True)):
                            if (((j+fg_produced[new_order[z][i][0]]<=new_order[z][i][6]) & (day<target_day-1)) | ((j+fg_produced[new_order[z][i][0]]==new_order[z][i][6]) & (day==target_day-1)) | ((fg_need_OT[i_old][0]>0)|(fg_need_OT[i_old][1]>0)|(fg_need_OT[i_old][2]>0)) | (fg_lack_of_part[new_order[z][i][0]]>0)):
                                for_2(arr_table,0,j,day,z,i,stable_can_pass)
                        
        elif (break_all_ops==1):
            j=0
        
        j = while_subtractor(j,new_order[z][i][6],box_fg[new_order[z][i][8]])

print('Preparing (0%)...')
print('')
order1 = pd.read_excel ('input_file.xlsx',sheet_name = 'Order')

table_cap1 = pd.read_excel ('input_file.xlsx',sheet_name = 'Table_Capacity')
set_up_table = pd.read_excel ('input_file.xlsx',sheet_name = 'Table_Capacity_2').to_numpy()
order1 = order1.sort_values(['Delivery Time', 'EXPORT/LOCAL'], ascending=[True, True])
order = order1.to_numpy()
table_cap1 = table_cap1[table_cap1['Table'].notna()]
table_cap = table_cap1.to_numpy()
stock_fg = pd.read_excel ('input_file.xlsx',sheet_name = 'Stock_FG').to_numpy()
stock_part_edit = pd.read_excel ('input_file.xlsx',sheet_name = 'Stock_Part').to_numpy()
stock_part_edit_2 = pd.read_excel ('input_file.xlsx',sheet_name = 'Stock_Part').to_numpy()
BOM = pd.read_excel ('input_file.xlsx',sheet_name = 'BOM').to_numpy()
BOM_set = pd.read_excel ('input_file.xlsx',sheet_name = 'BOM_SET').to_numpy()
box = pd.read_excel ('input_file.xlsx',sheet_name = 'Box').to_numpy()
wl = pd.read_excel ('input_file.xlsx',sheet_name = 'Over_Time').to_numpy()
produced_item = pd.read_excel ('input_file.xlsx',sheet_name = 'Produced_Item').to_numpy()
routing = pd.read_excel ('input_file.xlsx',sheet_name = 'Routing').to_numpy()
production_table_cap = pd.read_excel ('input_file.xlsx',sheet_name = 'Production_Table_Capacity').to_numpy()
fg_jig1 = pd.read_excel ('input_file.xlsx',sheet_name = 'FG_Jig').to_numpy()
jig_qty1 = pd.read_excel ('input_file.xlsx',sheet_name = 'Jig_Qty').to_numpy()
cogm = pd.read_excel ('input_file.xlsx',sheet_name = 'COGM').to_numpy()
stable_assy = pd.read_excel ('input_file.xlsx',sheet_name = 'Stable_Assy').to_numpy()
production_limit = pd.read_excel ('input_file.xlsx',sheet_name = 'Production_Limit').to_numpy()

print('Preparing (10%)...')
print('')

for i in range(len(stock_fg)):
    if (stock_fg[i,1]<0):
        rows = np.where(order[:,4] == stock_fg[i,0])
        if (len(rows[0])==0):
            arr_temp = []
            arr_temp.append(float("NaN"))
            arr_temp.append(9000000000+i)
            arr_temp.append(order[0,2])
            arr_temp.append(stock_fg[i,1]*-1)
            arr_temp.append(stock_fg[i,0])
            arr_temp.append('EXPORT-01')
            arr_temp.append(stock_fg[i,1]*-1)
            box_size = np.where(box[:,0] == stock_fg[i,0])
            if (len(box_size[0])==1):
                arr_temp.append(box[box_size[0][0]][1])
            else:
                arr_temp.append(1)
            arr_temp.append(float("NaN"))
            order = np.vstack((order,arr_temp))

global order_len
order_len = len(order)

#bikin unique table list
for i in range(len(table_cap)):
    found = 0
    for j in range(len(table_list)):
        if (table_list[j][0]==table_cap[i][1]):
            found=1
            table_cap[i][0]=j
            break
    if (found==0):
        arr = []
        arr.append(table_cap[i][1])
        arr.append(0)
        table_list.append(arr)
        table_cap[i][0]=len(table_list)-1

for i in range(len(table_list)):
    col = []
    for j in range(target_day_2):
        col2 = []
        col.append(col2)
    table_calendar_box.append(col)
    
for i in range(len(table_list)):
    col = []
    for j in range(target_day_2):
        col2 = []
        col.append(col2)
    table_calendar_time.append(col)
    
for i in range(len(table_list)):
    col = []
    for j in range(target_day):
        col += [0]
    table_calendar_load_box.append(col)
                
#DEDUCT SET ITEMS PRODUCED
for i in range(len(produced_item)):
    rows = np.where(BOM_set[:,0] == produced_item[i,0])
    if (len(rows[0])>0):
        for j in range(len(rows[0])):
            for k in range(len(produced_item)):
                if (BOM_set[rows[0][j]][1]==produced_item[k,0]):
                    qty = 0
                    rows_qty = np.where(BOM[:,0] == produced_item[i,0])
                    for l in range(len(rows_qty[0])):
                        if (BOM[rows_qty[0][l]][1]==produced_item[k,0]):
                            qty = BOM[rows_qty[0][l]][2]
                            break
                    produced_item[k,1]-=(qty*produced_item[i,1])
                    break

#DEDUCT FG WITH PRODUCED ITEMS AND ADD STOCK PART WITH PRODUCED ITEMS
for i in range(len(produced_item)):
    found = 0
    for j in range(len(stock_fg)):
        if (produced_item[i][0] == stock_fg[j][0]):
            found = 1
            stock_fg[j][1]+=produced_item[i][1]
        if (found==1):
            break
    if (found==0):
        rows = np.where(BOM_set[:,1] == produced_item[i,0])
        if (len(rows[0])>0):
            found_2 = 0
            for j in range(len(stock_part_edit)):
                if (stock_part_edit[j,0] == produced_item[i,0]):
                    stock_part_edit[j,1]+=produced_item[i,1]
                    found_2 = 1
                    break
            if (found_2==0):
                arr = []
                for j in range(15):
                    arr += [0]
                arr[0] = produced_item[i,0]
                arr[1] = produced_item[i,1]
                for j in range(13):
                    arr[2+j] = int(0)
                stock_part_edit = np.vstack((stock_part_edit,arr))
            
        stock_fg = np.vstack((stock_fg,produced_item[i]))

order_not_in_bom = []
#delete order that not included in BOM (avoid part item)
for i in range(order_len):
    rows = np.where(BOM[:,0] == order[i,4])
    if (len(rows[0])==0):
        rows_routing = np.where(routing[:,0] == order[i,4])
        if (len(rows_routing[0])==0):
            order[i,6]=0
            found = 0
            for j in range(len(order_not_in_bom)):
                if (order_not_in_bom[j]==order[i,4]):
                    found = 1
                    break
            if (found == 0):
                order_not_in_bom.append(order[i,4])
        else:
            found = 0
            for j in range(len(arr_production_item)):
                if (arr_production_item[j][0]==order[i,4]):
                    found = 1
                    arr_production_item[j][1]+=order[i,6]
                    break
            if (found==0):
                arr = []
                arr.append(order[i,4])
                arr.append(order[i,6])
                arr_production_item.append(arr)
            order[i,6]=0

if (len(order_not_in_bom)>0):
    print('==============\nWARNING!!! WE DELETED THIS ORDER BECAUSE WE CAN''T FIND THE BOM OF IT\n')
    for i in range(len(order_not_in_bom)):
        print (order_not_in_bom[i])
    print ('\n==============\n')
    
order = order[order[:, 6] != 0]
order_len = len(order)
#create order row 6 for addition or subtraction
for i in range(order_len):
    order[i,6] = order[i,3]

#merge orders by FG & Ex/Loc
for i in range(order_len):
    for j in range(i):
        if (order[i,4] == order[j,4]):
            if (order[i,5]==order[j,5]):
                order[j,6] += order[i,6]
                order[i,6] = 0
                break
        
#add fg index in order array and add a new row for stock_fg if the fg is not available in stock_fg
for i in range(order_len):
    rows = np.where(stock_fg[:,0] == order[i,4])
    if (len(rows[0])>0):
        order[i,8] = int(rows[0])
    else:
        rows2 = np.where(stock_part_edit[:,0] == order[i,4])
        arr_temp = []
        arr_temp.append(order[i,4])
        if (len(rows2[0])>0):
            arr_temp.append(int(stock_part_edit[rows2[0][0]][1]))
        else:
            arr_temp.append(0)
        stock_fg = np.vstack((stock_fg,arr_temp))
        order[i,8] = len(stock_fg)-1

order = order[order[:, 6] != 0]
order_len = len(order)

#reset order additional qty from negative stock_fg 
for i in range(len(order)):
    if (int(order[i,1])>=9000000000):
        order[i,3] = 0
        order[i,6] = 0

#create draft order and fg_stock
draft_order = copy.deepcopy(order)
draft_stock_fg = []

#DEDUCT WITH STOCK FG
for k in range(len(arr_ex_loc)):
    for i in range(order_len):
        arr = []
        if (order[i,5]==arr_ex_loc[k]):
            rows = np.where(stock_fg[:,0] == order[i,4])
            if (len(rows[0])==1):
                if (order[i,6]>int(stock_fg[rows,1])):
                    found=0
                    for j in range(len(draft_stock_fg)):
                        if ((draft_stock_fg[j][0]==order[i,4])&(draft_stock_fg[j][1]==order[i,5])):
                            found=1
                            draft_stock_fg[j][2]+=int(stock_fg[rows,1])
                    if (found==0):
                        arr.append(order[i,4])
                        arr.append(order[i,5])
                        arr.append(int(stock_fg[rows,1]))
                        draft_stock_fg.append(arr)
                    
                    order[i,6]-=int(stock_fg[rows,1])
                    change_stock_fg(order[i,4],0)
                else:
                    found=0
                    for j in range(len(draft_stock_fg)):
                        if ((draft_stock_fg[j][0]==order[i,4])&(draft_stock_fg[j][1]==order[i,5])):
                            found=1
                            draft_stock_fg[j][2]+=int(order[i,6])
                    if (found==0):
                        arr.append(order[i,4])
                        arr.append(order[i,5])
                        arr.append(order[i,6])
                        draft_stock_fg.append(arr)
                        
                    change_stock_fg(order[i,4],0-order[i,6])
                    order[i,6] = int(0)
            elif (len(rows[0])>1):
                print('ERROR STOCK FG DUPLICATED FOR ITEM: ',order[i,4])
                operation_mode = 0

print('Preparing (20%)...')
print('')

if (len(set_up_table)!=len(wl)):
    print('ERROR OVER TIME AND TABLE CAPACITY 2 DO NOT MATCH! \n')
    operation_mode = 0
    
order = order[order[:, 6] != 0]
order_len = len(order)

draft_order_no_box = copy.deepcopy(order)

arr_temp_box = []
#round up order qty to box size
for i in range (order_len):
    for k in range (len(arr_ex_loc)):
        if (order[i,5]==arr_ex_loc[k]):
            rows = np.where(box[:,0] == order[i,4])
            if(len(rows[0])==1):
                index_temp_box = -1
                for j in range(len(arr_temp_box)):
                    if (arr_temp_box[j][0]==order[i,4]):
                        index_temp_box = j
                        if (order[i,6]>=arr_temp_box[j][1]):
                            order[i,6]-=arr_temp_box[j][1]
                            arr_temp_box[j][1] = 0
                        else:
                            arr_temp_box[j][1]-=order[i,6]
                            order[i,6] = 0
                        break
                qty_new = math.ceil(order[i,6]/box[rows][0][1])*box[rows][0][1]
                add_qty = qty_new-order[i,6]
                order[i,6] = qty_new
                
                if (add_qty>0):
                    if (index_temp_box>-1):
                        arr_temp_box[index_temp_box][1]+=add_qty
                    else:
                        arr_temp = []
                        arr_temp.append(order[i,4])
                        arr_temp.append(add_qty)
                        arr_temp_box.append(arr_temp)
            elif (len(rows[0])>1):
                print('ERROR BOX SIZE DUPLICATED FOR ITEM: ',order[i,4])
                operation_mode = 0

#recreate stable assy
stable_assy_unique = []
for i in range(len(stable_assy)):
    found = 0
    for j in range(len(stable_assy_unique)):
        if (stable_assy_unique[j][0]==stable_assy[i][0]):
            found=1
            arr = []
            arr.append(stable_assy[i][1])
            arr.append(stable_assy[i][2])
            stable_assy_unique[j][1].append(arr)
            arr = []
            arr.append(stable_assy[i][1])
            arr.append(stable_assy[i][3])
            stable_assy_unique[j][2].append(arr)
            stable_assy_unique[j][3]+=stable_assy[i][2]
            stable_assy_unique[j][4]+=stable_assy[i][3]
            break
    if (found==0):
        arr = []
        arr.append(stable_assy[i][0])
        arr3 = []
        arr2 = []
        arr2.append(stable_assy[i][1])
        arr2.append(stable_assy[i][2])
        arr3.append(arr2)
        arr.append(arr3)
        arr3 = []
        arr2 = []
        arr2.append(stable_assy[i][1])
        arr2.append(stable_assy[i][3])
        arr3.append(arr2)
        arr.append(arr3)
        arr.append(stable_assy[i][2])
        arr.append(stable_assy[i][3])
        stable_assy_unique.append(arr)
    
#add set to stable assy
i = 0
while i <= len(stable_assy_unique)-1:
    rows_set = np.where(BOM_set[:,0] == stable_assy_unique[i][0])
    for j in range(len(rows_set[0])):
        rows_BOM = np.where((BOM[:,0] == stable_assy_unique[i][0])&(BOM[:,1] == BOM_set[rows_set[0][j]][1]))
        
        arr = []
        arr.append(BOM[rows_BOM[0][0]][1])
        arr3 = []
        for k in range(len(stable_assy_unique[i][1])):
            arr2 = []
            arr2.append(stable_assy_unique[i][1][k][0])
            arr2.append(stable_assy_unique[i][1][k][1]*BOM[rows_BOM[0][0]][2])
            arr3.append(arr2)
        arr.append(arr3)
        arr3 = []
        for k in range(len(stable_assy_unique[i][2])):
            arr2 = []
            arr2.append(stable_assy_unique[i][2][k][0])
            arr2.append(stable_assy_unique[i][2][k][1]*BOM[rows_BOM[0][0]][2])
            arr3.append(arr2)
        arr.append(arr3)
        arr.append(stable_assy_unique[i][3]*BOM[rows_BOM[0][0]][2])
        arr.append(stable_assy_unique[i][4]*BOM[rows_BOM[0][0]][2])
        stable_assy_unique.append(arr)
    i+=1
    
#create qty production for stable assy
satsun = []    
if (Monday<=2):
    satsun.append(Monday + 4)
    satsun.append(Monday + 11)
else:
    satsun.append(Monday - 3)
    satsun.append(Monday + 4)
    
if (Monday<=1):
    satsun.append(Monday + 5)
    satsun.append(Monday + 12)
else:
    satsun.append(Monday - 2)
    satsun.append(Monday + 5)
    
stable_qty_prod = []
for i in range(len(stable_assy_unique)):
    rows_set = np.where(BOM_set[:,1] == stable_assy_unique[i][0])
    if (len(rows_set[0])==0):
        friday = []
        if (Monday<=3):
            friday.append(Monday + 3)
            friday.append(Monday + 10)
        else:
            friday.append(Monday - 4)
            friday.append(Monday + 3)
        
        start_day = []
        off_day = []
        rows = np.where(table_cap[:,2] == stable_assy_unique[i][0])
        if (len(rows[0])>0):
            for j in range(len(wl)):
                if (wl[j,0]==table_cap[rows[0]][0][1]):
                    previous_0 = 0
                    if (day_off_before_additional == 1):
                        previous_0 = 1
                    first_day = True
                    for k in range(len(wl[j])-1):
                        if (wl[j,k+1]!=0):
                            if (previous_0==1):
                                if (first_day==True):
                                    if (day_off_before_additional == 1):
                                        start_day.append(k)
                                else:
                                    start_day.append(k)
                            first_day = False
                            previous_0 = 0
                        else:
                            off_day.append(k)
                            previous_0 = 1
                    break
        else:
            print('\nERROR CANT FIND STABLE PRODUCTION IN TABLE CAPACITY!!\n') 
        
        arr = []
        arr.append(stable_assy_unique[i][0])
        for j in range(target_day):
            is_start_day = False
            is_friday = False
            is_off_day = False
            max_qty_prod = 0
            for k in range(len(start_day)):
                if (j==start_day[k]):
                    is_start_day = True
                    break
            for k in range(len(friday)):
                if (j==friday[k]):
                    is_friday = True
                    break
            for k in range(len(off_day)):
                if (j==off_day[k]):
                    is_off_day = True
                    break
            if ((is_friday)&(is_start_day)):
                max_qty_prod = stable_assy_unique[i][4] - (stable_assy_unique[i][3] - stable_assy_unique[i][4])
            elif ((is_friday)|(is_start_day)):
                max_qty_prod = stable_assy_unique[i][4]
            elif (is_off_day):
                max_qty_prod = 0
            else:
                max_qty_prod = stable_assy_unique[i][3]
            arr.append(max_qty_prod)
        stable_qty_prod.append(arr)

# stable_qty_prod for set item
for i in range(len(stable_qty_prod)):
    rows_set2 = np.where(BOM_set[:,0] == stable_assy_unique[i][0])
    for j in range(len(rows_set2[0])):
        rows_BOM = np.where((BOM[:,0] == stable_qty_prod[i][0])&(BOM[:,1] == BOM_set[rows_set2[0][j]][1]))
        found = False
        for k in range(len(stable_qty_prod)):
            if (stable_qty_prod[k][0] == BOM_set[rows_set2[0][j]][1]):
                rows = np.where(table_cap[:,2] == BOM_set[rows_set2[0][j]][1])
                if (len(rows[0])>0):
                    for l in range(len(wl)):
                        if (wl[l,0]==table_cap[rows[0]][0][1]):
                            idx_fg = 2
                            idx_set = 1
                            while idx_set<=target_day:
                                if (wl[l,idx_set]>0):
                                    while (idx_fg<=target_day):
                                        if (stable_qty_prod[i][idx_fg]==0):
                                            idx_fg+=1
                                        else:
                                            break
                                    if (idx_fg<=target_day):
                                        stable_qty_prod[k][idx_set]+=stable_qty_prod[i][idx_fg]*BOM[rows_BOM[0][0]][2]
                                        idx_fg+=1
                                    else:
                                        if ((Monday==1)|(Monday==4)):
                                            stable_qty_prod[k][idx_set]+=stable_assy_unique[i][4]*BOM[rows_BOM[0][0]][2]
                                        else:
                                            stable_qty_prod[k][idx_set]+=stable_assy_unique[i][3]*BOM[rows_BOM[0][0]][2]
                                else:
                                    arr.append(0)
                                idx_set+=1
                            
                            stable_qty_prod.append(arr)
                            break
                found = True
                break
        if (found == False):
            arr = []
            arr.append(BOM_set[rows_set2[0][j]][1])
            rows = np.where(table_cap[:,2] == BOM_set[rows_set2[0][j]][1])
            if (len(rows[0])>0):
                for l in range(len(wl)):
                    if (wl[l,0]==table_cap[rows[0]][0][1]):
                        idx_fg = 2
                        idx_set = 1
                        while idx_set<=target_day:
                            if (wl[l,idx_set]>0):
                                while (idx_fg<=target_day):
                                    if (stable_qty_prod[i][idx_fg]==0):
                                        idx_fg+=1
                                    else:
                                        break
                                if (idx_fg<=target_day):
                                    arr.append(stable_qty_prod[i][idx_fg]*BOM[rows_BOM[0][0]][2])
                                    idx_fg+=1
                                else:
                                    if ((Monday==1)|(Monday==4)):
                                        arr.append(stable_assy_unique[i][4]*BOM[rows_BOM[0][0]][2])
                                    else:
                                        arr.append(stable_assy_unique[i][3]*BOM[rows_BOM[0][0]][2])
                            else:
                                arr.append(0)
                            idx_set+=1
                        
                        stable_qty_prod.append(arr)
                        break
                    
# add first working day for set item
for i in range(len(stable_qty_prod)):
    idx = 1
    while (stable_qty_prod[i][idx]==0):
        idx+=1
    stable_qty_prod[i].append(idx-1)
    
for j in range(len(stable_assy_unique)):
    rows_set = np.where(BOM_set[:,1] == stable_qty_prod[j][0])
    if(len(rows_set[0])==0):
        found = False
        total_order = 0
        for i in range(target_day):
            total_order+=stable_qty_prod[j][i+1]
        for i in range(len(order)):
            if (order[i,4]==stable_qty_prod[j][0]):
                if (found == False):
                    found = True
                    order[i,6]=total_order
                else:
                    order[i,6] = 0
        if (found == False):
            arr_temp = []
            arr_temp.append(float("NaN"))
            arr_temp.append(8000000000+j)
            arr_temp.append(order[0,2])
            arr_temp.append(total_order)
            arr_temp.append(stable_qty_prod[j][0])
            arr_temp.append('EXPORT-01')
            arr_temp.append(total_order)
            box_size = np.where(box[:,0] == stable_qty_prod[j][0])
            if (len(box_size[0])==1):
                arr_temp.append(box[box_size[0][0]][1])
            else:
                arr_temp.append(1)
            arr_temp.append(float("NaN"))
            order = np.vstack((order,arr_temp))

for i in range(len(order)):
    rows = np.where(stock_fg[:,0] == order[i,4])
    if (len(rows[0])>0):
        order[i,8] = int(rows[0])
    else:
        rows2 = np.where(stock_part_edit[:,0] == order[i,4])
        arr_temp = []
        arr_temp.append(order[i,4])
        if (len(rows2[0])>0):
            arr_temp.append(int(stock_part_edit[rows2[0][0]][1]))
        else:
            arr_temp.append(0)
        stock_fg = np.vstack((stock_fg,arr_temp))
        order[i,8] = len(stock_fg)-1

order_len = len(order)
#create new order for set items
finish_loop_order = 0
i=order_len-1
while finish_loop_order!=1:
    rows = np.where(BOM_set[:,0] == order[i,4])
    if(len(rows[0])>0):
        rows2 = np.where(BOM[:,0] == order[i,4])
        for j in range(len(rows[0])):
            qty_mult=0
            for k in range(len(rows2[0])):
                if (BOM[rows2][k][1]==BOM_set[rows][j][1]):
                    qty_mult=BOM[rows2][k][2]
                    break
            found = 0
            if(found==0):
                arr_temp = []
                arr_temp.append(-1)
                arr_temp.append(order[i,1])
                arr_temp.append(order[i,2])
                arr_temp.append(order[i,3]*qty_mult)
                arr_temp.append(BOM_set[rows][j][1])
                arr_temp.append(order[i,5])
                arr_temp.append(order[i,6]*qty_mult)
                arr_temp.append(order[i,7])
                arr_temp.append(-1)
                order_temp = []
                order_temp = np.vstack((order[:i,:],arr_temp))
                order = np.vstack((order_temp,order[i:,:]))
                i+=1
    i-=1
    if (i==-1):
        finish_loop_order=1

order_len = len(order)

#DEDUCT WITH STOCK FG FOR SET ITEMS
for k in range(len(arr_ex_loc)):
    for i in range(order_len):
        arr = []
        is_stable_bool = False
        for j in range(len(stable_assy_unique)):
            if (stable_assy_unique[j][0]==order[i,4]):
                is_stable_bool = True
                break
        if ((order[i,5]==arr_ex_loc[k])&(is_stable_bool==False)):
            rows = np.where(stock_fg[:,0] == order[i,4])
            if (len(rows[0])==1):
                if (order[i,6]>int(stock_fg[rows,1])):
                    found=0
                    for j in range(len(draft_stock_fg)):
                        if ((draft_stock_fg[j][0]==order[i,4])&(draft_stock_fg[j][1]==order[i,5])):
                            found=1
                            draft_stock_fg[j][2]+=int(stock_fg[rows,1])
                    if (found==0):
                        arr.append(order[i,4])
                        arr.append(order[i,5])
                        arr.append(int(stock_fg[rows,1]))
                        draft_stock_fg.append(arr)
                    
                    order[i,6]-=int(stock_fg[rows,1])
                    change_stock_fg(order[i,4],0)
                else:
                    found=0
                    for j in range(len(draft_stock_fg)):
                        if ((draft_stock_fg[j][0]==order[i,4])&(draft_stock_fg[j][1]==order[i,5])):
                            found=1
                            draft_stock_fg[j][2]+=int(order[i,6])
                    if (found==0):
                        arr.append(order[i,4])
                        arr.append(order[i,5])
                        arr.append(order[i,6])
                        draft_stock_fg.append(arr)
                        
                    change_stock_fg(order[i,4],0-order[i,6])
                    order[i,6] = int(0)
                    
print('Preparing (30%)...')
print('')
#initialize calendar
for i in range(order_len):
    col = []
    for j in range(target_day):
        col += [0]
    calendar.append(col)

#create order idx
for i in range(order_len):
    order[i,0] = i

#initialize order_capacity
for i in range(order_len):
    col = []
    order_capacity.append(col)
    
arr_error = []
#fill order capacity   
for i in range(order_len):
    order_capacity[i]=find_capacity(table_cap, order[i,4])
    if (len(order_capacity[i])==0):
        arr_error.append(order[i,4])

if (len(arr_error)>0):
    print("=========ERROR: NO CAPACITY TABLE=========")
    print('FG: ')
    print(*arr_error, sep = '\n')
    print('')
    operation_mode = 0

#fill max_cap
for i in range(order_len):
    max_cap += [0]
    
for i in range(order_len):
    for j in range(len(order_capacity[i])):
        max_cap[i]+=math.floor(order_capacity[i][j][3])
    
print('Preparing (40%)...')
print('')

#initialize deviation_sum for print combination
for i in range(print_comb):
    col = []
    for j in range(3):
        col+=[0]
    deviation_sum.append(col)

#assign deviation_sum for print combination
for i in range(print_comb):
    deviation_sum[i][0]=2147483647
    deviation_sum[i][1]=2147483647
    deviation_sum[i][2]=-1

#initialize fg_produced for temp produce qty
for i in range(order_len):
    fg_produced += [0]
    
#initialize fg_need_OT
for i in range(order_len):
    col = []
    for j in range(3):
        col2 = 0
        col.append(col2)
    fg_need_OT.append(col)
    
#initialize fg_lack_of_part
for i in range(order_len):
    fg_lack_of_part += [0]
    
for i in range(order_len):
    fg_lack_of_part[i] = 0

#initialize calendar_stock_part
for i in range(order_len):
    col = []
    for j in range(target_day_2):
        col2 = []
        col.append(col2)
    calendar_stock_part.append(col)
    
#initialize calendar_stock_part_prod
for i in range(order_len):
    col = []
    for j in range(target_day_2):
        col2 = []
        col.append(col2)
    calendar_stock_part_prod.append(col)  

#add fg index in order array and add a new row for stock_fg if the fg is not available in stock_fg (FOR THE NEW SET ORDER)
for i in range(order_len):
    if (order[i,8]==-1):
        rows = np.where(stock_fg[:,0] == order[i,4])
        if (len(rows[0])>0):
            order[i,8] = int(rows[0])
        else:
            rows2 = np.where(stock_part_edit[:,0] == order[i,4])
            arr_temp = []
            arr_temp.append(order[i,4])
            if (len(rows2[0])>0):
                arr_temp.append(int(stock_part_edit[rows2[0][0]][1]))
            else:
                arr_temp.append(0)
            stock_fg = np.vstack((stock_fg,arr_temp))
            order[i,8] = len(stock_fg)-1
print('Preparing (50%)...')
print('')
#set box for fg
for i in range(len(stock_fg)):
    box_fg+=[0]
    
for i in range(len(stock_fg)):
    rows = np.where(box[:,0] == stock_fg[i,0])
    if (len(rows[0])>0):
        if (box[rows[0][0],1]) > 0:
            box_fg[i] = box[rows[0][0],1]
        else:
            box_fg[i] = 1
    else:
        box_fg[i] = 1

#create list of fg
for i in range(len(stock_fg)):       
    col = []
    for j in range(2):
        col+=[0]
    fg_need_part.append(col)

for i in range(len(stock_part_edit)):
    make_fg_need_part(stock_part_edit[i,0])
    
for i in range(len(stock_fg)):
    temporary_fg_need_part.append(0)
    
for i in range(len(production_limit)):
    temporary_make_fg_need_part(production_limit[i,0])
        
#create fg_BOM and add a new row if the part is not available in stock_part_edit
bom_error = 0
arr_error = []
for i in range(len(stock_fg)):
    rows_BOM = np.where(BOM[:,0] == stock_fg[i,0])
    arr_fg_BOM_temp = []
    rows_order = np.where(order[:,4] == stock_fg[i,0])
    if(len(rows_order[0])>0):
        if(len(rows_BOM[0])>0):
            for j in range(len(BOM[rows_BOM])):
                rows_part = np.where(stock_part_edit[:,0] == BOM[rows_BOM[0][j]][1])
                arr_temp = []
                if (len(rows_part[0])>0):
                    arr_temp.append(int(rows_part[0]))
                else:
                    arr_temp2 = []
                    arr_temp2.append(BOM[rows_BOM[0][j]][1])
                    rows_set = np.where(BOM_set[:,1] == BOM[rows_BOM[0][j]][1])
#                     rows_part_prod = np.where(routing[:,0] == BOM[rows_BOM[0][j]][1])
#                     if ((len(rows_set[0])>0)|(len(rows_part_prod[0])>0)):
                    if (len(rows_set[0])>0):
                        arr_temp2.append(0)
                    else:
                        arr_temp2.append(1000000)
                    for k in range(target_day_2-1):
                        arr_temp2.append(int(0))
                    stock_part_edit = np.vstack((stock_part_edit,arr_temp2))
                    arr_temp.append(len(stock_part_edit)-1)
                arr_temp.append(BOM[rows_BOM[0][j]][2])
                arr_fg_BOM_temp.append(arr_temp)
            fg_BOM.append(arr_fg_BOM_temp)
        else:
            arr_error.append(stock_fg[i,0])
    else:
        fg_BOM.append([])


if (len(arr_error)>0):
    print('=========ERROR: BOM NOT FOUND=========')
    print('FG: ')
    print(*arr_error, sep = '\n')
    print('')
    operation_mode = 0
    bom_error = 1
print('Preparing (60%)...')
print('')

#create array for item levelling
arr_part_routing = []

for i in range(len(stock_part_edit)):
    arr = []
    arr.append(stock_part_edit[i][0])
    rows = np.where(routing[:,0] == stock_part_edit[i][0])
    if(len(rows[0])>0):
        rows2 = np.where(routing[:,7] == routing[rows[0][0]][7])
        arr_temp = routing[rows2]
        arr_temp = sorted(arr_temp, key=lambda x: x[8])
        for j in range(len(arr_temp)):
            arr2 = []
            arr2.append(arr_temp[j][1])
            
            for k in range(len(production_table_cap)):
                if (production_table_cap[k][0]==arr_temp[j][2]):
                    arr2.append(k)
                    break
            
            arr2.append(arr_temp[j][2])
            arr2.append(arr_temp[j][3])
            arr2.append(arr_temp[j][4])
            arr2.append(arr_temp[j][5])
            arr.append(arr2)
    arr_part_routing.append(arr)

calendar_production = []
calendar_production_load = []
        
for i in range(len(production_table_cap)):
    arr = []
    arr2 = []
    arr.append(production_table_cap[i][0])
    for k in range(28):
        arr.append(arr2)
    calendar_production.append(arr)

for i in range(len(production_table_cap)):
    arr = []
    arr2 = 0
    arr.append(production_table_cap[i][0])
    for k in range(28):
        arr.append(arr2)
    calendar_production_load.append(arr)
    
for i in range(len(order)):
    col = []
    col2 = []
    for j in range(target_day_2):
        col2.append(col)
    calendar_prod_summary.append(col2)
    
arr_temp = sorted(routing, key=lambda x: x[2])
arr_prod_table_not_found = []
for i in range(len(arr_temp)):
    found = 0
    for j in range(len(calendar_production)):
        if (arr_temp[i][2] == calendar_production[j][0]):
            found=1
            break
    if (found == 0):
        for j in range(len(arr_prod_table_not_found)):
            if (arr_temp[i][2] == arr_prod_table_not_found[j]):
                found=1
                break
    if (found == 0):
        arr_prod_table_not_found.append(arr_temp[i][2])
arr_temp = []

if (len(arr_prod_table_not_found)>1):
    print ('ERROR: SOME OF THE PRODUCTION TABLE(s) CAN''T BE FOUND:')
    print (arr_prod_table_not_found,'\n')

#initialize stock_part
for i in range(len(stock_part_edit)):
    col = []
    for j in range(target_day_2):
        col += [0]
    stock_part.append(col)

#create stock_part schedule based on stock_part_edit
for i in range(len(stock_part_edit)):
    for j in range(target_day_2):
        for k in range(j+1):
            stock_part[i][j]+=int(float(stock_part_edit[i,k+1]))

for i in range(len(stock_fg)):
    rows_set = np.where(BOM_set[:,0] == stock_fg[i,0])
    if (len(rows_set[0])>0):
        fg_need_part[i][0]=1

for i in range(len(stock_fg)):
    fg_need_part[i][1]= -1
    
for i in range(len(stock_fg)):
    rows_set = np.where(BOM_set[:,1] == stock_fg[i,0])
    rows_order = np.where(order[:,4] == stock_fg[i,0])
    if ((len(rows_set[0])>0)&(len(rows_order[0])>0)):
        fg_need_part[i][0]=1
        rows = np.where(stock_part_edit[:,0] == stock_fg[i,0])
        fg_need_part[i][1]=int(rows[0])

#initialize BOM_set_id
for i in range(len(BOM_set)):
    col = []
    for j in range(2):
        col += [0]
    BOM_set_id.append(col)

#create BOM set id
for i in range(len(BOM_set)):
    rows = np.where(stock_fg[:,0] == BOM_set[i,1])
    if (len(rows[0])>0):
        BOM_set_id[i][0] = int(rows[0])
    rows = np.where(stock_part_edit[:,0] == BOM_set[i,1])
    if (len(rows[0])>0):
        BOM_set_id[i][1] = int(rows[0])
        
print('Preparing (70%)...')
print('')

#initialize part_test_production
for i in range(len(stock_part)):
    part_test_production+=[0]
    
#assign part_test_production value
for i in range(len(stock_part)):
    part_test_production[i]=stock_part[i][target_day_2-1]

#calculate enough part
part_problem = ''
arr_error = []
if (bom_error==0):
    for i in range(order_len):
        qty_insufficient = 0
        item = order[i,8]
        qty_part_temp = 0
        
        for j in range(len(fg_BOM[item])):
            rows = np.where(BOM_set[:,1] == stock_part_edit[fg_BOM[item][j][0]][0])
            rows_part = np.where(stock_part_edit_2[:,0] == stock_part_edit[fg_BOM[item][j][0]][0])
            if ((len(rows[0])==0)&(len(rows_part[0])>0)):
                qty_part = order[i,6]*fg_BOM[item][j][1]
                part_test_production[fg_BOM[item][j][0]]-=qty_part
                if (part_test_production[fg_BOM[item][j][0]]<0):
                    qty_insufficient=1
                    qty_part_temp = stock_part[fg_BOM[item][j][0]][target_day_2-1]
                    part_problem = stock_part_edit[fg_BOM[item][j][0]][0]
                    break
        if (qty_insufficient==1):
            arr_temp = []
            arr_temp.append(order[i,4])
            arr_temp.append(part_problem)
            arr_temp.append(qty_part_temp)
            arr_temp.append(order[i,6])
            arr_error.append(arr_temp)

if (len(arr_error)>0):
    print('=========ERROR: PART NOT ENOUGH=========')
    print('FG\t\tPart\t\tQty\t\tOrder')
    printX3(arr_error)
    print('')
    operation_mode = 0

print('Preparing (80%)...')
print('')  
#initialize fg_calendar
for i in range(len(stock_fg)):
    col = []
    for j in range(target_day_2):
        col += [0]
    fg_calendar.append(col)
    
#initialize additional_table_fg
for i in range(len(table_list)):
    col = []
    for j in range(target_day_2):
        col +=[0]
    additional_table_fg.append(col)
    
#initialize additional_fg
for i in range(len(stock_fg)):
    col = []
    for j in range(target_day_2):
        col +=[0]
    additional_fg.append(col)

for i in range(target_day):
    avail = 0
    for j in range(len(wl)):
        if (wl[j][i+1]>0):
            avail = 1
            break
    if (avail==0):
        workload.append(-1)
    else:
        workload.append(1)
        
for i in range(target_day):
    if (workload[i]!=-1):
        start_day = i
        break

for i in reversed(range(target_day_2)):
    if (workload[i]!=-1):
        break
    else:
        target_day-=1
print('Preparing (90%)...')
print('')
    
for i in range(target_day_2):
    column_names += [0]
for i in range(target_day_2):
    column_names[i] = 'Day '+str(i+1)

for i in range(order_len):
    row_names += [0]
for i in range(order_len):
    row_names[i] = str(order[i][1]) + ' | ' + str(order[i][4])

for i in range(len(table_list)):
    row_names_2 += [0]
for i in range(len(table_list)):
    row_names_2[i] = table_list[i][0]

for i in range(len(stock_fg)):
    row_names_fg += [0]
for i in range(len(stock_fg)):
    row_names_fg[i] = stock_fg[i][0]
    
for i in range(len(jig_qty1)):
    row_names_jig.append(jig_qty1[i][0])

#TEMPORARY - LIMIT BY PART
for i in range(len(stock_part_edit)):
    arr = []
    temporary_part_list.append(arr)

satsun = []

for i in range(len(production_limit)):
    found=-1
    for j in range(len(stock_part_edit)):
        if (stock_part_edit[j,0]==production_limit[i,0]):
            found=j
            break
    if (found>-1):
        arr = []
        arr.append(production_limit[i,0])
        for j in range(target_day):
            found_1 = False
            for k in range(len(satsun)):
                if (j==satsun[k]):
                    found_1 = True
                    break
            prod_qty = 0
            if (found_1 == False):
                prod_qty = production_limit[i,1]
            arr.append(prod_qty)
        temporary_part_list[found]=arr

#create fg_jig
for i in range(len(stock_fg)):
    rows = np.where(fg_jig1[:,1] == stock_fg[i,0])
    if (len(rows[0])>0):
        fg_jig.append(int(fg_jig1[rows[0][0]][2][4:9])-1)
    else:
        fg_jig.append(-1)

#create jig_qty
for i in range(len(jig_qty1)):
    arr = []
    arr.append(jig_qty1[i][0])
    for j in range(target_day):
        arr.append(jig_qty1[i][1])
    jig_qty.append(arr)
        
#create jig_schedule
for i in range(len(jig_qty1)):
    arr = []
    for j in range(jig_qty1[i][1]):
        arr2 = []
        for k in range(target_day):
            arr2.append([])
        arr.append(arr2)
    jig_schedule.append(arr)
    
print('Preparing (100%)...')
print('')

#count order by table
for i in range(order_len):
    rows = np.where(table_cap[:,2] == order[i,4])
    for j in range(len(rows[0])):
        table_list[table_cap[rows[0][j]][0]][1]+=1

#see table relation
relation = []
for i in range(order_len):
    find_j = 0
    find_new = 1
    for j in range(len(relation)):
        for k in range(len(order_capacity[i])):
            find_l=0
            for l in range(len(relation[j][1])):
                if (order_capacity[i][k][1]==relation[j][1][l]):
                    find_j=1
                    find_l=1
                    if (find_new==1):
                        find_new=0
                        relation[j][0].append(i)
            if (find_j == 1):
                if (find_l==0):
                    relation[j][1].append(order_capacity[i][k][1])
        if (find_j == 1):
            for k in range(len(fg_BOM[order[i,8]])):
                find_l=0
                if (fg_BOM[order[i,8]][k][0]<(len(stock_part_edit_2)-1)):
                    for l in range(len(relation[j][2])):
                        if (fg_BOM[order[i,8]][k][0]==relation[j][2][l]):
                            find_l=1
                    if (find_l==0):
                        relation[j][2].append(fg_BOM[order[i,8]][k][0])
            break
    if (find_j==0):
        arr = []
        arr2 = []
        arr3 = []
        arr4 = []
        arr.append(i)
        for k in range(len(order_capacity[i])):
            arr2.append(order_capacity[i][k][1])
        for k in range(len(fg_BOM[order[i,8]])):
            if (fg_BOM[order[i,8]][k][0]<(len(stock_part_edit_2)-1)):
                arr3.append(fg_BOM[order[i,8]][k][0])
        arr4.append(arr)    
        arr4.append(arr2)
        arr4.append(arr3)
        relation.append(arr4)
    
avail_relation = []
for i in range(len(relation)):
    avail_relation +=[1]
    
for i in range(len(relation)):
    if (avail_relation[i]==1):
        j = 0
        while (j < len(relation[i][1])):
            found_relation = -1
            for i_2 in range(len(relation)):
                if (i!=i_2):
                    if (avail_relation[i_2]==1):
                        for j_2 in range(len(relation[i_2][1])):
                            if (relation[i][1][j]==relation[i_2][1][j_2]):
                                found_relation = i_2
                                break
                if (found_relation>-1):
                    if (avail_relation[found_relation]==1):
                        relation[i][0]+=relation[found_relation][0]
                        arr_1 = []
                        for y in range(len(relation[found_relation][1])):
                            found_table = 0
                            for y_2 in range(len(relation[i][1])):
                                if (relation[found_relation][1][y]==relation[i][1][y_2]):
                                    found_table=1
                            if (found_table==0):
                                arr_1.append(relation[found_relation][1][y])
                                
                        relation[i][1]+=arr_1
                        
                        arr_2 = []
                        for y in range(len(relation[found_relation][2])):
                            found_part = 0
                            for y_2 in range(len(relation[i][2])):
                                if (relation[found_relation][2][y]==relation[i][2][y_2]):
                                    found_part=1
                            if (found_part==0):
                                arr_2.append(relation[found_relation][2][y])
                        relation[i][2]+=arr_2
                        avail_relation[found_relation]=0
            j+=1
               
amount_pop=0
for i in range(len(relation)):
    if (avail_relation[i]==0):
        relation.pop(i-amount_pop)
        amount_pop+=1
    
for i in range(len(relation)):
    avail_relation[i] = 1
        
for i in range(len(relation)):
    j = 0
    while (j < len(relation[i][2])):
        find_i_2 = -1
        for i_2 in range(i+1,len(relation)):
            if (avail_relation[i_2]==1):
                for j_2 in range(len(relation[i_2][2])):
                    if (relation[i_2][2][j_2] == relation[i][2][j]):
                        find_i_2 = i_2
                        break
            if (find_i_2>-1):
                if (avail_relation[find_i_2]==1):
                    relation[i][0]+=relation[find_i_2][0]
                    relation[i][1]+=relation[find_i_2][1]
                    for k in range(len(relation[find_i_2][2])):
                        find_l = 0
                        for l in range(len(relation[i][2])):
                            if (relation[find_i_2][2][k]==relation[i][2][l]):
                                find_l = 1
                        if (find_l == 0):
                            relation[i][2].append(relation[find_i_2][2][k])
                    avail_relation[find_i_2]=0
        j+=1

amount_pop=0
for i in range(len(relation)):
    if (avail_relation[i]==0):
        relation.pop(i-amount_pop)
        amount_pop+=1
    
for x in range(3):
    for i in range(len(relation)):
        avail_relation[i] = 1
        
    for i in range(len(relation)):
        if (avail_relation[i]==1):
            j = 0
            while (j < len(relation[i][0])):
                rows_set = np.where(BOM_set[:,0] == order[relation[i][0][j],4])
                for k in range(len(rows_set[0])):
                    found_relation = -1
                    for i_2 in range(len(relation)):
                        if (i!=i_2):
                            if (avail_relation[i_2]==1):
                                for j_2 in range(len(relation[i_2][0])):
                                    if (BOM_set[rows_set[0][k]][1]==order[relation[i_2][0][j_2],4]):
                                        found_relation = i_2
                                        break
                        if (found_relation>-1):
                            if (avail_relation[found_relation]==1):
                                relation[i][0]+=relation[found_relation][0]
                                relation[i][1]+=relation[found_relation][1]
                                relation[i][2]+=relation[found_relation][2]
                                avail_relation[found_relation]=0
                j+=1
                   
    amount_pop=0
    for i in range(len(relation)):
        if (avail_relation[i]==0):
            relation.pop(i-amount_pop)
            amount_pop+=1
            
    for i in range(len(relation)):
        avail_relation[i] = 1
        
    for i in range(len(relation)):
        if (avail_relation[i]==1):
            j = 0
            while (j < len(relation[i][0])):
                rows_set = np.where(BOM_set[:,1] == order[relation[i][0][j],4])
                for k in range(len(rows_set[0])):
                    found_relation = -1
                    for i_2 in range(len(relation)):
                        if (i!=i_2):
                            if (avail_relation[i_2]==1):
                                for j_2 in range(len(relation[i_2][0])):
                                    if (BOM_set[rows_set[0][k]][0]==order[relation[i_2][0][j_2],4]):
                                        found_relation = i_2
                                        break
                        if (found_relation>-1):
                            if (avail_relation[found_relation]==1):
                                relation[i][0]+=relation[found_relation][0]
                                relation[i][1]+=relation[found_relation][1]
                                relation[i][2]+=relation[found_relation][2]
                                avail_relation[found_relation]=0
                j+=1
                   
    amount_pop=0
    for i in range(len(relation)):
        if (avail_relation[i]==0):
            relation.pop(i-amount_pop)
            amount_pop+=1        
        
for i in range(len(relation)):
    relation[i][0].sort()

new_order = []
old_to_new_order = []

for i in range(order_len):
    old_to_new_order += [0]
for i in range(len(relation)):
    arr = []
    for j in range(len(relation[i][0])):
        arr.append(order[relation[i][0][j]])
        arr2 = []
        arr2.append(i)
        arr2.append(len(arr)-1)
        old_to_new_order[relation[i][0][j]] = []
        old_to_new_order[relation[i][0][j]].append(arr2)
    new_order.append(arr)

def sort_order(z,idx_search,flag_filter,flag_ok):
    global new_order
    add = 0
    
    order_filter = 1
    if (flag_filter==1):
        order_filter = 0
    
    rows_set = np.where(BOM_set[:,0] == new_order[z][idx_search][4])
    if (len(rows_set[0])>0):
        for k in range(len(rows_set[0])):
            for l in range (len(new_order[z])):
                if (BOM_set[rows_set[0][k]][1] == new_order[z][l][4]):
                    if (new_order[z][l][1]==new_order[z][idx_search][1]):
                        rows = np.where(BOM[:,0] == new_order[z][idx_search][4])
                        for m in range(len(rows[0])):
                            if (BOM[rows[0][m]][1]==new_order[z][l][4]):
                                if (BOM[rows[0][m]][2]*new_order[z][idx_search][6]==new_order[z][l][6]):
                                    if (ordered_order[new_order[z][l][0]]<=order_filter):
                                        if (flag_ok==1):
                                            ordered_order[new_order[z][l][0]] = 1
                                        new_order[z].insert(idx_search,new_order[z][l])
                                        new_order[z].pop(l+1)
                                        add += 1
                                        add += sort_order(z,idx_search,flag_filter,flag_ok)
                                        idx_search+=add
                                        break
    return add

def check_table_size(z,idx_search,order_id, amount):
    global new_order
    result = 0
    
    rows_set = np.where(BOM_set[:,0] == new_order[z][idx_search][4])
    if (len(rows_set[0])>0):
        for k in range(len(rows_set[0])):
            for l in range (len(new_order[z])):
                if (BOM_set[rows_set[0][k]][1] == new_order[z][l][4]):
                    if (new_order[z][l][1]==order_id):
                        if (len(order_capacity[new_order[z][l][0]])==amount):
                            result+=1
                        result+=check_table_size(z,idx_search-1,order_id,amount)
                        break
    return result

for i in range(len(order)):
    is_set += [0]
    
for i in range(len(order)):
    rows_set = np.where(BOM_set[:,1] == order[i][4])
    if(len(rows_set[0])==0):
        is_set[i] = 0
    else:
        is_set[i] = 1
        
#create is_stable
is_stable = []
for i in range(len(order)):
    is_stable += [0]
    
for i in range(len(order)):
    for j in range(len(stable_assy_unique)):
        if (stable_assy_unique[j][0]==order[i][4]):
            is_stable[i] = 1
            break

ordered_order = []
for i in range (len(order)):
    ordered_order += [0]
    
ordered_by_jig = []
for z in range(len(new_order)):
    for i in range(len(new_order[z])):
        if (fg_jig[new_order[z][i][8]]>=0):
            found = False
            amount = round_up_box(new_order[z][i][6],box_fg[new_order[z][i][8]])*order_capacity[new_order[z][i][0]][0][4]/set_up_table[order_capacity[new_order[z][i][0]][0][0]][2]/jig_qty1[fg_jig[new_order[z][i][8]],1]
            for j in range(len(ordered_by_jig)):
                if (ordered_by_jig[j][0]==fg_jig[new_order[z][i][8]]):
                    found=True
                    ordered_by_jig[j][1]+=amount
                    break
            if(found==False):
                arr = []
                arr.append(fg_jig[new_order[z][i][8]])
                arr.append(amount)
                ordered_by_jig.append(arr)

ordered_by_jig = sorted(ordered_by_jig, key=lambda x: x[1], reverse=False)

ordered_by_set = []
for z in range(len(new_order)):
    for i in range(len(new_order[z])):
        rows_set = np.where(BOM_set[:,1] == new_order[z][i][4])
        if (len(rows_set[0])>0):
            found = False
            amount = round_up_box(new_order[z][i][6],box_fg[new_order[z][i][8]])*order_capacity[new_order[z][i][0]][0][4]/set_up_table[order_capacity[new_order[z][i][0]][0][0]][2]/jig_qty1[fg_jig[new_order[z][i][8]],1]
            for j in range(len(ordered_by_set)):
                if (ordered_by_set[j][0]==new_order[z][i][4]):
                    found=True
                    ordered_by_set[j][1]+=amount
                    break
            if(found==False):
                arr = []
                arr.append(new_order[z][i][4])
                arr.append(amount)
                ordered_by_set.append(arr)
ordered_by_set = sorted(ordered_by_set, key=lambda x: x[1], reverse=False)

ordered_by_prod_limit = []
for z in range(len(new_order)):
    for i in range(len(new_order[z])):
        rows_set = np.where(BOM_set[:,1] == new_order[z][i][4]) 
        if (len(rows_set[0])==0):
            for k in range(len(fg_BOM[new_order[z][i][8]])):
                found = False
                if (len(temporary_part_list[fg_BOM[new_order[z][i][8]][k][0]])>0):
                    amount = round_up_box(new_order[z][i][6],box_fg[new_order[z][i][8]])*fg_BOM[new_order[z][i][8]][k][1]/temporary_part_list[fg_BOM[new_order[z][i][8]][k][0]][1]
                    for j in range(len(ordered_by_prod_limit)):
                        if (ordered_by_prod_limit[j][0]==temporary_part_list[fg_BOM[new_order[z][i][8]][k][0]][0]):
                            found=True
                            ordered_by_prod_limit[j][1]+=amount
                            break
                    if(found==False):
                        arr = []
                        arr.append(temporary_part_list[fg_BOM[new_order[z][i][8]][k][0]][0])
                        arr.append(amount)
                        ordered_by_prod_limit.append(arr)
ordered_by_prod_limit = sorted(ordered_by_prod_limit, key=lambda x: x[1], reverse=False)
        
for z in range(len(relation)):
    len_order_now = len(new_order[z])
    
    if (sort_mode==1):
        first_item = ''
        start_idx_after_jig = 0
        
        #need jig first
        for i in range(len(stable_assy_unique)):
            j = 0
            while j < len(new_order[z]):
                if (is_set[new_order[z][j][0]]==0):
                    if (new_order[z][j][4]==stable_assy_unique[i][0]):
                        if (first_item==''):
                            first_item = new_order[z][j][0]
                        ordered_order[new_order[z][j][0]] = 1
                        new_order[z].insert(0,new_order[z][j])
                        new_order[z].pop(j+1)
                        sort_order(z,0,0,1)
                j += 1
        
        for i in range(len(new_order[z])):
            if (new_order[z][i][0]==first_item):
                start_idx_after_jig = i+1
                break
                
        #order by export-local priority
        for i in reversed(range(len(arr_ex_loc))):
            j = start_idx_after_jig
            while j < len_order_now:
                rows_set = np.where(BOM_set[:,1] == new_order[z][j][4])
                if (len(rows_set[0])==0):
                    if (new_order[z][j][5]==arr_ex_loc[i]):
                        if ((ordered_order[new_order[z][j][0]]==0)&(is_set[new_order[z][j][0]]==0)):
                            new_order[z].insert(start_idx_after_jig,new_order[z][j])
                            new_order[z].pop(j+1)
                            sort_order(z,start_idx_after_jig,0,0)
                j += 1
        
        #set start and end idx
        idx_start_end = []
        for i in reversed(range(len(arr_ex_loc))):
            arr = []
            arr.append(-1)
            arr.append(-1)
            for j in range(len(new_order[z])):
                if (new_order[z][j][5]==arr_ex_loc[len(arr_ex_loc)-1-i]):
                    if (arr[0]==-1):
                        arr[0]=j
                elif (new_order[z][j][5]!=arr_ex_loc[len(arr_ex_loc)-1-i]):
                    if (arr[0]!=-1):
                        if (arr[1]==-1):
                            arr[1]=j-1
                
            idx_start_end.append(arr)
        
        for i in reversed(range(len(arr_ex_loc))):
            if (idx_start_end[i][0]!=-1):
                if (idx_start_end[i][1]==-1):
                    idx_start_end[i][1] = len(new_order[z])-1
                    break
                
        for i in range(len(arr_ex_loc)):
            if (idx_start_end[i][0]!=-1):
                #prioritize: FG that need bigger capacity
                sorted_arr = []
                j = idx_start_end[i][0]
                while j <= idx_start_end[i][1]:
                    rows_set = np.where(BOM_set[:,1] == new_order[z][j][4])
                    if (len(rows_set[0])==0):
                        arr = []
                        arr.append(new_order[z][j][0])
                        arr.append(order_capacity[new_order[z][j][0]][0][3])
                        if (len(sorted_arr)==0):
                            sorted_arr.append(arr)
                        else:
                            for k in range(len(sorted_arr)):
                                if (k==len(sorted_arr)-1):
                                    if (order_capacity[new_order[z][j][0]][0][3]>=sorted_arr[k][1]):
                                        sorted_arr.append(arr)
                                        break
                                    elif (order_capacity[new_order[z][j][0]][0][3]<=sorted_arr[0][1]):
                                        sorted_arr.insert(0,arr)
                                        break
                                    else:
                                        print ('------------ERROR------------')
                                elif (order_capacity[new_order[z][j][0]][0][3]>=sorted_arr[k][1]):
                                    if (order_capacity[new_order[z][j][0]][0][3]<=sorted_arr[k+1][1]):
                                        sorted_arr.insert(k+1,arr)
                                        break
                    j += 1
                
                for q in range(len(sorted_arr)):
                    j = idx_start_end[i][0]
                    while j <= idx_start_end[i][1]:
                        if (new_order[z][j][0]==sorted_arr[q][0]):
                            ordered_order[new_order[z][j][0]] = 1
                            new_order[z].insert(idx_start_end[i][0],new_order[z][j])
                            new_order[z].pop(j+1)
                            sort_order(z,idx_start_end[i][0],0,1)
                            break
                        j += 1

                #prioritize: FG that need important part
                j = idx_start_end[i][0]
                while j <= idx_start_end[i][1]:
                    rows_set = np.where(BOM_set[:,1] == new_order[z][j][4])
                    if (len(rows_set[0])==0):
                        need_part_var = 0
                        rows_BOM = np.where(BOM[:,0] == new_order[z][j][4])
                        for k in range(len(rows_BOM[0])):
                            rows_part = np.where(stock_part_edit_2[:,0] == BOM[rows_BOM][k][1])
                            if (len(rows_part[0])>0):
                                need_part_var=1
                                break
                        if (need_part_var==1):
                            if ((is_set[new_order[z][j][0]]==0)):
                                ordered_order[new_order[z][j][0]] = 1
                                new_order[z].insert(idx_start_end[i][0],new_order[z][j])
                                new_order[z].pop(j+1)
                                sort_order(z,idx_start_end[i][0],0,1)
                    j += 1

                #prioritize: FG that need part from prod
                for q in range(len(ordered_by_prod_limit)):
                    j = idx_start_end[i][0]
                    while j <= idx_start_end[i][1]:
                        if (is_set[new_order[z][j][0]]==0):
                            item = new_order[z][j][8]
                            for k in range(len(fg_BOM[item])):
                                if (len(temporary_part_list[fg_BOM[item][k][0]])>0):
                                    if (temporary_part_list[fg_BOM[item][k][0]][0]==ordered_by_prod_limit[q][0]):
                                        ordered_order[new_order[z][j][0]] = 1
                                        new_order[z].insert(idx_start_end[i][0],new_order[z][j])
                                        new_order[z].pop(j+1)
                                        sort_order(z,idx_start_end[i][0],0,1)
                                        break
                        j += 1
                    
                #prioritize: FG that need jig
                for q in range(len(ordered_by_jig)):
                    j = idx_start_end[i][0]
                    while j <= idx_start_end[i][1]:
                        if (is_set[new_order[z][j][0]]==0):
                            if (fg_jig[new_order[z][j][8]]==ordered_by_jig[q][0]):
                                ordered_order[new_order[z][j][0]] = 1
                                new_order[z].insert(idx_start_end[i][0],new_order[z][j])
                                new_order[z].pop(j+1)
                                sort_order(z,idx_start_end[i][0],0,1)
                        j += 1
                    
                #prioritize: FG that need set
                for q in range(len(ordered_by_set)):
                    j = idx_start_end[i][0]
                    while j <= idx_start_end[i][1]:
                        rows_set = np.where(BOM_set[:,0] == new_order[z][j][4])
                        for k in range(len(rows_set[0])):
                            if (BOM_set[rows_set[0][k]][1]==ordered_by_set[q][0]):
                                ordered_order[new_order[z][j][0]] = 1
                                new_order[z].insert(idx_start_end[i][0],new_order[z][j])
                                new_order[z].pop(j+1)
                                sort_order(z,idx_start_end[i][0],0,1)
                                break
                        j += 1    
    elif (sort_mode==2):  
        for k in reversed(range(2,11)):
            j = 0
            while j < len_order_now:
                rows_set = np.where(BOM_set[:,1] == new_order[z][j][4])
                if (len(rows_set[0])==0):
                    if (len(order_capacity[new_order[z][j][0]])==k):
                        if ((ordered_order[new_order[z][j][0]]==0)&(is_set[new_order[z][j][0]]==0)):
                            ordered_order[new_order[z][j][0]] = 1
                            new_order[z].insert(0,new_order[z][j])
                            new_order[z].pop(j+1)
                            sort_order(z,0,1,1)
                j += 1
        
        j = 0
        while j < len_order_now:
            rows_set = np.where(BOM_set[:,1] == new_order[z][j][4])
            if (len(rows_set[0])==0):
                need_part_var = 0
                rows_BOM = np.where(BOM[:,0] == new_order[z][j][4])
                for k in range(len(rows_BOM[0])):
                    rows_part = np.where(stock_part_edit_2[:,0] == BOM[rows_BOM][k][1])
                    if (len(rows_part[0])>0):
                        need_part_var=1
                        break
                if (need_part_var==1):
                    if ((ordered_order[new_order[z][j][0]]==0)&(is_set[new_order[z][j][0]]==0)):
                        ordered_order[new_order[z][j][0]] = 1
                        new_order[z].insert(0,new_order[z][j])
                        new_order[z].pop(j+1)
                        sort_order(z,0,1,1)
            j += 1
            
        j = 0
        while j < len_order_now:
            rows_set = np.where(BOM_set[:,1] == new_order[z][j][4])
            sort_flag = 0
            if (len(rows_set[0])==0):
                if (ordered_order[new_order[z][j][0]]==0):
                    sort_flag = check_table_size(z,j,new_order[z][j][1],1)
                if (sort_flag>0):
                    ordered_order[new_order[z][j][0]] = 1
                    new_order[z].insert(0,new_order[z][j])
                    new_order[z].pop(j+1)
                    sort_order(z,0,1,1)
            j += 1
            
        j = 0
        while j < len_order_now:
            rows_set = np.where(BOM_set[:,1] == new_order[z][j][4])
            if (len(rows_set[0])==0):
                if (len(order_capacity[new_order[z][j][0]])==1):
                    if (ordered_order[new_order[z][j][0]]==0):
                        ordered_order[new_order[z][j][0]] = 1
                        new_order[z].insert(0,new_order[z][j])
                        new_order[z].pop(j+1)
                        sort_order(z,0,1,1)
            j += 1
                
def make_OT_schedule(item_for_OT, item_for_add_table):
    arr_for_OT = []
    for i in range(len(item_for_OT)):
        lowest = -1
        table_id = -1
        new = 0
        for j in range(len(item_for_OT[i][2])):
            found = 0
            for k in range(len(arr_for_OT)):
                if (arr_for_OT[k][0]==item_for_OT[i][2][j]):
                    found = 1
                    if ((lowest == -1)|(lowest > arr_for_OT[k][2])):
                        lowest = arr_for_OT[k][2]
                        table_id = k
            if (found == 0):
                arr2 = []
                arr2.append(item_for_OT[i][2][j])
                
                arr4 = []
                arr4.append(item_for_OT[i][0])
                arr4.append(item_for_OT[i][3])
                
                arr3 = []
                arr3.append(arr4)
                
                arr2.append(arr3)
                arr2.append(item_for_OT[i][3])
                arr_for_OT.append(arr2)
                new = 1
                break
        if (new == 0):
            arr3 = []
            arr3.append(item_for_OT[i][0])
            arr3.append(item_for_OT[i][3])
            arr_for_OT[table_id][1].append(arr3)
            arr_for_OT[table_id][2]+=item_for_OT[i][3]
    
    arr = []        
    for i in range(len(item_for_add_table)):
        lowest = -1
        table_id = -1
        new = 0
        for j in range(len(item_for_add_table[i][2])):
            found = 0
            for k in range(len(arr)):
                if (arr[k][0]==item_for_add_table[i][2][j]):
                    found = 1
                    if ((lowest == -1)|(lowest > arr[k][2])):
                        lowest = arr[k][2]
                        table_id = k
            if (found == 0):
                arr2 = []
                arr2.append(item_for_add_table[i][2][j])
                
                arr4 = []
                arr4.append(item_for_add_table[i][0])
                arr4.append(item_for_add_table[i][3])
                
                arr3 = []
                arr3.append(arr4)
                
                arr2.append(arr3)
                arr2.append(item_for_add_table[i][3])
                arr.append(arr2)
                new = 1
                break
        if (new == 0):
            arr3 = []
            arr3.append(item_for_add_table[i][0])
            arr3.append(item_for_add_table[i][3])
            arr[table_id][1].append(arr3)
            arr[table_id][2]+=item_for_add_table[i][3]
            
    def get_table(arr):
        return arr[0]
    arr.sort(key=get_table)
    arr_for_OT.sort(key=get_table)
    print ('')
    print ('\n======== FOR THE NEXT ORDER ========\n')
    idx = 0
    while idx<len(arr_need_OT):
        rows = np.where(BOM_set[:,1] == arr_need_OT[idx][0])
        if (len(rows[0])>0):
            arr_need_OT.pop(idx)
            idx-=1
        idx+=1
    printX3 (arr_need_OT)
    
    arr_table_load = []
    
    for i in range(len(table_calendar_load_box)):
        if (table_list[i][0][2]!='C'):
            idx_table = -1
            for j in range(len(arr_table_load)):
                if (arr_table_load[j][0]==table_list[i][0][0:2]):
                    idx_table = j
                    arr_table_load[j][1]+=1
                    break
            if (idx_table==-1):
                arr_temp = []
                arr_temp.append(table_list[i][0][0:2])
                arr_temp.append(1)
                arr_temp.append(0)
                arr_table_load.append(arr_temp)
                idx_table = len(arr_table_load)-1
                
            for j in range(len(table_calendar_load_box[i])):
                arr_table_load[idx_table][2]+=table_calendar_load_box[i][j]
    
    for i in range(len(arr)):
        if (arr[i][0][2]!='C'):
            idx_table = -1
            for j in range(len(arr_table_load)):
                if (arr_table_load[j][0]==arr[i][0][0:2]):
                    idx_table = j
                    break
                
            arr_table_load[idx_table][2]+=arr[i][2]

    table_list_new = []
    for i in range(len(set_up_table)):
        table_group_name = ''
        if (isinstance(set_up_table[i][0][1],int)):
            table_group_name = set_up_table[i][0][0:1]
        else:
            table_group_name = set_up_table[i][0][0:2]
            
        conveyor = 0
        if (set_up_table[i][0][2]=='C'):
            conveyor = 1
            
        found = False
        for j in range(len(table_list_new)):
            if ((table_group_name==table_list_new[j][0])&(conveyor==table_list_new[j][3])):
                found = True
                table_list_new[j][1]+=1
                
        if (found==False):
            arr_1 = []
            arr_1.append(table_group_name)
            arr_1.append(1)
            arr_1.append(set_up_table[i][1])
            arr_1.append(conveyor)
            arr_1.append(set_up_table[i][2])
            table_list_new.append(arr_1)

    for i in range(len(arr_table_load)):
        table_count = 0
        for j in range(len(wl)):
            if ((wl[j,0][0:2]==arr_table_load[i][0])&(wl[j,0][2]!='C')):
                table_count+=1
                sum_temp = 0
                day_temp = 0
                for k in range(target_day):
                    if (wl[j,k+1]>0):
                        sum_temp+=wl[j,k+1]
                        day_temp+=1
                if (len(arr_table_load[i])==3):
                    arr_table_load[i].append(sum_temp/day_temp)
                    arr_table_load[i].append(day_temp)
                else:
                    arr_table_load[i][3]+=sum_temp/day_temp
                    arr_table_load[i][4]+=day_temp
        arr_table_load[i][3]/=table_count
        arr_table_load[i][4]/=table_count
    
    print ('\n======== TABLE ADDITION ========\n')
    print('REMOVE THIS TABLE:')
    over_table = 0
    total_remove = 0
    for i in range(len(arr_table_load)):
        if (arr_table_load[i][1]>math.ceil(arr_table_load[i][2]/arr_table_load[i][4]/0.9)):
            over_table+=(arr_table_load[i][1]-math.ceil(arr_table_load[i][2]/arr_table_load[i][4]/0.9))
            total_remove +=(arr_table_load[i][1]-math.ceil(arr_table_load[i][2]/arr_table_load[i][4]/0.9))
            print(arr_table_load[i][0],':',arr_table_load[i][1],'->',math.ceil(arr_table_load[i][2]/arr_table_load[i][4]/0.9),'= -',arr_table_load[i][1]-math.ceil(arr_table_load[i][2]/arr_table_load[i][4]/0.9))
            for j in range(len(table_list_new)):
                if (table_list_new[j][0]==arr_table_load[i][0]):
                    if (table_list_new[j][3]==0):
                        table_list_new[j][1]=math.ceil(arr_table_load[i][2]/arr_table_load[i][4]/0.9)
                        break
                    
    print('TOTAL: ', -1*over_table,'\n')
    
    print('ADD THIS TABLE:')
    total_add = 0
    for i in range(len(arr_table_load)):
        if ((arr_table_load[i][1]<math.floor(arr_table_load[i][2]/arr_table_load[i][4]))&(arr_table_load[i][3]<=1)):
            over_table-=(math.ceil(arr_table_load[i][2]/arr_table_load[i][4])-arr_table_load[i][1])
            total_add+=(math.ceil(arr_table_load[i][2]/arr_table_load[i][4])-arr_table_load[i][1])
            print(arr_table_load[i][0],':',arr_table_load[i][1],'->',math.ceil(arr_table_load[i][2]/arr_table_load[i][4]),'= +',math.ceil(arr_table_load[i][2]/arr_table_load[i][4])-arr_table_load[i][1])
            for j in range(len(table_list_new)):
                if (table_list_new[j][0]==arr_table_load[i][0]):
                    if (table_list_new[j][3]==0):
                        table_list_new[j][1]=math.ceil(arr_table_load[i][2]/arr_table_load[i][4])
                        break
                    
    print('TOTAL: ', -1*over_table)
    
    if ((total_add==0)&(len(arr)>0)):
        print('\n======== TRY TO ADD OVER TIME ========\n')
        
        arr_OT_print = []
        for i in range(len(arr)):
            found = False
            for j in range(len(arr_OT_print)):
                if (arr_OT_print[j][0]==arr[i][0][0:2]):
                    found = True
                    arr_OT_print[j][1] += arr[i][2]
                    break
            if (found==False):
                arr_temp = []
                arr_temp.append(arr[i][0][0:2])
                arr_temp.append(arr[i][2])
                arr_OT_print.append(arr_temp)
        
        printX3(arr_OT_print)
    
    for i in range(len(table_list_new)):
        if (len(table_list_new[i][0])>1):
            if (table_list_new[i][0][1]=='0'):
                table_list_new[i][0]=table_list_new[i][0][0]
    
    if ((total_remove>0)|(total_add>0)):
        print('\n======== NEW TABLE LIST ========\n')
        printX3(table_list_new)
    arr = []

    total_table = len(wl)
    daily_load = []
    daily_free = []
    active_day = []
    total_load = 0
    for i in range(target_day):
        arr = []
        arr.append(i)
        arr.append(0)
        daily_load.append(arr)
        daily_free += [len(wl)]
        
    for i in range(len(wl)):
        arr = []
        arr2 = []
        arr2.append(i)
        arr2.append(wl[i,0])
        arr.append(arr2)
        arr.append(0)
        arr.append([])
        arr.append([])
        active_day.append(arr)
        for j in range(target_day):
            if (table_calendar_load_box[i][j]>0):
                daily_free[j] -= 1
                total_load += 1
    
    for i in range(target_day):
        if (daily_free[i]==len(wl)):
            daily_free[i] = 0
        
    for i in range(len(wl)):
        active_day_temp = 0
        holiday_count = 0
        arr_day = []
        for j in range(target_day):
            if ((table_calendar_load_box[i][j]>0)|(wl[i,j+1]==0)):
                active_day_temp += 1
                if (wl[i,j+1]==0):
                    holiday_count+=1
                else:
                    arr_day.append(j)
        active_day[i][1]=active_day_temp-holiday_count
        active_day[i][2]=arr_day
        for j in range(target_day):
            if (table_calendar_load_box[i][j]>0):
                daily_load[j][1] += 1
    
    active_day = sorted(active_day, key=lambda x: x[1])
    
    i = 0
    while i<len(daily_load):
        if (daily_load[i][1]==0):
            daily_load.pop(i)
            i-=1
        i+=1
    
    for i in range(len(active_day)):
        if ((active_day[i][1] == len(active_day[i][2]))&(active_day[i][1]<10)&(len(active_day[i][3])==0)):
            avail_to_move = True
            day_to_move = active_day[i][1]
            for j in range(len(active_day[i][2])):
                for k in range(len(table_calendar_box[active_day[i][0][0]][active_day[i][2][j]])):
                    rows_jig = np.where(jig_qty1[:,1] == table_calendar_box[active_day[i][0][0]][active_day[i][2][j]][k][0])
                    rows_set = np.where(BOM_set[:,0] == table_calendar_box[active_day[i][0][0]][active_day[i][2][j]][k][0])
                    rows_set2 = np.where(BOM_set[:,1] == table_calendar_box[active_day[i][0][0]][active_day[i][2][j]][k][0])
                    need_temporary = False
                    for l in range(len(stock_fg)):
                        if (stock_fg[l,0]==table_calendar_box[active_day[i][0][0]][active_day[i][2][j]][k][0]):
                            if (temporary_fg_need_part[l]==1):
                                need_temporary = True
                            break
                    if ((len(rows_jig[0])>0)|(len(rows_set[0])>0)|(len(rows_set2[0])>0)|(need_temporary==True)):
                        avail_to_move = False
                        break
                if (avail_to_move==False):
                    break
            if (avail_to_move):
                arr_day=[]
                daily_load = sorted(daily_load, key=lambda x: x[1])
                for j in range(len(daily_load)):
                    if (wl[active_day[i][0][0]][daily_load[j][0]+1]>0):
                        arr_temp = []
                        arr_temp.append(daily_load[j][0]+1)
                        arr_day.append(arr_temp)
                        day_to_move -= 1
                        if (day_to_move==0):
                            break
                
                for j in range(len(active_day[i][2])):
                    for k in range(len(daily_load)):
                        if (daily_load[k][0]==active_day[i][2][j]):
                            daily_load[k][1]-=1
                            break
                        
                for j in range(len(arr_day)):
                    for k in range(len(daily_load)):
                        if (daily_load[k][0]==arr_day[j][0]-1):
                            daily_load[k][1]+=1
                            break
                active_day[i][2]=arr_day
    
#     print('\n================== MOVE THESE WORKLOADS ==================')                    
#     
#     new_workload = []
#     for i in range(len(table_list)):
#         for j in range(len(active_day)):
#             if (active_day[j][0][0]==i):
#                 arr = []
#                 if (isinstance(active_day[j][2][0],int)):
#                     for k in range(target_day_2):
#                         arr.append(wl[i,k+1])
#                 else:
#                     for k in range(target_day_2):
#                         found = False
#                         for l in range(len(active_day[j][2])):
#                             if (active_day[j][2][l][0]-1==k):
#                                 found = True
#                                 break
#                         if (found==True):
#                             arr.append('100%'.strip('"\''))
#                         else:
#                             arr.append('0%'.strip('"\''))
#                 new_workload.append(arr)
#                 break
#     print('\n')
#     printX3(new_workload)
    print ('\nNEED OVER TIME, PLEASE ADD THE WORKLOAD AND RUN AGAIN')
            
if (operation_mode == 1):
    for i in range (len(table_list)):
        print (table_list[i][0])
elif (operation_mode==2):
    print('Running...')
    print('')
    max_attempt = 1
    for i in range(len(new_order)):
        print('----- ',i,' -----')
        make_schedule(start_day,i, 0)
        break_all_ops=0
        attempt = 0
        load_saved_data()
    if(break_all_ops==0):
        index_dev = -1
        max_dev = 2147483647
        for k_d in range(print_comb):
            if (deviation_sum[k_d][1]<max_dev):
                max_dev = deviation_sum[k_d][1]
                index_dev = k_d
        print_to_excel(stock_part_edit, stock_fg, table_calendar_box, table_calendar_load_box, order_capacity)
        print ('\nDONE!!\n')
        
        for a in range(len(table_calendar_time)):
            for b in range(len(table_calendar_time[a])):
                for c in range(len(table_calendar_time[a][b])):
                    if (table_calendar_time[a][b][c][1]>8*3600+435*60):
                        if ((set_up_table[a][0][2]!='C')&(wl[a][b+1]==1)):
                            print('ERROR!! TOO LONG',set_up_table[a][0],'-',b,' | ', table_calendar_time[a][b][c])
                    for d in range(len(table_calendar_time[a][b])):
                        if (table_calendar_time[a][b][c][2]!=table_calendar_time[a][b][d][2]):
                            if (is_intersect(table_calendar_time[a][b][c][0],table_calendar_time[a][b][c][1],table_calendar_time[a][b][d][0],table_calendar_time[a][b][d][1])):
                                print('ERROR!! INTERSECT',set_up_table[a][0],'-',b,' | ', table_calendar_time[a][b][c],'-',table_calendar_time[a][b][d])                
        
        if (need_part == 1):
            print ('\n======== PART NOT ENOUGH ========\n')
            arr_need_part = sorted(arr_need_part, key=lambda x: x[0])
            printX3 (arr_need_part)   
        if (need_OT==1):
            item_for_OT = []
            item_for_add_table = []
            for z in range (len(new_order)):
                for idx_i in range(len(new_order[z])):
                    if (fg_need_OT[new_order[z][idx_i][0]][2]>0):
                        arr = []
                        for i_p in range(len(order_capacity[new_order[z][idx_i][0]])):
                            arr.append(order_capacity[new_order[z][idx_i][0]][i_p][1])
                        arr2 = []
                        arr2.append(new_order[z][idx_i][0])
                        arr2.append(fg_need_OT[new_order[z][idx_i][0]][2])
                        arr2.append(arr)
                        cal_qty_box = math.ceil(fg_need_OT[new_order[z][idx_i][0]][2]/box_fg[new_order[z][idx_i][8]])*box_fg[new_order[z][idx_i][8]]
                        cal_cap_box = math.floor((order_capacity[new_order[z][idx_i][0]][0][3])/box_fg[new_order[z][idx_i][8]])*box_fg[new_order[z][idx_i][8]]
                        arr2.append(cal_qty_box/cal_cap_box)
                        item_for_add_table.append(arr2)
                    
                    if (fg_need_OT[new_order[z][idx_i][0]][1]>0):
                        arr = []
                        for i_p in range(len(order_capacity[new_order[z][idx_i][0]])):
                            arr.append(order_capacity[new_order[z][idx_i][0]][i_p][1])
                        arr2 = []
                        arr2.append(new_order[z][idx_i][0])
                        arr2.append(fg_need_OT[new_order[z][idx_i][0]][1])
                        arr2.append(arr)
                        cal_qty_box = math.ceil(fg_need_OT[new_order[z][idx_i][0]][1]/box_fg[new_order[z][idx_i][8]])*box_fg[new_order[z][idx_i][8]]
                        cal_cap_box = math.floor((order_capacity[new_order[z][idx_i][0]][0][3])/box_fg[new_order[z][idx_i][8]])*box_fg[new_order[z][idx_i][8]]
                        arr2.append(cal_qty_box/cal_cap_box)                                    
                        item_for_OT.append(arr2)
            
            make_OT_schedule(item_for_OT, item_for_add_table)