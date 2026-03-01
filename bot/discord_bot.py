"""
Discord bot main file
"""
import discord
from discord.ext import commands
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(
    command_prefix=Config.COMMAND_PREFIX,
    intents=intents,
    help_command=commands.DefaultHelpCommand()
)

@bot.event
async def on_ready():
    """Event triggered when bot is ready"""
    print(f'Bot is ready! Logged in as {bot.user.name} (ID: {bot.user.id})')
    print(f'Connected to {len(bot.guilds)} server(s)')

    # Set bot status
    activity = discord.Game(name="Age of Empires 2 | ?help")
    await bot.change_presence(activity=activity)

    # Load commands cog
    try:
        await bot.load_extension('bot.commands')
        print('Commands loaded successfully!')
    except Exception as e:
        print(f'Failed to load commands: {e}')
        import traceback
        traceback.print_exc()

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use `?help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        print(f'Error: {error}')
        import traceback
        traceback.print_exc()
        await ctx.send("An error occurred while processing your command.")

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Process commands
    await bot.process_commands(message)

@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latency: {latency}ms')

@bot.command(name='info')
async def bot_info(ctx):
    """Get bot information"""
    embed = discord.Embed(
        title="AoE2 Discord Bot",
        description="A bot for Age of Empires 2: Definitive Edition information",
        color=discord.Color.blue()
    )

    embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Prefix", value=Config.COMMAND_PREFIX, inline=True)
    embed.add_field(
        name="Commands",
        value="Use `?help` to see all available commands",
        inline=False
    )
    embed.add_field(
        name="Data Source",
        value="[GitHub - aoe2techtree](https://github.com/SiegeEngineers/aoe2techtree)",
        inline=False
    )
    embed.add_field(
        name="Key Commands",
        value="`?civ <name>` - Get civ info\n`?unit <name>` - Get unit stats\n`?civs` - List all civs\n`?datainfo` - Show data info",
        inline=False
    )

    await ctx.send(embed=embed)

def main():
    """Main function to run the bot"""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file and ensure DISCORD_TOKEN is set.")
        return

    # Run bot
    try:
        print("Starting bot...")
        print(f"Data will be cached in: {Config.DATA_CACHE_DIR}/")
        print(f"Cache duration: {Config.DATA_CACHE_HOURS} hours")
        bot.run(Config.DISCORD_TOKEN)
    except discord.LoginFailure:
        print("Failed to login. Please check your DISCORD_TOKEN.")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()