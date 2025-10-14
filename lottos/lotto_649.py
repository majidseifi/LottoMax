from datetime import datetime
from dateutil.parser import parse as parse_date
from .base_lottery import BaseLottery

class Lotto649(BaseLottery):
    """Lotto 6/49 lottery implementation"""
    
    def __init__(self):
        super().__init__("Lotto 649", "data/lotto_649")
    
    def get_game_config(self):
        """Return Lotto 6/49 game configuration"""
        return {
            'main_count': 6,           # 6 main numbers
            'main_range': (1, 49),     # Numbers from 1 to 49
            'bonus_count': 1,          # 1 bonus number
            'bonus_range': (1, 49),    # Bonus from same range
        }

    def get_api_lottery_type(self):
        """Return API lottery type identifier"""
        return "6-49"

    def get_year_range(self):
        """Return year range for Lotto 6/49 (started in 1982)"""
        current_year = datetime.now().year
        return (1982, current_year)
    
    def parse_api_draw(self, draw_data):
        """
        Parse a single Lotto 6/49 draw from API response

        API Format:
        {
            "date": "2024-01-01",
            "classic": {
                "numbers": [1, 2, 3, 4, 5, 6],
                "bonus": 7,
                "prize": 5000000
            },
            "guaranteed": [...],
            "goldBall": {...}
        }

        Returns:
            Tuple of (formatted_date, formatted_numbers, jackpot_string)
        """
        try:
            # Parse date from ISO format to M/D/YYYY
            date_obj = datetime.strptime(draw_data['date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%-m/%-d/%Y')

            # Extract classic draw data (we ignore guaranteed and goldBall)
            classic = draw_data['classic']
            main_numbers = classic['numbers']
            bonus = classic['bonus']
            formatted_numbers = '-'.join(map(str, main_numbers)) + f'-{bonus}'

            # Format prize
            prize = classic.get('prize')
            if prize and prize > 0:
                jackpot = f"${prize:,.0f}"
            else:
                jackpot = "Not Available"

            return (formatted_date, formatted_numbers, jackpot)

        except Exception as e:
            self.log_message(f"Error parsing API draw: {e}")
            return None