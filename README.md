# Repgen Telegram Bot

A modular Telegram bot for defect photo analysis and report generation, using OpenAI and DOCX export. 

## Features
- Upload and analyze defect photos via Telegram
- Generate DOCX reports automatically
- User access control (whitelist, admin approval)
- Dockerized for easy deployment

## Project Structure
```
core/              # Main bot logic (handlers, photo manager)
common/            # Utilities and shared modules
settings.py        # Configuration and constants
main.py            # Entry point
requirements.txt   # Python dependencies
docx_generator/    # DOCX report generation
```

## Quick Start
1. **Clone the repo**
2. **Configure environment**
   - Copy `.env.example` to `.env` and set your variables (see below)
3. **Build and run with Docker Compose**
   ```sh
   docker compose up --build
   ```

## .env Example
```
GOOGLE_APPLICATION_CREDENTIALS=secrets/gcs_key.json
OPENAI_API_KEY=sk-...
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
```