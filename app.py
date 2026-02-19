import streamlit as st
import pandas as pd
import numpy as np
from pyxirr import xirr

st.set_page_config(page_title="MF Multi-Year Analyzer", layout="wide")
st.title("📈 Multi-Year Portfolio Performance")

uploaded_file = st.sidebar.file_uploader("Upload your Transaction CSV", type="csv")

if uploaded_file:
    # Load the data
    df = pd.read_csv(uploaded_file)
    
    # --- RUGGED COLUMN CLEANING ---
    # 1. Strip spaces from all column names to prevent "Key Errors"
    df.columns = df.columns.str.strip()
    
    # 2. Map your specific column names to the ones the code needs
    # We look for your specific header "Name of the Fund" here
    mapping = {
        'Name of the Fund': 'Scheme Name', 
        'Name of the': 'Scheme Name', # Backup for the cut-off version
        'Amount (INR)': 'Amount',
        'Current Nav': 'Current_NAV'
    }
    df = df.rename(columns=mapping)

    # 3. Ensure 'Scheme Name' exists before proceeding
    if 'Scheme Name' not in df.columns:
        st.error(f"Required column 'Name of the Fund' not found. Available columns: {list(df.columns)}")
        st.stop()

    # 4. Clean Data Types
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    df['Units'] = pd.to_numeric(df['Units'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Current_NAV'] = pd.to_numeric(df['Current_NAV'], errors='coerce')

    # --- PERFORMANCE CALCULATIONS ---
    # Group by Fund to handle multiple transactions over years
    summary = df.groupby('Scheme Name').agg({
        'Units': 'sum',
        'Amount': 'sum'
    }).reset_index()
    
    # Map the latest NAV to calculate Current Value
    latest_navs = df.groupby('Scheme Name')['Current_NAV'].last().to_dict()
    summary['Current Value'] = summary['Scheme Name'].map(latest_navs) * summary['Units']
    
    # Calculate XIRR (Value Research's standard for multi-year returns)
    xirr_results = []
    for scheme in summary['Scheme Name']:
        scheme_tx = df[df['Scheme Name'] == scheme].copy()
        
        # We need dates and amounts (investments are negative, current value is positive)
        dates = scheme_tx['Date'].tolist() + [pd.Timestamp.now()]
        amounts = (-scheme_tx['Amount']).tolist() + [summary.loc[summary['Scheme Name'] == scheme, 'Current Value'].iloc[0]]
        
        try:
            rate = xirr(dates, amounts) * 100
            xirr_results.append(round(rate, 2))
        except:
            xirr_results.append(0.0)

    summary['XIRR (%)'] = xirr_results

    # --- RESULTS DASHBOARD ---
    st.subheader("Your Consolidated Portfolio Performance")
    
    # Highlight the best-performing fund based on XIRR
    st.dataframe(summary.style.highlight_max(axis=0, subset=['XIRR (%)']))

    # Visual Comparison
    st.write("### Annualized Returns (XIRR) by Fund")
    st.bar_chart(data=summary, x='Scheme Name', y='XIRR (%)')

else:
    st.info("Please upload your Transaction CSV to begin.")
