# Facebook Rentals Telegram Bot

A Python application that automatically scrapes rental posts from Facebook
groups, filters them using a local LLaMA model (via Ollama), and sends relevant
results as Telegram messages.

## Features

- 🏠 **Facebook Group Scraping**: Automatically scrapes posts from specified
  Facebook rental groups using Playwright
- 🤖 **AI Filtering**: Uses local LLaMA models via Ollama to intelligently
  filter relevant rental posts
- 📱 **Telegram Notifications**: Sends formatted notifications to your Telegram
  chat
- 🗃️ **Duplicate Prevention**: Stores seen posts in SQLite database to avoid
  duplicate notifications
- 🔄 **Scheduled Scraping**: Runs continuously with configurable intervals
- 🐳 **Docker Support**: Includes Docker and docker-compose configurations
- 📊 **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Prerequisites

- Python 3.11+
- Facebook account (for group access)
- Telegram Bot Token
- Ollama (for LLM filtering)
- Docker (optional)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fb-rentals-telegram
cp .env.example .env
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configure Environment

Edit `.env` file with your configuration:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Facebook Groups URLs (comma-separated)
FB_GROUP_URLS=https://www.facebook.com/groups/group1,https://www.facebook.com/groups/group2

# Scraping Configuration
SCRAPE_INTERVAL_MINUTES=30
MAX_POSTS_PER_SCRAPE=50

# LLaMA Model Configuration
OLLAMA_MODEL=llama3.1:latest
OLLAMA_HOST=http://localhost:11434
```

### 3. Setup Telegram Bot

1. Create a new bot via [@BotFather](https://t.me/BotFather)
2. Get your bot token
3. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)
4. Add these values to your `.env` file

### 4. Setup Ollama (for AI filtering)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull the model (in another terminal)
ollama pull llama3.1:latest
```

## Installation Methods

### Method 1: Local Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install pre-commit and code quality tools (optional)
pip install pre-commit black isort ruff pydocstyle pyupgrade autoflake
pre-commit install

# Install Playwright browsers
playwright install chromium

# Run once to test
python app.py once

# Run continuously
python app.py continuous
```

### Method 2: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f fb-rentals-bot

# Stop services
docker-compose down
```

### Method 3: Docker Manual

```bash
# Build the image
docker build -t fb-rentals-bot .

# Run Ollama separately
docker run -d --name ollama -p 11434:11434 ollama/ollama:latest

# Run the bot
docker run -d \
  --name fb-rentals-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/browser_data:/app/browser_data \
  fb-rentals-bot
```

## Facebook Login Setup

Since this app scrapes Facebook, you need to log in to your Facebook account
first:

1. **Start the application** with GUI mode (set `HEADLESS_MODE=false` in `.env`)
2. **Run the test command**:
   ```bash
   python app.py test
   ```
3. **Log in manually** when the browser opens
4. **Stop the application** and set `HEADLESS_MODE=true`
5. **Restart** - the login session will be preserved

The browser data is stored in `./browser_data` directory and persists between
runs.

## Usage Commands

```bash
# Test configuration and send test message
python app.py test

# Run scraper once (for testing)
python app.py once

# Run continuously (default)
python app.py continuous
# or simply
python app.py
```

## Cron Job Setup

To run the scraper periodically via cron instead of continuously:

```bash
# Edit crontab
crontab -e

# Add line to run every 30 minutes
*/30 * * * * cd /path/to/fb-rentals-telegram && /usr/bin/python app.py once >> logs/cron.log 2>&1

# Or run daily at specific time
0 9,17 * * * cd /path/to/fb-rentals-telegram && /usr/bin/python app.py once >> logs/cron.log 2>&1
```

## Configuration Options

### Core Settings

| Variable             | Description                         | Default  |
| -------------------- | ----------------------------------- | -------- |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token             | Required |
| `TELEGRAM_CHAT_ID`   | Your Telegram chat ID               | Required |
| `FB_GROUP_URLS`      | Comma-separated Facebook group URLs | Required |

### Filtering Settings

### Scraping Settings

| Variable                  | Description                     | Default |
| ------------------------- | ------------------------------- | ------- |
| `SCRAPE_INTERVAL_MINUTES` | Minutes between scraping cycles | 30      |
| `MAX_POSTS_PER_SCRAPE`    | Max posts to scrape per group   | 50      |
| `HEADLESS_MODE`           | Run browser in headless mode    | true    |

### LLM Settings

| Variable       | Description       | Default                |
| -------------- | ----------------- | ---------------------- |
| `OLLAMA_HOST`  | Ollama server URL | http://localhost:11434 |
| `OLLAMA_MODEL` | LLM model name    | llama3.1:latest            |

## Project Structure

