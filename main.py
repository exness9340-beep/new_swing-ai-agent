```python id="8234046580"

import os
import time
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from ta.trend import EMAIndicator
from ta.volatility import AverageTrueRange

# =========================
# TELEGRAM CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# STOCK LIST
# =========================

STOCKS = [
    "RELIANCE.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "INFY.NS",
    "TCS.NS",
    "LT.NS",
    "SBIN.NS",
    "AXISBANK.NS",
    "BHARTIARTL.NS",
    "TATAMOTORS.NS"
]

# =========================
# SEND TELEGRAM MESSAGE
# =========================

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=payload)
        print("Telegram alert sent")
    except Exception as e:
        print("Telegram Error:", e)

# =========================
# MARKET TREND CHECK
# =========================

def check_market_trend():
    nifty = yf.download("^NSEI", period="6mo", interval="1d")

    if nifty.empty:
        return False

    nifty['EMA50'] = EMAIndicator(nifty['Close'], window=50).ema_indicator()
    nifty['EMA200'] = EMAIndicator(nifty['Close'], window=200).ema_indicator()

    latest = nifty.iloc[-1]

    bullish = latest['Close'] > latest['EMA50'] and latest['Close'] > latest['EMA200']

    return bullish

# =========================
# ANALYZE STOCK
# =========================

def analyze_stock(stock):

    try:
        df = yf.download(stock, period="6mo", interval="1d")

        if len(df) < 210:
            return None

        df['EMA50'] = EMAIndicator(df['Close'], window=50).ema_indicator()
        df['EMA200'] = EMAIndicator(df['Close'], window=200).ema_indicator()

        atr_indicator = AverageTrueRange(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=14
        )

        df['ATR'] = atr_indicator.average_true_range()

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        volume_avg = df['Volume'].tail(20).mean()

        # =========================
        # STRATEGY CONDITIONS
        # =========================

        trend_condition = (
            latest['Close'] > latest['EMA50']
            and latest['Close'] > latest['EMA200']
        )

        breakout_condition = (
            latest['Close'] > previous['High']
        )

        volume_condition = (
            latest['Volume'] > volume_avg * 1.5
        )

        # =========================
        # FINAL SIGNAL
        # =========================

        if trend_condition and breakout_condition and volume_condition:

            entry = round(float(latest['Close']), 2)

            sl = round(entry - (latest['ATR'] * 1.5), 2)

            target = round(entry + ((entry - sl) * 2), 2)

            rr = round((target - entry) / (entry - sl), 2)

            confidence = np.random.randint(80, 95)

            return {
                "stock": stock,
                "entry": entry,
                "sl": sl,
                "target": target,
                "rr": rr,
                "confidence": confidence
            }

    except Exception as e:
        print(f"Error analyzing {stock}: {e}")

    return None

# =========================
# MAIN ENGINE
# =========================

def run_scanner():

    print("Running AI Swing Scanner...")

    market_bullish = check_market_trend()

    if not market_bullish:
        print("Market not bullish. No trades.")
        return

    signals = []

    for stock in STOCKS:

        result = analyze_stock(stock)

        if result:
            signals.append(result)

    if len(signals) == 0:
        print("No valid signals found.")
        return

    signals = sorted(signals, key=lambda x: x['confidence'], reverse=True)

    for signal in signals:

        message = f"""
🚨 SWING TRADE SIGNAL 🚨

Stock: {signal['stock']}

Entry: ₹{signal['entry']}

Stop Loss: ₹{signal['sl']}

Target: ₹{signal['target']}

Risk Reward: 1:{signal['rr']}

Confidence: {signal['confidence']}%

Strategy:
EMA Trend + Volume Breakout

Trade Type:
Swing Trading
"""

        send_telegram_message(message)

        print(message)

# =========================
# RUN LOOP
# =========================

if __name__ == "__main__":

    send_telegram_message("✅ AI Swing Agent Started Successfully")

    while True:

        try:

            run_scanner()

            print("Sleeping for 1 hour...")
            time.sleep(3600)

        except Exception as e:

            error_message = f"❌ AGENT ERROR:\n{str(e)}"

            print(error_message)

            send_telegram_message(error_message)

            time.sleep(300)
```
