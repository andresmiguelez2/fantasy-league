import os
import psycopg2
from market import Market


def load_market():
    try:
        # Connect to PostgreSQL database using environment variables
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres_db"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"), 
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432")
        )
        
        cursor = conn.cursor()
        
        # Example query to load market data
        cursor.execute("""
            SELECT id, closing_timestamp
            FROM markets
            WHERE closing_timestamp > now()
        """)
        market_data = cursor.fetchall()
        
        markets = []
        for row in market_data:
            market = Market()
            market._id = row[0]
            market._closing_ts = row[1]
            markets.append(market)
        
        cursor.close()
        conn.close()
        
        return markets
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return []


if __name__ == '__main__':
    print("backend app is running...")
    markets = load_market()
    print(f"Loaded {len(markets)} markets from database")