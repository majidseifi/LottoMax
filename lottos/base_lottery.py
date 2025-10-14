from abc import ABC, abstractmethod
import os
import logging
from datetime import datetime
from collections import Counter
from dateutil.parser import parse as parse_date
from .api_client import CanadaLotteryAPI

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

        # API client
        self.api_client = CanadaLotteryAPI()

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
    def get_api_lottery_type(self):
        """Return API lottery type identifier (e.g., 'lottomax', '6-49', 'daily-grand')"""
        pass

    @abstractmethod
    def parse_api_draw(self, draw_data):
        """
        Parse a single draw from API response

        Args:
            draw_data: Dictionary from API response

        Returns:
            Tuple of (formatted_date, formatted_numbers, jackpot_string)
        """
        pass

    @abstractmethod
    def get_year_range(self):
        """Return tuple of (start_year, end_year) for this lottery"""
        pass
    
    def fetch_from_api(self):
        """Fetch all historical draw data from API"""
        self.log_message(f"🌐 Fetching {self.name} draw history from API...")

        try:
            start_year, end_year = self.get_year_range()
            lottery_type = self.get_api_lottery_type()

            all_draws = []
            for year in range(start_year, end_year + 1):
                self.log_message(f"📅 Fetching data for {year}...")
                year_draws = self.api_client.fetch_draws_for_year(lottery_type, year)

                if year_draws:
                    for draw in year_draws:
                        parsed_draw = self.parse_api_draw(draw)
                        if parsed_draw:
                            all_draws.append(parsed_draw)

            if all_draws:
                # Sort by date (newest first)
                all_draws.sort(key=lambda x: parse_date(x[0]), reverse=True)
                self._save_draws_to_file(all_draws)
                self.log_message(f"✅ {self.past_numbers_file} updated with full draw history! 🎯")

                # Auto-regenerate statistics
                self.log_message("📊 Regenerating statistics...")
                self.generate_statistics_from_past_numbers()
                self.log_message("✅ Statistics updated!")
            else:
                self.log_message("⚠️ No draws fetched from API.")

        except Exception as e:
            self.log_message(f"💥 Error fetching data from API: {e}")

    def check_for_new_draws(self):
        """
        Check if there are new draws available from API

        Returns:
            Integer count of new draws available, 0 if none or on error
        """
        try:
            # If no local file exists, all draws are "new"
            if not os.path.exists(self.past_numbers_file):
                self.log_message(f"📁 No local data found for {self.name}")
                return -1  # Special value indicating initial fetch needed

            # Get local latest date
            with open(self.past_numbers_file, 'r') as f:
                lines = f.readlines()
                if len(lines) <= 1:  # Empty or header only
                    return -1

                # First data line (newest draw)
                last_line = lines[1].strip()
                local_date_str = last_line.split(',')[0]
                local_date = parse_date(local_date_str)

            # Get latest draw from API
            lottery_type = self.get_api_lottery_type()
            current_year = datetime.now().year

            # Try current year and previous year (in case we're at year boundary)
            api_draws = []
            for year in [current_year, current_year - 1]:
                year_draws = self.api_client.fetch_draws_for_year(lottery_type, year)
                if year_draws:
                    api_draws.extend(year_draws)

            if not api_draws:
                self.log_message(f"⚠️ Could not fetch data from API for {self.name}")
                return 0

            # Count draws newer than local latest
            new_count = 0
            for draw in api_draws:
                parsed_draw = self.parse_api_draw(draw)
                if parsed_draw:
                    api_date = parse_date(parsed_draw[0])
                    if api_date > local_date:
                        new_count += 1

            return new_count

        except Exception as e:
            self.log_message(f"❌ Error checking for new draws: {e}")
            return 0

    def _get_local_draw_counts(self):
        """
        Efficiently count draws per year from local file (single pass)

        Returns:
            Dictionary mapping year to draw count
        """
        local_draws_per_year = {}

        if not os.path.exists(self.past_numbers_file):
            return local_draws_per_year

        try:
            with open(self.past_numbers_file, 'r') as f:
                next(f)  # Skip header
                for line in f:
                    if line.strip():
                        date_str = line.split(',', 1)[0]  # Only split once, get first field
                        try:
                            year = parse_date(date_str).year
                            local_draws_per_year[year] = local_draws_per_year.get(year, 0) + 1
                        except:
                            continue
        except Exception as e:
            self.log_message(f"⚠️ Error reading local file: {e}")

        return local_draws_per_year

    def check_for_missing_years(self, quick_check=False, progress_callback=None):
        """
        Check for gaps in historical data by comparing draw counts with API

        Args:
            quick_check: If True, only check last 3 years (faster)
            progress_callback: Function to call with progress updates (year, total)

        Returns:
            Dictionary mapping year to issue details, empty dict if complete
        """
        try:
            if not os.path.exists(self.past_numbers_file):
                self.log_message("📁 No local data file found")
                return {}

            # OPTIMIZATION 1: Single-pass local file reading
            local_draws_per_year = self._get_local_draw_counts()

            # Get expected year range
            start_year, end_year = self.get_year_range()

            # OPTIMIZATION 2: Quick check mode - only check recent years
            if quick_check:
                start_year = max(start_year, end_year - 2)  # Last 3 years only
                self.log_message(f"📋 Quick check mode: checking {start_year}-{end_year}")

            lottery_type = self.get_api_lottery_type()
            years_to_check = list(range(start_year, end_year + 1))
            total_years = len(years_to_check)

            # OPTIMIZATION 3: Check each year against API with progress
            years_with_issues = {}

            for idx, year in enumerate(years_to_check, 1):
                # Progress callback for UI updates
                if progress_callback:
                    progress_callback(year, idx, total_years)

                self.log_message(f"🔍 Checking {year}... ({idx}/{total_years})")

                # Get API count for this year
                api_draws = self.api_client.fetch_draws_for_year(lottery_type, year)
                api_count = len(api_draws) if api_draws else 0

                # Get local count for this year (O(1) lookup in dictionary)
                local_count = local_draws_per_year.get(year, 0)

                # If counts don't match, we have missing or extra data
                if api_count != local_count:
                    years_with_issues[year] = {
                        'api_count': api_count,
                        'local_count': local_count,
                        'missing': api_count - local_count
                    }
                    self.log_message(f"⚠️  {year}: API has {api_count}, local has {local_count}")

            return years_with_issues

        except Exception as e:
            self.log_message(f"❌ Error checking for missing data: {e}")
            return {}

    def fetch_missing_years(self, years_with_issues):
        """
        Refetch data for years with missing draws and replace local data

        Args:
            years_with_issues: Dictionary mapping year to issue details

        Returns:
            Number of draws added
        """
        if not years_with_issues:
            return 0

        years_list = sorted(years_with_issues.keys())
        self.log_message(f"🔄 Refetching data for years with issues: {years_list}")

        try:
            lottery_type = self.get_api_lottery_type()

            # Read existing data and filter out problematic years
            existing_draws = []
            if os.path.exists(self.past_numbers_file):
                with open(self.past_numbers_file, 'r') as f:
                    existing_lines = f.readlines()[1:]  # Skip header

                for line in existing_lines:
                    if line.strip():
                        parts = line.strip().split(',', 2)
                        if len(parts) >= 3:
                            try:
                                date_obj = parse_date(parts[0])
                                # Only keep draws from years that are NOT being refetched
                                if date_obj.year not in years_with_issues:
                                    existing_draws.append((parts[0], parts[1], parts[2].strip('"')))
                            except:
                                continue

            # Fetch fresh data for problematic years
            new_draws = []
            for year in years_list:
                self.log_message(f"📅 Refetching {year}...")
                year_draws = self.api_client.fetch_draws_for_year(lottery_type, year)

                if year_draws:
                    for draw in year_draws:
                        parsed_draw = self.parse_api_draw(draw)
                        if parsed_draw:
                            new_draws.append(parsed_draw)

            if not new_draws:
                self.log_message("⚠️ No draws fetched from API")
                return 0

            # Combine all draws (existing from good years + new from refetched years)
            all_draws = new_draws + existing_draws

            # Sort by date (newest first)
            all_draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

            # Remove any duplicates (shouldn't happen, but just in case)
            seen_dates = set()
            unique_draws = []
            for draw in all_draws:
                if draw[0] not in seen_dates:
                    seen_dates.add(draw[0])
                    unique_draws.append(draw)

            # Save combined data
            self._save_draws_to_file(unique_draws)

            total_added = len(new_draws) - sum(info['local_count'] for info in years_with_issues.values())
            self.log_message(f"✅ Refetched {len(new_draws)} draws, net change: +{total_added}")

            # Auto-regenerate statistics
            self.log_message("📊 Regenerating statistics...")
            self.generate_statistics_from_past_numbers()
            self.log_message("✅ Statistics updated!")

            return len(new_draws)

        except Exception as e:
            self.log_message(f"💥 Error fetching missing data: {e}")
            return 0

    def update_from_api(self):
        """Fetch only new draws and update local data"""
        self.log_message(f"🔄 Updating {self.name} with new draws from API...")

        try:
            # Get local latest date
            local_date = None
            if os.path.exists(self.past_numbers_file):
                with open(self.past_numbers_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        last_line = lines[1].strip()
                        local_date_str = last_line.split(',')[0]
                        local_date = parse_date(local_date_str)

            # Fetch recent draws from API
            lottery_type = self.get_api_lottery_type()
            current_year = datetime.now().year

            new_draws = []
            for year in [current_year, current_year - 1]:
                year_draws = self.api_client.fetch_draws_for_year(lottery_type, year)
                if year_draws:
                    for draw in year_draws:
                        parsed_draw = self.parse_api_draw(draw)
                        if parsed_draw:
                            api_date = parse_date(parsed_draw[0])
                            if local_date is None or api_date > local_date:
                                new_draws.append(parsed_draw)

            if new_draws:
                # Sort newest first
                new_draws.sort(key=lambda x: parse_date(x[0]), reverse=True)

                # Merge with existing data
                if os.path.exists(self.past_numbers_file):
                    with open(self.past_numbers_file, 'r') as f:
                        existing_lines = f.readlines()
                else:
                    existing_lines = ["Date,Draw Results,Jackpot\n"]

                # Write new draws at the top
                with open(self.past_numbers_file, 'w') as f:
                    f.write(existing_lines[0])  # Header
                    for draw in new_draws:
                        jackpot_clean = str(draw[2]).replace('\n', ' ').replace('\r', ' ').replace('"', '""')
                        f.write(f"{draw[0]},{draw[1]},\"{jackpot_clean}\"\n")
                    # Write existing draws (skip header)
                    for line in existing_lines[1:]:
                        f.write(line)

                self.log_message(f"✅ Added {len(new_draws)} new draw(s) to {self.past_numbers_file}")

                # Auto-regenerate statistics
                self.log_message("📊 Regenerating statistics...")
                self.generate_statistics_from_past_numbers()
                self.log_message("✅ Statistics updated!")

                return len(new_draws)
            else:
                self.log_message("ℹ️ No new draws to add")
                return 0

        except Exception as e:
            self.log_message(f"💥 Error updating from API: {e}")
            return 0

    def _save_draws_to_file(self, draws):
        """Save draws to past_numbers.txt file"""
        with open(self.past_numbers_file, "w") as f:
            f.write("Date,Draw Results,Jackpot\n")
            for draw in draws:
                # Clean jackpot text and escape quotes properly
                jackpot_clean = str(draw[2]).replace('\n', ' ').replace('\r', ' ').replace('"', '""')
                f.write(f"{draw[0]},{draw[1]},\"{jackpot_clean}\"\n")
    
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
            self.fetch_from_api()
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
            summary += f"🔥 HOT {self.name.upper()} NUMBERS (Most Frequent):\n"
            summary += f"   {hot_nums[:10]}\n"
            summary += f"   {hot_nums[10:]}\n\n"
        
        # Cold numbers (use main_freq directly for accuracy)
        if data['main_freq']:
            cold = sorted(data['main_freq'].items(), key=lambda x: x[1])[:15]
            cold_nums = [num for num, freq in cold]
            summary += f"🥶 COLD {self.name.upper()} NUMBERS (Least Frequent):\n"
            summary += f"   {cold_nums[:10]}\n"
            summary += f"   {cold_nums[10:]}\n\n"
        
        # Most overdue numbers (use main_freq for calculation)
        if data['main_freq']:
            # Calculate overdue based on inverse frequency
            all_freq = sorted(data['main_freq'].items(), key=lambda x: x[1])[:15]
            overdue_nums = [num for num, freq in all_freq]
            summary += f"⏰ MOST OVERDUE {self.name.upper()} NUMBERS:\n"
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