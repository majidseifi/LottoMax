# Multi-Lottery Prediction System

A comprehensive prediction system for Canadian lotteries (Lotto Max, Lotto 6/49, Daily Grand) that fetches historical draw data, generates statistics, and uses various strategies to predict winning numbers.

## Features

- **Three Canadian Lotteries:**
  - Lotto Max (7 numbers from 1-50 + bonus)
  - Lotto 6/49 (6 numbers from 1-49 + bonus)
  - Daily Grand (5 numbers from 1-49 + Grand Number 1-7)

- **Prediction Strategies:**
  - Frequency Analysis (hot/cold numbers, pairs, triplets)
  - Random Generation
  - Balanced Strategy (mix of both)

- **Data Management:**
  - Automatic API updates from Canada Lottery Results
  - Historical data validation and integrity checks
  - Comprehensive statistics generation

- **User Interfaces:**
  - Interactive CLI menu system
  - PyQt6 GUI application with charts and visualizations

## Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Configure API Key

Get your free RapidAPI key from [Canada Lottery API](https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/canada-lottery).

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
RAPIDAPI_KEY=your_api_key_here
```

### 3. Run the Application

**CLI Version:**
```bash
python3 lotto.py
```

**GUI Version:**
```bash
python3 lotto_gui.py
```

Or use the launcher:
```bash
./launch_app.command
```

## Usage

### CLI Interface

- Navigate using numbered menus
- Type `:qa` at any prompt to quit
- Select lottery, choose strategy, generate predictions
- Update data from API when new draws are available
- View statistics and latest draws

### GUI Interface

- Select lottery from dropdown
- View latest draw and statistics
- Generate predictions with different strategies
- Visual charts for number frequencies and patterns

## Project Structure

```
LottoMax/
├── lotto.py              # CLI application
├── lotto_gui.py          # GUI application
├── lottos/
│   ├── base_lottery.py   # Base class for all lotteries
│   ├── lotto_max.py      # Lotto Max implementation
│   ├── lotto_649.py      # Lotto 6/49 implementation
│   ├── daily_grand.py    # Daily Grand implementation
│   ├── api_client.py     # Canada Lottery API client
│   └── strategies/       # Prediction strategies
├── data/                 # Historical draw data and statistics
└── .env                  # API configuration (not tracked)
```

## Data Sources

Historical draw data is fetched from the [Canada Lottery Results API](https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/canada-lottery) via RapidAPI.

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`
- RapidAPI key (free tier available)

## Security

- API keys are stored in `.env` file (excluded from git)
- Never commit credentials or sensitive data
- See `SETUP.md` for detailed security configuration

## License

This project is for educational and entertainment purposes only. Lottery predictions are based on statistical analysis and do not guarantee winning outcomes.

## Contributing

Feel free to open issues or submit pull requests for improvements.

---

**Quick Exit:** Type `:qa` in CLI mode to quit immediately
