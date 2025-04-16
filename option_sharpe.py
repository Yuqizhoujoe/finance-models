from polygon import RESTClient
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize global variables
client = None
cache = None

def get_user_input():
    """
    Get configuration from user through interactive prompts.
    Returns a dictionary containing all the configuration values.
    """
    print("\n🔧 Configuration")
    print("=" * 50)
    
    config = {}
    
    # Get API key
    config['api_key'] = input("Enter your Polygon.io API key: ").strip()
    
    # Get ticker
    config['ticker'] = input("Enter the base ticker symbol (e.g., SPY): ").strip().upper()
    
    # Get expiry date
    while True:
        expiry = input("Enter option expiration date (YYYY-MM-DD): ").strip()
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

def initialize_clients(config: Dict):
    """
    Initialize the API client and cache with the given configuration.
    """
    global client, cache
    client = RateLimitedClient(config['api_key'])
    cache = DataCache(Path(config['cache_dir']), config['cache_expiry'])

def construct_option_ticker(ticker: str, expiry: str, strike: float, option_type: str) -> str:
    """
    Construct the option ticker symbol in the format: O:SPY251219C00650000
    
    Args:
        ticker (str): Base ticker symbol (e.g., 'SPY')
        expiry (str): Expiration date in YYYY-MM-DD format
        strike (float): Strike price
        option_type (str): 'C' for Call or 'P' for Put
    
    Returns:
        str: Formatted option ticker symbol
    """
    # Convert expiry date to required format (YYMMDD)
    expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
    expiry_str = expiry_date.strftime('%y%m%d')
    
    # Convert strike to integer (x1000), then zero-pad to 8 digits
    strike_int = int(round(strike * 1000))  # ensure rounding before int
    strike_str = f"{strike_int:08d}"
    
    # Construct the option ticker
    option_ticker = f"O:{ticker}{expiry_str}{option_type}{strike_str}"
    return option_ticker

class RateLimitedClient:
    def __init__(self, api_key: str, max_retries: int = 3, backoff_factor: float = 0.5):
        """
        Initialize the rate-limited client with error handling and retry logic.
        
        Error Handling Strategy:
        1. Retries: Will attempt the request up to max_retries times (default: 3)
        2. Backoff: Uses exponential backoff timing between retries
           - 1st retry: 0.5s wait
           - 2nd retry: 1.0s wait (0.5 * 2)
           - 3rd retry: 2.0s wait (0.5 * 4)
        3. Error Recovery: Automatically retries on specific HTTP status codes:
           - 429: Too Many Requests (rate limit)
           - 500: Internal Server Error
           - 502: Bad Gateway
           - 503: Service Unavailable
           - 504: Gateway Timeout
        """
        self.client = RESTClient(api_key)
        self.session = requests.Session()
        
        # Configure retry strategy with error recovery
        retry_strategy = Retry(
            total=max_retries,          # Maximum number of retry attempts
            backoff_factor=backoff_factor,  # Base time to wait between retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP codes that trigger retries
        )
        
        # Apply retry strategy to both HTTP and HTTPS connections
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Rate limiting counters
        self._request_count = 0         # Track number of requests made today
        self._last_request_time = None  # Track when the last request was made
        self._daily_limit = 5           # Maximum requests per day (free plan)
        self._reset_time = None         # When the daily counter resets

    def _check_rate_limit(self):
        """
        Rate limiting logic:
        1. Daily Limit: Maximum 5 requests per day (free plan)
        2. Request Spacing: Minimum 1 second between requests
        3. Reset Time: Counter resets at midnight
        
        Example of rate limit handling:
        - If 5 requests made today: Must wait until tomorrow
        - If requests too close: Waits to maintain 1s spacing
        """
        current_time = datetime.now()
        
        # Reset counter at midnight
        if self._reset_time and current_time.date() > self._reset_time.date():
            self._request_count = 0
            self._reset_time = None

        # Set initial reset time if not set
        if not self._reset_time:
            self._reset_time = current_time

        # Check if we've hit the daily limit
        if self._request_count >= self._daily_limit:
            time_until_reset = (self._reset_time + timedelta(days=1) - current_time).total_seconds()
            raise Exception(f"Daily API limit reached. Resets in {time_until_reset/3600:.1f} hours")

        # Ensure minimum 1 second between requests
        if self._last_request_time:
            time_since_last = (current_time - self._last_request_time).total_seconds()
            if time_since_last < 1:
                time.sleep(1 - time_since_last)

        # Update counters
        self._request_count += 1
        self._last_request_time = current_time

    def get_aggs(self, *args, **kwargs):
        """
        Make an API request with built-in error handling:
        1. Checks rate limits before making request
        2. If request fails:
           - Retries up to 3 times
           - Uses exponential backoff (0.5s, 1s, 2s)
           - Only retries on specific error codes
        3. If all retries fail:
           - Raises exception with error details
        """
        self._check_rate_limit()
        return self.client.get_aggs(*args, **kwargs)

