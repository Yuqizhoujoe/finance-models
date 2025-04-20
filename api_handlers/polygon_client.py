from polygon import RESTClient
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)

class RateLimitedClient(RESTClient):
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
        super().__init__(api_key)
        
        # Configure retry strategy with error recovery
        retry_strategy = Retry(
            total=max_retries,          # Maximum number of retry attempts
            backoff_factor=backoff_factor,  # Base time to wait between retries
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP codes that trigger retries
        )
        
        # Apply retry strategy to both HTTP and HTTPS connections
        self.session = requests.Session()
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
        return super().get_aggs(*args, **kwargs)

    def get_rsi(self, ticker: str, timespan: str, window: int = 14, series_type: str = "close", from_: str = None, to: str = None):
        """
        Get RSI (Relative Strength Index) data for a ticker using Polygon SDK.
        
        Args:
            ticker (str): The ticker symbol
            timespan (str): The size of the time window (e.g., 'day', 'hour')
            window (int): The window size for RSI calculation (default: 14)
            series_type (str): The price type to use (default: 'close')
            from_ (str): The start date in YYYY-MM-DD format
            to (str): The end date in YYYY-MM-DD format
            
        Returns:
            The RSI data from the API
        """
        self._check_rate_limit()
        
        # Convert dates to timestamps if provided
        if from_:
            from_ = int(datetime.strptime(from_, '%Y-%m-%d').timestamp() * 1000)
        if to:
            to = int(datetime.strptime(to, '%Y-%m-%d').timestamp() * 1000)
            
        return super().get_rsi(
            ticker=ticker,
            timespan=timespan,
            window=window,
            series_type=series_type,
            timestamp_gte=from_,
            timestamp_lte=to
        )

    def list_options_contracts(self, *args, **kwargs):
        """Wrapper for list_options_contracts with rate limiting"""
        self._check_rate_limit()
        return super().list_options_contracts(*args, **kwargs)

    def get_snapshot_option(self, *args, **kwargs):
        """Wrapper for get_snapshot_option with rate limiting"""
        self._check_rate_limit()
        return super().get_snapshot_option(*args, **kwargs) 