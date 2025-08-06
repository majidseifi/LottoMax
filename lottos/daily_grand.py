import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
import os
from .base_lottery import BaseLottery

class DailyGrand(BaseLottery):
    """Daily Grand lottery implementation"""
    
    def __init__(self):
        super().__init__("Daily Grand", "data/daily_grand")
    
    def get_game_config(self):
        """Return Daily Grand game configuration"""
        return {
            'main_count': 5,           # 5 main numbers
            'main_range': (1, 49),     # Numbers from 1 to 49
            'bonus_count': 1,          # 1 Grand Number
            'bonus_range': (1, 7),     # Grand Number from 1 to 7
        }
    
    def get_scraping_urls(self):
        """Return URLs for scraping Daily Grand data"""
        return [f"https://ca.lottonumbers.com/daily-grand/numbers/{year}" for year in range(2016, 2026)]
    
    def should_fetch_data(self):
        """Check if we need to fetch new Daily Grand data"""
        if not os.path.exists(self.past_numbers_file):
            self.log_message("🚨 No past_numbers.txt found! Grabbing fresh data! 🌟")
            return True
        
        try:
            with open(self.past_numbers_file, 'r') as f:
                lines = f.readlines()
                if len(lines) <= 1:
                    self.log_message("😬 past_numbers.txt is empty or just has a header. Fetching new data! 🌈")
                    return True
                last_line = lines[1].strip()  # Second line (first data line)
                last_date_str = last_line.split(',')[0]
                
                try:
                    last_date = parse_date(last_date_str, dayfirst=False)
                except ValueError:
                    self.log_message(f"😣 Bad date format in past_numbers.txt: {last_date_str}. Fetching new data! 🌟")
                    return True
                
                # Check online for newer data
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                numbers_url = "https://ca.lottonumbers.com/daily-grand/numbers/2025"
                try:
                    response = requests.get(numbers_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    table = soup.find('table')
                    
                    if table:
                        tbody = table.find('tbody')
                        if tbody:
                            first_row = tbody.find('tr')
                            if first_row:
                                date_cell = first_row.find_all('td')[0]  # First column is date
                                if date_cell:
                                    web_date_str = date_cell.text.strip()
                                    web_date = parse_date(web_date_str, dayfirst=False)
                                    if web_date <= last_date:
                                        self.log_message(f"😴 No new draw since {last_date_str}! Using cached data. 🛌")
                                        return False
                                    self.log_message(f"🎉 New draw found ({web_date_str})! Fetching fresh data! 🚀")
                                    return True
                                else:
                                    self.log_message("🤔 Couldn't find draw date cell. Fetching data to be safe! 🔄")
                                    return True
                            else:
                                self.log_message("🤔 No table rows found. Fetching data to be safe! 🔄")
                                return True
                    else:
                        self.log_message("😕 No draw table found. Fetching data anyway! 🔄")
                        return True
                        
                except requests.RequestException as e:
                    self.log_message(f"🌩️ Trouble checking online: {e}. Fetching data anyway! 🔄")
                    return True
                    
        except Exception as e:
            self.log_message(f"😣 Issue with past_numbers.txt: {e}. Fetching new data! 🌟")
            return True
    
    def _scrape_all_years(self):
        """Scrape Daily Grand data for all years"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        urls = self.get_scraping_urls()
        all_draws = []
        
        for url in urls:
            try:
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, 'html.parser')
                table = soup.find("table")
                
                if not table:
                    self.log_message(f"❌ No table found on {url}")
                    continue
                
                tbody = table.find("tbody")
                if not tbody:
                    self.log_message(f"❌ No tbody found on {url}")
                    continue
                
                rows = tbody.find_all("tr")
                for row in rows:
                    draw_data = self.parse_draw_row(row)
                    if draw_data:
                        all_draws.append(draw_data)
                        
            except Exception as e:
                self.log_message(f"💥 Error scraping {url}: {e}")
        
        if all_draws:
            # Sort by date (newest first)
            all_draws.sort(key=lambda x: parse_date(x[0]), reverse=True)
            return all_draws
        
        return []
    
    def parse_draw_row(self, row):
        """Parse a single Daily Grand draw row"""
        try:
            cols = row.find_all("td")
            if len(cols) < 2:
                return None
            
            # Skip header rows (month rows)
            if len(cols) == 1 or 'monthRow' in cols[0].get('class', []):
                return None
            
            # Get date from first column
            date_text = cols[0].text.strip().replace('\n', ' ')
            
            # Get winning numbers from second column (balls)
            balls_ul = cols[1].find("ul", class_="balls")
            if not balls_ul:
                return None
            
            # Get all ball numbers
            main_numbers = []
            grand_number = None
            
            balls = balls_ul.find_all("li")
            for ball in balls:
                number = ball.text.strip()
                if number.isdigit():
                    if 'bonus-ball' in ball.get('class', []):
                        grand_number = number
                    else:
                        main_numbers.append(number)
            
            # Validate we have correct count
            if len(main_numbers) != 5 or grand_number is None:
                return None
            
            # Format numbers as "12-23-35-48-49-2"
            formatted_numbers = "-".join(main_numbers) + "-" + grand_number
            
            # Format date to match our format (M/D/YYYY)
            try:
                # Handle format like "MondayAugust 4 2025"
                date_clean = date_text.replace('Monday', '').replace('Tuesday', '').replace('Wednesday', '').replace('Thursday', '').replace('Friday', '').replace('Saturday', '').replace('Sunday', '').strip()
                formatted_date = parse_date(date_clean).strftime("%-m/%-d/%Y")
            except:
                # If date parsing fails, try to extract date manually
                import re
                date_match = re.search(r'(\w+ \d+ \d{4})', date_text)
                if date_match:
                    try:
                        formatted_date = parse_date(date_match.group(1)).strftime("%-m/%-d/%Y")
                    except:
                        formatted_date = date_text
                else:
                    formatted_date = date_text
            
            # Daily Grand doesn't have traditional jackpot amounts like Lotto Max
            jackpot = "Life Prize"
            
            return (formatted_date, formatted_numbers, jackpot)
            
        except Exception as e:
            self.log_message(f"Error parsing draw row: {e}")
            return None