```
fb-rentals-telegram/
├── main.py                    # Main application entry point
├── scraper.py                 # Facebook scraping logic
├── analyzer.py                # AI apartment analysis logic
├── notifier.py                # Telegram notifications
├── db.py                     # Database operations
├── requirements.txt          # Production dependencies
├── .env.example              # Environment variables template
├── Dockerfile               # Docker image configuration
├── docker-compose.yaml      # Multi-service Docker setup
├── .pre-commit-config.yaml  # Code quality hooks
├── .editorconfig            # Editor configuration
├── README.md                # Project documentation
├── .github/                 # GitHub-specific files
│   └── scripts/             # Utility scripts
│       └── docker.sh        # Enhanced Docker management script
├── data/                    # Database files (created at runtime)
├── logs/                    # Log files (created at runtime)
└── browser_data/            # Browser session data (created at runtime)
```

## How It Works

1. **Scraping**: Uses Playwright to scrape posts from Facebook groups
2. **Filtering**:
   - Basic filtering (price, keywords, location)
   - AI filtering using local LLaMA model via Ollama
   - Fallback filtering if AI is unavailable
3. **Storage**: Stores posts in SQLite to prevent duplicate notifications
4. **Notification**: Sends formatted messages to Telegram with post details
5. **Scheduling**: Runs continuously or on schedule

## Troubleshooting

### Common Issues

**1. Facebook Login Issues**

- Make sure to log in manually first with `HEADLESS_MODE=false`
- Check if your account has access to the groups
- Facebook may require verification for suspicious activity

**2. Telegram Not Working**

- Verify bot token and chat ID
- Make sure the bot is started (send `/start` to your bot)
- Check if the bot has permission to send messages

**3. Ollama/LLM Issues**

- Ensure Ollama is running: `ollama serve`
- Check if model is available: `ollama list`
- The app will use fallback filtering if LLM is unavailable

**4. No Posts Found**

- Check if Facebook groups are public or if you have access
- Verify group URLs are correct
- Check filter settings (price, keywords)

### Logs

Check logs for detailed information:

```bash
# View recent logs
tail -f logs/app.log

# View Docker logs
docker-compose logs -f fb-rentals-bot
```

## Security Considerations

- Keep your `.env` file secure and never commit it
- Use a dedicated Facebook account for scraping
- Be respectful of Facebook's terms of service
- Monitor your usage to avoid rate limiting

## Development

### Code Quality Tools

This project includes comprehensive code quality tools and pre-commit hooks:

- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Fast Python linter (replaces flake8, pylint, etc.)
- **pydocstyle**: Docstring style checking
- **Pre-commit hooks**: Automatic code quality checks on commit

### Development Setup

```bash
# Install code quality tools
pip install pre-commit black isort ruff pydocstyle pyupgrade autoflake
pre-commit install
```

**Note about pre-commit**: Pre-commit hooks require the actual linter tools to
be installed in your environment. The `.pre-commit-config.yaml` file defines
which tools to run, but the tools themselves (black, ruff, etc.) need to be
installed via pip for the hooks to work.

### Development Commands

```bash
# Format code
black .                  # Format code
isort .                  # Sort imports

# Lint and check code quality
ruff check .             # Lint code
ruff check --fix .       # Lint and auto-fix

# Pre-commit (runs automatically on git commit)
pre-commit run --all-files  # Run on all files manually
pre-commit install          # Install hooks
```

### Git Hooks

Pre-commit hooks automatically run when you commit code:

- Code formatting (Black, isort)
- Linting (Ruff)
- Import optimization
- Trailing whitespace removal
- File size limits
- Merge conflict detection

## Project Structure

```
fb-rentals-telegram/
├── src/                    # Main source code
│   ├── __init__.py
│   ├── main.py            # Main application class
│   ├── scraper.py         # Facebook scraping logic
│   ├── analyzer.py        # AI apartment analysis
│   ├── notifier.py        # Telegram notifications
│   └── db.py             # Database operations
├── tests/                 # Test files
│   ├── __init__.py
│   ├── conftest.py        # Pytest configuration
│   ├── test_db.py         # Database tests
│   ├── test_scraper.py    # Scraper test script
│   └── simple_test.py     # Simple scraper test
├── app.py                 # Main entry point
├── setup.py               # Package setup
├── pyproject.toml         # Project configuration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── Dockerfile            # Docker configuration
├── docker-compose.yaml   # Docker Compose setup
└── README.md            # This file
```

## Running Tests

```bash
# Run the scraper test (no LLM)
python tests/test_scraper.py

# Run simple interactive test
python tests/simple_test.py

# Run unit tests (requires pytest)
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes. Please ensure compliance with
Facebook's Terms of Service and local laws regarding web scraping.

## Disclaimer

This tool is for personal use only. Users are responsible for complying with
Facebook's Terms of Service and any applicable laws. The authors are not
responsible for any misuse of this tool.

---

**Need Help?** Check the logs, verify your configuration, and ensure all
prerequisites are met. For Facebook login issues, try running in non-headless
mode first.
