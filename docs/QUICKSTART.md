# Quick Start Guide

Get your AoE2 Discord bot running in 5 minutes!

## Step 1: Get Your Discord Bot Token

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Give it a name (e.g., "AoE2 Bot")
4. Go to "Bot" section
5. Click "Add Bot"
6. Under "Token", click "Copy" to copy your bot token
7. Enable "Message Content Intent" under "Privileged Gateway Intents"

## Step 2: Install Python

### Windows
1. Download Python from https://www.python.org/downloads/
2. Run installer
3. **Important:** Check "Add Python to PATH"
4. Click "Install Now"

### Raspberry Pi
```bash
sudo apt update
sudo apt install python3 python3-pip
```

## Step 3: Setup Bot

### Windows
```bash
# Open Command Prompt in the bot folder
# Install dependencies
pip install -r requirements.txt

# Copy example config
copy .env.example .env

# Edit .env with Notepad
notepad .env
```

### Raspberry Pi
```bash
# Navigate to bot folder
cd ~/aoe2_bot

# Install dependencies
pip3 install -r requirements.txt

# Copy example config
cp .env.example .env

# Edit .env
nano .env
```

## Step 4: Configure

In the `.env` file, add your Discord bot token:

```
DISCORD_TOKEN=paste_your_token_here
```

Save and close the file.

## Step 5: Test

Test that everything works:

```bash
# Windows
python test_bot.py

# Raspberry Pi
python3 test_bot.py
```

You should see "All tests passed!"

## Step 6: Run the Bot

### Windows
```bash
python discord_bot.py

# Or just double-click run_bot.bat
```

### Raspberry Pi
```bash
python3 discord_bot.py
```

You should see:
```
Bot is ready! Logged in as AoE2 Bot
Connected to X server(s)
Commands loaded successfully!
```

## Step 7: Invite Bot to Your Server

1. Go back to https://discord.com/developers/applications
2. Select your bot application
3. Go to "OAuth2" > "URL Generator"
4. Select scopes:
   - bot
5. Select bot permissions:
   - Send Messages
   - Embed Links
   - Read Message History
6. Copy the generated URL
7. Paste in browser and select your server

## Step 8: Test in Discord

In your Discord server, try these commands:

```
?ping
?info
?civs
?civ Britons
?unit Knight
?compare Britons Franks
```

## Troubleshooting

### "DISCORD_TOKEN is required"
- Make sure you edited `.env` and added your token
- Make sure the file is named `.env` not `.env.txt`

### "Module not found"
- Run: `pip install -r requirements.txt`
- Make sure you're using Python 3.8 or higher

### Bot connects but doesn't respond
- Check you enabled "Message Content Intent" in Discord Developer Portal
- Make sure bot has permission to read/send messages in the channel
- Try mentioning the bot to see if it's online

### "Data not loading"
- Check your internet connection
- The bot needs to download data from GitHub on first run
- Wait a minute for the download to complete

## Next Steps

- Read `README.md` for full documentation
- Adjust settings in `.env` as needed
- Set up auto-start on Raspberry Pi (see README.md)

## Common Configurations

### Change Command Prefix
In `.env`:
```
COMMAND_PREFIX=?
```
Now use `?civ Britons` instead of `?civ Britons`

### Update Data More Frequently
In `.env`:
```
DATA_CACHE_HOURS=12
```
Bot will check for updates every 12 hours

### Add LLM Support (Optional)
1. Get a Groq API key from https://console.groq.com
2. In `.env`:
```
GROQ_API_KEY=your_groq_key_here
```
3. Now you can use natural language: `?aoe2 What are the Britons bonuses?`

## That's It!

Your bot should now be running. Enjoy!

For help, questions, or issues, check the README.md file.
