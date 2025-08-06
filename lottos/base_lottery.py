from abc import ABC, abstractmethod
import os
import logging
from datetime import datetime
from collections import Counter

class BaseLottery(ABC):
    """Abstract base class for all lottery games"""
    
    def __init__(self, name, data_dir):
        self.name = name
        self.data_dir = data_dir
        self.debug_mode = False  # Will be set by main app
        self.logger = logging.getLogger(f"{name.lower().replace(' ', '_')}")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # File paths
        self.past_numbers_file = os.path.join(data_dir, "past_numbers.txt")
        self.statistics_file = os.path.join(data_dir, "statistics.txt")
        self.log_file = os.path.join(data_dir, f"{name.lower().replace(' ', '_')}.log")
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for this lottery"""
        # Only add file handler, no console handler
        handler = logging.FileHandler(self.log_file, mode='a')
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        # Prevent logging from propagating to root logger
        self.logger.propagate = False
    
    def log_message(self, message):
        """Log message only if debug mode is enabled"""
        if self.debug_mode:
            print(message)
        # Always log to file
        self.logger.info(message)
    
    @abstractmethod
    def get_game_config(self):
        """Return game configuration (main_numbers_range, bonus_range, etc.)"""
        pass
    
    @abstractmethod
    def get_scraping_urls(self):
        """Return URLs for scraping historical data"""
        pass
    
    @abstractmethod
    def parse_draw_row(self, row):
        """Parse a single draw row from scraped data"""
        pass
    
    @abstractmethod
    def should_fetch_data(self):
        """Check if new data should be fetched"""
        pass
    
    def scrape_draw_tables(self):
        """Scrape and save historical draw data"""
        self.log_message(f"🧹 Scraping {self.name} draw history...")
        
        try:
            all_draws = self._scrape_all_years()
            if all_draws:
                self._save_draws_to_file(all_draws)
                self.log_message(f"✅ {self.past_numbers_file} updated with full draw history! 🎯")
            else:
                self.log_message("⚠️ No draws scraped.")
        except Exception as e:
            self.log_message(f"💥 Error scraping data: {e}")
    
    @abstractmethod
    def _scrape_all_years(self):
        """Scrape data for all years - implemented by each lottery"""
        pass
    
    def _save_draws_to_file(self, draws):
        """Save draws to past_numbers.txt file"""
        with open(self.past_numbers_file, "w") as f:
            f.write("Date,Draw Results,Jackpot\n")
            for draw in draws:
                f.write(f"{draw[0]},{draw[1]},\"{draw[2]}\"\n")
    
    def generate_statistics_from_past_numbers(self):
        """Generate comprehensive statistics.txt from past_numbers.txt data"""
        if not os.path.exists(self.past_numbers_file):
            return
        
        config = self.get_game_config()
        main_freq = Counter()
        bonus_freq = Counter()
        all_pairs = []
        consecutive_pairs = []
        all_triplets = []
        consecutive_triplets = []
        
        with open(self.past_numbers_file, 'r') as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    numbers = [int(n) for n in parts[1].split('-')]
                    main_nums = sorted(numbers[:config['main_count']])  # Sort for consecutive analysis
                    if len(numbers) > config['main_count']:
                        bonus_num = numbers[config['main_count']]
                        bonus_freq[bonus_num] += 1
                    
                    # Count frequencies
                    for num in main_nums:
                        main_freq[num] += 1
                    
                    # Collect all pairs
                    for i in range(len(main_nums)):
                        for j in range(i+1, len(main_nums)):
                            all_pairs.append(tuple(sorted([main_nums[i], main_nums[j]])))
                            # Check for consecutive pairs
                            if abs(main_nums[i] - main_nums[j]) == 1:
                                consecutive_pairs.append(tuple(sorted([main_nums[i], main_nums[j]])))
                    
                    # Collect all triplets
                    for i in range(len(main_nums)):
                        for j in range(i+1, len(main_nums)):
                            for k in range(j+1, len(main_nums)):
                                triplet = tuple(sorted([main_nums[i], main_nums[j], main_nums[k]]))
                                all_triplets.append(triplet)
                                
                                # Check for consecutive triplets
                                sorted_triplet = sorted([main_nums[i], main_nums[j], main_nums[k]])
                                if (sorted_triplet[1] - sorted_triplet[0] == 1 and 
                                    sorted_triplet[2] - sorted_triplet[1] == 1):
                                    consecutive_triplets.append(tuple(sorted_triplet))
        
        # Calculate statistics
        pair_freq = Counter(all_pairs)
        consecutive_pair_freq = Counter(consecutive_pairs)
        triplet_freq = Counter(all_triplets)
        consecutive_triplet_freq = Counter(consecutive_triplets)
        
        # Get top items for each category
        common_pairs = pair_freq.most_common(20)
        common_consecutive_pairs = consecutive_pair_freq.most_common(10)
        common_triplets = triplet_freq.most_common(15)
        common_consecutive_triplets = consecutive_triplet_freq.most_common(10)
        
        # Hot numbers (most frequent)
        hot_numbers = dict(main_freq.most_common(15))
        
        # Cold numbers (least frequent)
        cold_numbers = dict(main_freq.most_common()[:-16:-1])  # Get 15 least frequent
        
        # Most overdue numbers (simulate as inverse frequency)
        all_numbers_freq = dict(main_freq.most_common())
        max_freq = max(all_numbers_freq.values()) if all_numbers_freq else 0
        overdue_numbers = {num: max_freq - freq + 10 for num, freq in main_freq.most_common()[-15:]}
        
        # Write comprehensive statistics file
        with open(self.statistics_file, 'w') as f:
            f.write("Main Number Frequencies:\n")
            for num, freq in sorted(main_freq.items()):
                f.write(f"{num}: {freq}\n")
            
            f.write("\nBonus Number Frequencies:\n")
            for num, freq in sorted(bonus_freq.items()):
                f.write(f"{num}: {freq}\n")
            
            f.write("\nHot Numbers:\n")
            for num, freq in hot_numbers.items():
                f.write(f"{num}: {freq}\n")
            
            f.write("\nCold Numbers:\n")
            for num, freq in cold_numbers.items():
                f.write(f"{num}: {freq}\n")
            
            f.write("\nMost Overdue Numbers:\n")
            for num, days in sorted(overdue_numbers.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{num}: {days}\n")
            
            f.write("\nMost Common Pairs:\n")
            for (num1, num2), freq in common_pairs:
                f.write(f"{num1}-{num2}: {freq}\n")
            
            f.write("\nMost Common Consecutive Pairs:\n")
            for (num1, num2), freq in common_consecutive_pairs:
                f.write(f"{num1}-{num2}: {freq}\n")
            
            f.write("\nMost Common Triplets:\n")
            for (num1, num2, num3), freq in common_triplets:
                f.write(f"{num1}-{num2}-{num3}: {freq}\n")
            
            f.write("\nMost Common Consecutive Triplets:\n")
            for (num1, num2, num3), freq in common_consecutive_triplets:
                f.write(f"{num1}-{num2}-{num3}: {freq}\n")
    
    def load_from_files(self):
        """Load lottery data from files"""
        self.log_message("📂 Loading data from files! 🗃️")
        data = {
            'main_freq': {}, 'bonus_freq': {}, 'hot_numbers': {}, 'cold_numbers': {},
            'overdue_numbers': {}, 'common_pairs': [], 'consecutive_pairs': [],
            'common_triplets': [], 'consecutive_triplets': [], 'latest_draw': {}
        }
        
        try:
            # Generate statistics if missing
            if not os.path.exists(self.statistics_file):
                self.generate_statistics_from_past_numbers()
            
            # Load statistics
            self._load_statistics(data)
            
            # Load latest draw
            self._load_latest_draw(data)
            
            self.log_message("🎉 Loaded data from files like a champ! 🚀")
            return data
        except Exception as e:
            self.log_message(f"😣 Trouble loading files: {e}. Fetching fresh data! 🌟")
            self.scrape_draw_tables()
            return self.load_from_files()
    
    def _load_statistics(self, data):
        """Load statistics from statistics.txt"""
        with open(self.statistics_file, 'r') as f:
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
                elif line == "Cold Numbers:":
                    section = 'cold_numbers'
                elif line == "Most Overdue Numbers:":
                    section = 'overdue_numbers'
                elif line == "Most Common Pairs:":
                    section = 'common_pairs'
                elif line == "Most Common Consecutive Pairs:":
                    section = 'consecutive_pairs'
                elif line == "Most Common Triplets:":
                    section = 'common_triplets'
                elif line == "Most Common Consecutive Triplets:":
                    section = 'consecutive_triplets'
                elif line and section and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        num_part = parts[0].strip()
                        value = int(parts[1].strip())
                        
                        if section in ['common_pairs', 'consecutive_pairs']:
                            num1, num2 = map(int, num_part.split('-'))
                            data[section].append((num1, num2))
                        elif section in ['common_triplets', 'consecutive_triplets']:
                            num1, num2, num3 = map(int, num_part.split('-'))
                            data[section].append((num1, num2, num3))
                        else:
                            data[section][int(num_part)] = value
                elif line and section in ['common_pairs', 'consecutive_pairs'] and '-' in line and ':' not in line:
                    # Handle pairs without frequency values
                    num1, num2 = map(int, line.split('-'))
                    data[section].append((num1, num2))
                elif line and section in ['common_triplets', 'consecutive_triplets'] and '-' in line and ':' not in line:
                    # Handle triplets without frequency values
                    num1, num2, num3 = map(int, line.split('-'))
                    data[section].append((num1, num2, num3))
    
    def _load_latest_draw(self, data):
        """Load latest draw from past_numbers.txt"""
        config = self.get_game_config()
        with open(self.past_numbers_file, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                last_line = lines[1].strip()  # Skip header, get first data line
                parts = last_line.split(',')
                date = parts[0]
                numbers = parts[1]
                jackpot = ','.join(parts[2:]) if len(parts) > 2 else ''
                numbers = [int(n) for n in numbers.split('-')]
                
                data['latest_draw'] = {
                    'date': date,
                    'numbers': numbers[:config['main_count']],
                    'jackpot': jackpot.strip('"')
                }
                
                # Add bonus if applicable
                if len(numbers) > config['main_count']:
                    data['latest_draw']['bonus'] = numbers[config['main_count']]
    
    def get_latest_draw_info(self):
        """Get formatted latest draw information"""
        data = self.load_from_files()
        latest = data.get('latest_draw', {})
        if not latest:
            return "No draw data available"
        
        info = f"Latest {self.name} Draw: {latest.get('date', 'Unknown')}\n"
        info += f"Numbers: {latest.get('numbers', [])}"
        if 'bonus' in latest:
            info += f", Bonus: {latest['bonus']}"
        if 'jackpot' in latest:
            info += f"\nJackpot: {latest['jackpot']}"
        return info
    
    def get_statistics_summary(self):
        """Get comprehensive formatted statistics summary"""
        data = self.load_from_files()
        
        summary = f"\n" + "="*60 + "\n"
        summary += f"🎰 {self.name} COMPREHENSIVE STATISTICS 🎰\n"
        summary += "="*60 + "\n\n"
        
        # Hot numbers (use main_freq directly for accuracy)
        if data['main_freq']:
            hot = sorted(data['main_freq'].items(), key=lambda x: x[1], reverse=True)[:15]
            hot_nums = [num for num, freq in hot]
            summary += "🔥 HOT LOTTO MAX NUMBERS (Most Frequent):\n"
            summary += f"   {hot_nums[:10]}\n"
            summary += f"   {hot_nums[10:]}\n\n"
        
        # Cold numbers (use main_freq directly for accuracy)
        if data['main_freq']:
            cold = sorted(data['main_freq'].items(), key=lambda x: x[1])[:15]
            cold_nums = [num for num, freq in cold]
            summary += "🥶 COLD LOTTO MAX NUMBERS (Least Frequent):\n"
            summary += f"   {cold_nums[:10]}\n"
            summary += f"   {cold_nums[10:]}\n\n"
        
        # Most overdue numbers (use main_freq for calculation)
        if data['main_freq']:
            # Calculate overdue based on inverse frequency
            all_freq = sorted(data['main_freq'].items(), key=lambda x: x[1])[:15]
            overdue_nums = [num for num, freq in all_freq]
            summary += "⏰ MOST OVERDUE LOTTO MAX NUMBERS:\n"
            summary += f"   {overdue_nums[:10]}\n"
            summary += f"   {overdue_nums[10:]}\n\n"
        
        # Most common pairs
        if data['common_pairs']:
            pairs = data['common_pairs'][:10]
            summary += "👫 MOST COMMON PAIRS:\n"
            summary += f"   {[f'({pair[0]}-{pair[1]})' for pair in pairs[:5]]}\n"
            summary += f"   {[f'({pair[0]}-{pair[1]})' for pair in pairs[5:]]}\n\n"
        
        # Most common consecutive pairs
        if data['consecutive_pairs']:
            cons_pairs = data['consecutive_pairs'][:8]
            summary += "🔗 MOST COMMON CONSECUTIVE PAIRS:\n"
            summary += f"   {[f'({pair[0]}-{pair[1]})' for pair in cons_pairs[:4]]}\n"
            summary += f"   {[f'({pair[0]}-{pair[1]})' for pair in cons_pairs[4:]]}\n\n"
        
        # Most common triplets
        if data['common_triplets']:
            triplets = data['common_triplets'][:8]
            summary += "🎯 MOST COMMON TRIPLETS:\n"
            summary += f"   {[f'({trip[0]}-{trip[1]}-{trip[2]})' for trip in triplets[:4]]}\n"
            summary += f"   {[f'({trip[0]}-{trip[1]}-{trip[2]})' for trip in triplets[4:]]}\n\n"
        
        # Most common consecutive triplets
        if data['consecutive_triplets']:
            cons_triplets = data['consecutive_triplets'][:6]
            summary += "🔗 MOST COMMON CONSECUTIVE TRIPLETS:\n"
            summary += f"   {[f'({trip[0]}-{trip[1]}-{trip[2]})' for trip in cons_triplets[:3]]}\n"
            summary += f"   {[f'({trip[0]}-{trip[1]}-{trip[2]})' for trip in cons_triplets[3:]]}\n\n"
        
        summary += "="*60 + "\n"
        summary += "📊 Numbers sorted by frequency (hot to cold) and recency\n"
        summary += "="*60
        
        return summary