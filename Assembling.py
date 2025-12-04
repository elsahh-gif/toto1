import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import sys
import json

# Check dependencies
try:
    import openpyxl
except ImportError:
    st.error("Missing dependency: openpyxl")
    st.info("Add this to requirements.txt file in your repo:")
    st.code("""streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0""")
    st.stop()

# Set pandas display options to show all rows
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Page config
st.set_page_config(
    page_title="Production Scheduler",
    page_icon="chart_with_upwards_trend",
    layout="wide"
)

# Title
st.title("Assembling Scheduler")
st.markdown("Upload Excel files - Run Scheduler - Edit Results - Download")
st.markdown("---")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'files_loaded' not in st.session_state:
    st.session_state.files_loaded = False

# STEP 1: FILE UPLOAD
st.header("Step 1: Upload Files")

col1, col2, col3, col4 = st.columns(4)

with col1:
    input_file = st.file_uploader("input_file.xlsx", type=['xlsx'], key='input')
    
with col2:
    table_setting = st.file_uploader("table_setting.xlsx", type=['xlsx'], key='table_setting')
    
with col3:
    table_list = st.file_uploader("table_list.xlsx", type=['xlsx'], key='table_list')
    
with col4:
    order_list = st.file_uploader("order_list.xlsx", type=['xlsx'], key='order_list')

# Check if all files uploaded
all_files_uploaded = all([input_file, table_setting, table_list, order_list])

