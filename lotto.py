#!/usr/bin/env python3
"""
Multi-Lottery System
Supports Lotto Max, Lotto 6/49, and Daily Grand
"""

import os
import sys
import logging
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lottos.lotto_max import LottoMax
from lottos.lotto_649 import Lotto649
from lottos.daily_grand import DailyGrand
from lottos.strategies.base_strategy import StrategyManager

# Setup main logging (no console output, only file logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[]  # No default handlers
)
logger = logging.getLogger(__name__)

class LottoApp:
    """Main application class for the multi-lottery system"""
    
    def __init__(self):
        self.lotteries = {
            '1': LottoMax(),
            '2': Lotto649(),
            '3': DailyGrand(),
        }
        self.strategy_manager = StrategyManager()
        self.current_lottery = None
        self.current_strategy = "frequency"  # Default strategy
        self.debug_mode = False  # Debug logging toggle
        
        # Set debug mode on all lottery instances
        self._update_lottery_debug_mode()
    
    def show_main_menu(self):
        """Display the main lottery selection menu"""
        print("\n" + "="*50)
        print("🎰 Welcome to the Multi-Lottery System! 🎰")
        print("="*50)
        print("1. 🎯 Lotto Max")
        print("2. 🎲 Lotto 6/49")
        print("3. 🌟 Daily Grand")
        print("4. ⚙️  System Config")
        print("5. 🚪 Exit")
        print("="*50)
        debug_status = "ON" if self.debug_mode else "OFF"
        print(f"💡 Debug Mode: {debug_status}")
    
    def _update_lottery_debug_mode(self):
        """Update debug mode on all lottery instances"""
        for lottery in self.lotteries.values():
            lottery.debug_mode = self.debug_mode
    
    def show_lottery_menu(self, lottery_name):
        """Display the menu for a specific lottery"""
        print(f"\n" + "="*50)
        print(f"🎰 {lottery_name} Menu 🎰")
        print("="*50)
        print("1. 🎲 Generate Numbers")
        print("2. 📊 View Latest Draw")
        print("3. 📈 View Statistics")
        print("4. 🔄 Update Statistics")
        print("5. ⚙️  Configure Strategy")
        print("0. ⬅️  Back to Main Menu")
        print("="*50)
    
    def show_number_generation_menu(self):
        """Display the number generation submenu"""
        print(f"\n" + "="*40)
        print("🎲 Number Generation 🎲")
        print("="*40)
        print(f"Current Strategy: 🎯 {self.current_strategy.title()}")
        print("1. 🎯 Generate Single Set")
        print("2. 🎯 Generate Multiple Sets")
        print("3. ⚙️  Change Strategy")
        print("0. ⬅️  Back")
        print("="*40)
    
    def show_strategy_menu(self):
        """Display available strategies"""
        print(f"\n" + "="*40)
        print("⚙️ Strategy Selection ⚙️")
        print("="*40)
        print("1. 🔥 Frequency Strategy (Hot/Cold Numbers)")
        print("2. 🎲 Random Strategy")
        print("3. 📊 Balanced Strategy (Mix of approaches)")
        print("0. ⬅️  Back")
        print("="*40)
        debug_status = "ON" if self.debug_mode else "OFF"
        print(f"💡 Debug Mode: {debug_status}")
    
    def show_config_menu(self):
        """Display the system configuration menu"""
        print(f"\n" + "="*50)
        print("⚙️ System Configuration ⚙️")
        print("="*50)
        debug_status = "ON" if self.debug_mode else "OFF"
        print(f"1. 🐛 Debug Mode: {debug_status}")
        print("2. 🌐 Update Lottery Data from API")
        print("3. 🔍 Check for Missing Data")
        print("0. ⬅️  Back to Main Menu")
        print("="*50)
    
    def get_user_choice(self, max_choice: int, allow_zero: bool = False) -> int:
        """Get and validate user input"""
        while True:
            try:
                min_choice = 0 if allow_zero else 1
                range_text = f"{min_choice}-{max_choice}" if allow_zero else f"1-{max_choice}"
                choice = input(f"\nEnter your choice ({range_text}): ").strip()
                
                # Check for quit command
                if choice.lower() == ':qa':
                    print("\n👋 Exiting... Goodbye!")
                    sys.exit(0)
                
                choice_num = int(choice)
                if min_choice <= choice_num <= max_choice:
                    return choice_num
                else:
                    print(f"❌ Please enter a number between {min_choice} and {max_choice}")
            except ValueError:
                print("❌ Please enter a valid number or ':qa' to quit")
            except KeyboardInterrupt:
                print("\n👋 Exiting... Goodbye!")
                sys.exit(0)
    
    def handle_main_menu(self):
        """Handle main menu selection"""
        while True:
            self.show_main_menu()
            choice = self.get_user_choice(5)
            
            if choice == 1:
                self.current_lottery = self.lotteries['1']
                self.handle_lottery_menu()
            elif choice == 2:
                self.current_lottery = self.lotteries['2']
                self.handle_lottery_menu()
            elif choice == 3:
                self.current_lottery = self.lotteries['3']
                self.handle_lottery_menu()
            elif choice == 4:
                self.handle_config_menu()
            elif choice == 5:
                print("👋 Thanks for playing! Goodbye! 🎰")
                sys.exit(0)
    
    def handle_lottery_menu(self):
        """Handle lottery-specific menu"""
        while True:
            self.show_lottery_menu(self.current_lottery.name)
            choice = self.get_user_choice(5, allow_zero=True)

            if choice == 1:
                self.handle_number_generation()
            elif choice == 2:
                self.show_latest_draw()
            elif choice == 3:
                self.show_statistics()
            elif choice == 4:
                self.update_statistics()
            elif choice == 5:
                self.configure_strategy()
            elif choice == 0:
                self.current_lottery = None
                return
    
    def handle_number_generation(self):
        """Handle number generation submenu"""
        while True:
            self.show_number_generation_menu()
            choice = self.get_user_choice(3, allow_zero=True)
            
            if choice == 1:
                self.generate_single_set()
            elif choice == 2:
                self.generate_multiple_sets()
            elif choice == 3:
                self.change_strategy()
            elif choice == 0:
                return
    
    def generate_single_set(self):
        """Generate a single set of numbers"""
        self.log_message(f"\n🎲 Generating numbers using {self.current_strategy} strategy...")
        try:
            data = self.current_lottery.load_from_files()
            strategy = self.strategy_manager.get_strategy(self.current_strategy)
            main_numbers, bonus_number = strategy.generate_numbers(data, self.current_lottery.get_game_config())
            
            print("\n🎯 Your Lucky Numbers:")
            print(f"Main Numbers: {sorted(main_numbers)}")
            if bonus_number is not None:
                print(f"Bonus Number: {bonus_number}")
            print("\n🍀 Good luck! 🍀")
            
        except Exception as e:
            print(f"❌ Error generating numbers: {e}")
        
        input("\nPress Enter to continue...")
    
    def generate_multiple_sets(self):
        """Generate multiple sets of numbers"""
        while True:
            try:
                count = int(input("\nHow many sets would you like (1-10)? "))
                if 1 <= count <= 10:
                    break
                else:
                    print("❌ Please enter a number between 1 and 10")
            except ValueError:
                print("❌ Please enter a valid number")
        
        self.log_message(f"\n🎲 Generating {count} sets using {self.current_strategy} strategy...")
        
        try:
            data = self.current_lottery.load_from_files()
            strategy = self.strategy_manager.get_strategy(self.current_strategy)
            config = self.current_lottery.get_game_config()
            
            print(f"\n🎯 Your {count} Lucky Number Sets:")
            print("=" * 40)
            
            used_sets = set()
            sets_generated = 0
            attempts = 0
            max_attempts = count * 10
            
            while sets_generated < count and attempts < max_attempts:
                attempts += 1
                main_numbers, bonus_number = strategy.generate_numbers(data, config)
                main_tuple = tuple(sorted(main_numbers))
                
                if main_tuple not in used_sets:
                    used_sets.add(main_tuple)
                    sets_generated += 1
                    print(f"Set {sets_generated}: {sorted(main_numbers)}", end="")
                    if bonus_number is not None:
                        print(f", Bonus: {bonus_number}")
                    else:
                        print()
            
            print("=" * 40)
            print("🍀 Good luck with all your sets! 🍀")
            
        except Exception as e:
            print(f"❌ Error generating numbers: {e}")
        
        input("\nPress Enter to continue...")
    
    def show_latest_draw(self):
        """Show latest draw information"""
        self.log_message("\n📊 Loading latest draw information...")
        try:
            info = self.current_lottery.get_latest_draw_info()
            print(f"\n{info}")
        except Exception as e:
            print(f"❌ Error loading draw information: {e}")
        
        input("\nPress Enter to continue...")
    
    def update_lottery_data_from_api(self):
        """Check for new draws via API and prompt user for updates"""
        print("\n" + "="*50)
        print("🌐 Checking for new lottery data from API...")
        print("="*50)

        # Check all lotteries for new data
        updates_available = {}
        for key, lottery in self.lotteries.items():
            try:
                new_count = lottery.check_for_new_draws()
                if new_count == -1:
                    updates_available[lottery.name] = "initial"
                    print(f"\n📁 {lottery.name}: No local data found (initial fetch needed)")
                elif new_count > 0:
                    updates_available[lottery.name] = new_count
                    draw_word = "draw" if new_count == 1 else "draws"
                    print(f"\n🎉 {lottery.name}: {new_count} new {draw_word} available")
                else:
                    print(f"\n✅ {lottery.name}: Up to date")
            except Exception as e:
                print(f"\n❌ {lottery.name}: Error checking for updates - {e}")

        # If no updates available, exit
        if not updates_available:
            print("\n✨ All lotteries are up to date!")
            input("\nPress Enter to continue...")
            return

        # Prompt for each lottery with updates
        print("\n" + "="*50)
        for lottery_name, update_info in updates_available.items():
            if update_info == "initial":
                prompt = f"📥 {lottery_name} has no local data. Would you like to fetch all historical data? (Y/N): "
            else:
                draw_word = "draw" if update_info == 1 else "draws"
                prompt = f"📥 There is/are {update_info} new {draw_word} for {lottery_name}, would you like to update? (Y/N): "

            while True:
                response = input(prompt).strip().upper()
                if response in ['Y', 'N']:
                    break
                print("❌ Please enter Y or N")

            if response == 'Y':
                lottery = None
                for key, lott in self.lotteries.items():
                    if lott.name == lottery_name:
                        lottery = lott
                        break

                if lottery:
                    try:
                        if update_info == "initial":
                            print(f"\n🌐 Fetching all historical data for {lottery_name}...")
                            lottery.fetch_from_api()
                            print(f"✅ {lottery_name} data fetched and saved successfully!")
                        else:
                            print(f"\n🔄 Updating {lottery_name} with new draws...")
                            added = lottery.update_from_api()
                            print(f"✅ {lottery_name} updated with {added} new draw(s)!")
                    except Exception as e:
                        print(f"❌ Error updating {lottery_name}: {e}")
            else:
                print(f"⏭️  Skipping {lottery_name}")

        print("\n" + "="*50)
        print("✨ API update process completed!")
        input("\nPress Enter to continue...")

    def check_for_missing_data(self):
        """Check all lotteries for missing data by comparing with API"""
        print("\n" + "="*50)
        print("🔍 Checking data integrity (comparing with API)...")
        print("This may take a minute as we check each year...")
        print("="*50)

        # Check all lotteries for missing data
        missing_data = {}
        for key, lottery in self.lotteries.items():
            try:
                print(f"\n🔎 Checking {lottery.name}...")
                years_with_issues = lottery.check_for_missing_years()

                if years_with_issues:
                    missing_data[lottery.name] = years_with_issues
                    total_missing = sum(info['missing'] for info in years_with_issues.values())

                    print(f"⚠️  {lottery.name}: Found issues in {len(years_with_issues)} year(s)")
                    for year, info in sorted(years_with_issues.items()):
                        status = "missing" if info['missing'] > 0 else "extra"
                        count = abs(info['missing'])
                        print(f"    • {year}: {count} {status} draw(s) (API: {info['api_count']}, Local: {info['local_count']})")
                else:
                    print(f"✅ {lottery.name}: Complete data (all draws match API)")
            except Exception as e:
                print(f"❌ {lottery.name}: Error checking - {e}")

        # If no missing data, exit
        if not missing_data:
            print("\n✨ All lotteries have complete and accurate data!")
            input("\nPress Enter to continue...")
            return

        # Offer to fix missing data
        print("\n" + "="*50)
        print("Would you like to refetch the data for years with issues?")
        print("This will replace local data for those years with fresh API data.")
        print("="*50)

        for lottery_name, years_with_issues in missing_data.items():
            years_list = sorted(years_with_issues.keys())
            year_ranges = self._format_year_ranges(years_list)
            total_missing = sum(info['missing'] for info in years_with_issues.values())

            prompt = f"📥 Refetch data for {lottery_name} ({year_ranges})? (Y/N): "

            while True:
                response = input(prompt).strip().upper()
                if response in ['Y', 'N']:
                    break
                print("❌ Please enter Y or N")

            if response == 'Y':
                lottery = None
                for key, lott in self.lotteries.items():
                    if lott.name == lottery_name:
                        lottery = lott
                        break

                if lottery:
                    try:
                        print(f"\n🌐 Refetching data for {lottery_name}...")
                        print(f"   Processing {len(years_with_issues)} year(s)...")
                        added = lottery.fetch_missing_years(years_with_issues)
                        print(f"✅ {lottery_name} data refreshed - fetched {added} draw(s)!")
                    except Exception as e:
                        print(f"❌ Error fetching data for {lottery_name}: {e}")
            else:
                print(f"⏭️  Skipping {lottery_name}")

        print("\n" + "="*50)
        print("✨ Data integrity check completed!")
        input("\nPress Enter to continue...")

    def _format_year_ranges(self, years):
        """Format a list of years into readable ranges (e.g., '2010-2015, 2018, 2020-2023')"""
        if not years:
            return ""

        ranges = []
        start = years[0]
        end = years[0]

        for i in range(1, len(years)):
            if years[i] == end + 1:
                end = years[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = years[i]
                end = years[i]

        # Add the last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return ", ".join(ranges)

    def show_statistics(self):
        """Show lottery statistics"""
        self.log_message("\n📈 Loading statistics...")
        try:
            stats = self.current_lottery.get_statistics_summary()
            print(stats)
        except Exception as e:
            print(f"❌ Error loading statistics: {e}")
        
        input("\nPress Enter to continue...")
    
    def update_statistics(self):
        """Update/regenerate lottery statistics"""
        self.log_message("\n🔄 Regenerating statistics from historical data...")
        try:
            print("\n🔄 Updating statistics...")
            
            # Force regeneration of statistics
            self.current_lottery.generate_statistics_from_past_numbers()
            
            print("✅ Statistics updated successfully!")
            self.log_message("✅ Statistics regenerated successfully!")
            
            # Show a preview of the updated stats
            if not self.debug_mode:
                print("\n📊 Quick preview of updated statistics:")
                stats = self.current_lottery.get_statistics_summary()
                preview = stats[:500] + "..." if len(stats) > 500 else stats
                print(preview)
            
        except Exception as e:
            print(f"❌ Error updating statistics: {e}")
            self.log_message(f"❌ Error updating statistics: {e}")
        
        input("\nPress Enter to continue...")
    
    def configure_strategy(self):
        """Configure number generation strategy"""
        self.change_strategy()
    
    def change_strategy(self):
        """Change the current number generation strategy"""
        while True:
            self.show_strategy_menu()
            choice = self.get_user_choice(3, allow_zero=True)
            
            if choice == 1:
                self.current_strategy = "frequency"
                print("✅ Strategy changed to Frequency (Hot/Cold Numbers)")
                break
            elif choice == 2:
                self.current_strategy = "random"
                print("✅ Strategy changed to Random")
                break
            elif choice == 3:
                self.current_strategy = "balanced"
                print("✅ Strategy changed to Balanced")
                break
            elif choice == 0:
                return
        
        input("\nPress Enter to continue...")
    
    def handle_config_menu(self):
        """Handle system configuration menu"""
        while True:
            self.show_config_menu()
            choice = self.get_user_choice(3, allow_zero=True)

            if choice == 1:
                self.debug_mode = not self.debug_mode
                self._update_lottery_debug_mode()  # Update all lottery instances
                status = "ON" if self.debug_mode else "OFF"
                print(f"✅ Debug mode toggled {status}")
                input("\nPress Enter to continue...")
            elif choice == 2:
                self.update_lottery_data_from_api()
            elif choice == 3:
                self.check_for_missing_data()
            elif choice == 0:
                return
    
    def log_message(self, message):
        """Display message only if debug mode is on"""
        if self.debug_mode:
            print(message)
    
    def run(self):
        """Main application loop"""
        try:
            print("🎰 Starting Multi-Lottery System...")
            self.handle_main_menu()
        except KeyboardInterrupt:
            print("\n👋 Exiting... Goodbye!")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}")

def main():
    """Main entry point"""
    app = LottoApp()
    app.run()

if __name__ == "__main__":
    main()