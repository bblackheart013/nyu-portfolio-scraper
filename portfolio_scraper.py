#!/usr/bin/env python3
"""
PORTFOLIO SCRAPER - Scrapes ALL companies from portfolio pages
This visits EACH company website to get complete founder data
"""

import time
import json
import re
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import openai
from collections import defaultdict
import pickle

# YOUR API KEY
import os
openai.api_key = os.getenv("OPENAI_API_KEY")

class PortfolioScraper:
    def __init__(self, headless=False):
        print("🚀 Initializing Portfolio Scraper...")
        
        # Chrome options
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.wait = WebDriverWait(self.driver, 20)
        
        self.portfolio_data = []
        
    def find_portfolio_companies(self, portfolio_url):
        """Find all company links on a portfolio page"""
        print(f"\n📂 Finding companies on: {portfolio_url}")
        
        self.driver.get(portfolio_url)
        time.sleep(3)
        
        # Scroll to load all content
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for i in range(5):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        companies = []
        
        # Method 1: Look for portfolio grid/list items
        selectors = [
            "a[href*='/portfolio/']",
            "a[href*='/companies/']", 
            "div.portfolio-company a",
            "div[class*='portfolio'] a",
            "div[class*='company'] a",
            "article a",
            "div.grid a",
            "div[class*='card'] a",
            "li[class*='company'] a",
            "div[class*='item'] a"
        ]
        
        found_links = set()
        
        for selector in selectors:
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    href = link.get_attribute('href')
                    if href and href.startswith('http'):
                        # Filter out social media and non-company links
                        if not any(skip in href for skip in ['linkedin.com', 'twitter.com', 'facebook.com', 'youtube.com', '#', 'mailto:']):
                            found_links.add(href)
            except:
                continue
        
        # Method 2: Find all links and filter
        all_links = self.driver.find_elements(By.TAG_NAME, 'a')
        for link in all_links:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                if href and text and len(text) > 3:
                    # Check if it looks like a company link
                    if any(pattern in href for pattern in ['.com', '.io', '.co', '.ai', '.xyz']):
                        if href not in found_links and portfolio_url not in href:
                            if not any(skip in href for skip in ['linkedin', 'twitter', 'facebook', 'mailto']):
                                parent_class = link.find_element(By.XPATH, '..').get_attribute('class') or ''
                                if any(keyword in parent_class.lower() for keyword in ['portfolio', 'company', 'card', 'item']):
                                    found_links.add(href)
            except:
                continue
        
        # Get company names where possible
        for link in found_links:
            companies.append({
                'url': link,
                'name': urlparse(link).netloc.replace('www.', '').split('.')[0].title()
            })
        
        print(f"✅ Found {len(companies)} portfolio companies")
        return companies
    
    def scrape_company(self, company_url, company_name=""):
        """Scrape a single company website for founder information"""
        print(f"\n🏢 Scraping: {company_name or company_url}")
        
        try:
            self.driver.get(company_url)
            time.sleep(3)
            
            # Get basic info
            title = self.driver.title
            domain = urlparse(company_url).netloc
            
            # Try to get company name
            if not company_name:
                company_name = title.split(' - ')[0].split(' | ')[0].strip()
            
            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract description
            description = ""
            try:
                meta_desc = self.driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute('content')
                description = meta_desc
            except:
                pass
            
            # Find about/team page links
            about_links = []
            for link in self.driver.find_elements(By.TAG_NAME, 'a'):
                href = link.get_attribute('href') or ''
                text = link.text.lower()
                if any(keyword in href.lower() or keyword in text for keyword in ['about', 'team', 'founders', 'leadership', 'people']):
                    if company_url in href:
                        about_links.append(href)
            
            # Extract founders from main page
            founders = self.extract_founders_from_page(page_source, company_url)
            
            # Visit about/team pages for more founder info
            for about_link in about_links[:2]:  # Limit to 2 pages
                try:
                    print(f"   📄 Checking {about_link}")
                    self.driver.get(about_link)
                    time.sleep(2)
                    about_source = self.driver.page_source
                    more_founders = self.extract_founders_from_page(about_source, about_link)
                    
                    # Merge founders (avoid duplicates)
                    existing_names = {f['name'].lower() for f in founders}
                    for founder in more_founders:
                        if founder['name'].lower() not in existing_names:
                            founders.append(founder)
                            existing_names.add(founder['name'].lower())
                except:
                    continue
            
            # Extract emails
            all_emails = self.extract_all_emails(page_source)
            
            # Extract tech stack
            tech_stack = self.extract_tech_stack(page_source)
            
            # Match emails to founders
            for founder in founders:
                if not founder.get('email'):
                    name_parts = founder['name'].lower().split()
                    for email in all_emails:
                        email_local = email.split('@')[0].lower()
                        if any(part in email_local for part in name_parts):
                            founder['email'] = email
                            break
                    
                    # Generate email if not found
                    if not founder.get('email') and name_parts:
                        founder['email'] = f"{name_parts[0]}@{domain}"
            
            company_data = {
                'company_name': company_name,
                'company_url': company_url,
                'description': description,
                'founders': founders,
                'all_emails': all_emails,
                'tech_stack': tech_stack,
                'scraped_at': datetime.now().isoformat()
            }
            
            print(f"   ✅ Found {len(founders)} founders")
            return company_data
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None
    
    def extract_founders_from_page(self, page_source, url):
        """Extract founder information from a page"""
        soup = BeautifulSoup(page_source, 'html.parser')
        founders = []
        seen_names = set()
        
        # Method 1: Look for structured data
        team_sections = soup.find_all(['section', 'div'], class_=re.compile('team|founder|leadership|people|about', re.I))
        
        for section in team_sections:
            # Look for person cards
            person_cards = section.find_all(['div', 'article', 'li'], class_=re.compile('person|member|profile|card|founder', re.I))
            
            for card in person_cards:
                # Extract name
                name = ""
                name_elem = card.find(['h2', 'h3', 'h4', 'h5', 'p'], class_=re.compile('name|title', re.I))
                if name_elem:
                    name = name_elem.get_text().strip()
                else:
                    # Try any heading
                    heading = card.find(['h2', 'h3', 'h4', 'h5'])
                    if heading:
                        name = heading.get_text().strip()
                
                # Validate name
                if name and len(name) > 3 and len(name) < 50 and ' ' in name:
                    # Extract role
                    role = "Team Member"
                    role_elem = card.find(['p', 'span', 'div'], class_=re.compile('role|title|position', re.I))
                    if role_elem:
                        role_text = role_elem.get_text().strip()
                        if len(role_text) < 100:
                            role = role_text
                    else:
                        # Look for role keywords in card text
                        card_text = card.get_text()
                        for role_keyword in ['CEO', 'CTO', 'CFO', 'Founder', 'Co-founder', 'Chief', 'President', 'Director', 'VP', 'Head']:
                            if role_keyword in card_text:
                                role = role_keyword
                                break
                    
                    # Extract LinkedIn
                    linkedin = ""
                    linkedin_link = card.find('a', href=re.compile('linkedin.com/in/', re.I))
                    if linkedin_link:
                        linkedin = linkedin_link.get('href')
                    
                    # Extract Twitter
                    twitter = ""
                    twitter_link = card.find('a', href=re.compile('twitter.com/|x.com/', re.I))
                    if twitter_link:
                        twitter = twitter_link.get('href')
                    
                    if name not in seen_names:
                        seen_names.add(name)
                        founders.append({
                            'name': name,
                            'role': role,
                            'email': '',
                            'linkedin': linkedin,
                            'twitter': twitter
                        })
        
        # Method 2: Look for name + role patterns in text
        text = soup.get_text()
        patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+)[\s,-]+(CEO|CTO|CFO|Founder|Co-founder)',
            r'(CEO|CTO|CFO|Founder|Co-founder)[\s:-]+([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:
                    name = match[0] if match[0][0].isupper() else match[1]
                    role = match[1] if match[0][0].isupper() else match[0]
                    
                    if name not in seen_names and len(name) > 5:
                        seen_names.add(name)
                        founders.append({
                            'name': name,
                            'role': role,
                            'email': '',
                            'linkedin': '',
                            'twitter': ''
                        })
        
        # Method 3: Use AI if enabled
        if len(founders) < 2 and OPENAI_API_KEY:
            try:
                # Get clean text
                clean_text = ' '.join(text.split())[:3000]
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Extract founder/CEO/team member names and roles. Return JSON array."},
                        {"role": "user", "content": f"Find founders in this text:\n{clean_text}"}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                ai_result = response.choices[0].message.content
                try:
                    ai_founders = json.loads(ai_result)
                    for founder in ai_founders:
                        if isinstance(founder, dict) and founder.get('name'):
                            if founder['name'] not in seen_names:
                                seen_names.add(founder['name'])
                                founders.append({
                                    'name': founder['name'],
                                    'role': founder.get('role', 'Team Member'),
                                    'email': founder.get('email', ''),
                                    'linkedin': '',
                                    'twitter': ''
                                })
                except:
                    pass
            except:
                pass
        
        return founders
    
    def extract_all_emails(self, page_source):
        """Extract all email addresses from page"""
        emails = set()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        for match in re.findall(email_pattern, page_source):
            email = match.lower()
            # Filter out fake/example emails
            if not any(skip in email for skip in ['example.', 'test.', 'demo.', 'sentry.', 'wix.']):
                emails.add(email)
        
        return list(emails)
    
    def extract_tech_stack(self, page_source):
        """Extract technology keywords"""
        tech_keywords = [
            'React', 'Angular', 'Vue', 'Node.js', 'Python', 'Django', 'Flask',
            'Ruby on Rails', 'PHP', 'Laravel', 'Java', 'Spring', '.NET',
            'AWS', 'Google Cloud', 'Azure', 'Docker', 'Kubernetes',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
            'Machine Learning', 'AI', 'Blockchain', 'IoT'
        ]
        
        found_tech = []
        page_lower = page_source.lower()
        
        for tech in tech_keywords:
            if tech.lower() in page_lower:
                found_tech.append(tech)
        
        return found_tech
    
    def scrape_portfolio(self, portfolio_url):
        """Main method to scrape an entire portfolio"""
        print(f"\n🚀 SCRAPING PORTFOLIO: {portfolio_url}")
        print("=" * 60)
        
        # Find all portfolio companies
        companies = self.find_portfolio_companies(portfolio_url)
        
        if not companies:
            print("❌ No companies found on portfolio page")
            return []
        
        print(f"\n📊 Found {len(companies)} companies to scrape")
        print("=" * 60)
        
        # Scrape each company
        for i, company in enumerate(companies):
            print(f"\n[{i+1}/{len(companies)}] Processing {company['name']}...")
            
            company_data = self.scrape_company(company['url'], company['name'])
            
            if company_data:
                self.portfolio_data.append(company_data)
                
                # Save progress after each company
                self.save_data()
            
            # Small delay between companies
            time.sleep(2)
        
        print("\n" + "=" * 60)
        print("✅ PORTFOLIO SCRAPING COMPLETE!")
        print(f"   Total companies scraped: {len(self.portfolio_data)}")
        print(f"   Total founders found: {sum(len(c['founders']) for c in self.portfolio_data)}")
        
        # Final save
        self.save_all_formats()
        
        return self.portfolio_data
    
    def save_data(self):
        """Save current data to pickle for dashboard"""
        with open('portfolio_data.pkl', 'wb') as f:
            pickle.dump(self.portfolio_data, f)
    
    def save_all_formats(self):
        """Save data in all formats"""
        if not self.portfolio_data:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Save detailed Excel with multiple sheets
        with pd.ExcelWriter(f'portfolio_founders_{timestamp}.xlsx', engine='openpyxl') as writer:
            # Overview sheet
            overview_data = []
            for company in self.portfolio_data:
                overview_data.append({
                    'Company Name': company['company_name'],
                    'Website': company['company_url'],
                    'Description': company['description'][:200] + '...' if len(company['description']) > 200 else company['description'],
                    'Founders Count': len(company['founders']),
                    'Emails Found': len(company['all_emails']),
                    'Tech Stack': ', '.join(company['tech_stack']),
                    'Scraped At': company['scraped_at']
                })
            
            pd.DataFrame(overview_data).to_excel(writer, sheet_name='Overview', index=False)
            
            # Founders sheet
            founders_data = []
            for company in self.portfolio_data:
                for founder in company['founders']:
                    founders_data.append({
                        'Company': company['company_name'],
                        'Company URL': company['company_url'],
                        'Founder Name': founder['name'],
                        'Role': founder['role'],
                        'Email': founder.get('email', ''),
                        'LinkedIn': founder.get('linkedin', ''),
                        'Twitter': founder.get('twitter', '')
                    })
            
            if founders_data:
                pd.DataFrame(founders_data).to_excel(writer, sheet_name='All Founders', index=False)
            
            # Emails sheet
            emails_data = []
            for company in self.portfolio_data:
                for email in company['all_emails']:
                    emails_data.append({
                        'Company': company['company_name'],
                        'Email': email,
                        'Company URL': company['company_url']
                    })
            
            if emails_data:
                pd.DataFrame(emails_data).to_excel(writer, sheet_name='All Emails', index=False)
        
        # 2. Save simple CSV
        csv_data = []
        for company in self.portfolio_data:
            if company['founders']:
                for founder in company['founders']:
                    csv_data.append({
                        'company_name': company['company_name'],
                        'company_url': company['company_url'],
                        'company_description': company['description'],
                        'founder_name': founder['name'],
                        'founder_role': founder['role'],
                        'founder_email': founder.get('email', ''),
                        'linkedin': founder.get('linkedin', ''),
                        'twitter': founder.get('twitter', ''),
                        'tech_stack': ', '.join(company['tech_stack'])
                    })
            else:
                csv_data.append({
                    'company_name': company['company_name'],
                    'company_url': company['company_url'],
                    'company_description': company['description'],
                    'founder_name': '',
                    'founder_role': '',
                    'founder_email': '',
                    'linkedin': '',
                    'twitter': '',
                    'tech_stack': ', '.join(company['tech_stack'])
                })
        
        pd.DataFrame(csv_data).to_csv(f'portfolio_founders_{timestamp}.csv', index=False)
        
        # 3. Save JSON
        with open(f'portfolio_data_{timestamp}.json', 'w') as f:
            json.dump(self.portfolio_data, f, indent=2)
        
        print(f"\n📁 Data saved to:")
        print(f"   - portfolio_founders_{timestamp}.xlsx (Excel with sheets)")
        print(f"   - portfolio_founders_{timestamp}.csv (Simple CSV)")
        print(f"   - portfolio_data_{timestamp}.json (Complete JSON)")
        print(f"   - portfolio_data.pkl (For dashboard)")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

# Example usage
if __name__ == "__main__":
    # Portfolio URLs to scrape
    portfolio_urls = [
        "https://www.orangecollective.vc/portfolio",
        # Add more portfolio URLs here
    ]
    
    scraper = PortfolioScraper(headless=False)
    
    try:
        for url in portfolio_urls:
            scraper.scrape_portfolio(url)
    finally:
        scraper.close()