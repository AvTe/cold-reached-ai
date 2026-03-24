import re
import requests
from bs4 import BeautifulSoup
from models import db, Email, Business
from config import Config
from urllib.parse import urljoin, urlparse

def get_emails_from_text(text):
    """
    Extract unique email addresses from text using regex.
    """
    email_regex = r'[\w.-]+@[\w.-]+\.\w+'
    emails = re.findall(email_regex, text)
    
    # Generic ignore list
    ignore_list = ['noreply', 'no-reply', 'example.com', 'sentry.io', 'domain.com', 'png', 'jpg', 'jpeg', 'gif']
    
    valid_emails = set()
    for email in emails:
        email = email.lower()
        # Basic validation check
        if any(ignore in email for ignore in ignore_list):
            continue
        # Ensure it doesn't end with a common file extension or junk
        if re.search(r'\.(png|jpg|jpeg|gif|css|js|svg|webp|aspx|php)$', email):
            continue
        valid_emails.add(email)
        
    return list(valid_emails)

def find_emails_for_business(business_id, app):
    """
    Scrapes the business website and contact pages for emails.
    Falls back to Hunter.io if none found.
    """
    with app.app_context():
        business = Business.query.get(business_id)
        if not business or not business.website:
            return []

        website = business.website
        found_emails = set()
        source = "scraped"
        
        try:
            # 1. Fetch Homepage
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(website, headers=headers, timeout=10)
            if response.status_code == 200:
                found_emails.update(get_emails_from_text(response.text))
                
                # 2. Look for Contact Page link
                soup = BeautifulSoup(response.text, 'html.parser')
                contact_links = []
                for a in soup.find_all('a', href=True):
                    href = a['href'].lower()
                    if 'contact' in href or 'support' in href or 'about' in href:
                        contact_links.append(urljoin(website, a['href']))
                
                # Visit the first couple of contact/about pages found
                for link in list(set(contact_links))[:2]:
                    try:
                        res = requests.get(link, headers=headers, timeout=5)
                        if res.status_code == 200:
                            found_emails.update(get_emails_from_text(res.text))
                    except:
                        continue
        except Exception as e:
            print(f"Error scraping {website}: {e}")

        # 3. Hunter.io Fallback
        if not found_emails and Config.HUNTER_API_KEY:
            domain = urlparse(website).netloc.replace('www.', '')
            try:
                hunter_url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={Config.HUNTER_API_KEY}"
                hunter_res = requests.get(hunter_url, timeout=10)
                if hunter_res.status_code == 200:
                    hunter_data = hunter_res.json()
                    for em in hunter_data.get('data', {}).get('emails', []):
                        found_emails.add(em.get('value'))
                    if found_emails:
                        source = "hunter"
            except Exception as e:
                print(f"Hunter.io API error for {domain}: {e}")

        # 4. Save to DB
        new_emails = []
        for email_addr in found_emails:
            # Avoid duplicates for this business
            existing = Email.query.filter_by(business_id=business_id, email=email_addr).first()
            if not existing:
                new_email = Email(
                    business_id=business_id,
                    email=email_addr,
                    source=source
                )
                db.session.add(new_email)
                new_emails.append(email_addr)
        
        db.session.commit()
        return new_emails
