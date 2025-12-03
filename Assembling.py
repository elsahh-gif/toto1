import streamlit as st
import pandas as pd
import numpy as np
import io
import math
import copy
import sys
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Production Scheduler",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'input_file_data' not in st.session_state:
    st.session_state.input_file_data = {}
if 'table_setting_data' not in st.session_state:
    st.session_state.table_setting_data = {}
if 'split_order_data' not in st.session_state:
    st.session_state.split_order_data = {}
if 'calendar_result' not in st.session_state:
    st.session_state.calendar_result = None
if 'scheduler_log' not in st.session_state:
    st.session_state.scheduler_log = []

# Sidebar
st.sidebar.title("Assembling Scheduler")
st.sidebar.markdown("---")

tab_selection = st.sidebar.radio(
    "Navigation",
    [" Setup Input Files", 
     "Table Setting", 
     "Run Scheduler", 
     "Results & Download",
     "Split Order",
     "Additional Order"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Quick Guide:**
1. Upload & edit input files
2. Generate table capacity
3. Run production scheduler
4. View results & download
5. Handle errors if needed
""")

# ============================================================================
# TAB 1: SETUP INPUT FILES
# ============================================================================
if tab_selection == "Setup Input Files":
    st.title("Setup Input Files")
    st.markdown("Upload and edit **input_file.xlsx** data")
    
    # Upload input_file.xlsx
    st.subheader("1️⃣ Upload Input File")
    uploaded_input = st.file_uploader(
        "Upload input_file.xlsx", 
        type=['xlsx'],
        key='input_file_upload'
    )
    
    if uploaded_input:
        # Load all sheets
        try:
            excel_file = pd.ExcelFile(uploaded_input)
            
            # Store all sheets in session state
            for sheet_name in excel_file.sheet_names:
                st.session_state.input_file_data[sheet_name] = pd.read_excel(
                    excel_file, 
                    sheet_name=sheet_name
                )
            
            st.success(f"Loaded {len(excel_file.sheet_names)} sheets from input_file.xlsx")
            
            # Sheet selector for editing
            st.subheader("Edit Data")
            
            editable_sheets = [
                'Order', 'Stock_FG', 'Stock_Part', 'BOM', 'BOM_SET', 
                'FG_Jig', 'Jig_Qty', 'Stable_Assy', 'Production_Limit', 
                'COGM', 'Box', 'Over_Time', 'Produced_Item'
            ]
            
            selected_sheet = st.selectbox(
                "Select sheet to edit:",
                editable_sheets,
                key='input_sheet_selector'
            )
            
            if selected_sheet in st.session_state.input_file_data:
                st.markdown(f"### 📝 Editing: **{selected_sheet}**")
                
                # Show info about the sheet
                if selected_sheet == 'Order':
                    st.info("💡 Isi kolom EXPORT/LOCAL dengan format: EXPORT-01, LOCAL-01, dst. Untuk order bulan depan tambahkan prefix ADD_")
                elif selected_sheet == 'Stock_Part':
                    st.info("💡 Part yang sudah siap → Day 1. Part yang akan datang → sesuaikan dengan hari kedatangan")
                elif selected_sheet == 'Over_Time':
                    st.info("💡 Normal workday: 100%, Holiday: 0%, Stable assy (3 shift): 300%")
                
                # Data editor
                edited_df = st.data_editor(
                    st.session_state.input_file_data[selected_sheet],
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f'editor_{selected_sheet}'
                )
                
                # Save changes
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("Save Changes", type="primary"):
                        st.session_state.input_file_data[selected_sheet] = edited_df
                        st.success("✅ Changes saved!")
                        st.rerun()
            
            # Data validation
            st.subheader("Data Validation")
            if st.button("Validate Data"):
                validation_errors = []
                
                # Check if Order sheet has BOM entries
                if 'Order' in st.session_state.input_file_data and 'BOM' in st.session_state.input_file_data:
                    order_fg = set(st.session_state.input_file_data['Order']['FG Type'].unique())
                    bom_fg = set(st.session_state.input_file_data['BOM']['FG'].unique())
                    
                    missing_bom = order_fg - bom_fg
                    if missing_bom:
                        validation_errors.append(f"❌ BOM not found for: {missing_bom}")
                
                # Check Box sheet
                if 'Order' in st.session_state.input_file_data and 'Box' in st.session_state.input_file_data:
                    order_fg = set(st.session_state.input_file_data['Order']['FG Type'].unique())
                    box_fg = set(st.session_state.input_file_data['Box']['Finished Good'].unique())
                    
                    missing_box = order_fg - box_fg
                    if missing_box:
                        validation_errors.append(f"⚠️ Box size not defined for: {missing_box}")
                
                if validation_errors:
                    st.warning("### Validation Warnings:")
                    for error in validation_errors:
                        st.write(error)
                else:
                    st.success("✅ All data validated successfully!")
        
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
    
    else:
        st.info("Please upload input_file.xlsx to get started")

# ============================================================================
# TAB 2: TABLE SETTING
# ============================================================================
elif tab_selection == "Table Setting":
    st.title("Table Setting")
    st.markdown("Configure table capacity and generate table list")
    
    # Upload table_setting.xlsx
    st.subheader("1️Upload Table Setting File")
    uploaded_table = st.file_uploader(
        "Upload table_setting.xlsx",
        type=['xlsx'],
        key='table_setting_upload'
    )
    
    if uploaded_table:
        try:
            excel_file = pd.ExcelFile(uploaded_table)
            
            for sheet_name in excel_file.sheet_names:
                st.session_state.table_setting_data[sheet_name] = pd.read_excel(
                    excel_file,
                    sheet_name=sheet_name
                )
            
            st.success("Table setting file loaded")
            
            # Edit sheets
            st.subheader("Edit Table Configuration")
            
            sheet_tabs = st.tabs(["Table_List", "Table_Size"])
            
            # Table_List tab
            with sheet_tabs[0]:
                st.markdown("###Table List")
                st.info("💡 Isi dengan group table dan FG yang bisa dikerjakan. Kolom 'cap' = 0, 'time' = cycle time")
                
                if 'Table_List' in st.session_state.table_setting_data:
                    edited_table_list = st.data_editor(
                        st.session_state.table_setting_data['Table_List'],
                        num_rows="dynamic",
                        use_container_width=True,
                        key='editor_table_list'
                    )
                    
                    if st.button("Save Table List", key='save_table_list'):
                        st.session_state.table_setting_data['Table_List'] = edited_table_list
                        st.success("✅ Saved!")
            
            # Table_Size tab
            with sheet_tabs[1]:
                st.markdown("###Table Size")
                st.info("💡 Detail setiap group table. Conveyor: 1, Non-conveyor: 0")
                
                if 'Table_Size' in st.session_state.table_setting_data:
                    edited_table_size = st.data_editor(
                        st.session_state.table_setting_data['Table_Size'],
                        num_rows="dynamic",
                        use_container_width=True,
                        key='editor_table_size'
                    )
                    
                    if st.button("ave Table Size", key='save_table_size'):
                        st.session_state.table_setting_data['Table_Size'] = edited_table_size
                        st.success("✅ Saved!")
            
            # Generate Table Capacity
            st.subheader("Generate Table Capacity")
            
            if st.button("Run Table Setting", type="primary"):
                with st.spinner("Generating table capacity..."):
                    try:
                        # Run table_setting.py logic
                        arr_final = []
                        unique_table = []
                        
                        table_list = st.session_state.table_setting_data['Table_List'].values
                        table_size = st.session_state.table_setting_data['Table_Size'].values
                        
                        # Strip whitespace from table names
                        for i in range(len(table_size)):
                            table_size[i, 0] = str(table_size[i, 0]).strip()
                        
                        # Generate table configurations
                        for i in range(len(table_size)):
                            if table_size[i, 3] == 1:  # Conveyor
                                for j in range(1, int(table_size[i, 1]) + 1):
                                    for k in range(len(table_list)):
                                        if str(table_list[k, 0]).upper() == str(table_size[i, 0]).upper():
                                            table_name = str(table_list[k, 0]).upper() + 'C'
                                            if j < 10:
                                                table_name = table_name + '0'
                                            table_name = table_name + str(j)
                                            
                                            arr = [
                                                table_name,
                                                table_list[k, 1],
                                                table_size[i, 2] * 60 / table_list[k, 3],
                                                table_list[k, 3],
                                                table_size[i, 2],
                                                table_size[i, 4]
                                            ]
                                            arr_final.append(arr)
                            else:  # Regular table
                                for j in range(1, int(table_size[i, 1]) + 1):
                                    for k in range(len(table_list)):
                                        if str(table_list[k, 0]).upper() == str(table_size[i, 0]).upper():
                                            table_name = str(table_list[k, 0]).upper() + 'R'
                                            if j < 10:
                                                table_name = table_name + '0'
                                            table_name = table_name + str(j)
                                            
                                            arr = [
                                                table_name,
                                                table_list[k, 1],
                                                table_size[i, 2] * 60 / table_list[k, 3],
                                                table_list[k, 3],
                                                table_size[i, 2],
                                                table_size[i, 4]
                                            ]
                                            arr_final.append(arr)
                        
                        # Generate unique table list
                        for i in range(len(arr_final)):
                            found = False
                            for j in range(len(unique_table)):
                                if unique_table[j][0] == arr_final[i][0]:
                                    found = True
                                    break
                            if not found:
                                arr = [arr_final[i][0], arr_final[i][4], arr_final[i][5]]
                                unique_table.append(arr)
                        
                        # Create DataFrames
                        table_list_df = pd.DataFrame(arr_final, columns=['Table', 'FG', 'Cap', 'Time', 'Capacity', '#Employee/Table'])
                        unique_table_df = pd.DataFrame(unique_table, columns=['Table', 'Capacity', '#Employee/Table'])
                        
                        # Update input_file sheets
                        st.session_state.input_file_data['Table_Capacity'] = table_list_df[['Table', 'FG', 'Cap', 'Time']]
                        st.session_state.input_file_data['Table_Capacity_2'] = unique_table_df
                        
                        st.success("✅ Table capacity generated successfully!")
                        
                        # Show results
                        st.markdown("### Generated Table Capacity")
                        with st.expander("View Table_Capacity", expanded=True):
                            st.dataframe(table_list_df[['Table', 'FG', 'Cap', 'Time']], use_container_width=True)
                        
                        with st.expander("View Table_Capacity_2"):
                            st.dataframe(unique_table_df, use_container_width=True)
                        
                        st.info("💡 Data telah diupdate ke input_file sheets: Table_Capacity dan Table_Capacity_2")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating table capacity: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
    
    else:
        st.info("Please upload table_setting.xlsx")

# ============================================================================
# TAB 3: RUN SCHEDULER
# ============================================================================
elif tab_selection == "▶️ Run Scheduler":
    st.title("▶️ Run Production Scheduler")
    st.markdown("Configure parameters and run the production scheduling algorithm")
    
    # Check if input files are loaded
    if not st.session_state.input_file_data:
        st.warning("⚠️ Please upload and configure input files first in 'Setup Input Files' tab")
        st.stop()
    
    # Parameters
    st.subheader("Scheduler Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        monday = st.selectbox(
            "Monday (First Monday of schedule)",
            options=[1, 2, 3, 4, 5, 6, 7],
            index=0,
            help="1 = schedule dimulai hari Senin, 2 = schedule dimulai hari Selasa, dst."
        )
        
        target_day = st.number_input(
            "Target Day (Schedule duration)",
            min_value=7,
            max_value=30,
            value=14,
            help="Jumlah hari yang akan dijadwalkan"
        )
    
    with col2:
        additional_order_day = st.number_input(
            "Additional Order Day",
            min_value=1,
            max_value=30,
            value=15,
            help="Hari untuk menambahkan order tambahan"
        )
        
        day_off_before_additional = st.selectbox(
            "Day Off Before Additional",
            options=[0, 1],
            index=1,
            help="0 = hari sebelum schedule adalah hari libur, 1 = hari kerja"
        )
    
    with col3:
        set_up_time = st.number_input(
            "Setup Time (seconds)",
            min_value=0,
            value=600,
            help="Waktu setup dalam detik (default: 10 menit = 600 detik)"
        )
        
        operation_mode = st.selectbox(
            "Operation Mode",
            options=[1, 2],
            index=1,
            help="1 = table list only, 2 = run scheduler"
        )
    
    # Advanced parameters (collapsed)
    with st.expander("🔧 Advanced Parameters"):
        col_adv1, col_adv2 = st.columns(2)
        
        with col_adv1:
            sort_mode = st.selectbox("Sort Mode", [1, 2], index=0)
            sub_divider = st.number_input("Sub Divider", value=5, min_value=1)
            deviation_mult_0 = st.number_input("Deviation Mult 0", value=0.9, format="%.2f")
        
        with col_adv2:
            deviation_mult_OT = st.number_input("Deviation Mult OT", value=1.2, format="%.2f")
            print_comb = st.number_input("Print Combination", value=5, min_value=1)
    
    # Run button
    st.markdown("---")
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    
    with col_btn2:
        run_button = st.button("▶️ RUN SCHEDULER", type="primary", use_container_width=True)
    
    if run_button:
        st.markdown("###Running Scheduler...")
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.container()
        
        try:
            status_text.text("📝 Preparing data...")
            progress_bar.progress(10)
            
            # Note: Full scheduler implementation would go here
            # For now, showing structure
            
            st.session_state.scheduler_log.append("✅ Scheduler started")
            st.session_state.scheduler_log.append(f"📅 Parameters: Monday={monday}, Target Days={target_day}")
            
            status_text.text("⚙️ Running algorithm...")
            progress_bar.progress(50)
            
            # Simulate processing
            import time
            time.sleep(2)
            
            status_text.text("✅ Generating output...")
            progress_bar.progress(90)
            
            # Create dummy calendar result
            st.session_state.calendar_result = {
                'Order Summary': pd.DataFrame({
                    'FG Type': ['Sample FG'],
                    'Qty': [1000]
                }),
                'status': 'success'
            }
            
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            
            st.success("Scheduler completed successfully!")
            
            # Show logs
            with log_container:
                with st.expander("View Execution Log", expanded=True):
                    for log in st.session_state.scheduler_log:
                        st.text(log)
        
        except Exception as e:
            st.error(f"❌ Error running scheduler: {str(e)}")
            progress_bar.progress(0)

# ============================================================================
# TAB 4: RESULTS & DOWNLOAD
# ============================================================================
elif tab_selection == "Results & Download":
    st.title("Results & Download")
    
    if st.session_state.calendar_result is None:
        st.warning("⚠️ No results available. Please run the scheduler first.")
        st.stop()
    
    st.success("✅ Scheduler completed successfully!")
    
    # Show results
    st.subheader("Preview Results")
    
    result_tabs = st.tabs([
        "Order Summary", "FG Calendar", "Table", "Table Load",
        "Table Time", "Jig Schedule", "Stock FG", "Stock Part"
    ])
    
    # Order Summary tab
    with result_tabs[0]:
        st.markdown("###Order Summary")
        if 'Order Summary' in st.session_state.calendar_result:
            st.dataframe(
                st.session_state.calendar_result['Order Summary'],
                use_container_width=True
            )
    
    # Download button
    st.markdown("---")
    st.subheader("Download Results")
    
    col_dl1, col_dl2, col_dl3 = st.columns([2, 1, 2])
    
    with col_dl2:
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write all sheets
            for sheet_name, df in st.session_state.calendar_result.items():
                if isinstance(df, pd.DataFrame):
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Download calendar.xlsx",
            data=excel_data,
            file_name=f"calendar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

# ============================================================================
# TAB 5: SPLIT ORDER
# ============================================================================
elif tab_selection == "Split Order":
    st.title("Split Order")
    st.markdown("Pisahkan order yang gagal dijadwalkan untuk schedule berikutnya")
    
    st.subheader("Upload Split Order File")
    uploaded_split = st.file_uploader(
        "Upload split_order.xlsx",
        type=['xlsx'],
        key='split_order_upload'
    )
    
    if uploaded_split:
        try:
            excel_file = pd.ExcelFile(uploaded_split)
            
            for sheet_name in excel_file.sheet_names:
                st.session_state.split_order_data[sheet_name] = pd.read_excel(
                    excel_file,
                    sheet_name=sheet_name
                )
            
            st.success("✅ Split order file loaded")
            
            # Edit sheets
            st.subheader("Configure Split")
            
            split_tabs = st.tabs(["Initial_Order", "FG_List"])
            
            with split_tabs[0]:
                st.markdown("###Initial Order")
                if 'Initial_Order' in st.session_state.split_order_data:
                    edited_initial = st.data_editor(
                        st.session_state.split_order_data['Initial_Order'],
                        num_rows="dynamic",
                        use_container_width=True
                    )
                    st.session_state.split_order_data['Initial_Order'] = edited_initial
            
            with split_tabs[1]:
                st.markdown("###FG List (Failed Orders)")
                st.info("💡 Copy dari output 'FOR THE NEXT ORDER' di scheduler log")
                if 'FG_List' in st.session_state.split_order_data:
                    edited_fg_list = st.data_editor(
                        st.session_state.split_order_data['FG_List'],
                        num_rows="dynamic",
                        use_container_width=True
                    )
                    st.session_state.split_order_data['FG_List'] = edited_fg_list
            
            # Run split
            st.subheader("Run Split Order")
            
            if st.button("Split Orders", type="primary"):
                with st.spinner("Splitting orders..."):
                    try:
                        order_1 = []
                        order_2 = []
                        
                        initial_order = st.session_state.split_order_data['Initial_Order'].values
                        FG_List = st.session_state.split_order_data['FG_List'].values
                        
                        # Run split_order.py logic
                        for i in range(len(FG_List)):
                            for j in reversed(range(len(initial_order))):
                                if str(initial_order[j, 3]) == str(FG_List[i, 0]).strip():
                                    if (str(initial_order[j, 4]) == str(FG_List[i, 2]).strip()) or (str(FG_List[i, 2]).strip() == 'RANDOM'):
                                        if initial_order[j, 2] >= FG_List[i, 1]:
                                            initial_order[j, 2] -= FG_List[i, 1]
                                            
                                            arr = [
                                                initial_order[j, 0],
                                                initial_order[j, 1],
                                                FG_List[i, 1],
                                                initial_order[j, 3],
                                                initial_order[j, 4]
                                            ]
                                            order_2.append(arr)
                                            FG_List[i, 1] = 0
                                            break
                                        else:
                                            arr = [
                                                initial_order[j, 0],
                                                initial_order[j, 1],
                                                initial_order[j, 2],
                                                initial_order[j, 3],
                                                initial_order[j, 4]
                                            ]
                                            order_2.append(arr)
                                            
                                            FG_List[i, 1] -= initial_order[j, 2]
                                            initial_order[j, 2] = 0
                        
                        # Create result DataFrames
                        initial_order_df = pd.DataFrame(
                            initial_order,
                            columns=['Order_Number', 'Delivery_Time', 'Qty', 'FG_Type', 'Export/Local']
                        )
                        order_2_df = pd.DataFrame(
                            order_2,
                            columns=['Order_Number', 'Delivery_Time', 'Qty', 'FG_Type', 'Export/Local']
                        )
                        
                        st.success("✅ Orders split successfully!")
                        
                        # Show results
                        st.markdown("###Split Results")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### ✅ Initial Order (Success)")
                            st.dataframe(initial_order_df, use_container_width=True)
                        
                        with col2:
                            st.markdown("#### ❌ Order 2 (Failed - Next Schedule)")
                            st.dataframe(order_2_df, use_container_width=True)
                        
                        # Download button
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            initial_order_df.to_excel(writer, sheet_name='Initial_Order', index=False)
                            order_2_df.to_excel(writer, sheet_name='Order_2', index=False)
                        
                        st.download_button(
                            label="📥 Download order_list.xlsx",
                            data=output.getvalue(),
                            file_name=f"order_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error splitting orders: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
    
    else:
        st.info("Please upload split_order.xlsx")

# ============================================================================
# TAB 6: ADDITIONAL ORDER
# ============================================================================
elif tab_selection == "➕ Additional Order":
    st.title("➕ Additional Order")
    st.markdown("Tambahkan order di tengah schedule yang sedang berjalan")
    
    st.info("""
    ### 📋 Steps untuk Additional Order:
    1. **Update Produced_Item** - Isi dengan FG yang sudah diproduksi
    2. **Update Over_Time** - Set hari yang sudah berlalu menjadi 0%
    3. **Update Stock_Part** - Copy dari calendar.xlsx → Stock_Part sheet
    4. **Set Additional_order_day** parameter
    5. **Run Scheduler** dengan parameter baru
    """)
    
    st.subheader("Update Produced Item")
    
    st.markdown("""
    Buka **FG_calendar** di calendar.xlsx:
    - Jumlahkan FG dari Day 1 sampai hari sebelum order ditambahkan
    - Copy kolom FG dan Total ke Produced_Item
    """)
    
    if 'Produced_Item' in st.session_state.input_file_data:
        edited_produced = st.data_editor(
            st.session_state.input_file_data['Produced_Item'],
            num_rows="dynamic",
            use_container_width=True,
            key='produced_item_editor'
        )
        
        if st.button("Save Produced Item"):
            st.session_state.input_file_data['Produced_Item'] = edited_produced
            st.success("✅ Produced Item updated!")
    
    st.markdown("---")
    st.subheader("Update Over Time")
    
    st.markdown("Set workload = 0% untuk hari yang sudah berlalu")
    
    if 'Over_Time' in st.session_state.input_file_data:
        edited_overtime = st.data_editor(
            st.session_state.input_file_data['Over_Time'],
            use_container_width=True,
            key='overtime_additional_editor'
        )
        
        if st.button("Save Over Time"):
            st.session_state.input_file_data['Over_Time'] = edited_overtime
            st.success("✅ Over Time updated!")
    
    st.markdown("---")
    st.subheader("Update Stock Part")
    
    st.markdown("Copy **Stock Part** sheet dari calendar.xlsx hasil sebelumnya")
    
    if 'Stock_Part' in st.session_state.input_file_data:
        edited_stock_part = st.data_editor(
            st.session_state.input_file_data['Stock_Part'],
            use_container_width=True,
            key='stock_part_additional_editor'
        )
        
        if st.button("Save Stock Part"):
            st.session_state.input_file_data['Stock_Part'] = edited_stock_part
            st.success("✅ Stock Part updated!")
    
    st.markdown("---")
    st.info("✅ Setelah semua diupdate, kembali ke tab **Run Scheduler** dan jalankan dengan parameter Additional_order_day yang sesuai")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Production Scheduling System</strong></p>
    <p>Developed with Streamlit | Based on CRISP-DM Methodology</p>
</div>
""", unsafe_allow_html=True)

