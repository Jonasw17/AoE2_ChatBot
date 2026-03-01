# Age of Empires 2: Definitive Edition Discord Bot

A Discord bot that provides information about AoE2 DE civilizations, units, technologies, and more. Data is sourced directly from the [aoe2techtree.net GitHub repository](https://github.com/SiegeEngineers/aoe2techtree).

## Features

- Get civilization information (bonuses, unique units, unique techs)
- View unit statistics (cost, HP, attack, armor, etc.)
- Find unit counters
- Compare two civilizations
- List all civilizations and units
- Automatic data updates from GitHub
- Fuzzy name matching (handles typos)
- Optional LLM integration for natural language queries
- Lightweight - uses JSON files instead of a database

## Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- A Discord bot token ([Get one here](https://discord.com/developers/applications))
- (Optional) Groq API key for LLM features

### 2. Installation

```bash
# Clone or download the project
cd aoe2_bot

# Install dependencies
pip install -r requirements.txt

# Copy the example env file
cp .env.example .env

# Edit .env and add your Discord token
# On Windows: notepad .env
# On Linux/Mac: nano .env
```

### 3. Configuration

Edit the `.env` file and set your Discord bot token:

```
DISCORD_TOKEN=your_discord_bot_token_here
```

Optional settings:
- `COMMAND_PREFIX` - Bot command prefix (default: `?`)
- `DATA_CACHE_HOURS` - How long to cache data before re-downloading (default: 24 hours)
- `FUZZY_MATCH_THRESHOLD` - How strict name matching is, 0-100 (default: 80)
- `GROQ_API_KEY` - For natural language query support (optional)

### 4. Running the Bot

```bash
# Run the bot
python discord_bot.py
```

The bot will:
1. Download the latest AoE2 data from GitHub
2. Cache it locally in the `data/` folder
3. Connect to Discord and be ready to use

## Commands

### Basic Commands

- `?help` - Show all available commands
- `?ping` - Check bot latency
- `?info` - Show bot information
- `?datainfo` - Show loaded data statistics

### Civilization Commands

- `?civ <name>` - Get civilization info
  - Example: `?civ Britons`
  - Example: `?civ mongols`
  
- `?civs` - List all civilizations

- `?compare <civ1> <civ2>` - Compare two civilizations
  - Example: `?compare Britons Franks`

### Unit Commands

- `?unit <name>` - Get unit statistics
  - Example: `?unit Knight`
  - Example: `?unit longbowman`
  
- `?units` - List all units

- `?counter <unit>` - Get counter information
  - Example: `?counter Knight`

### Admin Commands

- `?update` - Force update data from GitHub (admin only)

### Natural Language (if LLM enabled)

- `?aoe2 <question>` - Ask any question
  - Example: `?aoe2 What are the Britons bonuses?`
  - Example: `?aoe2 How much does a knight cost?`

## How It Works

### Data Management

The bot downloads JSON files from the aoe2techtree GitHub repository:
- `data.json` - Civilization data
- `units.json` - Unit statistics
- `techs.json` - Technologies
- `buildings.json` - Building data
- `strings.json` - Localized strings

Data is cached locally and automatically refreshed based on `DATA_CACHE_HOURS`.

### Fuzzy Matching

The bot uses fuzzy string matching to handle typos and variations:
- `?civ briton` matches "Britons"
- `?unit knght` matches "Knight"
- `?civ mongol` matches "Mongols"

Matching threshold can be adjusted in `.env`.

### Automatic Updates

When the AoE2 team updates the game and the GitHub repo is updated:
1. The bot will detect outdated cache (after `DATA_CACHE_HOURS`)
2. Automatically download fresh data
3. No manual intervention needed

Admins can force an update with `?update`.

## Deployment

### Running on Windows

```bash
# Run directly
python discord_bot.py

# Or create a batch file (run_bot.bat):
@echo off
python discord_bot.py
pause
```

### Running on Raspberry Pi

```bash
# Install Python 3 if needed
sudo apt update
sudo apt install python3 python3-pip

# Install dependencies
pip3 install -r requirements.txt

# Run the bot
python3 discord_bot.py
```

#### Run on Startup (Raspberry Pi)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/aoe2bot.service
```

Add this content (adjust paths):

```ini
[Unit]
Description=AoE2 Discord Bot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/aoe2_bot
ExecStart=/usr/bin/python3 /home/pi/aoe2_bot/discord_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable aoe2bot
sudo systemctl start aoe2bot
sudo systemctl status aoe2bot
```

View logs:
```bash
sudo journalctl -u aoe2bot -f
```

## File Structure

```
aoe2_bot/
├── discord_bot.py        # Main bot file
├── commands.py           # Discord command handlers
├── data_manager.py       # JSON data management
├── retriever.py          # Data retrieval with fuzzy matching
├── llm_handler.py        # Optional LLM integration
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── .env                  # Your configuration (create from .env.example)
└── data/                 # Cached JSON files (auto-created)
```

## Troubleshooting

### Bot won't start

- Check your `DISCORD_TOKEN` in `.env`
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

### Commands not working

- Make sure bot has proper Discord permissions
- Check the command prefix in `.env` (default is `?`)
- Try `?help` to see available commands

### Data not loading

- Check internet connection (bot needs to download from GitHub)
- Check if GitHub is accessible: visit https://github.com/SiegeEngineers/aoe2techtree
- Delete the `data/` folder and restart the bot to force re-download

### "Civilization not found"

- Use `?civs` to see all civilization names
- Bot uses fuzzy matching, but try using exact names
- Try adjusting `FUZZY_MATCH_THRESHOLD` in `.env`

## Contributing

This bot uses data from the excellent [aoe2techtree.net](https://aoe2techtree.net) project. 

All game data is maintained by the AoE2 community at:
https://github.com/SiegeEngineers/aoe2techtree

## License

This bot is for educational purposes. Age of Empires 2 and all related content are property of Microsoft Corporation.
