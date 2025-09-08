> ⚠️ **Clarification**  
> This repository – along with every other “bot” project in the `constantinbender51-cmyk` namespace – is **scrap / legacy code** and should **not** be treated as a working or profitable trading system.  
>  
> The **only** repos that still receive updates and are intended for forward-testing are:  
> - `constantinbender51-cmyk/sigtrabot`  
> - `constantinbender51-cmyk/DeepSeekGenerator-v.-1.4` (a.k.a. “DeepSignal v. 1.4”)  
>  
> Complete list of repos that remain **functionally maintained** (but still **unproven** in live, statistically-significant trading):  
> - `constantinbender51-cmyk/Kraken-futures-API`  
> - `constantinbender51-cmyk/sigtrabot`  
> - `constantinbender51-cmyk/binance-btc-data`  
> - `constantinbender51-cmyk/SigtraConfig`  
> - `constantinbender51-cmyk/Simple-bot-complex-behavior-project-`  
> - `constantinbender51-cmyk/DeepSeekGenerator-v.-1.4`  
>  
> > None of the above has demonstrated **statistically significant profitability** in out-of-sample, live trading; **DeepSignal v. 1.4** is merely **showing early promise** and remains experimental.
> > # Kraken DeepSeek Trading Signal Generator

A Python application that fetches OHLC data from Kraken exchange and generates trading signals using DeepSeek AI.

## Features

- Fetches 50 OHLC data points from Kraken
- Generates trading signals (Buy/Sell/Hold) using DeepSeek AI
- Provides stop loss and target prices
- Includes reasoning for each signal

## Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/kraken-deepseek-trading.git
cd kraken-deepseek-trading
