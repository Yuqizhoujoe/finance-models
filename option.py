import logging
from datetime import datetime, timedelta
import time
from pathlib import Path

from api_handlers.polygon_client import RateLimitedClient
from api_handlers.option import get_option_contract, analyze_stock_and_option
from data.cache import DataCache
from data.metrics import (
    calculate_metrics,
    interpret_sharpe_ratio,
    interpret_option_sharpe_ratio,
    print_section,
    format_percentage
)
from data.visualization import plot_price_history
from data.contexts import print_context
from utils.input_handler import get_user_input

# Setup logging for debug purposes only
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the option analysis.
    """
    print_section("🚀 Option Analysis Tool", "=")
    
    # Get user configuration
    config = get_user_input()
    
    # Initialize clients
    print("\n🔄 Initializing...")
    init_start = time.time()
    client = RateLimitedClient(config['api_key'])
    cache = DataCache(Path(config['cache_dir']), config['cache_expiry'])
    init_end = time.time()
    print(f"✅ Initialization completed in {init_end - init_start:.2f} seconds")
    
    # Get the option contract
    option_symbol = get_option_contract(
        client,
        config['ticker'], 
        config['expiry'], 
        config['strike'], 
        config['type']
    )
    
    if not option_symbol:
        print(f"\n❌ No valid option contract found for {config['ticker']} {config['strike']} {config['type']} expiring {config['expiry']}")
        print("💡 Try using a different strike price or expiration date")
        return
    
    print_section("📊 Analysis Details")
    print(f"Option Symbol: {option_symbol}")
    
    # Calculate date range
    end_date = datetime.today()
    start_date = end_date - timedelta(days=config['days_back'])
    from_date = start_date.strftime('%Y-%m-%d')
    to_date = end_date.strftime('%Y-%m-%d')
    print(f"Date Range: {from_date} to {to_date}")
    
    # Get historical data for both option and stock
    print("\n📈 Fetching and analyzing data...")
    option_df, stock_df, divergence, volatility_analysis, vix_analysis = analyze_stock_and_option(
        client, 
        option_symbol, 
        config['ticker'], 
        from_date, 
        to_date
    )
    
    if option_df is None or stock_df is None:
        print("\n❌ Failed to retrieve historical data")
        return
    
    # Calculate metrics for both option and stock
    option_metrics = calculate_metrics(option_df, config['risk_free_rate'])
    stock_metrics = calculate_metrics(stock_df, config['risk_free_rate'])
    
    if option_metrics and stock_metrics:
        # Option Analysis Section
        print_section("📊 Option Analysis")
        
        # Display and interpret Sharpe ratio with market context
        sharpe_rating, sharpe_explanation = interpret_option_sharpe_ratio(option_metrics['sharpe_ratio'])
        print(f"Sharpe Ratio: {option_metrics['sharpe_ratio']:.2f}")
        print(f"Rating: {sharpe_rating}")
        print(f"Interpretation: {sharpe_explanation}")
        
        # Print option performance context
        print_context('option_performance', emoji="📊")
        
        print(f"\nReturns Analysis:")
        print(f"Average Daily Return: {format_percentage(option_metrics['avg_return'])}")
        print(f"Daily Return Std Dev: {format_percentage(option_metrics['std_dev'])}")
        print(f"Total Return: {format_percentage(option_metrics['total_return'])}")
        
        if option_metrics['rsi'] is not None:
            print(f"\nTechnical Indicators:")
            print(f"Current RSI: {option_metrics['rsi']:.2f}")
            print(f"Signal: {option_metrics['signal']}")
        
        # Stock Analysis Section
        print_section("📈 Stock Analysis")
        
        # Display and interpret Sharpe ratio for stock
        stock_sharpe_rating, stock_sharpe_explanation = interpret_sharpe_ratio(stock_metrics['sharpe_ratio'])
        print(f"Sharpe Ratio: {stock_metrics['sharpe_ratio']:.2f}")
        print(f"Rating: {stock_sharpe_rating}")
        print(f"Interpretation: {stock_sharpe_explanation}")
        
        # Print stock performance context
        print_context('stock_performance', emoji="📈")
        
        print(f"\nReturns Analysis:")
        print(f"Average Daily Return: {format_percentage(stock_metrics['avg_return'])}")
        print(f"Daily Return Std Dev: {format_percentage(stock_metrics['std_dev'])}")
        print(f"Total Return: {format_percentage(stock_metrics['total_return'])}")
        
        if stock_metrics['rsi'] is not None:
            print(f"\nTechnical Indicators:")
            print(f"Current RSI: {stock_metrics['rsi']:.2f}")
            print(f"Signal: {stock_metrics['signal']}")
        
        # Divergence Analysis Section
        if divergence:
            print_section("🔄 Divergence Analysis")
            print(f"Option RSI: {divergence['option_rsi']:.2f}")
            print(f"Stock RSI: {divergence['stock_rsi']:.2f}")
            print(f"RSI Difference: {divergence['rsi_difference']:.2f}")
            print(f"Divergence Type: {divergence['divergence_type']}")
            print(f"\n📝 Interpretation:")
            print(f"{divergence['interpretation']}")
            
            if divergence['buying_strategies']:
                print("\n🛒 Buying Strategies:")
                for strategy in divergence['buying_strategies']:
                    print(f"  • {strategy}")
                    
            if divergence['selling_strategies']:
                print("\n💰 Selling Strategies:")
                for strategy in divergence['selling_strategies']:
                    print(f"  • {strategy}")
            
            # Print divergence context
            print_context('divergence', emoji="🔄")
        
        # Volatility Analysis Section
        if volatility_analysis:
            print_section("📊 Volatility Analysis")
            print(f"Option Implied Volatility: {volatility_analysis['implied_volatility']:.2%}")
            print(f"Option Realized Volatility: {volatility_analysis['realized_volatility']:.2%}")
            print(f"Volatility Skew: {volatility_analysis['skew']:.2%}")
            print(f"Skew Type: {volatility_analysis['skew_type']}")
            print(f"\n📝 Interpretation:")
            print(f"{volatility_analysis['interpretation']}")
            
            if volatility_analysis['buying_strategies']:
                print("\n🛒 Buying Strategies:")
                for strategy in volatility_analysis['buying_strategies']:
                    print(f"  • {strategy}")
                    
            if volatility_analysis['selling_strategies']:
                print("\n💰 Selling Strategies:")
                for strategy in volatility_analysis['selling_strategies']:
                    print(f"  • {strategy}")
        
        # VIX Analysis Section
        if vix_analysis:
            print_section("🌊 VIX Analysis")
            print(f"Current VIX: {vix_analysis['current_vix']:.2f}")
            print(f"VIX Level: {vix_analysis['vix_level'].capitalize()}")
            print(f"VIX Trend: {vix_analysis['vix_trend'].capitalize()}")
            print(f"\n📝 Interpretation:")
            print(f"{vix_analysis['interpretation']}")
            
            if vix_analysis['trading_implications']:
                print("\n💡 Trading Implications:")
                for implication in vix_analysis['trading_implications']:
                    print(f"  • {implication}")
            
            # Print VIX context
            print_context('vix', emoji="🌊")
        
        # Plot the data
        print("\n📊 Generating price history plot...")
        plot_price_history(option_df, option_symbol)
        print("✅ Plot generated successfully")
    else:
        print("\n❌ Failed to calculate metrics")
    
    print_section("✨ Analysis Complete")
    print(f"Total execution time: {time.time() - init_start:.2f} seconds")

if __name__ == "__main__":
    main()