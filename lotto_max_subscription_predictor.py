import pandas as pd
import numpy as np
from collections import Counter
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import logging
from dateutil.parser import parse as parse_date

# Chill logging with emojis, no timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('lotto_max.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check if we need to fetch new data
def should_fetch_data():
    if not os.path.exists('past_numbers.txt'):
        logger.info("🚨 No past_numbers.txt found! Grabbing fresh data! 🌟")
        return True
    
    try:
        with open('past_numbers.txt', 'r') as f:
            lines = f.readlines()
            if len(lines) <= 1:
                logger.info("😬 past_numbers.txt is empty or just has a header. Fetching new data! 🌈")
                return True
            last_line = lines[-1].strip()
            last_date_str = last_line.split(',')[0]
            # Flexible date parsing
            try:
                last_date = parse_date(last_date_str, dayfirst=False)
            except ValueError:
                logger.error("😣 Bad date format in past_numbers.txt: %s. Fetching new data! 🌟", last_date_str)
                return True
            
            # Peek at latest draw date online
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            numbers_url = "https://www.lottomaxnumbers.com/past-numbers"
            try:
                response = requests.get(numbers_url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                draw_table = soup.find('table', class_='archiveResults')
                if draw_table:
                    # Try finding first <tr> in <tbody> or directly
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
                                logger.info("😴 No new draw since %s! Using cached data. 🛌", last_date_str)
                                return False
                            logger.info("🎉 New draw found (%s)! Fetching fresh data! 🚀", date_cell.text.strip())
                            return True
                        else:
                            logger.warning("🤔 Couldn't find draw date cell. Fetching data to be safe! 🔄")
                            return True
                    else:
                        logger.warning("🤔 No table rows found. Fetching data to be safe! 🔄")
                        return True
                else:
                    logger.warning("😕 No draw table found. Fetching data anyway! 🔄")
                    return True
            except requests.RequestException as e:
                logger.error("🌩️ Trouble checking online: %s. Fetching data anyway! 🔄", e)
                return True
    except Exception as e:
        logger.error("😣 Issue with past_numbers.txt: %s. Fetching new data! 🌟", e)
        return True
    
def clean_date(raw):
    return raw.strip().split("\n")[0].strip()

# Fetch and parse Lotto Max data
def scrape_draw_tables():
    logger.info("🧹 Scraping Lotto Max draw history from 2009–2025...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    base_urls = [f"https://www.lottomaxnumbers.com/numbers/{year}" for year in range(2009, 2026)]

    all_draws = []

    for url in base_urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.select_one("table")
            if not table:
                logger.warning(f"❌ No table found on {url}")
                continue
            rows = table.select("tbody tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue
                date = clean_date(cols[0].text)
                jackpot = cols[2].text.strip().replace("\n", " ").replace("\t", "").strip()

                ball_ul = cols[1].find("ul", class_="balls")
                if not ball_ul:
                    continue

                numbers = [li.text.strip() for li in ball_ul.find_all("li") if li.text.strip().isdigit()]
                if len(numbers) < 8:
                    continue
                main_numbers = "-".join(numbers[:-1])
                bonus = numbers[-1]
                all_draws.append((date, f"{main_numbers}-{bonus}", f'{jackpot}'))

        except Exception as e:
            logger.error(f"💥 Error scraping {url}: {e}")

    if all_draws:
        all_draws.sort(key=lambda x: parse_date(x[0]), reverse=True)
        with open("past_numbers.txt", "w") as f:
            f.write("Date,Draw Results,Jackpot\n")
            for draw in all_draws:
                formatted_date = parse_date(draw[0]).strftime("%-m/%-d/%Y")
                f.write(f"{formatted_date},{draw[1]},\"{draw[2]}\"\n")
        logger.info("✅ past_numbers.txt updated with full draw history! 🎯")
    else:
        logger.warning("⚠️ No draws scraped.")


# Load data from files if no fetch needed
def load_from_files():
    logger.info("📂 Loading data from files! 🗃️")
    data = {'main_freq': {}, 'bonus_freq': {}, 'hot_numbers': {}, 'overdue_numbers': {}, 'common_pairs': [], 'latest_draw': {}}
    
    try:
        # Load statistics.txt
        with open('statistics.txt', 'r') as f:
            lines = f.readlines()
            section = None
            for line in lines:
                line = line.strip()
                if line == "Main Number Frequencies:":
                    section = 'main_freq'
                elif line == "Bonus Number Frequencies:":
                    section = 'bonus_freq'
                elif line == "Hot Numbers:":
                    section = 'hot_numbers'
                elif line == "Overdue Numbers (days since last drawn):":
                    section = 'overdue_numbers'
                elif line == "Common Pairs:":
                    section = 'common_pairs'
                elif line and section and ':' in line:
                    num, value = line.split(':')
                    num = num.strip()
                    value = value.strip()
                    if section == 'common_pairs':
                        num1, num2 = map(int, num.split('-'))
                        data[section].append((num1, num2))
                    else:
                        data[section][int(num)] = int(value)
        
        # Load past_numbers.txt
        with open('past_numbers.txt', 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                last_line = lines[-1].strip()
                date, numbers, jackpot = last_line.split(',')
                numbers = [int(n) for n in numbers.split('-')]
                data['latest_draw'] = {
                    'date': date,
                    'numbers': numbers[:-1],
                    'bonus': numbers[-1],
                    'jackpot': jackpot
                }
        
        logger.info("🎉 Loaded data from files like a champ! 🚀")
        return data
    except Exception as e:
        logger.error("😣 Trouble loading files: %s. Fetching fresh data! 🌟", e)
        return scrape_draw_tables()

# Generate one set of numbers
def generate_number_set(data):
    main_freq = data['main_freq']
    hot_numbers = data['hot_numbers']
    overdue_numbers = data['overdue_numbers']
    common_pairs = data['common_pairs']
    
    # Pick a common pair
    selected_pair = random.choice(common_pairs)
    main_numbers = list(selected_pair)
    
    # Add hot numbers, no dupes
    hot_candidates = [num for num in hot_numbers.keys() if num not in main_numbers]
    main_numbers.extend(random.sample(hot_candidates, min(3, len(hot_candidates))))
    
    # Add one overdue number
    overdue_candidates = [num for num in overdue_numbers.keys() if num not in main_numbers]
    if overdue_candidates:
        main_numbers.append(random.choice(overdue_candidates))
    
    # Fill the rest randomly
    remaining_slots = 7 - len(main_numbers)
    available_nums = [num for num in range(1, 51) if num not in main_numbers]
    main_numbers.extend(random.sample(available_nums, min(remaining_slots, len(available_nums))))
    
    # Cap at 7 numbers
    main_numbers = main_numbers[:7]
    
    # Balance odds/evens (aim for 3-4 odds)
    odds = sum(1 for num in main_numbers if num % 2 == 1)
    evens = 7 - odds
    available_nums = [num for num in range(1, 51) if num not in main_numbers]
    
    for _ in range(2):
        if odds < 3 and available_nums:
            odd_nums = [num for num in available_nums if num % 2 == 1]
            if odd_nums:
                new_num = random.choice(odd_nums)
                main_numbers[random.randint(0, 6)] = new_num
                available_nums.remove(new_num)
        elif odds > 4 and available_nums:
            even_nums = [num for num in available_nums if num % 2 == 0]
            if even_nums:
                new_num = random.choice(even_nums)
                main_numbers[random.randint(0, 6)] = new_num
                available_nums.remove(new_num)
    
    # Pick bonus number based on freq
    bonus_prob = {k: v/sum(data['bonus_freq'].values()) for k, v in data['bonus_freq'].items()}
    bonus_number = random.choices(list(bonus_prob.keys()), weights=list(bonus_prob.values()), k=1)[0]
    
    return sorted(main_numbers), bonus_number

# Generate five unique sets
def generate_five_sets(data):
    sets = []
    used_numbers = set()
    
    for _ in range(5):
        while True:
            main_numbers, bonus_number = generate_number_set(data)
            main_tuple = tuple(main_numbers)
            if main_tuple not in used_numbers:
                used_numbers.add(main_tuple)
                sets.append((main_numbers, bonus_number))
                break
    return sets

# Main vibe
def main():
    logger.info("🎉 Kicking off the Lotto Max party! 🥳")
    
    # Fetch or load data
    if should_fetch_data():
        data = scrape_draw_tables()
    else:
        data = load_from_files()
    
    # Show latest draw
    latest_draw = data['latest_draw']
    logger.info("🔥 Latest Draw: %s", latest_draw['date'])
    logger.info("🎰 Numbers: %s, Bonus: %s", latest_draw['numbers'], latest_draw['bonus'])
    print(f"\nLatest Draw: {latest_draw['date']}")
    print(f"Numbers: {latest_draw['numbers']}, Bonus: {latest_draw['bonus']}\n")
    
    # Cook up some number sets
    logger.info("🎲 Whipping up 5 Lotto Max number sets! 🍳")
    number_sets = generate_five_sets(data)
    
    # Show the goods
    print("=== Your 5 Lotto Max Number Sets ===")
    for i, (main_numbers, bonus_number) in enumerate(number_sets, 1):
        print(f"Set {i}: {main_numbers}, Bonus: {bonus_number}")
        logger.info("🌟 Set %d: %s, Bonus: %s", i, main_numbers, bonus_number)
    print("\nNote: Play these for fun! Swap 'em out every few draws. Lotteries are random, so just enjoy the ride! 🎢")
    logger.info("🏁 All done! Go dream big! 💰")

if __name__ == "__main__":
    main()