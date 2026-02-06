#!/usr/bin/env python3
"""OMEGA-DEVIN Optimized Paper Trader"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json
import os

class OptimizedPaperTrader:
    def __init__(self, initial_capital=10000, risk_per_trade=0.02):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.min_confluence_score = 3
        self.sl_mult = 1.5
        self.tp_mult = 2.5
        self.assets = {'EURUSD': 'EURUSD=X', 'GBPUSD': 'GBPUSD=X', 'USDJPY': 'USDJPY=X', 'AUDUSD': 'AUDUSD=X', 'XAUUSD': 'GC=F'}
        self.positions = {}
        self.closed_trades = []
        self.trade_log = []
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0
        os.makedirs('paper_trading_logs', exist_ok=True)
        
    def fetch_data(self, asset, bars=250):
        ticker = self.assets.get(asset, asset)
        try:
            df = yf.download(ticker, period='30d', interval='1h', progress=False)
            return df.tail(bars)
        except Exception as e:
            print(f"Error fetching {asset}: {e}")
            return None
    
    def calculate_indicators(self, df):
        closes = df['Close'].values
        highs = df['High'].values
        lows = df['Low'].values
        atr_list = [0]
        for i in range(1, len(closes)):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            atr_list.append(tr)
        atr_14 = pd.Series(atr_list).rolling(14).mean().values
        ema_8 = pd.Series(closes).ewm(span=8).mean().values
        ema_21 = pd.Series(closes).ewm(span=21).mean().values
        ema_50 = pd.Series(closes).ewm(span=50).mean().values
        ema_200 = pd.Series(closes).ewm(span=200).mean().values
        delta = pd.Series(closes).diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).values
        ema_12 = pd.Series(closes).ewm(span=12).mean()
        ema_26 = pd.Series(closes).ewm(span=26).mean()
        macd = (ema_12 - ema_26).values
        macd_signal = pd.Series(macd).ewm(span=9).mean().values
        return {'close': closes, 'high': highs, 'low': lows, 'atr': atr_14, 'ema_8': ema_8, 'ema_21': ema_21, 'ema_50': ema_50, 'ema_200': ema_200, 'rsi': rsi, 'macd': macd, 'macd_signal': macd_signal}
    
    def get_signal(self, ind):
        i = -1
        bull_score = 0
        bear_score = 0
        reasons = []
        if ind['ema_8'][i] > ind['ema_21'][i] > ind['ema_50'][i]:
            bull_score += 2
            reasons.append("EMA_BULLISH")
        elif ind['ema_8'][i] < ind['ema_21'][i] < ind['ema_50'][i]:
            bear_score += 2
            reasons.append("EMA_BEARISH")
        if not np.isnan(ind['rsi'][i]):
            if ind['rsi'][i] < 40:
                bull_score += 1
                reasons.append("RSI_OVERSOLD")
            elif ind['rsi'][i] > 60:
                bear_score += 1
                reasons.append("RSI_OVERBOUGHT")
        if not np.isnan(ind['macd'][i]) and not np.isnan(ind['macd_signal'][i]):
            if ind['macd'][i] > ind['macd_signal'][i]:
                bull_score += 1
                reasons.append("MACD_BULLISH")
            else:
                bear_score += 1
                reasons.append("MACD_BEARISH")
        if ind['close'][i] > ind['ema_200'][i]:
            bull_score += 1
            reasons.append("ABOVE_EMA200")
        else:
            bear_score += 1
            reasons.append("BELOW_EMA200")
        if bull_score >= self.min_confluence_score and bull_score > bear_score + 1:
            return 1, bull_score, reasons
        elif bear_score >= self.min_confluence_score and bear_score > bull_score + 1:
            return -1, bear_score, reasons
        return 0, max(bull_score, bear_score), reasons
    
    def run_once(self):
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning markets...")
        for asset in self.assets:
            try:
                df = self.fetch_data(asset)
                if df is None or len(df) < 100:
                    continue
                ind = self.calculate_indicators(df)
                current_price = ind['close'][-1]
                current_atr = ind['atr'][-1]
                if np.isnan(current_atr) or current_atr == 0:
                    continue
                if asset not in self.positions:
                    signal, score, reasons = self.get_signal(ind)
                    if signal != 0:
                        direction = 'LONG' if signal == 1 else 'SHORT'
                        sl = current_price - self.sl_mult * current_atr if signal == 1 else current_price + self.sl_mult * current_atr
                        tp = current_price + self.tp_mult * current_atr if signal == 1 else current_price - self.tp_mult * current_atr
                        print(f"  SIGNAL: {direction} {asset} @ {current_price:.5f} | SL: {sl:.5f} | TP: {tp:.5f}")
                        print(f"    Reasons: {', '.join(reasons)}")
            except Exception as e:
                print(f"Error processing {asset}: {e}")
        print(f"\nStatus: Capital=${self.capital:.2f}")
        return self.capital

if __name__ == '__main__':
    trader = OptimizedPaperTrader()
    trader.run_once()
