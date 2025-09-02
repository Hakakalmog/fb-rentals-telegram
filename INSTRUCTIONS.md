# Facebook Rental Bot - Application Flow Instructions

## Overview

This application automatically monitors Facebook rental groups, analyzes posts using AI, and sends matching apartments to Telegram. It's designed to help you find suitable rental properties without manually checking multiple Facebook groups.

## 📋 Application Flow

### Main Process Cycle

The bot runs in a continuous loop that repeats every SCRAPE_INTERVAL_MINUTES (configurable in .env):

**1. Load Facebook Groups List**
   - From FB_GROUP_URLS environment variable
   - Or from hardcoded list in code

**2. For Each Facebook Group:**

   **2.1 Scrape Latest Posts**
   - Scrape MAX_POSTS_PER_SCRAPE posts using Playwright browser automation
   - Extract: content, author, timestamp, link

   **2.2 Check Database for New Posts**
   - Compare with existing posts in SQLite database
   - Filter out posts already processed
   - Save only NEW posts to database

   **2.3 AI Analysis with Ollama**
   - Send new posts to local OLLAMA_MODEL
   - Analyze based on criteria:
     - Price (max from MAX_PRICE env var)
     - Room count, apartment type, etc.
   - Get "MATCH" or "NO MATCH" result

   **2.4 Send Matching Posts to Telegram**
   - Only posts marked as "MATCH"
   - Include: content, price, location, link
   - Send to TELEGRAM_CHAT_ID

   **2.5 Update Database**
   - Mark posts as "match" or "no match"
   - Store analysis results
   - Update processing timestamp

**3. Move to Next Group**
   - Repeat steps 2.1-2.5 for next Facebook group

**4. Wait for Next Cycle**
   - Sleep for SCRAPE_INTERVAL_MINUTES
   - Then start over from step 1
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example | Default |
|----------|-------------|---------|---------|
| `FB_GROUP_URLS` | Comma-separated Facebook group URLs | `https://facebook.com/groups/X,https://facebook.com/groups/Y` | - |
| `SCRAPE_INTERVAL_MINUTES` | Minutes between scraping cycles | `X` | X |
| `MAX_POSTS_PER_SCRAPE` | Posts to scrape per group per cycle | `X` | X |
| `MAX_PRICE` | Maximum acceptable rent price | `X` | X |
| `OLLAMA_MODEL` | AI model for analysis | `llama3.1:latest` | llama3.1:latest |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` | http://localhost:11434 |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `XXXXXX:ABC-DEF...` | - |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | `XXXXXXXXX` | - |
| `DATABASE_PATH` | SQLite database file path | `./data/posts.db` | ./data/posts.db |
| `LOG_LEVEL` | Logging level | `INFO` | INFO |
| `LOG_FILE` | Log file path | `./logs/app.log` | ./logs/app.log |
| `HEADLESS_MODE` | Run browser in headless mode | `true` | true |
| `BROWSER_DATA_DIR` | Browser data directory | `./browser_data` | ./browser_data |

## 🏗️ System Components

### 1. Facebook Scraper (`src/scraper.py`)
- Uses Playwright for browser automation
- Handles login persistence and anti-detection
- Extracts post content, metadata, and links
- Manages rate limiting and error handling

### 2. AI Analyzer (`src/analyzer.py`)
- Connects to local Ollama server
- Uses LLaMA model for intelligent post analysis
- Evaluates posts against rental criteria
- Returns binary "match" or "no match" decisions

### 3. Database Manager (`src/database.py`)
- SQLite database for post storage
- Tracks processed posts to avoid duplicates
- Stores analysis results and metadata
- Handles schema migrations

### 4. Telegram Notifier (`src/telegram_notifier.py`)
- Sends formatted messages to Telegram
- Includes post content, analysis, and links
- Handles message formatting and error recovery

### 5. Main Orchestrator (`src/main.py`)
- Coordinates all components
- Manages the main processing loop
- Handles scheduling and error recovery
- Provides CLI interface

## 🚀 Running the Application

### Prerequisites
1. **Ollama** installed and running locally
2. **LLaMA model** pulled (e.g., `ollama pull llama3.1:latest`)
3. **Telegram bot** created via @BotFather
4. **Facebook account** logged in (for scraping)

### 🔐 First Run - Facebook Login

**Important**: On your first run, the application will automatically open a Chrome browser window and prompt you to log into Facebook manually.

```bash
# For first-time setup, run in test mode to establish Facebook login
python src/main.py test
```

**What happens during first login:**
1. A **visible Chrome browser** window opens
2. You'll be navigated to Facebook's login page
3. **Manually log in** with your Facebook credentials
4. The browser will stay open - press **ENTER** in the terminal when logged in
5. Your login session is **saved persistently** for future runs
6. After successful login, the app will scrape a test group to verify everything works

**Subsequent runs:**
- No manual login required - your session is remembered
- The application runs in **headless mode** (invisible browser)
- If your session expires, you'll need to re-login using the test mode

### Startup Commands

```bash
# One-time run (scrape once and exit)
python src/main.py once