class DataCache:
    def __init__(self, cache_dir: Path, expiry_hours: int):
        self.cache_dir = cache_dir
        self.expiry_hours = expiry_hours

    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        # Check if cache is expired
        if (datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)).total_seconds() > self.expiry_hours * 3600:
            cache_path.unlink()
            return None

        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None

    def set(self, key: str, value: Any):
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'w') as f:
                json.dump(value, f)
        except Exception as e:
            logger.error(f"Error writing cache: {e}")

def get_option_historical_data(ticker: str, from_date: str, to_date: str) -> List[Dict]:
    cache_key = f"historical_{ticker}_{from_date}_{to_date}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("Using cached historical data")
        return cached_data

    try:
        aggs = []
        iterator = client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=from_date,
            to=to_date,
            adjusted=True,
            sort="asc",
            limit=120
        )
        
        for agg in iterator:
            aggs.append({
                'timestamp': agg.timestamp,
                'close': agg.close,
                'volume': agg.volume
            })
            
        if aggs:
            cache.set(cache_key, aggs)
            return aggs
        
        logger.warning("⚠️ No results returned — data might not exist or was never traded.")
        return []
    
    except requests.exceptions.HTTPError as http_err:
        response = http_err.response
        if response is not None:
            if response.status_code == 429:
                logger.error("❌ Rate limit exceeded. You've hit the maximum requests allowed by your plan.")
            elif response.status_code in [401, 403]:
                logger.error("❌ Unauthorized. Please check your API key and plan access.")
            else:
                logger.error(f"❌ HTTP Error {response.status_code}: {response.text}")
        else:
            logger.error("❌ HTTP error with no response body.")
        return []
            
    
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        return []

def main():
    try:
        # Get configuration from user
        config = get_user_input()
        
        # Initialize clients with user configuration
        initialize_clients(config)
        
        # Construct the option ticker symbol
        option_symbol = construct_option_ticker(
            config['ticker'], 
            config['expiry'], 
            config['strike'], 
            config['type']
        )
        logger.info(f"Option symbol: {option_symbol}")

        # Fetch historical data
        to_date = datetime.today().strftime('%Y-%m-%d')
        from_date = (datetime.today() - timedelta(days=config['days_back'])).strftime('%Y-%m-%d')

        logger.info(f"Fetching historical data from {from_date} to {to_date}")
        historical_data = get_option_historical_data(option_symbol, from_date, to_date)

        if not historical_data:
            logger.error("No historical data available for the specified period.")
            return

        # Parse Data
        df = pd.DataFrame(historical_data)
        df['Date'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d')
        df['Return'] = df['close'].pct_change()

        # Calculate Sharpe Ratio
        rf_daily = 0.045 / 252
        mean_return = df['Return'].mean()
        volatility = df['Return'].std()
        sharpe_daily = (mean_return - rf_daily) / volatility
        sharpe_annual = sharpe_daily * np.sqrt(252)

        # Print Results
        print("\n📊 Analysis Results")
        print(f"Option: {option_symbol}")
        print(f"Period: {from_date} → {to_date}")
        print("-" * 60)
        print(f"Average Daily Return: {mean_return * 100:.2f}%")
        print(f"Daily Volatility: {volatility * 100:.2f}%")
        print(f"Sharpe Ratio (Daily): {sharpe_daily:.4f}")
        print(f"Sharpe Ratio (Annual): {sharpe_annual:.4f}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()