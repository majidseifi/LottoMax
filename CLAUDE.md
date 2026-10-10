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
- Defines common functionality: statistics generation, file I/O, logging
- Each lottery inherits and implements: `get_game_config()`, `parse_api_draw()` (legacy name, no live API), `get_year_range()`
- Key method: `generate_statistics_from_past_numbers()`

**Lottery Implementations:**
- `lottos/lotto_max.py` - 7 main numbers (1-52) + 1 bonus (1-52) - Started 2009; matrix expanded from 7/50 to 7/52 on Apr 14, 2026
- `lottos/lotto_649.py` - 6 main numbers (1-49) + 1 bonus (1-49) - Started 1982
- `lottos/daily_grand.py` - 5 main numbers (1-49) + 1 Grand Number (1-7) - Started 2016

Each lottery implements:
- `parse_api_draw()` (legacy name, no live API) - Converts a source record to internal format
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

1. **Manual Update:** New draws are found via web search and added to `past_numbers.txt` (see Updating Data)
2. **Statistics Generation:** `generate_statistics_from_past_numbers()` analyzes all historical data
3. **Loading:** `load_from_files()` reads statistics and latest draw from local cache
4. **Number Generation:** Strategy uses loaded statistics to generate predictions

### Logging System

- File logging: All operations logged to `data/{lottery_name}/{lottery_name}.log`
- Console output: Controlled by `debug_mode` flag
- No console spam in normal mode; full logging in debug mode
- Set via System Config menu in CLI

### Data Integrity

- Draw data is maintained by hand/web search; there is no API.
- Check for gaps by comparing draw dates against each lottery's schedule (Lotto Max: Tue/Fri, 6/49: Wed/Sat, Daily Grand: Mon/Thu).
- When merging new draws: dedupe by date, keep newest first, then regenerate statistics.

## Updating Data (Web Search)

1. Compare the latest date in `data/{lottery}/past_numbers.txt` with today's date
2. Search the web for results of each missing draw (date, main numbers, bonus/Grand Number, jackpot)
3. Cross-check each draw against a second source before adding it
4. Prepend new rows to `past_numbers.txt` (newest first, existing format)
5. Regenerate `statistics.txt` with `generate_statistics_from_past_numbers()`
6. Normal operation uses cached local files (no network calls)

## Testing Files

Note: Test files matching `test_*.py` are gitignored but exist in the working directory:
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
- `python-dateutil` - Flexible date parsing and formatting
- Standard library: `os`, `logging`, `collections`, `abc`, `random`, `datetime`, `typing`, `time`

## Adding New Lotteries

1. Create new class in `lottos/` inheriting from `BaseLottery`
2. Implement required abstract methods:
   - `get_game_config()` - Define number counts and ranges
   - `parse_api_draw()` (legacy name, no live API) - Convert a source record to (date, numbers, jackpot) tuple
   - `get_year_range()` - Return (start_year, current_year) tuple
3. Register in `LottoApp.__init__()` in `lotto.py`

## Adding New Strategies

1. Create new class inheriting from `BaseStrategy` in `lottos/strategies/base_strategy.py`
2. Implement `generate_numbers(data, config)` method
3. Register in `StrategyManager.__init__()`
4. Add menu option in `LottoApp.show_strategy_menu()`
