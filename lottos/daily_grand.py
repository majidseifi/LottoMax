from datetime import datetime
from dateutil.parser import parse as parse_date
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

    def get_api_lottery_type(self):
        """Return API lottery type identifier"""
        return "daily-grand"

    def get_year_range(self):
        """Return year range for Daily Grand (started in 2016)"""
        current_year = datetime.now().year
        return (2016, current_year)
    
    def parse_api_draw(self, draw_data):
        """
        Parse a single Daily Grand draw from API response

        API Format:
        {
            "date": "2024-01-01",
            "numbers": [1, 2, 3, 4, 5],
            "grandNumber": 6,
            "prize": 1000,
            "bonusesDraw": [...]
        }

        Returns:
            Tuple of (formatted_date, formatted_numbers, jackpot_string)
        """
        try:
            # Parse date from ISO format to M/D/YYYY
            date_obj = datetime.strptime(draw_data['date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%-m/%-d/%Y')

            # Format numbers: 5 main + 1 grand number
            main_numbers = draw_data['numbers']
            grand_number = draw_data['grandNumber']
            formatted_numbers = '-'.join(map(str, main_numbers)) + f'-{grand_number}'

            # Daily Grand has a life prize, not a traditional jackpot
            jackpot = "Life Prize"

            return (formatted_date, formatted_numbers, jackpot)

        except Exception as e:
            self.log_message(f"Error parsing API draw: {e}")
            return None