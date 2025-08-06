import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date
import os
from .base_lottery import BaseLottery

class LottoMax(BaseLottery):
    """Lotto Max lottery implementation"""
    
    def __init__(self):
        super().__init__("Lotto Max", "data/lotto_max")
    
    def get_game_config(self):
        """Return Lotto Max game configuration"""
        return {
            'main_count': 7,           # 7 main numbers
            'main_range': (1, 50),     # Numbers from 1 to 50
            'bonus_count': 1,          # 1 bonus number
            'bonus_range': (1, 50),    # Bonus from same range
        }
    
    def get_scraping_urls(self):
        """Return URLs for scraping Lotto Max data"""
        return [f"https://www.lottomaxnumbers.com/numbers/{year}" for year in range(2009, 2026)]
    
    def should_fetch_data(self):
        """Check if we need to fetch new Lotto Max data"""
        if not os.path.exists(self.past_numbers_file):
            self.log_message("🚨 No past_numbers.txt found! Grabbing fresh data! 🌟")
            return True
        
        try:
            with open(self.past_numbers_file, 'r') as f:
                lines = f.readlines()
                if len(lines) <= 1:
                    self.log_message("😬 past_numbers.txt is empty or just has a header. Fetching new data! 🌈")
                    return True
                last_line = lines[-1].strip()
                last_date_str = last_line.split(',')[0]
                
                try:
                    last_date = parse_date(last_date_str, dayfirst=False)
                except ValueError:
                    self.log_message(f"😣 Bad date format in past_numbers.txt: {last_date_str}. Fetching new data! 🌟")
                    return True
                
                # Check online for newer data
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                numbers_url = "https://www.lottomaxnumbers.com/past-numbers"
                try:
                    response = requests.get(numbers_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    draw_table = soup.find('table', class_='archiveResults')
                    
                    if draw_table:
                        tbody = draw_table.find('tbody')
                        if tbody:
                            first_row = tbody.find('tr')
                        else:
                            first_row = draw_table.find('tr')
                        
                        if first_row:
                            date_cell = first_row.find('td', class_='noBefore colour')
                            if date_cell:
                                web_date = parse_date(date_cell.text.strip(), dayfirst=False)
                                if web_date <= last_date:
                                    self.log_message(f"😴 No new draw since {last_date_str}! Using cached data. 🛌")
                                    return False
                                self.log_message(f"🎉 New draw found ({date_cell.text.strip()})! Fetching fresh data! 🚀")
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
        """Scrape Lotto Max data for all years"""
        headers = {'User-Agent': 'Mozilla/5.0'}
        urls = self.get_scraping_urls()
        all_draws = []
        
        for url in urls:
            try:
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, 'html.parser')
                table = soup.select_one("table")
                
                if not table:
                    self.log_message(f"❌ No table found on {url}")
                    continue
                
                rows = table.select("tbody tr")
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
        """Parse a single Lotto Max draw row"""
        try:
            cols = row.find_all("td")
            if len(cols) < 3:
                return None
            
            # Clean date
            date = self._clean_date(cols[0].text)
            
            # Get jackpot
            jackpot = cols[2].text.strip().replace("\n", " ").replace("\t", "").strip()
            
            # Parse numbers
            ball_ul = cols[1].find("ul", class_="balls")
            if not ball_ul:
                return None
            
            numbers = [li.text.strip() for li in ball_ul.find_all("li") if li.text.strip().isdigit()]
            if len(numbers) < 8:  # Need at least 7 main + 1 bonus
                return None
            
            # Format numbers (7 main + 1 bonus)
            main_numbers = "-".join(numbers[:-1])
            bonus = numbers[-1]
            formatted_numbers = f"{main_numbers}-{bonus}"
            
            # Format date
            formatted_date = parse_date(date).strftime("%-m/%-d/%Y")
            
            return (formatted_date, formatted_numbers, jackpot)
            
        except Exception as e:
            self.log_message(f"Error parsing draw row: {e}")
            return None
    
    def _clean_date(self, raw_date):
        """Clean date string from scraped data"""
        return raw_date.strip().split("\n")[0].strip()