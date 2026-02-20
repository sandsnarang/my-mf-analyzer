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
    
    # 1. Mapping based on your specific report headers
    mapping = {
        'Name of the Fund': 'Scheme Name', 
        'Name of the': 'Scheme Name',
        'Amount (INR)': 'Amount',
        'Current Nav': 'Current_NAV',
        'Order': 'Type'
    }
    df = df.rename(columns=mapping)

    # 2. RUGGED CLEANING: Prevent AttributeError
    df['Type'] = df['Type'].astype(str).str.lower().str.strip() # Forces text mode
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df['Units'] = pd.to_numeric(df['Units'], errors='coerce').fillna(0)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    df['Current_NAV'] = pd.to_numeric(df['Current_NAV'], errors='coerce').fillna(0)
    
    # Remove any rows where Scheme Name is missing
    df = df.dropna(subset=['Scheme Name'])

    # 3. Calculation Logic
    def calculate_summary(group):
        buy_units = group.loc[group['Type'] == 'buy', 'Units'].sum()
        sell_units = group.loc[group['Type'] == 'sell', 'Units'].sum()
        net_units = buy_units - sell_units
        
        total_invested = group.loc[group['Type'] == 'buy', 'Amount'].sum()
        # Use the very last NAV mentioned for this fund
        latest_nav = group['Current_NAV'].iloc[-1]
        
        return pd.Series({
            'Net Units': net_units,
            'Invested Amount': total_invested,
            'Current Value': net_units * latest_nav
        })

    summary = df.groupby('Scheme Name', group_keys=False).apply(calculate_summary).reset_index()

    portfolio_dates = []
    portfolio_flows = []
    xirr_results = []

    for scheme in summary['Scheme Name']:
        scheme_tx = df[df['Scheme Name'] == scheme].copy()
        # Buys are negative (outflow), Sells are positive (inflow)
        scheme_tx['Flow'] = np.where(scheme_tx['Type'] == 'buy', -scheme_tx['Amount'], scheme_tx['Amount'])
        
        dates = scheme_tx['Date'].dropna().tolist()
        amounts = scheme_tx['Flow'].tolist()
        
        # Add to global portfolio tracking
        portfolio_dates.extend(dates)
        portfolio_flows.extend(amounts)
        
        # Add final valuation as a positive flow
        current_val = summary.loc[summary['Scheme Name'] == scheme, 'Current Value'].iloc[0]
        if current_val > 0:
            dates.append(pd.Timestamp.now())
            amounts.append(current_val)
        
        try:
            rate = xirr(dates, amounts) * 100
            xirr_results.append(round(rate, 2) if rate else 0.0)
        except:
            xirr_results.append(0.0)

    summary['XIRR (%)'] = xirr_results

    # 4. Aggregate Portfolio Metrics
    total_portfolio_value = summary['Current Value'].sum()
    portfolio_dates.append(pd.Timestamp.now())
    portfolio_flows.append(total_portfolio_value)
    
    try:
        total_xirr = round(xirr(portfolio_dates, portfolio_flows) * 100, 2)
    except:
        total_xirr = 0.0

    # 5. Dashboard UI
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Portfolio Value", f"₹{total_portfolio_value:,.2f}")
    col2.metric("Aggregate Portfolio XIRR", f"{total_xirr}%")
    col3.metric("Number of Holdings", len(summary))

    def get_color(val):
        if val < 10: return 'Amber (<10%)'
        elif 10 <= val <= 15: return 'Green (10-15%)'
        else: return 'Blue (>15%)'

    summary['Performance Category'] = summary['XIRR (%)'].apply(get_color)
    color_map = {'Amber (<10%)': '#FFBF00', 'Green (10-15%)': '#228B22', 'Blue (>15%)': '#0000FF'}

    fig = px.bar(summary, x='Scheme Name', y='XIRR (%)', color='Performance Category',
                 color_discrete_map=color_map, text_auto='.2f', title="Performance Comparison")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Fund-wise Details")
    st.dataframe(summary)

else:
    st.info("Awaiting CSV upload. Make sure your 'Order' column contains 'buy' or 'sell'.")
