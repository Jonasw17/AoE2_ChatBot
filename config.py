import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the bot"""
    
    # Discord Settings
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '?')
    BOT_ADMIN_IDS = [int(id.strip()) for id in os.getenv('BOT_ADMIN_IDS', '').split(',') if id.strip()]
    
    # Data Settings
    DATA_CACHE_DIR = os.getenv('DATA_CACHE_DIR', 'data')
    DATA_CACHE_HOURS = int(os.getenv('DATA_CACHE_HOURS', '24'))  # 24 hours
    
    # LLM Settings (optional - bot works without LLM)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.1-70b-versatile')
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '1024'))
    
    # Bot Behavior
    MAX_RESPONSE_LENGTH = 2000  # Discord message limit
    FUZZY_MATCH_THRESHOLD = int(os.getenv('FUZZY_MATCH_THRESHOLD', '80'))
    
    # GitHub Data Source
    GITHUB_REPO = 'SiegeEngineers/aoe2techtree'
    GITHUB_DATA_URL = 'https://raw.githubusercontent.com/SiegeEngineers/aoe2techtree/master/data'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required in .env file")
        return True
