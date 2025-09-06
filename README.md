# Kraken DeepSeek Trading Signals

A Flask application that fetches cryptocurrency candle data from Kraken and uses DeepSeek AI to generate trading signals.

## Features

- Fetches 50 candles from Kraken Exchange
- Uses DeepSeek AI for technical analysis
- Generates BUY/SELL/HOLD signals with stop prices and targets
- Supports historical analysis with date parameter
- Real-time signal generation for current market conditions

## Deployment on Railway

1. Fork this repository
2. Connect your Railway account to the repository
3. Add environment variables:
   - `DEEPSEEK_API_KEY`: Your DeepSeek API key
   - `KRAKEN_API_KEY`: Optional Kraken API key (for higher rate limits)

4. Deploy!

## API Endpoints

### Get Signals
