#!/usr/bin/env python3
"""
Test script - Run this FIRST to make sure everything works!
"""

import os
import sys

print("""
🧪 TESTING PORTFOLIO SCRAPER SETUP
==================================
""")

# Test 1: Check files
print("1️⃣ Checking required files...")
required_files = ['portfolio_scraper.py', 'portfolio_dashboard.py', 'run_portfolio_scraper.py']
files_ok = True

for file in required_files:
    if os.path.exists(file):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} NOT FOUND")
        files_ok = False

if not files_ok:
    print("\n❌ Missing files! Make sure you have all 3 files.")
    sys.exit(1)

# Test 2: Check imports
print("\n2️⃣ Checking Python packages...")
packages = {
    'selenium': 'Web automation',
    'pandas': 'Data processing', 
    'streamlit': 'Dashboard',
    'plotly': 'Charts',
    'bs4': 'HTML parsing',
    'openai': 'AI features'
}

all_ok = True
for package, description in packages.items():
    try:
        __import__(package)
        print(f"   ✅ {package} - {description}")
    except ImportError:
        print(f"   ❌ {package} - {description} NOT INSTALLED")
        all_ok = False

if not all_ok:
    print("\n❌ Missing packages! Run:")
    print("pip install selenium pandas streamlit plotly webdriver-manager beautifulsoup4 openai openpyxl")
    sys.exit(1)

# Test 3: Quick scraper test
print("\n3️⃣ Testing scraper initialization...")
try:
    from portfolio_scraper import PortfolioScraper
    print("   ✅ Portfolio scraper imports successfully")
    
    # Try to initialize (headless to be quick)
    print("   🔄 Initializing scraper...")
    scraper = PortfolioScraper(headless=True)
    print("   ✅ Scraper initialized!")
    
    # Quick test on a simple page
    print("   🔄 Testing on example.com...")
    scraper.driver.get("https://example.com")
    title = scraper.driver.title
    print(f"   ✅ Browser working! Page title: {title}")
    
    scraper.close()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    print("\n   Make sure Chrome browser is installed!")
    sys.exit(1)

# Test 4: Check API key
print("\n4️⃣ Checking OpenAI API key...")
try:
    from portfolio_scraper import OPENAI_API_KEY
    if OPENAI_API_KEY:
        print(f"   ✅ API key found: {OPENAI_API_KEY[:20]}...")
    else:
        print("   ⚠️  No API key (scraper will still work without AI features)")
except:
    print("   ⚠️  Could not check API key")

print("\n" + "="*50)
print("✅ ALL TESTS PASSED! Your scraper is ready!")
print("="*50)

print("""
🚀 Next Steps:

1. Run the scraper:
   python run_portfolio_scraper.py

2. Choose option 1 (Dashboard)

3. Enter a portfolio URL like:
   https://www.orangecollective.vc/portfolio

4. Click 'START SCRAPING' and watch the magic!

💡 The scraper will:
   - Find all companies on the portfolio page
   - Visit each company website
   - Extract founder information
   - Save to Excel/CSV files

Happy scraping! 🎯
""")