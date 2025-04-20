import matplotlib.pyplot as plt
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def plot_price_history(df: pd.DataFrame, ticker: str):
    """
    Plot the price history and RSI.
    
    Args:
        df: DataFrame with historical price data
        ticker: Option ticker symbol
    """
    if df is None or len(df) < 2:
        return
        
    try:
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
        
        # Plot price delta history
        ax1.plot(df.index, df['price_delta'], label='Price Change', color='blue')
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        ax1.set_title(f'{ticker} Price Change History')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Price Change ($)')
        ax1.grid(True)
        ax1.legend()
        
        # Plot RSI
        if 'rsi' in df.columns:
            ax2.plot(df.index, df['rsi'], label='RSI', color='purple')
            ax2.axhline(y=70, color='r', linestyle='--', label='Overbought (70)')
            ax2.axhline(y=30, color='g', linestyle='--', label='Oversold (30)')
            ax2.set_title('Relative Strength Index (RSI)')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('RSI')
            ax2.grid(True)
            ax2.legend()
        
        plt.tight_layout()
        plt.show()
    except Exception as e:
        logger.error(f"Error plotting price history: {e}") 