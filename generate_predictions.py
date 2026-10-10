#!/usr/bin/env python3
"""
Generate predictions for all lotteries
"""

from lottos.lotto_max import LottoMax
from lottos.lotto_649 import Lotto649
from lottos.daily_grand import DailyGrand
from lottos.strategies.base_strategy import FrequencyStrategy

def generate_predictions():
    """Generate predictions for all lotteries"""

    # Initialize lotteries
    lotto_max = LottoMax()
    lotto_649 = Lotto649()
    daily_grand = DailyGrand()

    # Load data for all lotteries
    lotto_max_data = lotto_max.load_from_files()
    lotto_649_data = lotto_649.load_from_files()
    daily_grand_data = daily_grand.load_from_files()

    # Initialize strategy
    strategy = FrequencyStrategy()

    print("\n" + "="*60)
    print("LOTTERY PREDICTIONS - Frequency-Based Strategy")
    print("="*60)
    print(f"Generated on: {__import__('datetime').datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print("="*60)

    # Generate 5 plays for Lotto Max
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║              LOTTO MAX - 5 PLAYS                          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"Latest Draw: {lotto_max_data.get('latest_draw', {}).get('date', 'Unknown')}")
    print(f"Last Numbers: {lotto_max_data.get('latest_draw', {}).get('numbers', 'Unknown')}")
    print("-" * 60)

    for i in range(5):
        main_numbers, bonus_number = strategy.generate_numbers(lotto_max_data, lotto_max.get_game_config())
        main_numbers.sort()  # Sort for better readability
        print(f"Play {i+1}: {'-'.join(f'{n:02d}' for n in main_numbers)} + Bonus: {bonus_number:02d}")

    # Generate 5 plays for Lotto 6/49
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║              LOTTO 6/49 - 5 PLAYS                         ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"Latest Draw: {lotto_649_data.get('latest_draw', {}).get('date', 'Unknown')}")
    print(f"Last Numbers: {lotto_649_data.get('latest_draw', {}).get('numbers', 'Unknown')}")
    print("-" * 60)

    for i in range(5):
        main_numbers, bonus_number = strategy.generate_numbers(lotto_649_data, lotto_649.get_game_config())
        main_numbers.sort()  # Sort for better readability
        print(f"Play {i+1}: {'-'.join(f'{n:02d}' for n in main_numbers)} + Bonus: {bonus_number:02d}")

    # Generate 3 plays for Daily Grand
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║              DAILY GRAND - 3 PLAYS                        ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"Latest Draw: {daily_grand_data.get('latest_draw', {}).get('date', 'Unknown')}")
    print(f"Last Numbers: {daily_grand_data.get('latest_draw', {}).get('numbers', 'Unknown')}")
    print("-" * 60)

    for i in range(3):
        main_numbers, grand_number = strategy.generate_numbers(daily_grand_data, daily_grand.get_game_config())
        main_numbers.sort()  # Sort for better readability
        print(f"Play {i+1}: {'-'.join(f'{n:02d}' for n in main_numbers)} + Grand: {grand_number}")

    print("\n" + "="*60)
    print("Good luck! 🍀")
    print("="*60 + "\n")

if __name__ == "__main__":
    generate_predictions()
