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
- Defines common functionality: API fetching, statistics generation, file I/O, logging
- Each lottery inherits and implements: `get_game_config()`, `get_api_lottery_type()`, `parse_api_draw()`, `get_year_range()`
- Key methods: `fetch_from_api()`, `check_for_new_draws()`, `update_from_api()`, `check_for_missing_years()`, `fetch_missing_years()`, `generate_statistics_from_past_numbers()`

**Lottery Implementations:**
- `lottos/lotto_max.py` - 7 main numbers (1-50) + 1 bonus (1-50) - Started 2009
- `lottos/lotto_649.py` - 6 main numbers (1-49) + 1 bonus (1-49) - Started 1982
- `lottos/daily_grand.py` - 5 main numbers (1-49) + 1 Grand Number (1-7) - Started 2016

Each lottery implements:
- `get_api_lottery_type()` - Returns API endpoint identifier
- `parse_api_draw()` - Converts API JSON to internal format
- `get_year_range()` - Returns (start_year, current_year) tuple

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

1. **Manual Update Check:** User selects "Update Lottery Data from API" in Settings
2. **API Check:** `check_for_new_draws()` compares local latest date with API latest date
3. **API Fetch:** `update_from_api()` or `fetch_from_api()` retrieves draw data from Canada Lottery API
4. **Statistics Generation:** `generate_statistics_from_past_numbers()` analyzes all historical data (auto-triggered after API update)
5. **Loading:** `load_from_files()` reads statistics and latest draw from local cache
6. **Number Generation:** Strategy uses loaded statistics to generate predictions

### Logging System

- File logging: All operations logged to `data/{lottery_name}/{lottery_name}.log`
- Console output: Controlled by `debug_mode` flag
- No console spam in normal mode; full logging in debug mode
- Set via System Config menu in CLI

### Data Integrity

**Missing Data Detection (Optimized):**
- `_get_local_draw_counts()` - Single-pass file reading, builds year→count dictionary (O(n) time, O(years) space)
- `check_for_missing_years()` - Compares local vs API draw counts per year
  - **Quick Check Mode**: Only checks last 3 years (~9 API calls total)
  - **Full Check Mode**: Checks all years (e.g., 44 years for Lotto 649 = ~130 API calls)
- Uses progress callbacks for real-time status updates
- Returns dictionary mapping year → {api_count, local_count, missing}

**Performance Optimizations:**
1. **Single-pass local file reading**: Parses file once, builds hash map (was: multiple passes)
2. **Dictionary lookups**: O(1) year lookup instead of searching
3. **Quick check mode**: Only check recent data for routine verification
4. **Progress indicators**: Shows "year (x/total)" in real-time
5. **Lazy evaluation**: Only fetches API data when needed

**Missing Data Repair:**
- `fetch_missing_years(years_dict)` refetches problematic years
- Removes local data for those years, replaces with fresh API data
- Merges with untouched years, removes duplicates
- Sorts chronologically (newest first)
- Auto-regenerates statistics after merge

**Typical Check Times:**
- Quick Check (3 years × 3 lotteries): ~15-20 seconds
- Full Check (all years): ~3-5 minutes depending on API speed

## API Integration

The application uses the **Canada Lottery Results API** (RapidAPI) to fetch draw data:

**API Endpoints:**
- **Lotto Max:** `GET /lottomax/years/{year}` (2009-present)
- **Lotto 6/49:** `GET /6-49/years/{year}` (1982-present)
- **Daily Grand:** `GET /daily-grand/years/{year}` (2016-present)

**API Client:** `lottos/api_client.py` - `CanadaLotteryAPI` class handles all API interactions with retry logic and error handling.

**Update Process:**
1. User selects "Update Lottery Data from API" in System Config menu
2. System checks all 3 lotteries for new draws (compares local vs API)
3. User prompted per lottery: "There is/are {count} new draw(s) for {name}, would you like to update? (Y/N)"
4. If Yes: fetches new data, updates `past_numbers.txt`, auto-regenerates statistics
5. Normal operation uses cached local files (no API calls)

**Data Integrity Check:**
1. User selects "Check for Missing Data" in System Config menu
2. System scans all lotteries for gaps in historical data (missing years)
3. Reports missing year ranges (e.g., "2010-2023")
4. User prompted per lottery to fetch missing data
5. If Yes: fetches all missing years, merges with existing data, removes duplicates, auto-regenerates statistics

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
- `requests` - HTTP requests for API calls
- `python-dateutil` - Flexible date parsing and formatting
- Standard library: `os`, `logging`, `collections`, `abc`, `random`, `datetime`, `typing`, `time`

## API Response Formats

**Lotto Max** (`/lottomax/years/{year}`):
```json
{
  "date": "2024-01-01",
  "prize": 10000000,
  "numbers": [1, 2, 3, 4, 5, 6, 7],
  "bonus": 8
}
```

**Lotto 6/49** (`/6-49/years/{year}`):
```json
{
  "date": "2024-01-01",
  "classic": {
    "numbers": [1, 2, 3, 4, 5, 6],
    "bonus": 7,
    "prize": 5000000
  },
  "guaranteed": [...],  // Ignored
  "goldBall": {...}     // Ignored
}
```

**Daily Grand** (`/daily-grand/years/{year}`):
```json
{
  "date": "2024-01-01",
  "numbers": [1, 2, 3, 4, 5],
  "grandNumber": 6,
  "prize": 1000,
  "bonusesDraw": [...]  // Ignored
}
```

## Adding New Lotteries

1. Create new class in `lottos/` inheriting from `BaseLottery`
2. Implement required abstract methods:
   - `get_game_config()` - Define number counts and ranges
   - `get_api_lottery_type()` - Return API endpoint identifier
   - `parse_api_draw()` - Convert API JSON to (date, numbers, jackpot) tuple
   - `get_year_range()` - Return (start_year, current_year) tuple
3. Register in `LottoApp.__init__()` in `lotto.py`

## Adding New Strategies

1. Create new class inheriting from `BaseStrategy` in `lottos/strategies/base_strategy.py`
2. Implement `generate_numbers(data, config)` method
3. Register in `StrategyManager.__init__()`
4. Add menu option in `LottoApp.show_strategy_menu()`
