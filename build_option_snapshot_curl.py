def build_option_snapshot_curl(ticker: str, api_key: str, limit: int = 10, order: str = "asc", sort: str = "ticker") -> str:
    """
    Construct a curl command for Polygon's /v3/snapshot/options/{ticker} endpoint.
    """
    url = (
        f"https://api.polygon.io/v3/snapshot/options/{ticker.upper()}"
        f"?order={order}&limit={limit}&sort={sort}&apiKey={api_key}"
    )
    return f'curl -X GET "{url}"'

def get_user_input() -> dict:
    print("\n🔧 Polygon Option Snapshot CURL Generator")
    print("=========================================")

    # Validate ticker
    while True:
        ticker = input("Enter the stock ticker (e.g., AAPL): ").strip().upper()
        if ticker.isalpha():
            break
        print("❌ Invalid ticker. Please enter a valid stock symbol (letters only).")

    # Validate API key
    while True:
        api_key = input("Enter your Polygon.io API key: ").strip()
        if api_key:
            break
        print("❌ API key cannot be empty.")

    # Validate limit
    while True:
        limit_input = input("Enter result limit (default: 10): ").strip()
        if limit_input == "":
            limit = 10
            break
        if limit_input.isdigit() and int(limit_input) > 0:
            limit = int(limit_input)
            break
        print("❌ Limit must be a positive integer.")

    # Validate order
    while True:
        order_input = input("Sort order [asc/desc] (default: asc): ").strip().lower()
        if order_input in ["", "asc", "desc"]:
            order = order_input if order_input else "asc"
            break
        print("❌ Sort order must be 'asc' or 'desc'.")

    # Validate sort field
    while True:
        sort_input = input("Sort field (default: ticker): ").strip()
        if sort_input == "":
            sort = "ticker"
            break
        if sort_input.replace("_", "").isalnum():
            sort = sort_input
            break
        print("❌ Sort field must be alphanumeric (underscores allowed).")

    return {
        "ticker": ticker,
        "api_key": api_key,
        "limit": limit,
        "order": order,
        "sort": sort
    }

def main():
    config = get_user_input()

    curl_command = build_option_snapshot_curl(
        ticker=config['ticker'],
        api_key=config['api_key'],
        limit=config['limit'],
        order=config['order'],
        sort=config['sort']
    )

    print("\n✅ Generated CURL command:")
    print(curl_command)

if __name__ == "__main__":
    main()