if all_files_uploaded:
    st.success("All files uploaded successfully")
    
    # Load files into session state
    if not st.session_state.files_loaded:
        with st.spinner("Loading files..."):
            try:
                # Load input_file sheets
                st.session_state.input_data = {}
                excel_file = pd.ExcelFile(input_file)
                for sheet in excel_file.sheet_names:
                    st.session_state.input_data[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
                
                # Load table_setting
                st.session_state.table_setting_data = {}
                excel_file = pd.ExcelFile(table_setting)
                for sheet in excel_file.sheet_names:
                    st.session_state.table_setting_data[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
                
                # Load table_list
                st.session_state.table_list_data = {}
                excel_file = pd.ExcelFile(table_list)
                for sheet in excel_file.sheet_names:
                    st.session_state.table_list_data[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
                
                # Load order_list
                st.session_state.order_list_data = {}
                excel_file = pd.ExcelFile(order_list)
                for sheet in excel_file.sheet_names:
                    st.session_state.order_list_data[sheet] = pd.read_excel(excel_file, sheet_name=sheet)
                
                st.session_state.files_loaded = True
                st.success("Files loaded successfully!")
                
            except ImportError as e:
                st.error(f"Missing Python package: {str(e)}")
                st.info("Make sure requirements.txt exists in your repo with:")
                st.code("""streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0""")
                st.warning("After adding requirements.txt, redeploy the app from Streamlit Cloud dashboard")
                
            except Exception as e:
                st.error(f"Error loading files: {str(e)}")
                st.info("Please check:")
                st.markdown("""
                - File format is .xlsx
                - Files are not corrupted
                - Files have valid sheets
                """)

# ============================================================================
# STEP 2: RUN SCHEDULER
# ============================================================================
if all_files_uploaded and st.session_state.files_loaded:
    st.markdown("---")
    st.header("Step 2: Run Scheduler")
    
    # Parameters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        monday = st.selectbox("Monday (1-7)", [1,2,3,4,5,6,7], index=0)
    with col2:
        target_day = st.number_input("Target Days", value=14, min_value=1, max_value=30)
    with col3:
        set_up_time = st.number_input("Setup Time (seconds)", value=600, min_value=0)
    with col4:
        operation_mode = st.selectbox("Operation Mode", [1, 2], index=1)
    
    # Run button
    if st.button("RUN SCHEDULER", type="primary", use_container_width=True):
        with st.spinner("Running scheduler... Please wait..."):
            try:
                # =============================================================
                # TODO: INTEGRATE ASSEMBLING SCHEDULER HERE
                # =============================================================
                # Steps to integrate:
                # 1. Copy all functions from Assembling_Scheduler.py
                # 2. Load data from st.session_state
                # 3. Run scheduler algorithm
                # 4. Store results in st.session_state.results
                #
                # For now: Using dummy data with real structure
                # =============================================================
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Load input data
                status_text.text("Loading input data...")
                progress_bar.progress(10)
                
                # Get data from session state
                input_data = st.session_state.input_data
                table_setting_data = st.session_state.table_setting_data
                table_list_data = st.session_state.table_list_data
                order_list_data = st.session_state.order_list_data
                
                # Step 2: Process table setting
                status_text.text("Processing table settings...")
                progress_bar.progress(20)
                
                # Step 3: Initialize scheduler
                status_text.text("Initializing scheduler...")
                progress_bar.progress(30)
                
                # Step 4: Run main scheduling algorithm
                status_text.text("Running scheduling algorithm...")
                progress_bar.progress(50)
                
                # SIMULATE PROCESSING
                import time
                time.sleep(1)
                
                # Step 5: Generate results
                status_text.text("Generating results...")
                progress_bar.progress(80)
                
                # Create realistic dummy results (matching real calendar.xlsx structure)
                # Generate more rows to simulate real data
                
                # Order Summary (1100+ rows)
                fg_types = ['12149RXA', '14283BC', '15695XA', 'TC505#W', 'TX471SPN']
                order_summary_rows = []
                for i, fg in enumerate(fg_types * 225):  # 1125 rows
                    order_summary_rows.append({
                        'FG Type': fg,
                        'EXPORT/LOCAL': 'EXPORT-01',
                        'Qty Assy': np.random.randint(0, 1000),
                        'Order Qty': np.random.randint(100, 8000),
                        'Stock Qty': np.random.randint(0, 1000),
                        'Cancel Assy Qty': 0,
                        'Over Production Qty': 0,
                        'COGM': np.random.uniform(20000, 300000),
                        'TOTAL COGM': np.random.uniform(1000000, 200000000)
                    })
                
                # FG Calendar (885 rows with 14 days)
                fg_calendar_rows = []
                for fg in fg_types * 177:  # 885 rows
                    row = {'FG': fg}
                    for day in range(1, 15):
                        row[f'Day {day}'] = np.random.randint(0, 1000)
                    fg_calendar_rows.append(row)
                
                # Table (73 rows)
                table_names = [f'{i}AR{j:02d}' for i in range(1, 4) for j in range(1, 25)]
                table_rows = []
                for table in table_names[:73]:
                    row = {'Table': table}
                    for day in range(1, 15):
                        # Convert list to string to avoid pyarrow error
                        items = [[fg_types[i % len(fg_types)], np.random.randint(1, 100)] 
                                for i in range(np.random.randint(0, 3))]
                        row[f'Day {day}'] = str(items)
                    table_rows.append(row)
                
                # Table Load (73 rows)
                table_load_rows = []
                for table in table_names[:73]:
                    row = {'Table': table}
                    for day in range(1, 15):
                        row[f'Day {day}'] = np.random.uniform(0, 1)
                    table_load_rows.append(row)
                
                # Table Time (73 rows)
                table_time_rows = []
                for table in table_names[:73]:
                    row = {'Table': table}
                    for day in range(1, 15):
                        # Convert list to string to avoid pyarrow error
                        times = [[28800 + i*1000, 54000 + i*1000, fg_types[i % len(fg_types)], 
                                 np.random.randint(1, 100)] for i in range(np.random.randint(0, 2))]
                        row[f'Day {day}'] = str(times)
                    table_time_rows.append(row)
                
                # Jig Schedule (946 rows)
                jig_rows = []
                for i in range(946):
                    row = {'Jig': f'JIG-{i+1:05d}'}
                    for day in range(1, 12):
                        row[f'Day {day}'] = str([])
                    jig_rows.append(row)
                
                # Stock FG (1117 rows)
                stock_fg_rows = []
                for i, fg in enumerate(fg_types * 224):  # 1120 rows
                    stock_fg_rows.append({
                        'FG Type': fg,
                        'Qty': np.random.randint(0, 1000)
                    })
                
                # Stock Part (47 rows)
                parts = [f'PART{i:03d}' for i in range(47)]
                stock_part_rows = []
                for part in parts:
                    row = {'Part': part}
                    for day in range(1, 15):
                        row[f'Day {day}'] = np.random.randint(0, 20000)
                    stock_part_rows.append(row)
                
                # Create DataFrames
                st.session_state.results = {
                    'Order Summary': pd.DataFrame(order_summary_rows),
                    'FG Calendar': pd.DataFrame(fg_calendar_rows),
                    'Table': pd.DataFrame(table_rows),
                    'Table Load': pd.DataFrame(table_load_rows),
                    'Table Time': pd.DataFrame(table_time_rows),
                    'Jig Schedule': pd.DataFrame(jig_rows),
                    'Stock FG': pd.DataFrame(stock_fg_rows),
                    'Stock Part': pd.DataFrame(stock_part_rows)
                }
                
                # Complete
                status_text.text("Scheduler completed!")
                progress_bar.progress(100)
                time.sleep(0.5)
                status_text.empty()
                progress_bar.empty()
                
                st.success("Scheduler completed successfully!")
                st.info("NOTE: This is simulated data. To use real scheduler, integrate Assembling_Scheduler.py code at line 142")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error running scheduler: {str(e)}")
                st.exception(e)

# ============================================================================
# STEP 3: VIEW & EDIT RESULTS
# ============================================================================
if st.session_state.results is not None:
    st.markdown("---")
    st.header("Step 3: View and Edit Results")
    
    # Create tabs for each sheet
    sheet_names = list(st.session_state.results.keys())
    tabs = st.tabs(sheet_names)
    
    for idx, (sheet_name, tab) in enumerate(zip(sheet_names, tabs)):
        with tab:
            st.markdown(f"### {sheet_name}")
            
            # Show data editor with large height to display many rows
            edited_df = st.data_editor(
                st.session_state.results[sheet_name],
                use_container_width=True,
                num_rows="dynamic",
                height=600,  # Large enough to show many rows
                key=f"editor_{sheet_name}"
            )
            
            # Update session state with edited data
            st.session_state.results[sheet_name] = edited_df
            
            # Show row count
            st.caption(f"Total rows: {len(edited_df)}")
    
    # ============================================================================
    # STEP 4: DOWNLOAD
    # ============================================================================
    st.markdown("---")
    st.header("Step 4: Download Results")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet_name, df in st.session_state.results.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        excel_data = output.getvalue()
        
        # Download button
        st.download_button(
            label="Download calendar.xlsx",
            data=excel_data,
            file_name=f"calendar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
        
        st.info("File will be downloaded with timestamp")

else:
    if all_files_uploaded:
        st.info("Click RUN SCHEDULER button to process files")
    else:
        st.info("Please upload all 4 files to continue")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 10px;'>
    <p><strong>Production Scheduler v1.0</strong></p>
</div>
""", unsafe_allow_html=True)

