"""
Batch Crop Prediction Upload & Processing
Streamlit page for bulk prediction uploads.
"""

import streamlit as st
import pandas as pd
from batch_predictor import BatchPredictor
from export_utils import export_to_csv, export_to_excel, get_export_filename


# Page configuration
st.set_page_config(
    page_title="📤 Batch Upload",
    page_icon="📤",
    layout="wide"
)

st.markdown("""
<style>
    .upload-container {
        background-color: #f0f7f0;
        padding: 20px;
        border-radius: 8px;
        border: 2px dashed #2E7D32;
    }
    .success-box {background-color: #c8e6c9; padding: 12px; border-radius: 4px;}
    .error-box {background-color: #ffcdd2; padding: 12px; border-radius: 4px;}
    .stats-box {background-color: #e3f2fd; padding: 12px; border-radius: 4px; margin: 8px 0;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="text-align: center; color: #2E7D32;">📤 Batch Prediction Upload</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center;">Upload CSV file with multiple crop records for bulk predictions</p>', unsafe_allow_html=True)

# Initialize predictor
predictor = BatchPredictor()

# Sidebar: Instructions
with st.sidebar:
    st.markdown("### 📋 Instructions")
    st.markdown("""
1. **Prepare CSV** with columns:
   - rainfall, temperature, humidity
   - nitrogen, phosphorus, potassium, pH
   - soil_type, crop, state

2. **Soil Types**: Loamy, Clay, Sandy

3. **Crops**: Wheat, Rice, Maize, Sugarcane

4. **Max**: 10,000 rows per file

5. **Download** results as CSV/Excel
    """)
    
    st.divider()
    
    st.markdown("### 📥 Sample CSV Format")
    sample_data = {
        'rainfall': [100, 150],
        'temperature': [26, 28],
        'humidity': [65, 70],
        'nitrogen': [35, 40],
        'phosphorus': [20, 25],
        'potassium': [25, 30],
        'pH': [6.5, 7.0],
        'soil_type': ['Loamy', 'Clay'],
        'crop': ['Wheat', 'Rice'],
        'state': ['Maharashtra', 'Punjab']
    }
    sample_df = pd.DataFrame(sample_data)
    st.dataframe(sample_df, use_container_width=True, hide_index=True)


# Main content
tab1, tab2 = st.tabs(["Upload", "Results"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📁 Upload CSV File")
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type="csv",
            help="Maximum 10,000 rows per file"
        )
    
    with col2:
        st.markdown("### 📥 Download Template")
        if st.button("Get Sample CSV", use_container_width=True):
            sample_data = {
                'rainfall': [100, 150, 200],
                'temperature': [26, 28, 25],
                'humidity': [65, 70, 60],
                'nitrogen': [35, 40, 30],
                'phosphorus': [20, 25, 20],
                'potassium': [25, 30, 25],
                'pH': [6.5, 7.0, 6.0],
                'soil_type': ['Loamy', 'Clay', 'Sandy'],
                'crop': ['Wheat', 'Rice', 'Maize'],
                'state': ['Maharashtra', 'Punjab', 'Gujarat']
            }
            sample_df = pd.DataFrame(sample_data)
            csv_data = export_to_csv(sample_df.to_dict('records'))
            st.download_button(
                label="📥 Download Sample",
                data=csv_data,
                file_name="sample_predictions.csv",
                mime="text/csv"
            )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            st.markdown("### 📊 Preview Data")
            st.dataframe(df.head(10), use_container_width=True)
            
            st.markdown(f"**File size:** {len(df)} rows × {len(df.columns)} columns")
            
            # Validate
            st.markdown("### ✓ Validation")
            is_valid, validation_msg = predictor.validate_csv(df)
            
            if is_valid:
                st.success(f"✅ {validation_msg}")
                
                # Process
                if st.button("🚀 Process Predictions", use_container_width=True, type="primary"):
                    with st.spinner("Processing... This may take a moment"):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        def progress_callback(current, total):
                            progress_bar.progress(current / total)
                            status_text.text(f"Processing: {current}/{total}")
                        
                        results_df, errors = predictor.process_batch(
                            df,
                            progress_callback=progress_callback
                        )
                        
                        # Store results in session state
                        st.session_state.batch_results = results_df
                        st.session_state.batch_errors = errors
                        
                        status_text.text("")
                        progress_bar.empty()
                        
                        st.success("✅ Processing complete!")
                        
                        # Show statistics
                        stats = predictor.get_summary_stats(results_df)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total", stats["total_processed"])
                        with col2:
                            st.metric("Successful", stats["successful"])
                        with col3:
                            st.metric("Failed", stats["failed"])
                        with col4:
                            st.metric("Success Rate", stats["success_rate"])
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Avg Yield", f"{stats['avg_yield']:.2f} kg/acre")
                        with col2:
                            st.metric("Min Yield", f"{stats['min_yield']:.2f} kg/acre")
                        with col3:
                            st.metric("Max Yield", f"{stats['max_yield']:.2f} kg/acre")
                        
                        # Show errors if any
                        if errors:
                            st.warning(f"⚠️ {len(errors)} rows had errors:")
                            for error in errors[:10]:  # Show first 10
                                st.text(f"  • {error}")
                            if len(errors) > 10:
                                st.text(f"  ... and {len(errors) - 10} more")
            else:
                st.error(f"❌ Validation failed: {validation_msg}")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")


with tab2:
    st.markdown("### 📈 Results")
    
    if "batch_results" in st.session_state:
        results_df = st.session_state.batch_results
        
        # Display results
        st.markdown("### Prediction Results")
        st.dataframe(results_df, use_container_width=True)
        
        # Download options
        st.markdown("### 📥 Download Results")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv_data = export_to_csv(results_df.to_dict('records'))
            st.download_button(
                label="📥 CSV",
                data=csv_data,
                file_name=get_export_filename("csv"),
                mime="text/csv"
            )
        
        with col2:
            excel_data = export_to_excel(results_df.to_dict('records'))
            st.download_button(
                label="📥 Excel",
                data=excel_data,
                file_name=get_export_filename("excel"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col3:
            # Copy to clipboard
            if st.button("📋 Copy CSV to Clipboard"):
                st.info("Copy the CSV below:")
                csv_text = export_to_csv(results_df.to_dict('records')).decode()
                st.code(csv_text, language="csv")
        
        # Summary stats
        if "batch_errors" in st.session_state:
            successful = len(results_df[results_df['predicted_yield'].notna()])
            failed = len(results_df[results_df['predicted_yield'].isna()])
            
            st.markdown("### 📊 Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Processed", len(results_df))
            with col2:
                st.metric("Successful", successful)
            with col3:
                st.metric("Failed", failed)
    else:
        st.info("👆 Upload a CSV file and process predictions to see results here")


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.9em;'>
    <p>💡 Tip: For best results, ensure all values are within normal agricultural ranges</p>
    <p>For questions or issues, contact support or check the README</p>
</div>
""", unsafe_allow_html=True)
