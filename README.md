# Facebook Rentals Telegram Bot

A smart Python application that automatically scrapes rental posts from Facebook groups, filters them using AI (Ollama/LLaMA), and sends only the most relevant rental opportunities directly to your Telegram. Say goodbye to endless scrolling through Facebook groups - let the bot do the work while you focus on finding your perfect home! 🏠

## 🚀 Features

- 🏠 **Smart Facebook Scraping**: Automatically monitors multiple Facebook rental groups
- 🤖 **AI-Powered Filtering**: Uses local LLaMA models (via Ollama) to intelligently filter relevant rental posts
- 📱 **Telegram Notifications**: Clean, formatted notifications sent directly to your Telegram
- 🗃️ **Duplicate Prevention**: SQLite database prevents spam from duplicate posts
- 🔄 **Continuous Operation**: Runs 24/7 with configurable intervals and downtime scheduling
- 🎯 **Customizable Filters**: Exclude irrelevant posts with keyword blacklists
- 📊 **Model Accuracy Testing**: Test and tune your AI filtering for optimal results
- 🐳 **Docker Support**: Easy deployment with Docker and docker-compose

---

## 📋 Prerequisites

Before getting started, you'll need:

### 1. **Ollama** (Required for AI filtering)
Install Ollama to run local LLM models:
- **Regular Installation**: Follow the [official Ollama guide](https://ollama.com)
- **Docker Installation**: Use [Ollama's official Docker image](https://ollama.com/blog/ollama-is-now-available-as-an-official-docker-image)

### 2. **Python 3.11+**
### 3. **Facebook Account** (with access to rental groups)
### 4. **Telegram Bot** (we'll create this together)

---

## 🛠️ Installation & Setup

### Step 1: Clone and Setup Environment

```bash
git clone <repository-url>
cd fb-rentals-telegram

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers and dependencies
playwright install-deps

# Copy environment template
cp .env.example .env
```

### Step 2: Setup Ollama and AI Model

```bash
# First, pull the recommended model (this downloads it)
ollama pull llama3.1:latest

# Then start Ollama service
ollama serve
```

**💡 Tip**: `llama3.1:latest` is recommended.
**Note**: Change `OLLAMA_HOST` in your `.env` file if running Ollama on a different machine or port.

### Step 3: Create Telegram Bot

#### Get Bot Token:
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the bot token
4. **Detailed guide**: [Creating Telegram Bot](https://docs.radist.online/docs/our-products/radist-web/connections/telegram-bot/instructions-for-creating-and-configuring-a-bot-in-botfather)

#### Get Your Chat ID:
1. Start a chat with your new bot (send `/start`)
2. Follow this guide: [Get Telegram Chat ID Guide](https://gist.github.com/nafiesl/4ad622f344cd1dc3bb1ecbe468ff9f8a)

**💡 Pro Tip**: You can add the bot to a **Telegram group** with friends who are also looking for rentals! This way everyone gets the notifications. Perfect for coordinating with roommates or friends, unless you're a nerd without friends, then stick to direct messages.

### Step 4: Configure Environment Variables

Edit your `.env` file (this is an example):

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Facebook Groups (comma-separated URLs)
FB_GROUP_URLS=https://www.facebook.com/groups/group1,https://www.facebook.com/groups/group2

# Scraping Settings
SCRAPE_INTERVAL_MINUTES=60  # How often to check for new posts
MAX_POSTS_PER_SCRAPE=10     # Posts to scan per group each time

# AI Model Configuration
OLLAMA_MODEL=llama3.1:latest
OLLAMA_HOST=http://localhost:11434

# Browser Settings
HEADLESS_MODE=true  # Set to false for initial login

# Optional: Scheduled Downtime (quiet hours)
DOWNTIME_ENABLED=false
DOWNTIME_START_HOUR=22    # 10 PM
DOWNTIME_DURATION_HOURS=6 # Until 4 AM
```

### Step 5: Facebook Login & Group Setup

#### Initial Login Test:
```bash
# Set browser to visible mode for login
# In .env: HEADLESS_MODE=false

python app.py test
```

When the browser opens:
1. **Log in to Facebook** manually
2. **Join the rental groups** you want to monitor
3. **Close the browser** - your session is now saved

**🔒 Security**: Your login session is stored locally in `browser_data/` and persists between runs.

---

## ⚙️ Facebook Rate Limiting & Best Practices

**Important**: Facebook monitors scraping activity. Follow these guidelines:

- **Scrape Interval**: Don't go below 30 minutes (`SCRAPE_INTERVAL_MINUTES=30`) - not tested but smart guess, not recommended to go lower
- **Posts Limit**: Keep `MAX_POSTS_PER_SCRAPE` reasonable (10-20)
- **Group Access**: Only scrape groups you're legitimately a member of
- **Respectful Usage**: Don't hammer Facebook's servers

**Rate Limiting Signs**:
- Slow page loads
- Login challenges
- Temporary account restrictions

**If rate-limited**: Increase intervals, reduce post limits, or enable downtime scheduling.

---

## 🎯 Optimizing AI Filtering

### Configure Irrelevant Word Exclusions

Add words to exclude posts that aren't rentals:

```env
# In .env file - the more exclusions, the better the filtering
ANALYZER_EXCLUDE_WORDS=מחפש,מחפשת,מחפשים,מחפשות,דרוש,דרושה,דרושים,דרושות,למכירה,מכירה,שותף,שותפים,שותפות,שותפה,שותף/ה,שותףה,גבעתיים,סאבלט,סבלט
```

**💡 Pro Tip**: The more irrelevant keywords you exclude, the better your results!

### Customize the AI Prompt

The current prompt gives excellent results, but you can modify it in `src/analyzer.py` in the `create_analysis_prompt()` function.

**💡 Tip**: The current prompt template has been tested and gives excellent results.

### Test Model Accuracy

Before going live, test your AI filtering:

```bash
# Run accuracy tests
python -m pytest tests/model_accuracy_test.py -v

# Expected result: >90% accuracy
```

**Customizing Tests**: Use GitHub Copilot or modify `tests/model_accuracy_test.py` to create test cases specific to your target rental groups and language.

### Change Test Facebook Group

For testing, modify the test group in your configuration:

```env
# Use a small, active group for testing
FB_GROUP_URLS=https://www.facebook.com/groups/your-test-group
```

---

## 🏃‍♂️ Running the Application

### Test Everything First:
```bash
# Test Telegram connectivity, Facebook login, and AI model
python app.py test
```

### Run Once (for testing):
```bash
# Single scraping cycle
python app.py once
```

### Run Continuously:
```bash
# Starts continuous monitoring (recommended)
python app.py continuous

# Or simply:
python app.py
```

---

## 📊 Configuration Options

### Core Settings

| Setting | Description | Default | Notes |
|---------|-------------|---------|--------|
| `TELEGRAM_BOT_TOKEN` | Your bot token | Required | From @BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID | Required | From @userinfobot |
| `FB_GROUP_URLS` | Groups to monitor | Required | Comma-separated |

### Scraping Control

| Setting | Description | Default | Notes |
|---------|-------------|---------|--------|
| `SCRAPE_INTERVAL_MINUTES` | Minutes between cycles | 60 | Min recommended: 30 |
| `MAX_POSTS_PER_SCRAPE` | Posts per group per cycle | 10 | Balance speed vs coverage |

### AI Model Settings

| Setting | Description | Default | Notes |
|---------|-------------|---------|--------|
| `OLLAMA_HOST` | Ollama server URL | localhost:11434 | Change for remote Ollama |
| `OLLAMA_MODEL` | Model name | llama3.1:latest | **Highly recommended** |

### Smart Scheduling

| Setting | Description | Default | Notes |
|---------|-------------|---------|--------|
| `DOWNTIME_ENABLED` | Enable quiet hours | false | Useful for night hours |
| `DOWNTIME_START_HOUR` | Start hour (0-23) | 22 | 10 PM |
| `DOWNTIME_DURATION_HOURS` | Duration | 6 | Until 4 AM |

**Example**: Quiet hours from 10 PM to 4 AM:
```env
DOWNTIME_ENABLED=true
DOWNTIME_START_HOUR=22
DOWNTIME_DURATION_HOURS=6
```

---

## 🎯 The End Result

Once configured, sit back and relax! The bot will:

1. **Monitor** your Facebook groups 24/7
2. **Filter out** irrelevant posts using AI
3. **Send** only quality rental opportunities to your Telegram
4. **Prevent** duplicate notifications
5. **Respect** rate limits and quiet hours

**You get**: Quality rental posts delivered to your phone without spending hours scrolling through Facebook groups like an idiot! 🎉

---

## 🔧 Troubleshooting

### Facebook Issues
- **Can't log in**: Set `HEADLESS_MODE=false`, run test, log in manually
- **No posts found**: Check group access, verify URLs, test with single group
- **Rate limited**: Increase intervals, enable downtime, reduce post limits

### Telegram Issues  
- **No messages**: Verify token/chat ID, send `/start` to bot
- **Bot permissions**: Ensure bot can send messages

### AI/Ollama Issues
- **Model not working**: Check `ollama serve` is running, model is downloaded
- **Poor filtering**: Test accuracy, adjust prompt, add exclusion keywords
- **Ollama unavailable**: App uses fallback filtering automatically

### General Debugging
```bash
# Check logs
tail -f logs/app.log

# Test individual components
python app.py test

# Verify model accuracy  
python -m pytest tests/model_accuracy_test.py -v
```

---

## 🤝 Contributing

Found a bug? Want to improve the AI prompt? Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

---

## ⚖️ Disclaimer

This tool is for personal use only. Users are responsible for:
- Complying with Facebook's Terms of Service
- Respecting group rules and privacy
- Following local laws regarding data scraping
- Using the tool ethically and responsibly

**The authors are not responsible for any misuse of this application.**

---

**Ready to escape the Facebook rental scroll hell? Let's get started!** 🚀
