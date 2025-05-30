import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

st.set_page_config(page_title="Static Dashboard Demo", layout="wide")

def load_data():
    files = [f for f in os.listdir() if f.endswith('.json') and f.startswith('portfolio_data')]
    if files:
        latest_file = sorted(files)[-1]
    elif os.path.exists("sample_portfolio_data.json"):
        latest_file = "sample_portfolio_data.json"
    else:
        st.warning("No data file found. Please upload a JSON or rerun the scraper.")
        return None

    with open(latest_file, 'r') as f:
        data = json.load(f)
    return data

def display_dashboard(data):
    if not isinstance(data, dict):
        st.error("Data format invalid.")
        return

    companies = data.get("companies", [])
    founders = []
    for company in companies:
        for founder in company.get("founders", []):
            founders.append({
                "Company": company.get("name"),
                "Founder": founder.get("name"),
                "Role": founder.get("role"),
            })

    st.title("📊 Portfolio Founder Dashboard")
    st.markdown("This shows data from previously scraped startup portfolios.")

    st.metric("Total Companies", len(companies))
    st.metric("Total Founders", len(founders))

    if founders:
        df = pd.DataFrame(founders)
        st.dataframe(df)
        fig = px.histogram(df, x="Company", color="Role", title="Founders by Company")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No founder data found in the file.")

def main():
    data = load_data()
    if data:
        display_dashboard(data)

if __name__ == "__main__":
    main()
