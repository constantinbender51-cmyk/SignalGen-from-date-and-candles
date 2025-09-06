from flask import Flask, request, jsonify
import requests
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional

app = Flask(__name__)

# Configuration
KRAKEN_API_URL = "https://api.kraken.com/0/public/OHLC"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_SYMBOL = "XBTUSD"
DEFAULT_INTERVAL = 60  # 1 hour candles

class KrakenDeepSeekAnalyzer:
    def __init__(self):
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.kraken_api_key = os.getenv('KRAKEN_API_KEY', '')  # Optional for public endpoints
        
    def fetch_kraken_candles(self, symbol: str, interval: int, since: Optional[int] = None) -> List[Dict]:
        """Fetch candles from Kraken API"""
        params = {
            'pair': symbol,
            'interval': interval
        }
        
        if since:
            params['since'] = since
            
        try:
            response = requests.get(KRAKEN_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('error'):
                raise Exception(f"Kraken API error: {data['error']}")
                
            # Extract OHLC data
            ohlc_data = data['result'][list(data['result'].keys())[1]]
            candles = []
            
            for candle in ohlc_data:
                candles.append({
                    'timestamp': int(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[6])
                })
                
            return candles
            
        except Exception as e:
            raise Exception(f"Failed to fetch Kraken data: {str(e)}")
    
    def generate_analysis_prompt(self, candles: List[Dict]) -> str:
        """Generate prompt for DeepSeek analysis"""
        # Convert to DataFrame for technical analysis
        df = pd.DataFrame(candles)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Calculate technical indicators
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['rsi'] = self.calculate_rsi(df['close'])
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        # Get latest values
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        
        prompt = f"""
        Analyze the following cryptocurrency market data and provide trading signals:

        LATEST CANDLE DATA:
        - Timestamp: {latest['timestamp']}
        - Open: ${latest['open']:,.2f}
        - High: ${latest['high']:,.2f}
        - Low: ${latest['low']:,.2f}
        - Close: ${latest['close']:,.2f}
        - Volume: {latest['volume']:,.2f}
        
        TECHNICAL INDICATORS:
        - SMA 20: ${latest['sma_20']:,.2f}
        - SMA 50: ${latest['sma_50']:,.2f}
        - RSI: {latest['rsi']:.2f}
        - Volume MA: {latest['volume_ma']:,.2f}
        
        PRICE ACTION:
        - Price change: {((latest['close'] - previous['close']) / previous['close'] * 100):.2f}%
        - Relative to SMA 20: {((latest['close'] - latest['sma_20']) / latest['sma_20'] * 100):.2f}%
        - Relative to SMA 50: {((latest['close'] - latest['sma_50']) / latest['sma_50'] * 100):.2f}%

        PREVIOUS 5 CANDLES:
        {df.tail(6).head(5).to_string()}

        Provide a JSON response with:
        1. signal: "BUY", "SELL", or "HOLD"
        2. stop_price: appropriate stop loss price
        3. target: price target
        4. percentOfCapital: percentage of capital to allocate (0-100)
        5. reason: detailed reasoning for the signal

        Consider:
        - Trend direction and strength
        - Support/resistance levels
        - Volume analysis
        - RSI overbought/oversold conditions
        - Risk management principles
        """
        
        return prompt
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def get_deepseek_analysis(self, prompt: str) -> Dict:
        """Get analysis from DeepSeek API"""
        if not self.deepseek_api_key:
            raise Exception("DeepSeek API key not configured")
            
        headers = {
            'Authorization': f'Bearer {self.deepseek_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an expert cryptocurrency trading analyst. Provide clear, concise trading signals with proper risk management. Always respond with valid JSON.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }
        
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract JSON from response
            content = result['choices'][0]['message']['content']
            
            # Try to parse JSON from the response
            try:
                # Extract JSON string if wrapped in code blocks
                if '```json' in content:
                    json_str = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    json_str = content.split('```')[1].split('```')[0].strip()
                else:
                    json_str = content
                    
                return json.loads(json_str)
                
            except json.JSONDecodeError:
                # Fallback: try to find JSON object in the text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise Exception("Could not parse JSON from DeepSeek response")
                    
        except Exception as e:
            raise Exception(f"DeepSeek API error: {str(e)}")

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Main endpoint to get trading signals"""
    try:
        symbol = request.args.get('symbol', DEFAULT_SYMBOL)
        interval = int(request.args.get('interval', DEFAULT_INTERVAL))
        date_param = request.args.get('date')
        
        analyzer = KrakenDeepSeekAnalyzer()
        
        # Calculate timestamps
        current_time = int(time.time())
        fifty_hours_ago = current_time - (50 * 3600)
        
        if date_param:
            # Parse provided date
            try:
                target_date = datetime.fromisoformat(date_param.replace('Z', '+00:00'))
                target_timestamp = int(target_date.timestamp())
                
                if target_timestamp > fifty_hours_ago:
                    # Date is within last 50 hours, get remaining candles
                    hours_remaining = (target_timestamp - fifty_hours_ago) // 3600
                    candles_to_fetch = min(50, max(1, hours_remaining))
                else:
                    candles_to_fetch = 50
                    
                since = target_timestamp - (candles_to_fetch * interval * 60)
                
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use ISO format (e.g., 2024-01-15T12:00:00Z)'}), 400
        else:
            # No date provided, get current signal
            candles_to_fetch = 50
            since = current_time - (candles_to_fetch * interval * 60)
        
        # Fetch candles from Kraken
        candles = analyzer.fetch_kraken_candles(symbol, interval, since)
        
        if not candles:
            return jsonify({'error': 'No candle data found'}), 404
        
        # Generate signals
        signals = []
        
        if date_param and len(candles) > 1:
            # Generate signal for each candle (for historical analysis)
            for i in range(len(candles)):
                if i >= 49:  # Ensure we have enough data for indicators
                    current_candles = candles[:i+1]
                    prompt = analyzer.generate_analysis_prompt(current_candles)
                    analysis = analyzer.get_deepseek_analysis(prompt)
                    
                    signals.append({
                        'timestamp': candles[i]['timestamp'],
                        'datetime': datetime.fromtimestamp(candles[i]['timestamp']).isoformat(),
                        'price': candles[i]['close'],
                        'analysis': analysis
                    })
        else:
            # Generate single signal for latest candle
            prompt = analyzer.generate_analysis_prompt(candles)
            analysis = analyzer.get_deepseek_analysis(prompt)
            
            signals.append({
                'timestamp': candles[-1]['timestamp'],
                'datetime': datetime.fromtimestamp(candles[-1]['timestamp']).isoformat(),
                'price': candles[-1]['close'],
                'analysis': analysis
            })
        
        return jsonify({
            'symbol': symbol,
            'interval': interval,
            'total_candles': len(candles),
            'signals': signals
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
