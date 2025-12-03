"""
ASAP Security - Automated Bid Monitor
Phase 2A - SmartBid and PlanHub Scraper
"""

import time
import os
from datetime import datetime, timedelta
from typing import List, Dict
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# For web scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests

# For scheduling
import schedule

class BidMonitor:
    """Main bid monitoring class"""
    
    def __init__(self, config_file='bid_config.json'):
        """Initialize with config"""
        self.load_config(config_file)
        self.setup_driver()
        self.results = []
    
    def load_config(self, config_file):
        """Load configuration from JSON"""
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # Create default config
            self.config = {
                "platforms": {
                    "smartbid": {
                        "url": "https://www.smartbidnet.com",
                        "username": "YOUR_USERNAME",
                        "password": "YOUR_PASSWORD",
                        "enabled": True
                    },
                    "planhub": {
                        "url": "https://www.planhub.com",
                        "username": "YOUR_USERNAME", 
                        "password": "YOUR_PASSWORD",
                        "enabled": True
                    }
                },
                "filters": {
                    "keywords": ["fire", "fire alarm", "fire protection", "sprinkler", "smoke detector"],
                    "location_radius": 50,  # miles
                    "location_zip": "07010",  # New Jersey
                    "min_value": 10000,
                    "max_value": 1000000
                },
                "notifications": {
                    "email_to": "client@asapsecurity.com",
                    "email_from": "bids@yourdomain.com",
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "smtp_username": "your_email@gmail.com",
                    "smtp_password": "your_app_password"
                },
                "schedule": {
                    "check_interval_hours": 6,
                    "business_hours_only": True
                }
            }
            # Save default config
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"Created default config file: {config_file}")
            print("Please update with your credentials before running!")
    
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
    
    def scrape_smartbid(self) -> List[Dict]:
        """Scrape SmartBid for fire protection projects"""
        if not self.config["platforms"]["smartbid"]["enabled"]:
            return []
        
        print("🔍 Checking SmartBid...")
        projects = []
        
        try:
            # Navigate to SmartBid
            self.driver.get(self.config["platforms"]["smartbid"]["url"])
            time.sleep(3)
            
            # Login
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.send_keys(self.config["platforms"]["smartbid"]["username"])
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(self.config["platforms"]["smartbid"]["password"])
            
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            login_button.click()
            
            time.sleep(5)
            
            # Navigate to projects/bids section
            # This will vary based on SmartBid's actual structure
            projects_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Projects')]"))
            )
            projects_link.click()
            
            time.sleep(3)
            
            # Search for fire protection keywords
            search_box = self.driver.find_element(By.NAME, "search")
            search_terms = " OR ".join(self.config["filters"]["keywords"])
            search_box.send_keys(search_terms)
            search_box.submit()
            
            time.sleep(3)
            
            # Parse results
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find project listings (adjust selectors based on actual HTML)
            project_cards = soup.find_all('div', class_='project-card')
            
            for card in project_cards[:10]:  # Limit to first 10
                project = {
                    "platform": "SmartBid",
                    "title": card.find('h3').text.strip() if card.find('h3') else "No title",
                    "location": card.find('span', class_='location').text.strip() if card.find('span', class_='location') else "Unknown",
                    "deadline": card.find('span', class_='deadline').text.strip() if card.find('span', class_='deadline') else "Not specified",
                    "url": self.config["platforms"]["smartbid"]["url"] + card.find('a')['href'] if card.find('a') else "",
                    "found_date": datetime.now().isoformat(),
                    "relevant_keywords": [kw for kw in self.config["filters"]["keywords"] if kw.lower() in card.text.lower()]
                }
                
                # Only add if has relevant keywords
                if project["relevant_keywords"]:
                    projects.append(project)
                    print(f"  ✓ Found: {project['title'][:50]}...")
            
        except Exception as e:
            print(f"  ✗ SmartBid error: {str(e)}")
        
        return projects
    
    def scrape_planhub(self) -> List[Dict]:
        """Scrape PlanHub for fire protection projects"""
        if not self.config["platforms"]["planhub"]["enabled"]:
            return []
        
        print("🔍 Checking PlanHub...")
        projects = []
        
        try:
            # Navigate to PlanHub
            self.driver.get(self.config["platforms"]["planhub"]["url"])
            time.sleep(3)
            
            # Login process (adjust based on actual site)
            login_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Login')]"))
            )
            login_link.click()
            
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            username_field.send_keys(self.config["platforms"]["planhub"]["username"])
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.config["platforms"]["planhub"]["password"])
            
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            # Search for projects
            # Navigate to search or projects page
            search_url = f"{self.config['platforms']['planhub']['url']}/projects"
            self.driver.get(search_url)
            time.sleep(3)
            
            # Apply filters
            for keyword in self.config["filters"]["keywords"]:
                search_input = self.driver.find_element(By.NAME, "q")
                search_input.clear()
                search_input.send_keys(keyword)
                search_input.submit()
                time.sleep(2)
                
                # Parse results
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Find listings (adjust based on actual HTML)
                listings = soup.find_all('div', class_='project-listing')
                
                for listing in listings[:5]:  # Limit per keyword
                    project = {
                        "platform": "PlanHub",
                        "title": listing.find('h2').text.strip() if listing.find('h2') else "No title",
                        "location": listing.find('div', class_='location').text.strip() if listing.find('div', class_='location') else "Unknown",
                        "deadline": listing.find('div', class_='bid-date').text.strip() if listing.find('div', class_='bid-date') else "Not specified",
                        "url": self.config["platforms"]["planhub"]["url"] + listing.find('a')['href'] if listing.find('a') else "",
                        "found_date": datetime.now().isoformat(),
                        "keyword_matched": keyword
                    }
                    
                    # Check if already found
                    if not any(p['url'] == project['url'] for p in projects):
                        projects.append(project)
                        print(f"  ✓ Found: {project['title'][:50]}...")
            
        except Exception as e:
            print(f"  ✗ PlanHub error: {str(e)}")
        
        return projects
    
    def send_email_notification(self, new_projects: List[Dict]):
        """Send email with new projects found"""
        if not new_projects:
            return
        
        print(f"📧 Sending notification for {len(new_projects)} new projects...")
        
        # Create email content
        subject = f"🔥 {len(new_projects)} New Fire Protection Projects Found"
        
        html_body = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .project { 
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    margin: 10px 0;
                    border-radius: 5px;
                }
                .platform { 
                    background: #ff6b6b; 
                    color: white; 
                    padding: 3px 8px; 
                    border-radius: 3px;
                    display: inline-block;
                    font-size: 12px;
                }
                h2 { color: #333; }
                .deadline { color: #ff6b6b; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>🔥 New Fire Protection Projects</h1>
            <p>Found {count} new projects matching your criteria:</p>
        """.format(count=len(new_projects))
        
        for project in new_projects:
            html_body += f"""
            <div class="project">
                <span class="platform">{project['platform']}</span>
                <h2>{project['title']}</h2>
                <p><strong>Location:</strong> {project['location']}</p>
                <p><strong>Deadline:</strong> <span class="deadline">{project['deadline']}</span></p>
                <p><strong>Link:</strong> <a href="{project['url']}">View Project</a></p>
                <hr>
            </div>
            """
        
        html_body += """
            <p style="margin-top: 30px; color: #666;">
                This is an automated notification from ASAP Security Bid Monitor.<br>
                Configure settings in bid_config.json
            </p>
        </body>
        </html>
        """
        
        # Send email
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config["notifications"]["email_from"]
            msg['To'] = self.config["notifications"]["email_to"]
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Connect to server and send
            server = smtplib.SMTP(
                self.config["notifications"]["smtp_server"],
                self.config["notifications"]["smtp_port"]
            )
            server.starttls()
            server.login(
                self.config["notifications"]["smtp_username"],
                self.config["notifications"]["smtp_password"]
            )
            
            server.send_message(msg)
            server.quit()
            
            print("  ✓ Email sent successfully!")
            
        except Exception as e:
            print(f"  ✗ Email failed: {str(e)}")
    
    def save_results(self, projects: List[Dict]):
        """Save results to file for tracking"""
        filename = f"bid_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(projects, f, indent=2)
        print(f"💾 Results saved to {filename}")
    
    def check_for_new_bids(self):
        """Main function to check all platforms"""
        print(f"\n{'='*50}")
        print(f"🚀 Bid Monitor Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        all_projects = []
        
        # Scrape each platform
        all_projects.extend(self.scrape_smartbid())
        all_projects.extend(self.scrape_planhub())
        
        # Filter for truly new projects (not seen before)
        # In production, you'd check against a database
        new_projects = all_projects  # For now, treat all as new
        
        if new_projects:
            print(f"\n✅ Found {len(new_projects)} total projects!")
            self.save_results(new_projects)
            self.send_email_notification(new_projects)
        else:
            print("\n❌ No new projects found this run.")
        
        # Clean up
        self.driver.quit()
        self.setup_driver()  # Reset for next run
        
        return new_projects
    
    def run_scheduled(self):
        """Run on schedule"""
        interval = self.config["schedule"]["check_interval_hours"]
        
        # Schedule the job
        schedule.every(interval).hours.do(self.check_for_new_bids)
        
        print(f"🕐 Bid Monitor started - checking every {interval} hours")
        print(f"   First check starting now...")
        
        # Run immediately
        self.check_for_new_bids()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def test_single_run():
    """Test function for single run"""
    monitor = BidMonitor('bid_config.json')
    results = monitor.check_for_new_bids()
    monitor.driver.quit()
    return results

if __name__ == "__main__":
    print("""
    🔥 ASAP Security Bid Monitor - Phase 2A
    ========================================
    
    Options:
    1. Run once (test mode)
    2. Run scheduled (production mode)
    3. Setup configuration
    
    """)
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        print("\n📋 Running single check...")
        test_single_run()
        
    elif choice == "2":
        print("\n🚀 Starting scheduled monitoring...")
        monitor = BidMonitor('bid_config.json')
        monitor.run_scheduled()
        
    elif choice == "3":
        print("\n⚙️ Creating default configuration...")
        monitor = BidMonitor('bid_config.json')
        print("\n✅ Config file created: bid_config.json")
        print("   Please edit with your credentials before running!")
    
    else:
        print("Invalid choice!")
