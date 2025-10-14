# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A multi-lottery prediction system for Canadian lotteries (Lotto Max, Lotto 6/49, Daily Grand) that scrapes historical draw data, generates statistics, and uses various strategies to generate number predictions.

## Running the Application

**Main Entry Point:**
```bash
python3 lotto.py
```

This launches an interactive CLI menu system where users can:
- Select a lottery (Lotto Max, 6/49, Daily Grand)
- Generate number predictions using different strategies
- View statistics and latest draws
- Scrape new data
- Toggle debug mode

**Quick Exit:** Type `:qa` at any prompt to quit immediately.

## Architecture

### Core Components

**Base Class Pattern (`lottos/base_lottery.py`):**
- `BaseLottery` is the abstract base class for all lottery implementations
- Defines common functionality: scraping, statistics generation, file I/O, logging
- Each lottery inherits and implements: `get_game_config()`, `get_scraping_urls()`, `parse_draw_row()`, `should_fetch_data()`, `_scrape_all_years()`

**Lottery Implementations:**
- `lottos/lotto_max.py` - 7 main numbers (1-50) + 1 bonus (1-50)
- `lottos/lotto_649.py` - 6 main numbers (1-49) + 1 bonus (1-49)
- `lottos/daily_grand.py` - 5 main numbers (1-49) + 1 Grand Number (1-7)

**Strategy Pattern (`lottos/strategies/base_strategy.py`):**
- `BaseStrategy` abstract class for number generation algorithms
- Three strategies implemented:
  - `FrequencyStrategy` - Uses hot/cold numbers, common pairs, overdue numbers
  - `RandomStrategy` - Pure random generation
  - `BalancedStrategy` - Mix of frequency analysis (30%) and random
- `StrategyManager` handles strategy selection and instantiation

### Data Storage

Each lottery has its own data directory (`data/{lottery_name}/`):
- `past_numbers.txt` - Historical draw results (CSV: Date, Numbers, Jackpot)
- `statistics.txt` - Comprehensive statistics (frequencies, hot/cold numbers, pairs, triplets)
- `{lottery_name}.log` - Debug logs

**Statistics Sections:**
- Main Number Frequencies
- Bonus Number Frequencies
- Hot Numbers (most frequent)
- Cold Numbers (least frequent)
- Most Overdue Numbers
- Most Common Pairs / Consecutive Pairs
- Most Common Triplets / Consecutive Triplets

### Data Flow

1. **Data Check:** `should_fetch_data()` compares local cached data with latest online draw
2. **Scraping:** Web scraping from lottery websites (BeautifulSoup + requests)
3. **Statistics Generation:** `generate_statistics_from_past_numbers()` analyzes all historical data
4. **Loading:** `load_from_files()` reads statistics and latest draw
5. **Number Generation:** Strategy uses loaded statistics to generate predictions

### Logging System

- File logging: All operations logged to `data/{lottery_name}/{lottery_name}.log`
- Console output: Controlled by `debug_mode` flag
- No console spam in normal mode; full logging in debug mode
- Set via System Config menu in CLI

## Web Scraping Sources

- **Lotto Max:** https://www.lottomaxnumbers.com/numbers/{year} (2009-2025)
- **Lotto 6/49:** https://ca.lottonumbers.com/lotto-649/numbers/{year} (1982-2025)
- **Daily Grand:** https://ca.lottonumbers.com/daily-grand/numbers/{year} (2016-2025)

All scraping uses BeautifulSoup to parse HTML tables with lottery draw results.

## Testing Files

Note: Test files matching `test_*.py` are gitignored but exist in the working directory:
- `test_api.py` - RapidAPI integration tests (contains API keys - do not commit)
- `test_649_fix.py` - Lotto 6/49 specific testing
- `verify_all.py` - Full system verification

## Key Implementation Details

**Date Handling:**
- All dates stored as M/D/YYYY format (e.g., "8/6/2025")
- Uses `python-dateutil` for flexible parsing
- Newest draws stored first in `past_numbers.txt`

**Number Format:**
- Stored as hyphen-delimited strings: "12-23-35-48-49-01-42"
- Main numbers come first, bonus number last
- Statistics separate main and bonus numbers

**Menu Navigation:**
- Numeric choices for navigation
- 0 typically means "back"
- All menus support ':qa' quick exit

**Error Handling:**
- Missing data files trigger automatic scraping
- Bad date formats trigger fresh data fetch
- Network errors logged but don't crash the app
- Fallback to random generation if statistics unavailable

## Dependencies

Based on imports used throughout codebase:
- `requests` - HTTP requests for web scraping
- `beautifulsoup4` - HTML parsing
- `python-dateutil` - Flexible date parsing
- Standard library: `os`, `logging`, `collections`, `abc`, `random`, `datetime`, `typing`

## Adding New Lotteries

1. Create new class in `lottos/` inheriting from `BaseLottery`
2. Implement required abstract methods
3. Define game configuration (number counts and ranges)
4. Add scraping URLs and row parser for specific website format
5. Register in `LottoApp.__init__()` in `lotto.py`

## Adding New Strategies

1. Create new class inheriting from `BaseStrategy` in `lottos/strategies/base_strategy.py`
2. Implement `generate_numbers(data, config)` method
3. Register in `StrategyManager.__init__()`
4. Add menu option in `LottoApp.show_strategy_menu()`
