from datetime import datetime
from dateutil.parser import parse as parse_date
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

    def get_api_lottery_type(self):
        """Return API lottery type identifier"""
        return "lottomax"

    def get_year_range(self):
        """Return year range for Lotto Max (started in 2009)"""
        current_year = datetime.now().year
        return (2009, current_year)
    
    def parse_api_draw(self, draw_data):
        """
        Parse a single Lotto Max draw from API response

        API Format:
        {
            "date": "2024-01-01",
            "prize": 10000000,
            "numbers": [1, 2, 3, 4, 5, 6, 7],
            "bonus": 8
        }

        Returns:
            Tuple of (formatted_date, formatted_numbers, jackpot_string)
        """
        try:
            # Parse date from ISO format to M/D/YYYY
            date_obj = datetime.strptime(draw_data['date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%-m/%-d/%Y')

            # Format numbers: 7 main + 1 bonus
            main_numbers = draw_data['numbers']
            bonus = draw_data['bonus']
            formatted_numbers = '-'.join(map(str, main_numbers)) + f'-{bonus}'

            # Format prize
            prize = draw_data['prize']
            if prize > 0:
                jackpot = f"${prize:,.0f}"
            else:
                jackpot = "Not Available"

            return (formatted_date, formatted_numbers, jackpot)

        except Exception as e:
            self.log_message(f"Error parsing API draw: {e}")
            return None