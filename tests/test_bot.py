#!/usr/bin/env python3
"""
Test script to verify bot components are working
Run this before starting the Discord bot
"""

import sys

# Ensure project root is on sys.path so tests can import package modules when run from the tests/ folder.
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import discord
        print("  - discord.py: OK")
    except ImportError:
        print("  - discord.py: MISSING - Run: pip install discord.py")
        return False
    
    try:
        import requests
        print("  - requests: OK")
    except ImportError:
        print("  - requests: MISSING - Run: pip install requests")
        return False
    
    try:
        from fuzzywuzzy import fuzz
        print("  - fuzzywuzzy: OK")
    except ImportError:
        print("  - fuzzywuzzy: MISSING - Run: pip install fuzzywuzzy python-Levenshtein")
        return False
    
    try:
        from dotenv import load_dotenv
        print("  - python-dotenv: OK")
    except ImportError:
        print("  - python-dotenv: MISSING - Run: pip install python-dotenv")
        return False
    
    return True

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    
    try:
        from config import Config
        
        if not Config.DISCORD_TOKEN:
            print("  - WARNING: DISCORD_TOKEN not set in .env file")
            return False
        else:
            print(f"  - DISCORD_TOKEN: Set (length: {len(Config.DISCORD_TOKEN)})")
        
        print(f"  - Command prefix: {Config.COMMAND_PREFIX}")
        print(f"  - Cache directory: {Config.DATA_CACHE_DIR}")
        print(f"  - Cache hours: {Config.DATA_CACHE_HOURS}")
        print(f"  - Fuzzy threshold: {Config.FUZZY_MATCH_THRESHOLD}")
        
        return True
    except Exception as e:
        print(f"  - ERROR: {e}")
        return False

def test_data_manager():
    """Test data manager"""
    print("\nTesting data manager...")
    
    try:
        from manager.data_manager import DataManager
        
        print("  - Creating data manager...")
        dm = DataManager()
        
        print("  - Loading data from GitHub...")
        dm.load_all_data()
        
        info = dm.get_data_info()
        print(f"  - Loaded {info['civs_count']} civilizations")
        print(f"  - Loaded {info['units_count']} units")
        print(f"  - Loaded {info['techs_count']} technologies")
        print(f"  - Loaded {info['buildings_count']} buildings")
        
        if info['civs_count'] == 0:
            print("  - WARNING: No civilizations loaded!")
            return False
        
        # Test getting a civ
        britons = dm.get_civ_data('Britons')
        if britons:
            print(f"  - Test: Retrieved Britons data successfully")
        else:
            print("  - WARNING: Could not retrieve Britons data")
        
        return True
    except Exception as e:
        print(f"  - ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retriever():
    """Test data retriever"""
    print("\nTesting retriever...")
    
    try:
        from manager.retriever import DataRetriever
        
        print("  - Creating retriever...")
        retriever = DataRetriever()
        
        # Test fuzzy matching
        print("  - Testing fuzzy matching...")
        match = retriever.fuzzy_match_civ('briton')
        if match:
            print(f"    'briton' -> '{match}'")
        
        match = retriever.fuzzy_match_unit('knght')
        if match:
            print(f"    'knght' -> '{match}'")
        
        # Test data retrieval
        print("  - Testing data retrieval...")
        civ_info = retriever.get_civ_info('Britons')
        if civ_info:
            print(f"    Retrieved {civ_info['name']} with {len(civ_info['bonuses'])} bonuses")
        
        return True
    except Exception as e:
        print(f"  - ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_handler():
    """Test LLM handler (optional)"""
    print("\nTesting LLM handler (optional)...")
    
    try:
        from llm.llm_handler import LLMHandler
        
        llm = LLMHandler()
        
        if llm.is_available():
            print("  - LLM is available (Groq API key found)")
        else:
            print("  - LLM not available (no API key) - bot will use fallback methods")
        
        return True
    except Exception as e:
        print(f"  - ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("AoE2 Discord Bot - Component Test")
    print("=" * 60)
    
    results = {
        'Imports': test_imports(),
        'Configuration': test_config(),
        'Data Manager': test_data_manager(),
        'Retriever': test_retriever(),
        'LLM Handler': test_llm_handler()
    }
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20s}: {status}")
    
    print("=" * 60)
    
    if all(results.values()):
        print("\nAll tests passed! Bot is ready to run.")
        print("Start the bot with: python discord_bot.py")
        return 0
    else:
        print("\nSome tests failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