# Test configuration (verify setup)
python src/main.py test

# Continuous operation (default - runs every hour)
python src/main.py
# or
python src/main.py continuous
```

## 📊 Data Flow

### Database Schema
```sql
posts (
  id INTEGER PRIMARY KEY,
  content TEXT,
  author TEXT,
  timestamp TEXT,
  link TEXT,
  group_url TEXT,
  analysis_result TEXT,  -- "match" or "no match"
  created_at TIMESTAMP,
  processed_at TIMESTAMP
)
```

### Processing States
- **New**: Post scraped, saved to DB, not yet analyzed
- **Analyzed**: Post analyzed by AI, result stored
- **Notified**: Matching post sent to Telegram
- **Completed**: Full processing cycle finished

## 🔍 Monitoring & Logs

### Log Levels
- **INFO**: Normal operation, scraping progress
- **WARNING**: Non-critical issues, retries
- **ERROR**: Failed operations, missing configuration
- **DEBUG**: Detailed debugging information

### Key Log Messages
- `"Starting scrape cycle for X groups"`
- `"Found N new posts in group"`
- `"AI analysis complete: X matches, Y non-matches"`
- `"Sent N notifications to Telegram"`
- `"Cycle complete, sleeping for X minutes"`

## 🛠️ Troubleshooting

### Common Issues

1. **No posts found**: Check Facebook login status, group privacy
2. **AI analysis fails**: Verify Ollama is running, model is available
3. **Telegram not working**: Check bot token, chat ID, network
4. **Database errors**: Check file permissions, disk space
5. **Facebook login expired**: Run `python src/main.py test` to re-login
6. **Browser crashes**: Delete `./browser_data` folder and re-login

### Manual Testing

```bash
# Test Facebook login and scraping (with manual login prompt)
python tests/manual_login_test.py

# Test AI analysis
python tests/manual_analyzer_test.py

# Test full pipeline
python tests/test_manual_group_scraper.py
```

## 🎯 Customization

### Adding New Groups
1. Add URLs to `FB_GROUP_URLS` in `.env`
2. Restart the application
3. Monitor logs for successful scraping

### Adjusting AI Criteria
1. Modify prompts in `src/analyzer.py`
2. Update `MAX_PRICE`
3. Test with `python tests/manual_analyzer_test.py`

### Changing Schedule
1. Update `SCRAPE_INTERVAL_MINUTES` in `.env`
2. Restart application for changes to take effect

## 📈 Performance Notes

- **Processing time**: ~X-X minutes per group (MAX_POSTS_PER_SCRAPE posts)
- **AI analysis**: ~X-X seconds per post
- **Memory usage**: ~XMB-XMB during operation
- **Storage**: ~XMB per X posts in database

## 🔒 Privacy & Ethics

- Respects Facebook's rate limits
- Only scrapes public group posts
- Stores minimal necessary data
- Does not share or redistribute content
- Uses persistent browser sessions to minimize requests
