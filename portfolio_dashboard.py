#!/usr/bin/env python3
"""
Portfolio Dashboard - Shows all scraped portfolio companies and founders
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import pickle
import os
from datetime import datetime
import glob
import numpy as np
from collections import Counter

st.set_page_config(
    page_title="🚀 Portfolio Scraper Dashboard",
    page_icon="🎯",
    layout="wide"
)

# CSS styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        background: #0f0f23;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .company-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .founder-badge {
        background: #667eea;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 5px;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .email-badge {
        background: #48bb78;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 5px;
        display: inline-block;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = []
if 'scraping' not in st.session_state:
    st.session_state.scraping = False

def load_portfolio_data():
    """Load portfolio data from files"""
    # Try pickle first
    if os.path.exists('portfolio_data.pkl'):
        try:
            with open('portfolio_data.pkl', 'rb') as f:
                return pickle.load(f)
        except:
            pass
    
    # Try JSON files
    json_files = glob.glob('portfolio_data_*.json')
    if json_files:
        latest = max(json_files, key=os.path.getctime)
        try:
            with open(latest, 'r') as f:
                return json.load(f)
        except:
            pass
    
    return []

def run_portfolio_scraper(urls):
    """Run the portfolio scraper"""
    from portfolio_scraper import PortfolioScraper
    
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    results_placeholder = st.empty()
    
    scraper = PortfolioScraper(headless=False)
    
    try:
        for url in urls:
            status_placeholder.info(f"🔍 Scraping portfolio: {url}")
            
            # Find companies
            companies = scraper.find_portfolio_companies(url)
            progress_placeholder.progress(0.1)
            
            if companies:
                status_placeholder.info(f"📂 Found {len(companies)} companies to scrape...")
                
                # Scrape each company
                for i, company in enumerate(companies):
                    progress = 0.1 + (0.9 * (i / len(companies)))
                    progress_placeholder.progress(progress)
                    status_placeholder.info(f"🏢 [{i+1}/{len(companies)}] Scraping {company['name']}...")
                    
                    company_data = scraper.scrape_company(company['url'], company['name'])
                    
                    if company_data:
                        scraper.portfolio_data.append(company_data)
                        
                        # Show live results
                        with results_placeholder.container():
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Companies Scraped", len(scraper.portfolio_data))
                            with col2:
                                total_founders = sum(len(c['founders']) for c in scraper.portfolio_data)
                                st.metric("Total Founders", total_founders)
                            with col3:
                                total_emails = sum(len(c['all_emails']) for c in scraper.portfolio_data)
                                st.metric("Total Emails", total_emails)
                
                # Save final data
                scraper.save_all_formats()
                progress_placeholder.progress(1.0)
                status_placeholder.success(f"✅ Completed! Scraped {len(scraper.portfolio_data)} companies")
                
                # Update session state
                st.session_state.portfolio_data = scraper.portfolio_data
            else:
                status_placeholder.error("❌ No companies found on portfolio page")
        
    finally:
        scraper.close()

def display_metrics(data):
    """Display summary metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    total_companies = len(data)
    total_founders = sum(len(c['founders']) for c in data)
    total_emails = sum(len(c['all_emails']) for c in data)
    companies_with_founders = sum(1 for c in data if c['founders'])
    
    with col1:
        st.metric("🏢 Companies", total_companies)
    
    with col2:
        st.metric("👥 Founders", total_founders)
    
    with col3:
        st.metric("📧 Emails", total_emails)
    
    with col4:
        st.metric("✅ With Founders", f"{companies_with_founders}/{total_companies}")

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; margin: 0;">🚀 Portfolio Company Scraper</h1>
        <p style="color: white; opacity: 0.9; margin: 0.5rem 0 0 0;">
            Scrape ALL companies from portfolio pages with founder details
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎯 Scraping Control")
        
        # URL input
        portfolio_url = st.text_input(
            "Portfolio URL",
            placeholder="https://www.example.vc/portfolio",
            help="Enter a portfolio page URL that lists multiple companies"
        )
        
        # Common examples
        if st.button("📋 Use Example URLs"):
            st.code("""
https://www.orangecollective.vc/portfolio
https://www.ycombinator.com/companies
https://500.co/portfolio
https://techstars.com/portfolio
            """)
        
        if st.button("🚀 START SCRAPING", type="primary", disabled=st.session_state.scraping):
            if portfolio_url:
                st.session_state.scraping = True
                run_portfolio_scraper([portfolio_url])
                st.session_state.scraping = False
                st.rerun()
            else:
                st.warning("Please enter a portfolio URL")
        
        st.markdown("---")
        
        # Data management
        if st.button("🔄 Load Previous Data"):
            st.session_state.portfolio_data = load_portfolio_data()
            st.success(f"Loaded {len(st.session_state.portfolio_data)} companies")
            st.rerun()
        
        if st.button("🗑️ Clear All Data"):
            st.session_state.portfolio_data = []
            st.rerun()
        
        # Download section
        if st.session_state.portfolio_data:
            st.markdown("---")
            st.markdown("### 📥 Download Data")
            
            # Find latest files
            excel_files = glob.glob('portfolio_founders_*.xlsx')
            csv_files = glob.glob('portfolio_founders_*.csv')
            
            if excel_files:
                latest_excel = max(excel_files, key=os.path.getctime)
                with open(latest_excel, 'rb') as f:
                    st.download_button(
                        "📊 Download Excel",
                        data=f.read(),
                        file_name=latest_excel,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            if csv_files:
                latest_csv = max(csv_files, key=os.path.getctime)
                with open(latest_csv, 'rb') as f:
                    st.download_button(
                        "📄 Download CSV",
                        data=f.read(),
                        file_name=latest_csv,
                        mime="text/csv"
                    )
    
    # Load data
    if not st.session_state.portfolio_data:
        st.session_state.portfolio_data = load_portfolio_data()
    
    # Main content
    if st.session_state.portfolio_data:
        # Display metrics
        display_metrics(st.session_state.portfolio_data)
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏢 Companies & Founders", 
            "📊 Analytics", 
            "📧 All Emails",
            "🔍 Search"
        ])
        
        with tab1:
            st.markdown("## 🏢 Portfolio Companies")
            
            # Display each company
            for i, company in enumerate(st.session_state.portfolio_data):
                with st.expander(
                    f"**{company['company_name']}** - {len(company['founders'])} founders, {len(company['all_emails'])} emails",
                    expanded=(i < 5)  # Expand first 5
                ):
                    # Company info
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"🔗 **Website:** {company['company_url']}")
                        if company['description']:
                            st.markdown(f"📝 **Description:** {company['description']}")
                        if company['tech_stack']:
                            st.markdown(f"💻 **Tech Stack:** {', '.join(company['tech_stack'])}")
                    
                    with col2:
                        st.metric("Founders", len(company['founders']))
                        st.metric("Emails", len(company['all_emails']))
                    
                    # Founders
                    if company['founders']:
                        st.markdown("### 👥 Founders & Team")
                        
                        for founder in company['founders']:
                            founder_info = f"**{founder['name']}** - {founder['role']}"
                            
                            if founder.get('email'):
                                founder_info += f" | 📧 {founder['email']}"
                            
                            if founder.get('linkedin'):
                                founder_info += f" | [LinkedIn]({founder['linkedin']})"
                            
                            if founder.get('twitter'):
                                founder_info += f" | [Twitter]({founder['twitter']})"
                            
                            st.markdown(founder_info)
                    else:
                        st.info("No founders found for this company")
                    
                    # Emails
                    if company['all_emails']:
                        st.markdown("### 📧 All Emails Found")
                        email_cols = st.columns(3)
                        for idx, email in enumerate(company['all_emails']):
                            with email_cols[idx % 3]:
                                st.markdown(f"`{email}`")
        
        with tab2:
            st.markdown("## 📊 Portfolio Analytics")
            
            # Companies with/without founders
            fig1 = go.Figure(data=[
                go.Bar(name='With Founders', x=['Companies'], y=[sum(1 for c in st.session_state.portfolio_data if c['founders'])]),
                go.Bar(name='Without Founders', x=['Companies'], y=[sum(1 for c in st.session_state.portfolio_data if not c['founders'])])
            ])
            fig1.update_layout(title="Companies with Founder Data", barmode='stack')
            st.plotly_chart(fig1, use_container_width=True)
            
            # Founders per company
            company_names = [c['company_name'][:20] for c in st.session_state.portfolio_data[:20]]
            founder_counts = [len(c['founders']) for c in st.session_state.portfolio_data[:20]]
            
            fig2 = go.Figure(data=[go.Bar(x=company_names, y=founder_counts, marker_color='lightblue')])
            fig2.update_layout(title="Founders per Company (Top 20)", xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
            
            # Tech stack distribution
            all_tech = []
            for c in st.session_state.portfolio_data:
                all_tech.extend(c['tech_stack'])
            
            if all_tech:
                tech_counts = Counter(all_tech).most_common(15)
                fig3 = go.Figure(data=[go.Bar(
                    x=[t[1] for t in tech_counts],
                    y=[t[0] for t in tech_counts],
                    orientation='h'
                )])
                fig3.update_layout(title="Most Common Technologies")
                st.plotly_chart(fig3, use_container_width=True)
        
        with tab3:
            st.markdown("## 📧 All Email Addresses")
            
            # Collect all emails
            all_emails = []
            for company in st.session_state.portfolio_data:
                for email in company['all_emails']:
                    all_emails.append({
                        'Email': email,
                        'Company': company['company_name'],
                        'Domain': email.split('@')[-1] if '@' in email else ''
                    })
            
            if all_emails:
                email_df = pd.DataFrame(all_emails)
                
                # Email search
                search = st.text_input("🔍 Search emails", placeholder="Search by email, company, or domain...")
                
                if search:
                    mask = (
                        email_df['Email'].str.contains(search, case=False) |
                        email_df['Company'].str.contains(search, case=False) |
                        email_df['Domain'].str.contains(search, case=False)
                    )
                    filtered_df = email_df[mask]
                else:
                    filtered_df = email_df
                
                st.dataframe(filtered_df, use_container_width=True, height=600)
                
                # Domain distribution
                domain_counts = email_df['Domain'].value_counts().head(10)
                fig = px.pie(values=domain_counts.values, names=domain_counts.index, title="Top Email Domains")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.markdown("## 🔍 Search Founders")
            
            search_term = st.text_input("Search for founders, companies, or roles", placeholder="e.g., CEO, John, Tech Company...")
            
            if search_term:
                results = []
                
                for company in st.session_state.portfolio_data:
                    # Search in company name
                    if search_term.lower() in company['company_name'].lower():
                        for founder in company['founders']:
                            results.append({
                                'Company': company['company_name'],
                                'Founder': founder['name'],
                                'Role': founder['role'],
                                'Email': founder.get('email', ''),
                                'LinkedIn': founder.get('linkedin', ''),
                                'Match': 'Company Name'
                            })
                    
                    # Search in founders
                    for founder in company['founders']:
                        if (search_term.lower() in founder['name'].lower() or 
                            search_term.lower() in founder['role'].lower()):
                            results.append({
                                'Company': company['company_name'],
                                'Founder': founder['name'],
                                'Role': founder['role'],
                                'Email': founder.get('email', ''),
                                'LinkedIn': founder.get('linkedin', ''),
                                'Match': 'Founder/Role'
                            })
                
                if results:
                    st.success(f"Found {len(results)} matches")
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df, use_container_width=True)
                else:
                    st.info("No matches found")
    
    else:
        # Welcome screen
        st.markdown("""
        <div class="company-card" style="text-align: center; padding: 3rem;">
            <h2>Welcome to Portfolio Scraper!</h2>
            <p style="font-size: 1.2rem; opacity: 0.8;">
                This tool scrapes entire portfolio pages and extracts founder information from each company.
            </p>
            
            <h3>How it works:</h3>
            <ol style="text-align: left; max-width: 600px; margin: 2rem auto;">
                <li>Enter a portfolio URL (e.g., vc-firm.com/portfolio)</li>
                <li>The scraper finds all portfolio companies</li>
                <li>Visits each company website individually</li>
                <li>Extracts founder names, roles, emails, and social profiles</li>
                <li>Saves everything to Excel/CSV files</li>
            </ol>
            
            <p style="margin-top: 2rem;">
                <strong>Enter a portfolio URL in the sidebar to begin!</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()