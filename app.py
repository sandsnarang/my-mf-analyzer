import streamlit as st
import pandas as pd
import numpy as np
from pyxirr import xirr
import plotly.express as px

st.set_page_config(page_title="MF Multi-Year Analyzer", layout="wide")
st.title("📈 Multi-Year Portfolio Performance")

uploaded_file = st.sidebar.file_uploader("Upload your Transaction CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    
    # 1. Column Mapping
    mapping = {
        'Name of the Fund': 'Scheme Name', 
        'Name of the': 'Scheme Name',
        'Amount (INR)': 'Amount',
        'Current Nav': 'Current_NAV',
        'Order': 'Type' # 'buy' or 'sell'
    }
    df = df.rename(columns=mapping)

    # 2. Data Cleaning
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    df['Units'] = pd.to_numeric(df['Units'], errors='coerce').fillna(0)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    df['Current_NAV'] = pd.to_numeric(df['Current_NAV'], errors='coerce')

    # 3. Aggregation (Adjusting for Sells)
    # Net Units = sum of buy units - sum of sell units
    def calculate_summary(group):
        net_units = group.loc[group['Type'].str.lower() == 'buy', 'Units'].sum() - \
                    group.loc[group['Type'].str.lower() == 'sell', 'Units'].sum()
        total_invested = group.loc[group['Type'].str.lower() == 'buy', 'Amount'].sum()
        latest_nav = group['Current_NAV'].iloc[-1]
        return pd.Series({
            'Net Units': net_units,
            'Invested Amount': total_invested,
            'Current Value': net_units * latest_nav
        })

    summary = df.groupby('Scheme Name').apply(calculate_summary).reset_index()

    # 4. XIRR Calculation (Adjusted for Buy/Sell)
    xirr_results = []
    for scheme in summary['Scheme Name']:
        scheme_tx = df[df['Scheme Name'] == scheme].copy()
        
        # Prepare Cash Flows: 
        # Buys are negative, Sells are positive
        scheme_tx['Flow'] = np.where(scheme_tx['Type'].str.lower() == 'buy', 
                                     -scheme_tx['Amount'], 
                                     scheme_tx['Amount'])
        
        dates = scheme_tx['Date'].tolist()
        amounts = scheme_tx['Flow'].tolist()
        
        # Add Current Valuation as a final positive flow if units remain
        current_val = summary.loc[summary['Scheme Name'] == scheme, 'Current Value'].iloc[0]
        if current_val > 0:
            dates.append(pd.Timestamp.now())
            amounts.append(current_val)
        
        try:
            rate = xirr(dates, amounts) * 100
            xirr_results.append(round(rate, 2))
        except:
            xirr_results.append(0.0)

    summary['XIRR (%)'] = xirr_results

    # 5. Color Coding Logic
    def get_color(val):
        if val < 10: return 'Amber (<10%)'
        elif 10 <= val <= 15: return 'Green (10-15%)'
        else: return 'Blue (>15%)'

    summary['Performance Category'] = summary['XIRR (%)'].apply(get_color)
    color_map = {'Amber (<10%)': '#FFBF00', 'Green (10-15%)': '#228B22', 'Blue (>15%)': '#0000FF'}

    # 6. Display Dashboard
    st.subheader("Your Portfolio Comparison")
    
    # Custom Bar Chart with Plotly for Color Control
    fig = px.bar(summary, 
                 x='Scheme Name', 
                 y='XIRR (%)', 
                 color='Performance Category',
                 color_discrete_map=color_map,
                 title="Annualized Returns by Fund",
                 text_auto='.2f')
    
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(summary[['Scheme Name', 'Net Units', 'Invested Amount', 'Current Value', 'XIRR (%)']])

else:
    st.info("Upload your CSV. Ensure it has an 'Order' column with 'buy' or 'sell'.")
