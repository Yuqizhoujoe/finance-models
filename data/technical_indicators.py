import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)

def calculate_rsi(df: pd.DataFrame, period: int = 14, price_column: str = 'close') -> pd.DataFrame:
    """
    Calculate the Relative Strength Index (RSI) for a given price series.
    
    RSI Explanation:
    ----------------
    The Relative Strength Index (RSI) is a momentum oscillator that measures the speed and magnitude 
    of directional price movements. It compares the magnitude of recent gains to recent losses to 
    determine overbought or oversold conditions.
    
    Formula:
    1. Calculate price changes (delta) between consecutive periods
    2. Separate gains (positive changes) and losses (negative changes)
    3. Calculate average gains and losses over the specified period
    4. Calculate Relative Strength (RS) = Average Gain / Average Loss
    5. Calculate RSI = 100 - (100 / (1 + RS))
    
    Interpretation:
    - RSI > 70: Overbought condition (potential sell signal)
    - RSI < 30: Oversold condition (potential buy signal)
    - RSI between 30 and 70: Neutral zone
    
    Example:
    If a stock has been consistently rising, its RSI will be high (possibly above 70).
    If it has been consistently falling, its RSI will be low (possibly below 30).
    
    Args:
        df: DataFrame containing price data
        period: Number of periods for RSI calculation (default: 14)
        price_column: Column name containing price data (default: 'close')
    
    Returns:
        DataFrame with added RSI column
    """
    try:
        # Make a copy to avoid modifying the original dataframe
        df = df.copy()
        
        # Calculate price changes
        delta = df[price_column].diff()
        
        # Separate gains and losses
        gains = delta.copy()
        losses = delta.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Calculate Relative Strength (RS)
        rs = avg_gains / avg_losses
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        # Add RSI to dataframe
        df['rsi'] = rsi
        
        # Add overbought/oversold signals
        df['signal'] = 'neutral'
        df.loc[df['rsi'] > 70, 'signal'] = 'overbought'
        df.loc[df['rsi'] < 30, 'signal'] = 'oversold'
        
        return df
        
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        return df

