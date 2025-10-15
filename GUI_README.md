# Multi-Lottery System - GUI Version

A modern, user-friendly desktop application for Canadian lottery number generation and analysis.

## Features

### 🎰 Three Lotteries Supported
- **Lotto Max** - 7 numbers (1-50) + 1 bonus
- **Lotto 6/49** - 6 numbers (1-49) + 1 bonus
- **Daily Grand** - 5 numbers (1-49) + 1 Grand Number (1-7)

### 🎯 Number Generation Strategies
- **Frequency Strategy** - Uses hot/cold numbers, common pairs, overdue analysis
- **Random Strategy** - Pure random generation
- **Balanced Strategy** - Mix of frequency analysis (30%) and random (70%)

### 📊 Features
- **Visual Number Display** - Color-coded balls for easy reading
- **Latest Draw Information** - Current jackpot and winning numbers
- **Detailed Statistics** - Hot/cold numbers, pairs, triplets analysis
- **Multiple Set Generation** - Generate up to 10 sets at once
- **API Data Management** - Update and verify lottery data
- **Data Integrity Checks** - Quick (3 years) or Full (all years)

## Installation

### Requirements
- Python 3.9 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip3 install -r requirements.txt
```

This installs:
- PyQt6 (GUI framework)
- PyQt6-Charts (for statistics visualization)
- requests (API calls)
- python-dateutil (date parsing)

## Running the Application

### Method 1: Double-click Launcher (macOS)
Simply double-click `launch_app.command` in Finder.

**First time:** You may need to right-click → Open → Open to bypass macOS security.

### Method 2: Terminal

```bash
python3 lotto_gui.py
```

### Method 3: Make it executable

```bash
chmod +x lotto_gui.py
./lotto_gui.py
```

## How to Use

### Basic Workflow

1. **Launch the Application**
   - The app opens with three tabs: Lotto Max, 6/49, and Daily Grand

2. **Select Your Lottery**
   - Click on the tab for your desired lottery

3. **View Latest Draw** (Left Panel)
   - See the most recent winning numbers
   - Check the current jackpot
   - Click "Refresh" to reload data

4. **Generate Numbers** (Center Panel)
   - Choose a strategy from the dropdown
   - Click "Generate Numbers" for a single set
   - Use "Generate Multiple" with the spinner to create 2-10 sets

5. **View Statistics** (Right Panel)
   - See hot/cold numbers preview
   - Click "View Detailed Statistics" for full analysis

### Managing Data

#### Update Lottery Data from API

1. Go to **Settings → API & Data Management**
2. Click **"Update Lottery Data from API"**
3. The app checks all three lotteries for new draws
4. Confirm which lotteries you want to update
5. Wait for the update to complete

#### Check Data Integrity

**Quick Check (Recommended)**
- Checks last 3 years only
- Fast (~15-20 seconds)
- Good for routine verification

**Full Check**
- Checks all historical years
- Slower (~3-5 minutes)
- Use when you suspect data issues

### Understanding the UI

#### Number Ball Colors
- **Red** - Numbers 1-10
- **Teal** - Numbers 11-20
- **Blue** - Numbers 21-30
- **Green** - Numbers 31-40
- **Orange** - Numbers 41-50
- **Gold** - Bonus/Grand numbers

#### Strategy Descriptions

**Frequency Strategy**
- Starts with common pairs from historical data
- Adds 3 hot (most frequent) numbers
- Includes 1 overdue number
- Fills remaining slots randomly
- Balances odd/even distribution
- Bonus weighted by historical frequency

**Random Strategy**
- Completely random selection
- No historical analysis
- Pure luck-based

**Balanced Strategy**
- 30% chance to use common pair
- 30% of slots use hot numbers
- 70% random selection
- 50% bonus uses frequency, 50% random

## Keyboard Shortcuts

- **Cmd+Q** (Mac) / **Ctrl+Q** (Windows) - Quit application

## Troubleshooting

### Application Won't Launch
**Error:** "Python not found"
- **Solution:** Install Python 3.9+ from python.org

**Error:** "No module named 'PyQt6'"
- **Solution:** Run `pip3 install -r requirements.txt`

### Data Issues
**Problem:** "No draw data available"
- **Solution:** Go to Settings → Update Lottery Data from API

**Problem:** Statistics show 0 for everything
- **Solution:** Update data from API first, then refresh

### macOS Security Warning
**Error:** "Cannot be opened because it is from an unidentified developer"
- **Solution:** Right-click → Open → Open (instead of double-clicking)

### API Errors
**Error:** "Failed to fetch from API"
- **Solution:** Check your internet connection
- **Solution:** API rate limit may be hit - wait a few minutes

## File Structure

```
LottoMax/
├── lotto_gui.py              # GUI application (main entry point)
├── lotto.py                   # CLI version (still works!)
├── launch_app.command         # macOS launcher
├── requirements.txt           # Python dependencies
├── GUI_README.md             # This file
├── CLAUDE.md                 # Development documentation
├── lottos/                   # Lottery logic
│   ├── base_lottery.py
│   ├── lotto_max.py
│   ├── lotto_649.py
│   ├── daily_grand.py
│   ├── api_client.py
│   └── strategies/
└── data/                     # Historical data
    ├── lotto_max/
    ├── lotto_649/
    └── daily_grand/
```

## Tips for Best Results

1. **Keep Data Updated**
   - Check for new draws weekly (especially after draw dates)
   - Run Quick Check monthly to verify data integrity

2. **Try Different Strategies**
   - Frequency is best for data-driven approach
   - Balanced offers good middle ground
   - Random for pure luck players

3. **Generate Multiple Sets**
   - Increase your odds by playing multiple unique combinations
   - The app ensures no duplicate sets

4. **Review Statistics**
   - Hot numbers appear most frequently historically
   - Cold numbers appear least frequently
   - Overdue numbers haven't appeared in a while
   - Common pairs/triplets show historical patterns

## Known Limitations

- No automatic notifications for new draws
- Must manually update data from API
- API has rate limits (max ~10 requests/second)
- No cloud sync - data stored locally only

## CLI Version

The original command-line version (`lotto.py`) is still available:

```bash
python3 lotto.py
```

Both versions share the same data files and logic.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the main CLAUDE.md documentation
3. Check data files in `data/` directories

## Future Enhancements

Potential features for future versions:
- Dark mode theme
- Export numbers to PDF/CSV
- Draw result notifications
- Win checking (compare your numbers to actual draws)
- Number filtering (avoid consecutive, limit odd/even, etc.)
- Historical win analysis
- Custom strategy creation

## License

This is a personal project for educational and entertainment purposes.

**Remember:** Lottery games are games of chance. No system can guarantee winning. Play responsibly!
