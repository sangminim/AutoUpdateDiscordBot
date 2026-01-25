# Discord Bot for Automatic Update Notifications

This Discord bot automatically checks for updates from specified websites (English and Korean) every 30 minutes and sends the updates to designated Discord channels.

---

## Features

1. Scrapes update information from:
   - **English Update Website**: [Line Games English Notices](https://ud.floor.line.games/us/bbs/notice/notice_us/1)
   - **Korean Update Website**: [Line Games Korean Notices](https://ud.floor.line.games/kr/bbs/notice/notice_kr/1)
2. Sends new updates to specific Discord channels.
3. Automatically splits messages exceeding Discord's character limit (2000 characters).
4. Saves the most recent update details in JSON files to prevent duplicate notifications.

---

## Files

- **`config.json`**: Stores the most recent English update URL.
- **`Title.json`**: Stores the most recent English update title.
- **`configkr.json`**: Stores the most recent Korean update URL.
- **`Titlekr.json`**: Stores the most recent Korean update title.
- **`keep_alive.py`**: Keeps the bot alive for continuous operation.

---

## Requirements

### Python Packages
Install the following packages before running the bot:
- `discord.py`
- `beautifulsoup4`
- `requests`

You can install these packages using:
```bash
pip install discord.py beautifulsoup4 requests