def calculate_rsi_for_both(option_df: pd.DataFrame, stock_df: pd.DataFrame, 
                         period: int = 14) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate RSI for both option and underlying stock data.
    
    Option vs Stock RSI Explanation:
    ------------------------------
    Options and their underlying stocks often have different RSI patterns due to several factors:
    
    1. Leverage: Options are more sensitive to price changes in the underlying stock
       - A 1% move in the stock might cause a 5-10% move in the option
       - This leads to more extreme RSI values for options
    
    2. Time Decay: Options lose value as expiration approaches
       - This steady decline can create a downward bias in option RSI
       - Options nearing expiration might show lower RSI values than the stock
    
    3. Implied Volatility Changes: Options prices are affected by changes in implied volatility
       - Increasing IV can cause option prices to rise even if the stock is flat
       - Decreasing IV can cause option prices to fall even if the stock is rising
    
    Example:
    Consider AAPL stock with an RSI of 55 (neutral) and its call option with 30 days to expiration:
    - The option might have an RSI of 65 (showing more strength)
    - This could be due to increasing implied volatility or leverage effects
    - Or the option might have an RSI of 45 (showing more weakness)
    - This could be due to time decay or decreasing implied volatility
    
    Args:
        option_df: DataFrame containing option price data
        stock_df: DataFrame containing stock price data
        period: Number of periods for RSI calculation (default: 14)
    
    Returns:
        Tuple of (option DataFrame with RSI, stock DataFrame with RSI)
    """
    try:
        # Calculate RSI for option
        option_df = calculate_rsi(option_df, period=period)
        
        # Calculate RSI for stock
        stock_df = calculate_rsi(stock_df, period=period)
        
        return option_df, stock_df
        
    except Exception as e:
        logger.error(f"Error calculating RSI for both: {str(e)}")
        return option_df, stock_df

def analyze_rsi_divergence(option_df: pd.DataFrame, stock_df: pd.DataFrame) -> dict:
    """
    Analyze RSI divergence between option and stock.
    
    RSI Divergence Explanation:
    -------------------------
    RSI divergence between options and stocks can provide valuable insights into market sentiment
    and potential trading opportunities. There are two main types of divergence:
    
    1. Bullish Divergence (Option RSI < Stock RSI):
       - The option's RSI is lower than the stock's RSI
       - This suggests that options traders are more bearish than stock traders
       - This could indicate that options are undervalued relative to the stock's strength
       - Potential trading opportunities:
         * Buy calls if you believe the stock will continue to rise
         * Sell puts if you believe the stock will remain above the strike price
         * Write covered calls if you own the stock and want to generate income
    
    2. Bearish Divergence (Option RSI > Stock RSI):
       - The option's RSI is higher than the stock's RSI
       - This suggests that options traders are more bullish than stock traders
       - This could indicate overoptimism in the options market despite weakness in the underlying stock
       - Potential trading opportunities:
         * Buy puts if you believe the stock will continue to fall
         * Sell calls if you believe the stock will remain below the strike price
         * Write cash-secured puts if you want to potentially buy the stock at a lower price
    
    Factors Affecting Divergence:
    - Time Decay: Options nearing expiration tend to have lower RSI values
    - Leverage: Options show more extreme RSI values due to their leverage
    - Implied Volatility: Changes in IV can cause option RSI to diverge from stock RSI
    
    Example:
    Consider AAPL stock with an RSI of 60 and its call option with an RSI of 45:
    - This is a bullish divergence (option RSI < stock RSI)
    - It suggests the option might be undervalued relative to the stock's strength
    - If you believe AAPL will continue to rise, this might be a good time to buy calls
    - Alternatively, you could sell puts if you believe AAPL will remain above the strike price
    
    Another example: AAPL stock with an RSI of 40 and its call option with an RSI of 55:
    - This is a bearish divergence (option RSI > stock RSI)
    - It suggests the option might be overvalued relative to the stock's weakness
    - If you believe AAPL will continue to fall, this might be a good time to buy puts
    - Alternatively, you could sell calls if you believe AAPL will remain below the strike price
    
    Args:
        option_df: DataFrame containing option data with RSI
        stock_df: DataFrame containing stock data with RSI
    
    Returns:
        Dictionary containing divergence analysis
    """
    try:
        # Get the most recent RSI values
        option_rsi = option_df['rsi'].iloc[-1]
        stock_rsi = stock_df['rsi'].iloc[-1]
        
        # Calculate RSI difference
        rsi_diff = option_rsi - stock_rsi
        
        # Determine divergence type
        divergence = {
            'option_rsi': option_rsi,
            'stock_rsi': stock_rsi,
            'rsi_difference': rsi_diff,
            'divergence_type': 'none',
            'interpretation': 'No significant divergence detected',
            'buying_strategies': [],
            'selling_strategies': []
        }
        
        if abs(rsi_diff) > 10:  # Significant difference threshold
            if option_rsi > stock_rsi:
                # Option RSI is higher than stock RSI
                divergence['divergence_type'] = 'bearish'
                divergence['interpretation'] = 'Bearish divergence: Options traders are more bullish than stock traders, which may indicate overoptimism in options market despite stock weakness'
                divergence['buying_strategies'] = ['Buy puts if you believe the stock will continue to fall']
                divergence['selling_strategies'] = ['Sell calls if you believe the stock will remain below the strike price', 
                                                  'Write cash-secured puts if you want to potentially buy the stock at a lower price']
            else:
                # Option RSI is lower than stock RSI
                divergence['divergence_type'] = 'bullish'
                divergence['interpretation'] = 'Bullish divergence: Options traders are more bearish than stock traders, which may indicate undervaluation of options relative to stock strength'
                divergence['buying_strategies'] = ['Buy calls if you believe the stock will continue to rise']
                divergence['selling_strategies'] = ['Sell puts if you believe the stock will remain above the strike price',
                                                  'Write covered calls if you own the stock and want to generate income']
        
        return divergence
        
    except Exception as e:
        logger.error(f"Error analyzing RSI divergence: {str(e)}")
        return {
            'option_rsi': None,
            'stock_rsi': None,
            'rsi_difference': None,
            'divergence_type': 'error',
            'interpretation': 'Error analyzing divergence',
            'buying_strategies': [],
            'selling_strategies': []
        }

def calculate_realized_volatility(df: pd.DataFrame, window: int = 252, annualize: bool = True) -> float:
    """
    Calculate the realized volatility from historical price data.
    
    Realized Volatility Explanation:
    ------------------------------
    Realized volatility (also known as historical volatility) measures the actual price fluctuations
    of an asset over a specific period. It's calculated using the standard deviation of daily returns.
    
    Formula:
    1. Calculate daily returns: (Price_t / Price_t-1) - 1
    2. Calculate standard deviation of returns
    3. Annualize by multiplying by sqrt(trading days per year)
    
    Interpretation:
    - Higher realized volatility indicates more price fluctuation
    - Lower realized volatility indicates more stable price movement
    - Often compared to implied volatility to identify mispricings
    
    Args:
        df: DataFrame containing price data
        window: Number of days to use for calculation (default: 252 trading days)
        annualize: Whether to annualize the result (default: True)
        
    Returns:
        Realized volatility as a decimal (e.g., 0.25 for 25%)
    """
    try:
        # Make sure we have enough data
        if len(df) < window:
            logger.warning(f"Not enough data for realized volatility calculation. Using all available data ({len(df)} days)")
            window = len(df)
        
        # Calculate daily returns if not already present
        if 'daily_return' not in df.columns:
            df['daily_return'] = df['close'].pct_change()
        
        # Calculate standard deviation of returns
        std_dev = df['daily_return'].std()
        
        # Annualize if requested
        if annualize:
            # Assuming 252 trading days per year
            realized_vol = std_dev * np.sqrt(252)
        else:
            realized_vol = std_dev
        
        return realized_vol
        
    except Exception as e:
        logger.error(f"Error calculating realized volatility: {str(e)}")
        return 0.0

def analyze_volatility_skew(implied_vol: float, realized_vol: float) -> Dict:
    """
    Analyze the relationship between implied and realized volatility.
    
    Volatility Skew Explanation:
    --------------------------
    The relationship between implied volatility (IV) and realized volatility (RV) can provide
    insights into whether options are overpriced or underpriced:
    
    1. IV > RV (Positive Skew):
       - Option's implied volatility is higher than its actual historical volatility
       - This suggests the option may be overpriced
       - Common in high-fear environments or before earnings
       - Potential strategies: Sell premium (covered calls, cash-secured puts)
    
    2. IV < RV (Negative Skew):
       - Option's implied volatility is lower than its actual historical volatility
       - This suggests the option may be underpriced
       - Common after a period of low volatility followed by increased activity
       - Potential strategies: Buy options (calls or puts depending on direction)
    
    3. IV ≈ RV (Neutral):
       - Option is priced fairly relative to its actual price movements
       - No clear mispricing signal
       - Consider other factors for trading decisions
    
    Note: This analysis compares the option's implied volatility with its own realized volatility,
    not with the underlying stock's volatility. This provides a more direct comparison of whether
    the option itself is overpriced or underpriced.
    
    Args:
        implied_vol: Option's implied volatility as a decimal (e.g., 0.25 for 25%)
        realized_vol: Option's realized volatility as a decimal (e.g., 0.20 for 20%)
        
    Returns:
        Dictionary containing volatility analysis
    """
    try:
        # Calculate volatility skew (difference between IV and RV)
        skew = implied_vol - realized_vol
        
        # Determine skew type and interpretation
        analysis = {
            'implied_volatility': implied_vol,
            'realized_volatility': realized_vol,
            'skew': skew,
            'skew_type': 'neutral',
            'interpretation': 'No significant volatility skew detected',
            'buying_strategies': [],
            'selling_strategies': []
        }
        
        # Define significant skew threshold (5 percentage points)
        significant_skew = 0.05
        
        if abs(skew) > significant_skew:
            if skew > 0:
                # Positive skew: IV > RV
                analysis['skew_type'] = 'positive'
                analysis['interpretation'] = 'Positive volatility skew: Option is priced with higher volatility than its actual price movements, suggesting it may be overpriced'
                analysis['selling_strategies'] = [
                    'Sell covered calls if you own the stock',
                    'Write cash-secured puts if you want to potentially buy the stock at a lower price',
                    'Sell premium through credit spreads'
                ]
            else:
                # Negative skew: IV < RV
                analysis['skew_type'] = 'negative'
                analysis['interpretation'] = 'Negative volatility skew: Option is priced with lower volatility than its actual price movements, suggesting it may be underpriced'
                analysis['buying_strategies'] = [
                    'Buy calls if you expect the stock to rise',
                    'Buy puts if you expect the stock to fall',
                    'Consider debit spreads to reduce cost while maintaining directional exposure'
                ]
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing volatility skew: {str(e)}")
        return {
            'implied_volatility': implied_vol,
            'realized_volatility': realized_vol,
            'skew': 0.0,
            'skew_type': 'error',
            'interpretation': 'Error analyzing volatility skew',
            'buying_strategies': [],
            'selling_strategies': []
        } 