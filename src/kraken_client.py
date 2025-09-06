import requests
import pandas as pd
from typing import Dict, List, Optional
import time

class KrakenClient:
    def __init__(self):
        self.base_url = "https://api.kraken.com/0/public"
        
    def get_ohlc_data(self, pair: str = "XBTUSD", interval: int = 60, count: int = 50) -> pd.DataFrame:
        """
        Fetch OHLC data from Kraken
        
        Args:
            pair: Trading pair (default: XBTUSD for BTC/USD)
            interval: Timeframe in minutes (1, 5, 15, 30, 60, 240, 1440, 10080, 21600)
            count: Number of data points to fetch
            
        Returns:
            DataFrame with OHLC data
        """
        try:
            url = f"{self.base_url}/OHLC"
            params = {
                'pair': pair,
                'interval': interval,
                'count': count
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['error']:
                raise Exception(f"Kraken API error: {data['error']}")
            
            # Extract OHLC data
            ohlc_data = data['result'][pair]
            df = pd.DataFrame(ohlc_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'trades'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'trades']
            df[numeric_columns] = df[numeric_columns].astype(float)
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching OHLC data: {e}")
            return pd.DataFrame()

    def format_ohlc_for_prompt(self, df: pd.DataFrame) -> str:
        """
        Format OHLC data for the AI prompt
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Formatted string with OHLC data
        """
        if df.empty:
            return "No data available"
        
        # Get the latest 10 data points for the prompt
        recent_data = df.tail(10)
        
        formatted_data = []
        for _, row in recent_data.iterrows():
            formatted_data.append(
                f"Time: {row['timestamp']}, "
                f"O: {row['open']:.2f}, "
                f"H: {row['high']:.2f}, "
                f"L: {row['low']:.2f}, "
                f"C: {row['close']:.2f}, "
                f"V: {row['volume']:.2f}"
            )
        
        # Add summary statistics
        summary = (
            f"\nSummary (last 50 periods):\n"
            f"Current Price: {df['close'].iloc[-1]:.2f}\n"
            f"24h High: {df['high'].max():.2f}\n"
            f"24h Low: {df['low'].min():.2f}\n"
            f"Volume (24h): {df['volume'].sum():.2f}\n"
            f"Price Change: {((df['close'].iloc[-1] - df['open'].iloc[0]) / df['open'].iloc[0] * 100):.2f}%"
        )
        
        return "\n".join(formatted_data) + summary
