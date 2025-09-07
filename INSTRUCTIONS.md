# Facebook Rental Bot - Application Flow Instructions

## Overview

This application automatically monitors Facebook rental groups, analyzes posts
using AI, and sends matching apartments to Telegram. It's designed to help you
find suitable rental properties without manually checking multiple Facebook
groups.

## 📋 Application Flow

### Main Process Cycle

The bot runs in a continuous loop that repeats every SCRAPE_INTERVAL_MINUTES
(configurable in .env):

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
  - Price (within budget range)
  - Room count (minimum requirements), apartment type, etc.
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

````

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
````

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

1. Modify prompts in `src/analyzer.py` (price limit is set in the prompt)
2. Test with `python tests/manual_analyzer_test.py`

### Changing Schedule

1. Update `SCRAPE_INTERVAL_MINUTES` in `.env`
2. Restart application for changes to take effect

## 🔒 Privacy & Ethics

- Respects Facebook's rate limits
- Only scrapes public group posts
- Stores minimal necessary data
- Does not share or redistribute content
- Uses persistent browser sessions to minimize requests
