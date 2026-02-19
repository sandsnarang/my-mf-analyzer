import streamlit as st
import pandas as pd
import numpy as np
from pyxirr import xirr

st.set_page_config(page_title="MF Multi-Year Analyzer", layout="wide")
st.title("📈 Multi-Year Portfolio Performance")

uploaded_file = st.sidebar.file_uploader("Upload your Transaction CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # 1. Clean Column Names based on your image
    df.columns = df.columns.str.strip()
    # Handle the cut-off column name from the screenshot
    df = df.rename(columns={'Name of the': 'Scheme Name', 'Amount (INR': 'Amount'})

    # 2. Convert Date to a format the computer understands
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)

    # 3. Group by Fund to see Total Holding
    summary = df.groupby('Scheme Name').agg({
        'Units': 'sum',
        'Amount': 'sum'
    }).reset_index()
    
    # Get current NAV from your last entry for calculation
    latest_navs = df.groupby('Scheme Name')['Current Nav'].last().to_dict()
    summary['Current Value'] = summary['Scheme Name'].map(latest_navs) * summary['Units']
    summary['Absolute Return %'] = ((summary['Current Value'] - summary['Amount']) / summary['Amount']) * 100

    # 4. Calculate XIRR for each fund
    # This accounts for the 2020 vs 2026 timing
    xirr_results = []
    for scheme in summary['Scheme Name']:
        scheme_tx = df[df['Scheme Name'] == scheme].copy()
        
        # XIRR needs: [Investments as negative numbers] + [Current Value as positive number]
        dates = scheme_tx['Date'].tolist() + [pd.Timestamp.now()]
        amounts = (-scheme_tx['Amount']).tolist() + [summary.loc[summary['Scheme Name'] == scheme, 'Current Value'].iloc[0]]
        
        try:
            rate = xirr(dates, amounts) * 100
        except:
            rate = 0
        xirr_results.append(round(rate, 2))

    summary['XIRR (%)'] = xirr_results

    # 5. Display Results
    st.subheader("Fund Performance Summary")
    st.dataframe(summary.style.highlight_max(subset=['XIRR (%)'], color='#90EE90'))

    # 6. The Value Research Comparison
    st.subheader("XIRR Comparison (Annualized Growth)")
    st.bar_chart(data=summary, x='Scheme Name', y='XIRR (%)')
    
    st.info("💡 **Why XIRR?** Your 2020 SBI Large Cap units have had 6 years to grow, while 2026 units have had days. XIRR levels the playing field to show your true annual performance.")

else:
    st.info("Awaiting upload. Ensure your CSV has: Date, Name of the, Units, Amount (INR).")
