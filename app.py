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
    
    # 1. Aggressive Header Cleaning
    df.columns = df.columns.str.strip()
    
    # Define a flexible mapping to catch variations in your report headers
    # We map whatever your CSV has to the names our code needs
    name_cols = [c for c in df.columns if 'name' in c.lower()]
    order_cols = [c for c in df.columns if 'order' in c.lower() or 'type' in c.lower()]
    nav_cols = [c for c in df.columns if 'nav' in c.lower() and 'current' in c.lower()]
    amt_cols = [c for c in df.columns if 'amount' in c.lower()]
    
    if name_cols: df = df.rename(columns={name_cols[0]: 'Scheme Name'})
    if order_cols: df = df.rename(columns={order_cols[0]: 'Type'})
    if nav_cols: df = df.rename(columns={nav_cols[0]: 'Current_NAV'})
    if amt_cols: df = df.rename(columns={amt_cols[0]: 'Amount'})

    # 2. Safety Check: If 'Type' is still missing, create a dummy one or alert
    if 'Type' not in df.columns:
        st.error(f"Could not find the 'Order' column. Detected columns: {list(df.columns)}")
        st.stop()

    # 3. Data Cleaning with Error Handling
    df['Type'] = df['Type'].astype(str).str.lower().str.strip()
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df['Units'] = pd.to_numeric(df['Units'], errors='coerce').fillna(0)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    df['Current_NAV'] = pd.to_numeric(df['Current_NAV'], errors='coerce').fillna(0)
    
    df = df.dropna(subset=['Scheme Name'])

    # 4. Aggregation Logic
    def calculate_summary(group):
        buy_units = group.loc[group['Type'].str.contains('buy|purchase', na=False), 'Units'].sum()
        sell_units = group.loc[group['Type'].str.contains('sell|redemption', na=False), 'Units'].sum()
        net_units = buy_units - sell_units
        total_invested = group.loc[group['Type'].str.contains('buy|purchase', na=False), 'Amount'].sum()
        latest_nav = group['Current_NAV'].iloc[-1]
        
        return pd.Series({
            'Net Units': net_units,
            'Invested Amount': total_invested,
            'Current Value': net_units * latest_nav
        })

    summary = df.groupby('Scheme Name', group_keys=False).apply(calculate_summary).reset_index()

    # 5. XIRR Calculations
    portfolio_dates = []
    portfolio_flows = []
    xirr_results = []

    for scheme in summary['Scheme Name']:
        scheme_tx = df[df['Scheme Name'] == scheme].copy()
        # Handle Buy/Sell flows
        scheme_tx['Flow'] = np.where(scheme_tx['Type'].str.contains('buy|purchase', na=False), 
                                     -scheme_tx['Amount'], 
                                     scheme_tx['Amount'])
        
        dates = scheme_tx['Date'].dropna().tolist()
        amounts = scheme_tx['Flow'].tolist()
        
        portfolio_dates.extend(dates)
        portfolio_flows.extend(amounts)
        
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

    # 6. Aggregate Portfolio Logic
    total_portfolio_value = summary['Current Value'].sum()
    portfolio_dates.append(pd.Timestamp.now())
    portfolio_flows.append(total_portfolio_value)
    
    try:
        total_xirr = round(xirr(portfolio_dates, portfolio_flows) * 100, 2)
    except:
        total_xirr = 0.0

    # 7. Dashboard Display
    st.subheader("Aggregate Portfolio Performance")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Value", f"₹{total_portfolio_value:,.2f}")
    col2.metric("Portfolio XIRR", f"{total_xirr}%")
    col3.metric("Funds Held", len(summary))

    # Color Logic
    def get_color(val):
        if val < 10: return 'Amber (<10%)'
        elif 10 <= val <= 15: return 'Green (10-15%)'
        else: return 'Blue (>15%)'

    summary['Category'] = summary['XIRR (%)'].apply(get_color)
    color_map = {'Amber (<10%)': '#FFBF00', 'Green (10-15%)': '#228B22', 'Blue (>15%)': '#0000FF'}

    fig = px.bar(summary, x='Scheme Name', y='XIRR (%)', color='Category',
                 color_discrete_map=color_map, text_auto='.2f', title="Fund Performance")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(summary)
