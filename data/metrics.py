import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_metrics(df: pd.DataFrame, risk_free_rate: float = 0.0434) -> Optional[Dict]:
    """
    Calculate trading metrics from historical data.
    
    Args:
        df: DataFrame with historical price data
        risk_free_rate: Annual risk-free rate (default: 4.34%)
        
    Returns:
        Dictionary containing calculated metrics or None if calculation fails
    """
    if df is None or len(df) < 2:
        return None
        
    try:
        # Calculate daily returns
        df['daily_return'] = df['close'].pct_change()
        
        # Calculate metrics
        avg_return = df['daily_return'].mean() * 100  # Convert to percentage
        std_dev = df['daily_return'].std() * 100  # Convert to percentage
        total_return = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100  # Convert to percentage
        
        # Calculate Sharpe Ratio (using provided risk-free rate)
        daily_rf = (1 + risk_free_rate) ** (1/252) - 1  # Convert annual rate to daily
        excess_returns = df['daily_return'] - daily_rf
        sharpe_ratio = np.sqrt(252) * (excess_returns.mean() / excess_returns.std()) if excess_returns.std() != 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'avg_return': avg_return,
            'std_dev': std_dev,
            'total_return': total_return,
            'rsi': df['rsi'].iloc[-1] if 'rsi' in df.columns else None,
            'signal': df['signal'].iloc[-1] if 'signal' in df.columns else None
        }
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return None

def interpret_sharpe_ratio(sharpe_ratio: float) -> tuple[str, str]:
    """
    Interpret the Sharpe ratio value for stocks based on market benchmarks.
    
    Typical stock Sharpe ratio ranges:
    - S&P 500 historical average: ~0.4-0.5
    - Most individual stocks: 0.3-0.7
    - Top-performing stocks: 0.7-1.0
    - Exceptional performers: > 1.0
    
    Args:
        sharpe_ratio: The calculated Sharpe ratio
        
    Returns:
        Tuple of (rating, explanation)
    """
    if sharpe_ratio <= 0:
        return "Poor", "Stock returns are worse than risk-free rate, indicating poor risk management"
    elif sharpe_ratio < 0.3:
        return "Below Average", "Returns are below typical market performance, suggesting inefficient risk/return"
    elif sharpe_ratio < 0.5:
        return "Average", "Returns are in line with market indices like S&P 500 (0.4-0.5)"
    elif sharpe_ratio < 0.7:
        return "Good", "Above-market returns with reasonable risk management"
    elif sharpe_ratio < 1.0:
        return "Very Good", "Strong risk-adjusted returns, among top-performing stocks"
    else:
        return "Excellent", "Exceptional risk-adjusted performance, verify sustainability"

def interpret_option_sharpe_ratio(sharpe_ratio: float) -> tuple[str, str]:
    """
    Interpret the Sharpe ratio value specifically for options.
    
    Options have different Sharpe ratio characteristics:
    - More extreme values due to leverage
    - Negative ratios common from time decay
    - Higher volatility is normal
    - Short-term vs long-term options behave differently
    - LEAPS may have ratios closer to stocks
    
    Args:
        sharpe_ratio: The calculated Sharpe ratio
        
    Returns:
        Tuple of (rating, explanation)
    """
    if sharpe_ratio <= -2.0:
        return "Very Poor", "Severe losses, likely due to time decay and adverse price movement"
    elif sharpe_ratio <= -1.0:
        return "Poor", "Significant losses, common for out-of-money options nearing expiration"
    elif sharpe_ratio < 0:
        return "Below Average", "Negative returns, typical for options affected by time decay"
    elif sharpe_ratio < 1.0:
        return "Neutral", "Positive but volatile returns, common for options"
    elif sharpe_ratio < 2.0:
        return "Good", "Strong performance considering option's inherent volatility"
    elif sharpe_ratio < 3.0:
        return "Very Good", "Excellent risk-adjusted returns for an option"
    else:
        return "Outstanding", "Exceptional performance, verify if sustainable and not data anomaly"

def print_section(title: str, char: str = '=') -> None:
    """
    Print a section header with consistent formatting.
    
    Args:
        title: The section title to print
        char: The character to use for the separator line (default: '=')
    """
    print(f"\n{title}")
    print(char * 50)

def format_percentage(value: float | None) -> str:
    """
    Format percentage values consistently.
    
    Args:
        value: The percentage value to format
        
    Returns:
        Formatted string with 2 decimal places and % symbol, or 'N/A' if value is None
    """
    return f"{value:.2f}%" if value is not None else "N/A" 