import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# Load fixed sample data file
def load_data():
    file_path = "sample_portfolio_data.json"
    if not os.path.exists(file_path):
        st.warning("No sample data file found.")
        return None
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# Display founders in a table
def display_dashboard(data):
    companies = data.get("companies", [])
    founders = []
    for company in companies:
        for founder in company.get("founders", []):
            founders.append({
                "Company": company.get("name"),
                "Founder": founder.get("name"),
                "Role": founder.get("role"),
            })
    df = pd.DataFrame(founders)
    st.title("🧑‍🚀 Portfolio Founders Overview")
    st.dataframe(df)

# Set page config FIRST
st.set_page_config(page_title="Portfolio Scraper Dashboard", layout="wide")

# Main app
def main():
    st.title("📊 Static Dashboard Demo")
    st.markdown("This is a hosted preview of previously scraped portfolio founder data.")

    data = load_data()
    if data:
        display_dashboard(data)
    else:
        st.error("No data to display. Please scrape data first.")

if __name__ == "__main__":
    main()
