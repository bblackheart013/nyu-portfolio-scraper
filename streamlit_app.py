import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json

def load_data():
    files = [f for f in os.listdir() if f.endswith('.json') and f.startswith('portfolio_data')]
    if not files:
        st.warning("No data file found. Please run the scraper first.")
        return None

    latest_file = sorted(files)[-1]
    with open(latest_file, 'r') as f:
        data = json.load(f)
    return data

def display_dashboard(data):
    companies = data.get("companies", [])
    founders = []
    for company in companies:
        for founder in company.get("founders", []):
            founders.append({
                "Company": company.get("name"),
                "Founder": founder.get("name"),
                "Role": founder.get("role"),
                "LinkedIn": founder.get("linkedin"),
                "Email": founder.get("email"),
            })

    df = pd.DataFrame(founders)
    st.write(f"### Total Companies: {len(companies)}")
    st.write(f"### Total Founders: {len(founders)}")

    st.dataframe(df)

    # Plot founders per company
    founder_counts = df["Company"].value_counts().reset_index()
    founder_counts.columns = ["Company", "Founder Count"]

    fig = px.bar(founder_counts, x="Company", y="Founder Count", title="Founders per Company")
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("🚀 Startup Scraper Dashboard")

    st.markdown("View the scraped founders and portfolio data from VC websites.")

    data = load_data()
    if data:
        display_dashboard(data)
    else:
        st.info("No data to display. Run the scraper and refresh.")

