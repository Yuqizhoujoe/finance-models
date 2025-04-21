"""
Centralized storage for all context information used in the option analysis tool.
"""

CONTEXTS = {
    'option_performance': {
        'title': 'Option Performance Context',
        'points': [
            'Negative ratios common due to time decay',
            'Higher volatility than stocks expected',
            'Short-term options: more extreme ratios',
            'LEAPS: ratios closer to stock levels'
        ]
    },
    'stock_performance': {
        'title': 'Stock Performance Context',
        'points': [
            'S&P 500 typical: 0.4-0.5',
            'Average stock: 0.3-0.4',
            'Top performers: 0.7-1.0'
        ]
    },
    'divergence': {
        'title': 'Divergence Context',
        'points': [
            'RSI divergence compares the RSI values between the option and its underlying stock',
            'Bullish divergence: Option RSI < Stock RSI (options traders more bearish than stock traders)',
            'Bearish divergence: Option RSI > Stock RSI (options traders more bullish than stock traders)',
            'Divergence can signal potential mispricing between option and stock',
            'Stronger signals when RSI difference is significant (>10 points)'
        ]
    },
    'vix': {
        'title': 'VIX Context',
        'points': [
            'VIX (CBOE Volatility Index) measures market\'s expectation of 30-day volatility',
            'Often called the \'fear gauge\' of the market',
            'VIX < 15: Market is calm, low fear, good for premium selling strategies',
            'VIX 15-25: Normal to slightly elevated volatility, balanced market',
            'VIX 25-30: Elevated fear, possible market correction ahead',
            'VIX > 30: High fear, often during market panics or corrections',
            'VIX > 40: Extreme fear, often during market crashes or crises',
            'Rising VIX: Increasing market uncertainty, consider defensive strategies',
            'Falling VIX: Decreasing market uncertainty, consider aggressive strategies'
        ]
    }
}

def get_context(context_type: str) -> dict:
    """
    Get context information for a specific type.
    
    Args:
        context_type: Type of context to retrieve ('option_performance', 'stock_performance', 'divergence', 'vix')
        
    Returns:
        Dictionary containing the context information or empty dict if not found
    """
    return CONTEXTS.get(context_type, {})

def print_context(context_type: str, emoji: str = "📚") -> None:
    """
    Print context information for a specific type in a consistent format.
    
    Args:
        context_type: Type of context to print ('option_performance', 'stock_performance', 'divergence', 'vix')
        emoji: Optional emoji to use before the title (default: "📚")
    """
    context = get_context(context_type)
    if not context:
        return
        
    print(f"\n{emoji} {context['title']}:")
    for point in context['points']:
        print(f"• {point}") 