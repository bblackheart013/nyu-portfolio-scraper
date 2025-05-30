#!/usr/bin/env python3
"""
EASY RUN SCRIPT - Just run this!
"""

import sys
import subprocess

print("""
🚀 PORTFOLIO SCRAPER - COMPLETE SOLUTION
======================================

This will scrape ALL companies from portfolio pages!

Choose an option:
1. Run Dashboard (scrape from UI) - RECOMMENDED
2. Scrape directly (command line)
3. View existing data in dashboard

""")

choice = input("Enter your choice (1-3): ")

if choice == "1":
    print("\n🚀 Launching dashboard...")
    print("=" * 50)
    print("Instructions:")
    print("1. Enter a portfolio URL in the sidebar")
    print("2. Click 'START SCRAPING'")
    print("3. Watch as it scrapes ALL companies!")
    print("4. Download Excel/CSV when done")
    print("\nPress Ctrl+C to stop")
    print("=" * 50)
    
    subprocess.run(["streamlit", "run", "portfolio_dashboard.py"])

elif choice == "2":
    print("\n📝 Direct scraping mode")
    print("=" * 50)
    
    url = input("Enter portfolio URL: ").strip()
    
    if not url:
        print("❌ No URL provided")
        sys.exit(1)
    
    from portfolio_scraper import PortfolioScraper
    
    print(f"\n🚀 Scraping {url}...")
    
    scraper = PortfolioScraper(headless=False)
    try:
        scraper.scrape_portfolio(url)
        
        print("\n✅ Scraping complete!")
        print("\n📁 Your data is saved in:")
        print("   - portfolio_founders_*.xlsx (Excel)")
        print("   - portfolio_founders_*.csv (CSV)")
        print("\n🎯 To view in dashboard, run this script again and choose option 3")
        
    finally:
        scraper.close()

elif choice == "3":
    print("\n📊 Viewing existing data...")
    print("The dashboard will load your previous scraping results")
    print("\nPress Ctrl+C to stop")
    
    subprocess.run(["streamlit", "run", "portfolio_dashboard.py"])

else:
    print("❌ Invalid choice")