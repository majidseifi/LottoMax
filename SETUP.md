# Setup Instructions

## Initial Setup

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Configure API Key

This application requires a RapidAPI key for the Canada Lottery API.

1. **Get your API key:**
   - Visit: https://rapidapi.com/belchiorarkad-FqvHs2EDOtP/api/canada-lottery
   - Sign up or log in to RapidAPI
   - Subscribe to the Canada Lottery API (free tier available)
   - Copy your API key

2. **Create `.env` file:**
   - Copy the example file: `cp .env.example .env`
   - Open `.env` in a text editor
   - Replace `your_api_key_here` with your actual RapidAPI key

```bash
# Example .env file
RAPIDAPI_KEY=your_actual_api_key_here
RAPIDAPI_HOST=canada-lottery.p.rapidapi.com
```

### 3. Run the Application

```bash
python3 lotto.py
```

## Security Note

**NEVER commit your `.env` file to git!** The `.gitignore` file is configured to exclude it automatically.

## Optional: Google Sheets Integration

If you want to export data to Google Sheets (optional):

1. Create a Google Cloud project and enable the Sheets API
2. Download your service account credentials JSON file
3. Place it in `credentials/google_sheets_credentials.json`
4. Update your `.env` file with the path and spreadsheet ID

These directories are already excluded from git for security.

## Troubleshooting

**Error: "RAPIDAPI_KEY not found in environment variables"**
- Make sure you created the `.env` file in the project root
- Verify the file contains `RAPIDAPI_KEY=your_key_here`
- Ensure there are no extra spaces around the equals sign

**API Rate Limiting:**
- The free tier allows 50 requests per minute
- The app automatically enforces rate limiting (1.35 seconds between requests)
