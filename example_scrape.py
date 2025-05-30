#!/usr/bin/env python3
"""
WORKING EXAMPLE - Shows exactly how the portfolio scraper works
This will scrape a real portfolio and show you the results
"""

from portfolio_scraper import PortfolioScraper
import time

print("""
🚀 PORTFOLIO SCRAPER - WORKING EXAMPLE
=====================================

This example will:
1. Scrape a real VC portfolio page
2. Find all portfolio companies
3. Visit each company website
4. Extract founder information
5. Save to Excel/CSV files

""")

# The portfolio URL to scrape
PORTFOLIO_URL = "https://www.orangecollective.vc/portfolio"

print(f"Portfolio URL: {PORTFOLIO_URL}")
print("\nStarting in 3 seconds...")
time.sleep(3)

# Initialize scraper
print("\n" + "="*60)
print("STEP 1: Initializing scraper...")
print("="*60)

scraper = PortfolioScraper(headless=False)  # Set to True for faster scraping

try:
    # Find portfolio companies
    print("\n" + "="*60)
    print("STEP 2: Finding portfolio companies...")
    print("="*60)
    
    companies = scraper.find_portfolio_companies(PORTFOLIO_URL)
    
    if not companies:
        print("❌ No companies found!")
        scraper.close()
        exit()
    
    print(f"\n✅ Found {len(companies)} companies:")
    for i, company in enumerate(companies[:10]):  # Show first 10
        print(f"   {i+1}. {company['name']} - {company['url']}")
    
    if len(companies) > 10:
        print(f"   ... and {len(companies) - 10} more")
    
    # Scrape first few companies as demo
    print("\n" + "="*60)
    print("STEP 3: Scraping company websites...")
    print("="*60)
    print("\nFor this demo, we'll scrape the first 5 companies")
    
    demo_companies = companies[:5]  # Limit to 5 for demo
    
    for i, company in enumerate(demo_companies):
        print(f"\n[{i+1}/{len(demo_companies)}] Scraping {company['name']}...")
        print("-" * 40)
        
        company_data = scraper.scrape_company(company['url'], company['name'])
        
        if company_data:
            scraper.portfolio_data.append(company_data)
            
            # Show what we found
            print(f"✅ Company: {company_data['company_name']}")
            print(f"   Founders: {len(company_data['founders'])}")
            print(f"   Emails: {len(company_data['all_emails'])}")
            
            # Show founder details
            if company_data['founders']:
                print("   Found founders:")
                for founder in company_data['founders'][:3]:  # Show max 3
                    print(f"   - {founder['name']} ({founder['role']})")
                    if founder.get('email'):
                        print(f"     Email: {founder['email']}")
        else:
            print("❌ Could not scrape this company")
        
        time.sleep(2)  # Be nice to servers
    
    # Save results
    print("\n" + "="*60)
    print("STEP 4: Saving results...")
    print("="*60)
    
    scraper.save_all_formats()
    
    # Summary
    print("\n" + "="*60)
    print("🎉 SCRAPING COMPLETE!")
    print("="*60)
    
    total_founders = sum(len(c['founders']) for c in scraper.portfolio_data)
    total_emails = sum(len(c['all_emails']) for c in scraper.portfolio_data)
    
    print(f"\n📊 Results Summary:")
    print(f"   Companies scraped: {len(scraper.portfolio_data)}")
    print(f"   Total founders found: {total_founders}")
    print(f"   Total emails found: {total_emails}")
    
    print(f"\n📁 Your data is saved in:")
    print(f"   - portfolio_founders_*.xlsx (Open in Excel)")
    print(f"   - portfolio_founders_*.csv (Simple format)")
    print(f"   - portfolio_data.pkl (For dashboard)")
    
    print(f"\n🎯 To see full results in dashboard:")
    print(f"   Run: python run_portfolio_scraper.py")
    print(f"   Choose option 3 (View existing data)")
    
    print(f"\n💡 To scrape the ENTIRE portfolio ({len(companies)} companies):")
    print(f"   Run the dashboard and click 'START SCRAPING'")
    print(f"   It will take about {len(companies) * 30 // 60} minutes")

finally:
    # Always close browser
    scraper.close()
    
print("\n✅ Demo complete!")