"""
Prediction History & Export Page
View and download user's prediction history.
"""

import streamlit as st
import pandas as pd
from auth import UserDatabase
from export_utils import export_to_csv, export_to_excel, export_to_pdf, get_export_filename
from datetime import datetime


st.set_page_config(
    page_title="📊 History & Export",
    page_icon="📊",
    layout="wide"
)

st.markdown('<h1 style="text-align: center; color: #2E7D32;">📊 Prediction History & Export</h1>', unsafe_allow_html=True)

# Check if user authenticated
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Please login first to view your prediction history")
    st.info("Go to the home page and login or create an account")
    st.stop()

username = st.session_state.username
user_id = st.session_state.user_id
db = st.session_state.db

# Get user predictions
predictions = db.get_user_predictions(user_id, limit=100)

if not predictions:
    st.info("📭 No predictions yet. Go to 'Home - Predict Yield' to create your first prediction!")
    st.stop()

# Convert to DataFrame
predictions_df = pd.DataFrame(predictions)

# Get user stats
user_stats = db.get_user_stats(user_id)

# Sidebar filters
with st.sidebar:
    st.markdown("### 🔍 Filters")
    
    # Filter by crop
    all_crops = ["All"] + sorted(predictions_df['crop'].unique().tolist())
    selected_crop = st.selectbox("Filter by Crop", all_crops)
    
    # Filter by state
    all_states = ["All"] + sorted(predictions_df['state'].unique().tolist())
    selected_state = st.selectbox("Filter by State", all_states)
    
    # Filter number of days
    days_range = st.slider("Show last X days", 1, 365, 30)

# Apply filters
filtered_df = predictions_df.copy()

if selected_crop != "All":
    filtered_df = filtered_df[filtered_df['crop'] == selected_crop]

if selected_state != "All":
    filtered_df = filtered_df[filtered_df['state'] == selected_state]

# Filter by date
if 'timestamp' in filtered_df.columns:
    filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'])
    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days_range)
    filtered_df = filtered_df[filtered_df['timestamp'] > cutoff_date]

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["All Predictions", "Statistics", "Export", "Delete"])

with tab1:
    st.markdown("### 📋 Your Predictions")
    
    # Display table
    display_cols = ['timestamp', 'crop', 'state', 'predicted_yield', 'total_profit', 'total_acres']
    display_cols = [col for col in display_cols if col in filtered_df.columns]
    
    display_df = filtered_df[display_cols].copy()
    if 'timestamp' in display_df.columns:
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown(f"**Showing {len(filtered_df)} of {len(predictions_df)} predictions**")

with tab2:
    st.markdown("### 📊 User Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Predictions", user_stats['total_predictions'])
    with col2:
        st.metric("Avg Yield", f"{user_stats['avg_yield']:.2f} kg/acre")
    with col3:
        st.metric("Total Profit", f"₹{user_stats['total_profit']:,.0f}")
    with col4:
        st.metric("Avg Profit", f"₹{user_stats['avg_profit']:,.0f}")
    
    # Charts
    st.markdown("#### 📈 Yield Trends")
    if len(filtered_df) > 0:
        chart_data = filtered_df[['timestamp', 'predicted_yield']].copy()
        if 'timestamp' in chart_data.columns:
            chart_data['timestamp'] = pd.to_datetime(chart_data['timestamp'])
            chart_data = chart_data.sort_values('timestamp')
        
        st.line_chart(chart_data.set_index('timestamp')['predicted_yield'] if 'timestamp' in chart_data.columns else chart_data)
    
    st.markdown("#### 🌾 Crop Distribution")
    crop_counts = filtered_df['crop'].value_counts()
    st.bar_chart(crop_counts)

with tab3:
    st.markdown("### 📥 Export Predictions")
    
    export_format = st.radio("Select export format", ["CSV", "Excel", "PDF"])
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    if export_format == "CSV":
        csv_data = export_to_csv(filtered_df.to_dict('records'))
        with col1:
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=get_export_filename("csv", username),
                mime="text/csv"
            )
    
    elif export_format == "Excel":
        excel_data = export_to_excel(
            filtered_df.to_dict('records'),
            user_stats=user_stats
        )
        with col1:
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=get_export_filename("excel", username),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    elif export_format == "PDF":
        pdf_data = export_to_pdf(
            filtered_df.to_dict('records'),
            user_stats=user_stats,
            username=username
        )
        with col1:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_data,
                file_name=get_export_filename("pdf", username),
                mime="application/pdf"
            )
    
    st.markdown("---")
    st.markdown(f"**Export Summary**: {len(filtered_df)} predictions from {filtered_df['timestamp'].min() if 'timestamp' in filtered_df.columns else 'N/A'} to now")

with tab4:
    st.markdown("### 🗑️ Delete Predictions")
    st.warning("⚠️ Deletion is permanent and cannot be undone")
    
    if st.checkbox("I understand - show deletion options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Delete selected (filtered) predictions", type="secondary"):
                for idx, pred in filtered_df.iterrows():
                    db.delete_prediction(pred['id'])
                st.success(f"✅ Deleted {len(filtered_df)} predictions")
                st.rerun()
        
        with col2:
            if st.button("🔴 Delete ALL predictions", type="secondary"):
                for idx, pred in predictions_df.iterrows():
                    db.delete_prediction(pred['id'])
                st.success(f"✅ Deleted all {len(predictions_df)} predictions")
                st.rerun()


# Footer
st.divider()
st.markdown(f"""
<div style='text-align: center; color: #999; font-size: 0.9em;'>
    <p>👤 Logged in as: <b>{username}</b></p>
    <p>📊 Profile created on account registration</p>
</div>
""", unsafe_allow_html=True)
