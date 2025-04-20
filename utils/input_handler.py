from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

def get_cached_api_key() -> Optional[str]:
    """
    Get the cached API key if it exists.
    Returns None if no cached key is found.
    """
    api_key_path = Path.home() / ".polygon_api_key"
    if api_key_path.exists():
        try:
            with open(api_key_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading cached API key: {e}")
    return None

def cache_api_key(api_key: str):
    """
    Cache the API key for future use.
    """
    api_key_path = Path.home() / ".polygon_api_key"
    try:
        with open(api_key_path, 'w') as f:
            f.write(api_key)
        logger.info("API key cached successfully")
    except Exception as e:
        logger.error(f"Error caching API key: {e}")

def get_user_input() -> Dict:
    """
    Get configuration from user through interactive prompts.
    Returns a dictionary containing all the configuration values.
    """
    print("\n🔧 Configuration")
    print("=" * 50)
    
    config = {}
    
    # Check if API key is cached
    api_key = get_cached_api_key()
    if api_key:
        print(f"Using cached API key: {api_key[:5]}...{api_key[-5:]}")
        config['api_key'] = api_key
    else:
        # Get API key
        api_key = input("Enter your Polygon.io API key: ").strip()
        config['api_key'] = api_key
        # Cache the API key
        cache_api_key(api_key)
    
    # Get ticker
    config['ticker'] = input("Enter the base ticker symbol (e.g., SPY): ").strip().upper()
    
    # Get expiry date
    while True:
        expiry = input("Enter option expiration date (YYYY-MM-DD) or press Enter for today: ").strip()
        if not expiry:
            # Use today's date if no input provided
            expiry = datetime.today().strftime('%Y-%m-%d')
            print(f"Using today's date: {expiry}")
        
        try:
            datetime.strptime(expiry, '%Y-%m-%d')
            config['expiry'] = expiry
            break
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2025-12-19)")
    
    # Get strike price
    while True:
        try:
            strike = float(input("Enter strike price: ").strip())
            config['strike'] = strike
            break
        except ValueError:
            print("❌ Invalid strike price. Please enter a number (e.g., 650.0)")
    
    # Get option type
    while True:
        option_type = input("Enter option type (C for Call, P for Put): ").strip().upper()
        if option_type in ['C', 'P']:
            config['type'] = option_type
            break
        print("❌ Invalid option type. Please enter 'C' for Call or 'P' for Put")
    
    # Get days back (optional)
    while True:
        days_back = input("Enter number of days to look back (default: 30): ").strip()
        if not days_back:
            config['days_back'] = 30
            break
        try:
            days_back = int(days_back)
            if days_back > 0:
                config['days_back'] = days_back
                break
            print("❌ Days back must be positive")
        except ValueError:
            print("❌ Invalid number. Please enter a positive integer")
    
    # Get risk-free rate (optional)
    while True:
        risk_free_rate = input("Enter risk-free rate in percentage (default: 4.34): ").strip()
        if not risk_free_rate:
            config['risk_free_rate'] = 0.0434  # 4.34%
            break
        try:
            risk_free_rate = float(risk_free_rate) / 100  # Convert percentage to decimal
            if risk_free_rate > 0:
                config['risk_free_rate'] = risk_free_rate
                break
            print("❌ Risk-free rate must be positive")
        except ValueError:
            print("❌ Invalid number. Please enter a positive number")
    
    # Get cache settings (optional)
    while True:
        cache_dir = input("Enter cache directory (default: cache): ").strip() or "cache"
        try:
            # Convert to Path object and resolve to absolute path
            cache_path = Path(cache_dir).resolve()
            
            # Check if path exists and is a directory
            if cache_path.exists() and not cache_path.is_dir():
                print("❌ The path exists but is not a directory")
                continue
                
            # Try to create directory if it doesn't exist
            if not cache_path.exists():
                cache_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created cache directory: {cache_path}")
            
            # Check if we have write permissions
            if not os.access(cache_path, os.W_OK):
                print("❌ No write permission for the specified directory")
                continue
                
            config['cache_dir'] = str(cache_path)
            print(f"✅ Using cache directory: {cache_path}")
            break
            
        except Exception as e:
            print(f"❌ Invalid directory path: {e}")
            print("Please enter a valid directory path")
    
    while True:
        cache_expiry = input("Enter cache expiry in hours (default: 24): ").strip()
        if not cache_expiry:
            config['cache_expiry'] = 24
            break
        try:
            cache_expiry = int(cache_expiry)
            if cache_expiry > 0:
                config['cache_expiry'] = cache_expiry
                break
            print("❌ Cache expiry must be positive")
        except ValueError:
            print("❌ Invalid number. Please enter a positive integer")
    
    print("\n✅ Configuration complete!")
    print("=" * 50)
    return config 