import os
import requests
import json
from typing import Dict, Any
from dotenv import load_dotenv
from kraken_client import KrakenClient

load_dotenv()

class TradingSignalGenerator:
    def __init__(self):
        self.kraken_client = KrakenClient()
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    def generate_signal_prompt(self, ohlc_data: str) -> str:
        """
        Create prompt for DeepSeek to generate trading signals
        """
        prompt = f"""
        You are an expert cryptocurrency trading analyst. Analyze the following OHLC data from Kraken exchange and provide a trading signal.

        OHLC DATA:
        {ohlc_data}

        Please provide your analysis in the following JSON format:
        {{
            "signal": "BUY|SELL|HOLD",
            "stop_price": number,
            "target_price": number,
            "confidence": number (0-100),
            "timeframe": "string (e.g., 1-4 hours)",
            "reasoning": "detailed technical analysis reasoning"
        }}

        Considerations:
        1. Analyze price action, support/resistance levels
        2. Consider volume trends
        3. Identify potential entry/exit points
        4. Assess risk/reward ratio
        5. Current market conditions

        Provide only valid JSON output, no additional text.
        """
        
        return prompt
    
    def get_deepseek_response(self, prompt: str) -> Dict[str, Any]:
        """
        Send prompt to DeepSeek API and get response
        """
        if not self.deepseek_api_key:
            raise ValueError("DeepSeek API key not found in environment variables")
        
        headers = {
            "Authorization": f"Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert cryptocurrency trading analyst. Provide trading signals in exact JSON format as requested."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return json.loads(result['choices'][0]['message']['content'])
            
        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API request error: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {}
        except Exception as e:
            print(f"Error getting DeepSeek response: {e}")
            return {}
    
    def generate_signal(self):
        """
        Main function to generate trading signal
        """
        print("Fetching OHLC data from Kraken...")
        ohlc_df = self.kraken_client.get_ohlc_data()
        
        if ohlc_df.empty:
            print("Failed to fetch OHLC data")
            return
        
        print(f"Fetched {len(ohlc_df)} OHLC data points")
        print(f"Latest price: {ohlc_df['close'].iloc[-1]:.2f}")
        
        formatted_data = self.kraken_client.format_ohlc_for_prompt(ohlc_df)
        prompt = self.generate_signal_prompt(formatted_data)
        
        print("\nSending data to DeepSeek for analysis...")
        signal = self.get_deepseek_response(prompt)
        
        if signal:
            print("\n" + "="*50)
            print("TRADING SIGNAL GENERATED")
            print("="*50)
            print(f"Signal: {signal.get('signal', 'N/A')}")
            print(f"Current Price: {ohlc_df['close'].iloc[-1]:.2f}")
            print(f"Stop Price: {signal.get('stop_price', 'N/A')}")
            print(f"Target Price: {signal.get('target_price', 'N/A')}")
            print(f"Confidence: {signal.get('confidence', 'N/A')}%")
            print(f"Timeframe: {signal.get('timeframe', 'N/A')}")
            print(f"\nReasoning: {signal.get('reasoning', 'N/A')}")
        else:
            print("Failed to generate trading signal")

if __name__ == "__main__":
    generator = TradingSignalGenerator()
    generator.generate_signal()
