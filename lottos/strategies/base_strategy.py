from abc import ABC, abstractmethod
import random
from typing import Tuple, List, Dict, Any

class BaseStrategy(ABC):
    """Abstract base class for number generation strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def generate_numbers(self, data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List[int], int]:
        """
        Generate lottery numbers based on strategy
        
        Args:
            data: Dictionary containing frequency and statistics data
            config: Game configuration (main_count, ranges, etc.)
            
        Returns:
            Tuple of (main_numbers_list, bonus_number)
        """
        pass
    
    def _get_fallback_numbers(self, config: Dict[str, Any]) -> Tuple[List[int], int]:
        """Generate fallback random numbers if data is insufficient"""
        main_start, main_end = config['main_range']
        bonus_start, bonus_end = config['bonus_range']
        
        # Generate unique main numbers
        main_numbers = random.sample(range(main_start, main_end + 1), config['main_count'])
        
        # Generate bonus number
        bonus_number = random.randint(bonus_start, bonus_end)
        
        return main_numbers, bonus_number

class FrequencyStrategy(BaseStrategy):
    """Strategy based on number frequencies (hot/cold numbers)"""
    
    def __init__(self):
        super().__init__("Frequency Strategy")
    
    def generate_numbers(self, data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List[int], int]:
        """Generate numbers using frequency analysis"""
        main_freq = data.get('main_freq', {})
        bonus_freq = data.get('bonus_freq', {})
        hot_numbers = data.get('hot_numbers', {})
        overdue_numbers = data.get('overdue_numbers', {})
        common_pairs = data.get('common_pairs', [])
        
        main_start, main_end = config['main_range']
        bonus_start, bonus_end = config['bonus_range']
        
        # Start with a common pair if available
        if common_pairs:
            selected_pair = random.choice(common_pairs)
            main_numbers = list(selected_pair)
        else:
            main_numbers = [random.randint(main_start, main_end), random.randint(main_start, main_end)]
            while main_numbers[0] == main_numbers[1]:
                main_numbers[1] = random.randint(main_start, main_end)
        
        # Add hot numbers
        hot_candidates = [num for num in hot_numbers.keys() if num not in main_numbers]
        if hot_candidates:
            add_count = min(3, len(hot_candidates), config['main_count'] - len(main_numbers))
            main_numbers.extend(random.sample(hot_candidates, add_count))
        
        # Add one overdue number
        overdue_candidates = [num for num in overdue_numbers.keys() if num not in main_numbers]
        if overdue_candidates and len(main_numbers) < config['main_count']:
            main_numbers.append(random.choice(overdue_candidates))
        
        # Fill remaining slots randomly
        remaining_slots = config['main_count'] - len(main_numbers)
        if remaining_slots > 0:
            available_nums = [num for num in range(main_start, main_end + 1) if num not in main_numbers]
            if len(available_nums) >= remaining_slots:
                main_numbers.extend(random.sample(available_nums, remaining_slots))
            else:
                main_numbers.extend(available_nums)
        
        # Ensure we have exactly the right count
        main_numbers = main_numbers[:config['main_count']]
        
        # Balance odds/evens (aim for 3-4 odds out of 7)
        self._balance_odds_evens(main_numbers, main_start, main_end)
        
        # Generate bonus number
        if bonus_freq:
            bonus_prob = {k: v/sum(bonus_freq.values()) for k, v in bonus_freq.items()}
            bonus_number = random.choices(list(bonus_prob.keys()), weights=list(bonus_prob.values()), k=1)[0]
        else:
            bonus_number = random.randint(bonus_start, bonus_end)
        
        return main_numbers, bonus_number
    
    def _balance_odds_evens(self, main_numbers: List[int], min_num: int, max_num: int):
        """Balance odds and evens in the number set"""
        odds = sum(1 for num in main_numbers if num % 2 == 1)
        available_nums = [num for num in range(min_num, max_num + 1) if num not in main_numbers]
        
        # Try to adjust if too many odds or evens
        for _ in range(2):
            if odds < 3 and available_nums:
                odd_nums = [num for num in available_nums if num % 2 == 1]
                if odd_nums:
                    new_num = random.choice(odd_nums)
                    replace_idx = random.randint(0, len(main_numbers) - 1)
                    if main_numbers[replace_idx] % 2 == 0:  # Only replace if it's even
                        available_nums.remove(new_num)
                        main_numbers[replace_idx] = new_num
                        odds += 1
            elif odds > 4 and available_nums:
                even_nums = [num for num in available_nums if num % 2 == 0]
                if even_nums:
                    new_num = random.choice(even_nums)
                    replace_idx = random.randint(0, len(main_numbers) - 1)
                    if main_numbers[replace_idx] % 2 == 1:  # Only replace if it's odd
                        available_nums.remove(new_num)
                        main_numbers[replace_idx] = new_num
                        odds -= 1

class RandomStrategy(BaseStrategy):
    """Pure random number generation strategy"""
    
    def __init__(self):
        super().__init__("Random Strategy")
    
    def generate_numbers(self, data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List[int], int]:
        """Generate completely random numbers"""
        return self._get_fallback_numbers(config)

class BalancedStrategy(BaseStrategy):
    """Balanced strategy mixing different approaches"""
    
    def __init__(self):
        super().__init__("Balanced Strategy")
    
    def generate_numbers(self, data: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List[int], int]:
        """Generate numbers using a balanced approach"""
        main_freq = data.get('main_freq', {})
        hot_numbers = data.get('hot_numbers', {})
        common_pairs = data.get('common_pairs', [])
        
        main_start, main_end = config['main_range']
        bonus_start, bonus_end = config['bonus_range']
        
        main_numbers = []
        
        # 30% chance to use a common pair
        if common_pairs and random.random() < 0.3:
            selected_pair = random.choice(common_pairs)
            main_numbers.extend(selected_pair)
        
        # Add some hot numbers (30% of remaining slots)
        remaining_slots = config['main_count'] - len(main_numbers)
        hot_slots = max(1, int(remaining_slots * 0.3))
        
        if hot_numbers:
            hot_candidates = [num for num in hot_numbers.keys() if num not in main_numbers]
            if hot_candidates:
                add_count = min(hot_slots, len(hot_candidates))
                main_numbers.extend(random.sample(hot_candidates, add_count))
        
        # Fill remaining with random numbers
        remaining_slots = config['main_count'] - len(main_numbers)
        if remaining_slots > 0:
            available_nums = [num for num in range(main_start, main_end + 1) if num not in main_numbers]
            if len(available_nums) >= remaining_slots:
                main_numbers.extend(random.sample(available_nums, remaining_slots))
            else:
                # Fallback to pure random if not enough unique numbers
                return self._get_fallback_numbers(config)
        
        # Generate bonus number (50% frequency-based, 50% random)
        if data.get('bonus_freq') and random.random() < 0.5:
            bonus_freq = data['bonus_freq']
            bonus_prob = {k: v/sum(bonus_freq.values()) for k, v in bonus_freq.items()}
            bonus_number = random.choices(list(bonus_prob.keys()), weights=list(bonus_prob.values()), k=1)[0]
        else:
            bonus_number = random.randint(bonus_start, bonus_end)
        
        return main_numbers, bonus_number

class StrategyManager:
    """Manager for different number generation strategies"""
    
    def __init__(self):
        self.strategies = {
            'frequency': FrequencyStrategy(),
            'random': RandomStrategy(),
            'balanced': BalancedStrategy(),
        }
    
    def get_strategy(self, name: str) -> BaseStrategy:
        """Get a strategy by name"""
        return self.strategies.get(name, self.strategies['random'])
    
    def list_strategies(self) -> List[str]:
        """Get list of available strategy names"""
        return list(self.strategies.keys())
    
    def add_strategy(self, name: str, strategy: BaseStrategy):
        """Add a new strategy"""
        self.strategies[name] = strategy