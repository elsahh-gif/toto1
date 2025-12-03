import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import sys

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

# Page config
st.set_page_config(
    page_title="Production Scheduler",
    page_icon="chart_with_upwards_trend",
    layout="wide"
)

# Title
st.title("Production Scheduler")
st.markdown("Upload Excel files - Run Scheduler - Edit Results - Download")
st.markdown("---")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'files_loaded' not in st.session_state:
    st.session_state.files_loaded = False

# ============================================================================
# STEP 1: FILE UPLOAD
# ============================================================================
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
                # TODO: Insert full scheduler algorithm here
                # For now: Create dummy results
                
                # Simulate processing
                import time
                time.sleep(2)
                
                # Create sample results (8 sheets)
                st.session_state.results = {
                    'Order Summary': pd.DataFrame({
                        'FG Type': ['12149RXA', '14283BC', '15695XA'],
                        'EXPORT/LOCAL': ['EXPORT-01', 'EXPORT-01', 'EXPORT-01'],
                        'Qty Assy': [648, 120, 7200],
                        'Order Qty': [648, 120, 7200],
                        'Stock Qty': [528, 0, 0],
                        'Cancel Assy Qty': [0, 0, 0],
                        'Over Production Qty': [0, 0, 0],
                        'COGM': [250852.75, 86027.96, 24361.99],
                        'TOTAL COGM': [162552582.0, 10323355.2, 175406328.0]
                    }),
                    'FG Calendar': pd.DataFrame({
                        'FG': ['12149RXA', '14283BC', '15695XA'],
                        'Day 1': [100, 50, 1000],
                        'Day 2': [100, 50, 1000],
                        'Day 3': [100, 0, 1000],
                        'Day 4': [100, 0, 1000],
                        'Day 5': [100, 0, 1000]
                    }),
                    'Table': pd.DataFrame({
                        'Table': ['1AR01', '1AR02', '1AR03'],
                        'Day 1': [['12149RXA', 100], ['14283BC', 50], ['15695XA', 1000]],
                        'Day 2': [['12149RXA', 100], ['14283BC', 50], ['15695XA', 1000]],
                    }),
                    'Table Load': pd.DataFrame({
                        'Table': ['1AR01', '1AR02', '1AR03'],
                        'Day 1': [0.85, 0.45, 0.95],
                        'Day 2': [0.85, 0.45, 0.95],
                    }),
                    'Table Time': pd.DataFrame({
                        'Table': ['1AR01', '1AR02', '1AR03'],
                        'Day 1': ['08:00-16:00', '08:00-14:00', '08:00-17:00'],
                        'Day 2': ['08:00-16:00', '08:00-14:00', '08:00-17:00'],
                    }),
                    'Jig Schedule': pd.DataFrame({
                        'Jig': ['JIG-00001', 'JIG-00002'],
                        'Day 1': [['08:00-12:00'], ['13:00-17:00']],
                        'Day 2': [['08:00-12:00'], ['13:00-17:00']],
                    }),
                    'Stock FG': pd.DataFrame({
                        'FG Type': ['12149RXA', '14283BC', '15695XA'],
                        'Qty': [528, 0, 0]
                    }),
                    'Stock Part': pd.DataFrame({
                        'Part': ['PART001', 'PART002', 'PART003'],
                        'Day 1': [1000, 2000, 3000],
                        'Day 2': [900, 1800, 2700],
                        'Day 3': [800, 1600, 2400]
                    })
                }
                
                st.success("Scheduler completed successfully")
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
            
            # Show data editor
            edited_df = st.data_editor(
                st.session_state.results[sheet_name],
                use_container_width=True,
                num_rows="dynamic",
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
