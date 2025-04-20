import logging
from datetime import datetime
import pandas as pd
import yfinance as yf
from typing import Optional, Tuple

from api_handlers.polygon_client import RateLimitedClient
from data.technical_indicators import calculate_rsi, calculate_rsi_for_both, analyze_rsi_divergence

logger = logging.getLogger(__name__)

def get_option_contract(client: RateLimitedClient, ticker: str, expiry: str, strike: float, option_type: str) -> Optional[str]:
    """
    Get the option contract information using Polygon's SDK.
    
    Args:
        client: Polygon API client
        ticker: Base ticker symbol (e.g., 'AAPL')
        expiry: Expiration date in YYYY-MM-DD format
        strike: Strike price
        option_type: 'C' for Call or 'P' for Put
    
    Returns:
        Option ticker symbol if found, None otherwise
    """
    try:
        logger.info(f"Starting get_option_contract for {ticker} {strike} {option_type} {expiry}")
        
        # Convert expiry date to format needed for option symbol (YYMMDD)
        expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
        expiry_formatted = expiry_date.strftime('%y%m%d')
        
        # Format strike price to 8 digits with leading zeros
        strike_formatted = f"{int(strike * 1000):08d}"
        
        # Construct option symbol
        # Format: O:AAPL250425C00200000
        option_symbol = f"O:{ticker}{expiry_formatted}{option_type}{strike_formatted}"
        logger.info(f"Constructed option symbol: {option_symbol}")
        
        # Verify the option exists
        logger.info("Verifying option contract exists...")
        try:
            # Try to get a snapshot of the option to verify it exists
            snapshot = client.get_snapshot_option(
                underlying_asset=ticker,
                option_contract=option_symbol
            )
            if snapshot:
                logger.info(f"Verified option contract exists: {option_symbol}")
                return option_symbol
            else:
                logger.warning(f"Option contract not found: {option_symbol}")
                return None
        except Exception as e:
            logger.warning(f"Option contract verification failed: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting option contract: {str(e)}")
        return None

def get_option_historical_data(client: RateLimitedClient, ticker: str, from_date: str, to_date: str) -> Optional[pd.DataFrame]:
    """
    Get historical data for a ticker using Polygon API.
    
    Args:
        client: Polygon API client
        ticker: Option ticker symbol
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        
    Returns:
        DataFrame with historical data or None if retrieval fails
    """
    try:
        logger.info(f"Starting get_historical_data for {ticker} from {from_date} to {to_date}")
        
        # Get daily aggregates
        logger.info("Fetching daily aggregates...")
        aggs = client.get_aggs(
            ticker,
            multiplier=1,
            timespan="day",
            from_=from_date,
            to=to_date
        )
        
        if not aggs:
            logger.warning(f"No historical data found for {ticker}")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': pd.Timestamp(agg.timestamp),
            'open': agg.open,
            'high': agg.high,
            'low': agg.low,
            'close': agg.close,
            'volume': agg.volume
        } for agg in aggs])
        
        # Set date as index
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        return df
        
    except Exception as e:
        logger.error(f"Error getting historical data: {str(e)}")
        return None
    
    
def get_stock_historical_data(ticker: str, from_date: str, to_date: str) -> Optional[pd.DataFrame]:
    logger.info(f"Fetching stock data from Yahoo Finance for {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        stock_df = stock.history(start=from_date, end=to_date, interval="1d")
        logger.info(f"Stock historical data retrieved for {ticker}")
        return stock_df
    except Exception as e:
        logger.error(f"Error getting stock historical data: {str(e)}")
        return None

def analyze_stock_and_option(client: RateLimitedClient, option_ticker: str, stock_ticker: str, 
                            from_date: str, to_date: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[dict]]:
    """
    Analyze both the option and its underlying stock, including RSI calculation and divergence analysis.
    
    Args:
        client: Polygon API client
        option_ticker: Option ticker symbol
        stock_ticker: Stock ticker symbol
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        
    Returns:
        Tuple of (option DataFrame, stock DataFrame, divergence analysis) or (None, None, None) if retrieval fails
    """
    try:
        logger.info(f"Starting analysis of option {option_ticker} and stock {stock_ticker}")
        
        # Get option data
        option_df = get_option_historical_data(client, option_ticker, from_date, to_date)
        
        # Get stock data from Yahoo Finance
        stock_df = get_stock_historical_data(stock_ticker, from_date, to_date)
        
        if option_df is None or stock_df.empty:
            logger.error("Failed to retrieve data for option or stock")
            return None, None, None
        
        # Rename columns to match our standard format
        stock_df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        # Calculate RSI for both using our custom function
        logger.info("Calculating RSI for both option and stock...")
        option_df, stock_df = calculate_rsi_for_both(option_df, stock_df, period=14)
        
        # Process historical data for both DataFrames
        logger.info("Processing historical data...")
        
        # Process option data
        if option_df is not None and len(option_df) >= 2:
            # Add RSI-based signals
            option_df['signal'] = 'neutral'
            option_df.loc[option_df['rsi'] > 70, 'signal'] = 'overbought'
            option_df.loc[option_df['rsi'] < 30, 'signal'] = 'oversold'
            
            # Add price delta (change from first price)
            option_df['price_delta'] = option_df['close'] - option_df['close'].iloc[0]
            
            # Add daily returns
            option_df['daily_return'] = option_df['close'].pct_change()
        
        # Process stock data
        if stock_df is not None and len(stock_df) >= 2:
            # Add RSI-based signals
            stock_df['signal'] = 'neutral'
            stock_df.loc[stock_df['rsi'] > 70, 'signal'] = 'overbought'
            stock_df.loc[stock_df['rsi'] < 30, 'signal'] = 'oversold'
            
            # Add price delta (change from first price)
            stock_df['price_delta'] = stock_df['close'] - stock_df['close'].iloc[0]
            
            # Add daily returns
            stock_df['daily_return'] = stock_df['close'].pct_change()
        
        # Analyze RSI divergence
        logger.info("Analyzing RSI divergence between option and stock...")
        divergence = analyze_rsi_divergence(option_df, stock_df)
        
        # Log divergence analysis
        logger.info(f"RSI Divergence Analysis:")
        logger.info(f"Option RSI: {divergence['option_rsi']:.2f}")
        logger.info(f"Stock RSI: {divergence['stock_rsi']:.2f}")
        logger.info(f"RSI Difference: {divergence['rsi_difference']:.2f}")
        logger.info(f"Divergence Type: {divergence['divergence_type']}")
        logger.info(f"Interpretation: {divergence['interpretation']}")
        
        if divergence['buying_strategies']:
            logger.info("Buying Strategies:")
            for strategy in divergence['buying_strategies']:
                logger.info(f"  - {strategy}")
                
        if divergence['selling_strategies']:
            logger.info("Selling Strategies:")
            for strategy in divergence['selling_strategies']:
                logger.info(f"  - {strategy}")
        
        return option_df, stock_df, divergence
        
    except Exception as e:
        logger.error(f"Error analyzing option and stock: {str(e)}")
        return None, None, None