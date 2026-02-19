import streamlit as st
import pandas as pd
import numpy as np

# Title and UI
st.set_page_config(page_title="MF Performance Pro", layout="wide")
st.title("📊 Value Research Style MF Analyzer")

# 1. Data Input
st.sidebar.header("1. Data Input")
uploaded_file = st.sidebar.file_uploader("Upload your Transaction CSV", type="csv")

if uploaded_file:
    # Load the data
    df = pd.read_csv(uploaded_file)
    
    # --- NEW: Cleanup Column Names ---
    # This removes extra spaces and makes everything consistent
    df.columns = df.columns.str.strip() 
    
    # Check if 'Scheme Name' exists, if not, try to find the closest match
    if 'Scheme Name' not in df.columns:
        st.error(f"Could not find 'Scheme Name'. Your columns are: {list(df.columns)}")
        st.stop()

    # 2. Calculation Logic
    st.write("### Your Portfolio Overview")
    
    # Adding mock metrics for the "VR Grid"
    df['Return (%)'] = np.random.uniform(12, 22, len(df))
    df['Risk (Std Dev)'] = np.random.uniform(10, 18, len(df))
    df['Sharpe Ratio'] = (df['Return (%)'] - 6.5) / df['Risk (Std Dev)']
    
    st.dataframe(df)
    
    # 3. Visualization
    st.write("### Risk vs. Return (The VR Grid)")
    
    # We use st.scatter_chart and tell it exactly which columns to use
    st.scatter_chart(
        data=df, 
        x='Risk (Std Dev)', 
        y='Return (%)', 
        color='Scheme Name'
    )
    
    # 4. Portfolio Weighting
    st.write("### Portfolio Concentration")
    total_val = df['Current Value'].sum()
    df['Weight (%)'] = (df['Current Value'] / total_val) * 100
    st.bar_chart(data=df, x='Scheme Name', y='Weight (%)')

else:
    st.info("Waiting for CSV upload... Use the sidebar to upload 'test_data.csv'.")
