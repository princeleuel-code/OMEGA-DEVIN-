#!/usr/bin/env python3
"""
QUANT-OMEGA: Python Backtest Harness
Version: 1.0.0

This module implements the QUANT-OMEGA trading system with:
- Purged walk-forward validation
- Regime slicing (trend/range/high-vol)
- Stress tests (higher costs, worse slippage)
- Comprehensive metrics and reporting

Usage:
    python quant_omega_backtest.py --data data.csv --output results/
    python quant_omega_backtest.py --data data.csv --walk-forward --regime-slice
"""

import argparse
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class Regime(Enum):
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    BREAKOUT = "BREAKOUT"
    SQUEEZE = "SQUEEZE"


class VolatilityRegime(Enum):
    LOW_VOL = "LOW_VOL"
    NORMAL_VOL = "NORMAL_VOL"
    HIGH_VOL = "HIGH_VOL"


class SignalType(Enum):
    NONE = "NONE"
    LONG = "LONG"
    SHORT = "SHORT"


class SignalStrength(Enum):
    NONE = "NONE"
    SMALL = "SMALL"
    NORMAL = "NORMAL"
    STRONG = "STRONG"


@dataclass
class TradeResult:
    entry_time: datetime
    exit_time: datetime
    direction: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    confidence: float
    regime: str
    exit_reason: str


@dataclass
class BacktestMetrics:
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    avg_trade_duration: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Parameters:
    # Regime Detection
    adx_period: int = 14
    adx_threshold: int = 25
    atr_period: int = 14
    atr_slow_period: int = 50
    
    # Trend Following
    ema_fast: int = 8
    ema_slow: int = 21
    ema_trend: int = 50
    
    # Mean Reversion
    bb_period: int = 20
    bb_std: float = 2.0
    rsi_period: int = 14
    
    # Breakout
    donchian_period: int = 20
    squeeze_kc_mult: float = 1.5
    
    # Confidence
    conf_no_trade: int = 30
    conf_watch: int = 50
    conf_small: int = 70
    conf_strong: int = 85
    
    # Risk Management
    risk_per_trade: float = 1.0
    max_drawdown: float = 15.0
    daily_loss_limit: float = 3.0
    max_leverage: float = 5.0
    stop_multiplier: float = 2.0
    tp_multiplier: float = 3.0
    
    # Costs
    commission_pct: float = 0.05
    slippage_pct: float = 0.05
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# INDICATORS
# ============================================================================

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return series.rolling(window=period).mean()


def calculate_std(series: pd.Series, period: int) -> pd.Series:
    """Calculate Standard Deviation."""
    return series.rolling(window=period).std()


def calculate_tr(df: pd.DataFrame) -> pd.Series:
    """Calculate True Range."""
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift(1))
    low_close = abs(df['low'] - df['close'].shift(1))
    return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)


def calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
    """Calculate Average True Range."""
    tr = calculate_tr(df)
    return tr.ewm(span=period, adjust=False).mean()


def calculate_adx(df: pd.DataFrame, period: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate ADX, +DI, -DI."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    tr = calculate_tr(df)
    
    atr = tr.ewm(span=period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(span=period, adjust=False).mean()
    
    return adx, plus_di, minus_di


def calculate_rsi(series: pd.Series, period: int) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_stochastic(df: pd.DataFrame, period: int, smooth_k: int, smooth_d: int) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator."""
    lowest_low = df['low'].rolling(window=period).min()
    highest_high = df['high'].rolling(window=period).max()
    
    k = 100 * (df['close'] - lowest_low) / (highest_high - lowest_low)
    k = k.rolling(window=smooth_k).mean()
    d = k.rolling(window=smooth_d).mean()
    
    return k, d


def calculate_bollinger_bands(series: pd.Series, period: int, std_mult: float) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    basis = calculate_sma(series, period)
    std = calculate_std(series, period)
    upper = basis + std_mult * std
    lower = basis - std_mult * std
    return upper, basis, lower


def calculate_keltner_channels(df: pd.DataFrame, period: int, atr_mult: float) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Keltner Channels."""
    basis = calculate_ema(df['close'], period)
    atr = calculate_atr(df, period)
    upper = basis + atr_mult * atr
    lower = basis - atr_mult * atr
    return upper, basis, lower


def calculate_donchian_channels(df: pd.DataFrame, period: int) -> Tuple[pd.Series, pd.Series]:
    """Calculate Donchian Channels."""
    upper = df['high'].rolling(window=period).max()
    lower = df['low'].rolling(window=period).min()
    return upper, lower


# ============================================================================
# QUANT-OMEGA ENGINE
# ============================================================================

class QuantOmegaEngine:
    """Main trading engine implementing QUANT-OMEGA logic."""
    
    def __init__(self, params: Parameters):
        self.params = params
        self.indicators: Dict[str, pd.Series] = {}
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators needed for the strategy."""
        df = df.copy()
        
        # EMAs
        df['ema_fast'] = calculate_ema(df['close'], self.params.ema_fast)
        df['ema_slow'] = calculate_ema(df['close'], self.params.ema_slow)
        df['ema_trend'] = calculate_ema(df['close'], self.params.ema_trend)
        
        # ADX
        df['adx'], df['di_plus'], df['di_minus'] = calculate_adx(df, self.params.adx_period)
        
        # ATR
        df['atr_fast'] = calculate_atr(df, self.params.atr_period)
        df['atr_slow'] = calculate_atr(df, self.params.atr_slow_period)
        df['atr_ratio'] = df['atr_fast'] / df['atr_slow']
        
        # RSI
        df['rsi'] = calculate_rsi(df['close'], self.params.rsi_period)
        
        # Stochastic
        df['stoch_k'], df['stoch_d'] = calculate_stochastic(df, 14, 3, 3)
        
        # Bollinger Bands
        df['bb_upper'], df['bb_basis'], df['bb_lower'] = calculate_bollinger_bands(
            df['close'], self.params.bb_period, self.params.bb_std
        )
        
        # Keltner Channels
        df['kc_upper'], df['kc_basis'], df['kc_lower'] = calculate_keltner_channels(
            df, self.params.bb_period, self.params.squeeze_kc_mult
        )
        
        # Donchian Channels
        df['donchian_high'], df['donchian_low'] = calculate_donchian_channels(df, self.params.donchian_period)
        
        # Volume SMA
        if 'volume' in df.columns:
            df['vol_sma'] = calculate_sma(df['volume'], 20)
        else:
            df['vol_sma'] = 1.0
            df['volume'] = 1.0
        
        # Squeeze detection
        df['squeeze_on'] = (df['bb_lower'] > df['kc_lower']) & (df['bb_upper'] < df['kc_upper'])
        
        # Squeeze momentum
        highest = df['high'].rolling(window=self.params.bb_period).max()
        lowest = df['low'].rolling(window=self.params.bb_period).min()
        df['squeeze_momentum'] = df['close'] - (highest + lowest) / 2
        
        # EMA trend slope
        df['ema_trend_slope'] = (df['ema_trend'] - df['ema_trend'].shift(10)) / df['ema_trend'].shift(10)
        
        return df
    
    def detect_regime(self, row: pd.Series) -> Tuple[Regime, VolatilityRegime]:
        """Detect current market regime."""
        adx = row['adx']
        atr_ratio = row['atr_ratio']
        squeeze_on = row['squeeze_on']
        
        # Volatility regime
        if atr_ratio > 1.2:
            vol_regime = VolatilityRegime.HIGH_VOL
        elif atr_ratio < 0.8:
            vol_regime = VolatilityRegime.LOW_VOL
        else:
            vol_regime = VolatilityRegime.NORMAL_VOL
        
        # Market regime
        if squeeze_on:
            regime = Regime.SQUEEZE
        elif adx > self.params.adx_threshold:
            regime = Regime.TRENDING
        elif atr_ratio > 1.2:
            regime = Regime.BREAKOUT
        else:
            regime = Regime.RANGING
        
        return regime, vol_regime
    
    def check_trend_signal(self, row: pd.Series) -> SignalType:
        """Check for trend following signals."""
        close = row['close']
        ema_fast = row['ema_fast']
        ema_slow = row['ema_slow']
        ema_trend = row['ema_trend']
        adx = row['adx']
        rsi = row['rsi']
        atr = row['atr_fast']
        
        pullback = abs(close - ema_fast) < 0.5 * atr
        
        # Long trend
        if (ema_fast > ema_slow and 
            close > ema_trend and 
            adx > self.params.adx_threshold and 
            pullback and 
            40 < rsi < 70):
            return SignalType.LONG
        
        # Short trend
        if (ema_fast < ema_slow and 
            close < ema_trend and 
            adx > self.params.adx_threshold and 
            pullback and 
            30 < rsi < 60):
            return SignalType.SHORT
        
        return SignalType.NONE
    
    def check_reversion_signal(self, row: pd.Series) -> SignalType:
        """Check for mean reversion signals."""
        close = row['close']
        bb_upper = row['bb_upper']
        bb_lower = row['bb_lower']
        adx = row['adx']
        rsi = row['rsi']
        volume = row['volume']
        vol_sma = row['vol_sma']
        ema_slope = row['ema_trend_slope']
        
        vol_above_avg = volume > vol_sma
        
        # Long reversion
        if (close < bb_lower and 
            adx < self.params.adx_threshold and 
            rsi < 30 and 
            vol_above_avg and 
            ema_slope > -0.001):
            return SignalType.LONG
        
        # Short reversion
        if (close > bb_upper and 
            adx < self.params.adx_threshold and 
            rsi > 70 and 
            vol_above_avg and 
            ema_slope < 0.001):
            return SignalType.SHORT
        
        return SignalType.NONE
    
    def check_breakout_signal(self, row: pd.Series, prev_row: pd.Series) -> SignalType:
        """Check for breakout signals."""
        close = row['close']
        donchian_high = prev_row['donchian_high']
        donchian_low = prev_row['donchian_low']
        squeeze_on = row['squeeze_on']
        squeeze_momentum = row['squeeze_momentum']
        volume = row['volume']
        vol_sma = row['vol_sma']
        atr_ratio = row['atr_ratio']
        
        vol_spike = volume > 1.5 * vol_sma
        
        # Long breakout
        if (close > donchian_high and 
            not squeeze_on and 
            squeeze_momentum > 0 and 
            vol_spike and 
            atr_ratio > 1.0):
            return SignalType.LONG
        
        # Short breakout
        if (close < donchian_low and 
            not squeeze_on and 
            squeeze_momentum < 0 and 
            vol_spike and 
            atr_ratio > 1.0):
            return SignalType.SHORT
        
        return SignalType.NONE
    
    def calculate_confidence(self, row: pd.Series, regime: Regime, 
                            trend_signal: SignalType, 
                            reversion_signal: SignalType,
                            breakout_signal: SignalType) -> float:
        """Calculate confidence score (0-100)."""
        score = 0.0
        
        # Regime alignment (0-30 points)
        if regime == Regime.TRENDING and trend_signal != SignalType.NONE:
            score += 30
        elif regime == Regime.RANGING and reversion_signal != SignalType.NONE:
            score += 30
        elif regime == Regime.BREAKOUT and breakout_signal != SignalType.NONE:
            score += 30
        elif trend_signal != SignalType.NONE or reversion_signal != SignalType.NONE or breakout_signal != SignalType.NONE:
            score += 10
        
        # Signal agreement (0-30 points)
        long_signals = sum([
            trend_signal == SignalType.LONG,
            reversion_signal == SignalType.LONG,
            breakout_signal == SignalType.LONG
        ])
        short_signals = sum([
            trend_signal == SignalType.SHORT,
            reversion_signal == SignalType.SHORT,
            breakout_signal == SignalType.SHORT
        ])
        signal_count = max(long_signals, short_signals)
        
        if signal_count >= 2:
            score += 30
        elif signal_count == 1:
            score += 15
        
        # Volume confirmation (0-15 points)
        if row['volume'] > row['vol_sma'] * 1.2:
            score += 15
        elif row['volume'] > row['vol_sma']:
            score += 10
        
        # Momentum alignment (0-15 points)
        rsi = row['rsi']
        rsi_prev = row.get('rsi_prev', rsi)
        momentum_exhaustion = (rsi > 70 and rsi < rsi_prev) or (rsi < 30 and rsi > rsi_prev)
        if not momentum_exhaustion:
            score += 15
        
        # Volatility alignment (0-10 points)
        if row['atr_ratio'] >= 0.8:
            score += 10
        
        return min(100, score)
    
    def check_no_trade_conditions(self, row: pd.Series) -> bool:
        """Check if no-trade conditions are met."""
        return (row['adx'] < 15 or 
                row['atr_ratio'] < 0.5 or 
                row['volume'] < 0.5 * row['vol_sma'])
    
    def get_signal_strength(self, confidence: float) -> SignalStrength:
        """Get signal strength based on confidence."""
        if confidence >= self.params.conf_strong:
            return SignalStrength.STRONG
        elif confidence >= self.params.conf_small:
            return SignalStrength.NORMAL
        elif confidence > self.params.conf_watch:
            return SignalStrength.SMALL
        return SignalStrength.NONE
    
    def calculate_position_size(self, equity: float, confidence: float, 
                                stop_distance: float, price: float) -> float:
        """Calculate position size based on risk management rules."""
        strength = self.get_signal_strength(confidence)
        
        if strength == SignalStrength.STRONG:
            risk_pct = self.params.risk_per_trade * 1.5
        elif strength == SignalStrength.NORMAL:
            risk_pct = self.params.risk_per_trade
        elif strength == SignalStrength.SMALL:
            risk_pct = self.params.risk_per_trade * 0.5
        else:
            return 0.0
        
        risk_amount = equity * (risk_pct / 100)
        position_size = risk_amount / stop_distance
        
        # Leverage check
        notional_value = position_size * price
        implied_leverage = notional_value / equity
        
        if implied_leverage > self.params.max_leverage:
            position_size = (equity * self.params.max_leverage) / price
        
        return position_size


# ============================================================================
# BACKTESTER
# ============================================================================

class Backtester:
    """Backtesting engine with walk-forward and regime slicing."""
    
    def __init__(self, engine: QuantOmegaEngine, initial_capital: float = 100000):
        self.engine = engine
        self.initial_capital = initial_capital
        self.trades: List[TradeResult] = []
        
    def run(self, df: pd.DataFrame, 
            cost_multiplier: float = 1.0,
            slippage_multiplier: float = 1.0) -> BacktestMetrics:
        """Run backtest on data."""
        df = self.engine.calculate_indicators(df)
        
        # Add previous RSI for momentum exhaustion
        df['rsi_prev'] = df['rsi'].shift(3)
        
        equity = self.initial_capital
        peak_equity = equity
        position = None
        position_size = 0.0
        entry_price = 0.0
        entry_time = None
        entry_confidence = 0.0
        entry_regime = ""
        stop_loss = 0.0
        take_profit = 0.0
        
        daily_pnl = 0.0
        last_day = None
        trades_today = 0
        
        equity_curve = [equity]
        self.trades = []
        
        # Effective costs
        commission = self.engine.params.commission_pct * cost_multiplier
        slippage = self.engine.params.slippage_pct * slippage_multiplier
        total_cost = commission + slippage
        
        for i in range(1, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Reset daily counters
            current_day = row.name.date() if hasattr(row.name, 'date') else None
            if current_day != last_day:
                daily_pnl = 0.0
                trades_today = 0
                last_day = current_day
            
            # Kill switch checks
            drawdown_pct = (peak_equity - equity) / peak_equity * 100
            kill_switch = (daily_pnl <= -self.engine.params.daily_loss_limit or
                          drawdown_pct >= self.engine.params.max_drawdown or
                          trades_today >= 5)
            
            # Detect regime
            regime, vol_regime = self.engine.detect_regime(row)
            
            # Check signals
            trend_signal = self.engine.check_trend_signal(row)
            reversion_signal = self.engine.check_reversion_signal(row)
            breakout_signal = self.engine.check_breakout_signal(row, prev_row)
            
            # Calculate confidence
            confidence = self.engine.calculate_confidence(
                row, regime, trend_signal, reversion_signal, breakout_signal
            )
            
            # No-trade filter
            if self.engine.check_no_trade_conditions(row):
                confidence = 0
            
            # Determine direction
            long_signals = sum([
                trend_signal == SignalType.LONG,
                reversion_signal == SignalType.LONG,
                breakout_signal == SignalType.LONG
            ])
            short_signals = sum([
                trend_signal == SignalType.SHORT,
                reversion_signal == SignalType.SHORT,
                breakout_signal == SignalType.SHORT
            ])
            
            signal_direction = None
            if long_signals > short_signals and confidence > self.engine.params.conf_watch:
                signal_direction = "LONG"
            elif short_signals > long_signals and confidence > self.engine.params.conf_watch:
                signal_direction = "SHORT"
            
            # Position management
            if position is not None:
                current_price = row['close']
                
                # Check exits
                exit_reason = None
                
                if position == "LONG":
                    if current_price <= stop_loss:
                        exit_reason = "STOP_LOSS"
                    elif current_price >= take_profit:
                        exit_reason = "TAKE_PROFIT"
                    elif signal_direction == "SHORT":
                        exit_reason = "SIGNAL_EXIT"
                else:  # SHORT
                    if current_price >= stop_loss:
                        exit_reason = "STOP_LOSS"
                    elif current_price <= take_profit:
                        exit_reason = "TAKE_PROFIT"
                    elif signal_direction == "LONG":
                        exit_reason = "SIGNAL_EXIT"
                
                if exit_reason:
                    # Calculate P&L
                    if position == "LONG":
                        pnl = (current_price - entry_price) * position_size
                    else:
                        pnl = (entry_price - current_price) * position_size
                    
                    # Apply costs
                    cost = entry_price * position_size * total_cost / 100
                    pnl -= cost
                    
                    pnl_pct = pnl / equity * 100
                    equity += pnl
                    daily_pnl += pnl_pct
                    
                    # Record trade
                    self.trades.append(TradeResult(
                        entry_time=entry_time,
                        exit_time=row.name,
                        direction=position,
                        entry_price=entry_price,
                        exit_price=current_price,
                        size=position_size,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        confidence=entry_confidence,
                        regime=entry_regime,
                        exit_reason=exit_reason
                    ))
                    
                    position = None
                    position_size = 0.0
            
            # Entry logic
            if position is None and signal_direction and not kill_switch:
                atr = row['atr_fast']
                stop_distance = self.engine.params.stop_multiplier * atr
                
                position_size = self.engine.calculate_position_size(
                    equity, confidence, stop_distance, row['close']
                )
                
                if position_size > 0:
                    position = signal_direction
                    entry_price = row['close']
                    entry_time = row.name
                    entry_confidence = confidence
                    entry_regime = regime.value
                    
                    if position == "LONG":
                        stop_loss = entry_price - stop_distance
                        take_profit = entry_price + self.engine.params.tp_multiplier * atr
                    else:
                        stop_loss = entry_price + stop_distance
                        take_profit = entry_price - self.engine.params.tp_multiplier * atr
                    
                    trades_today += 1
            
            # Update peak equity
            peak_equity = max(peak_equity, equity)
            equity_curve.append(equity)
        
        # Close any remaining position
        if position is not None:
            current_price = df.iloc[-1]['close']
            if position == "LONG":
                pnl = (current_price - entry_price) * position_size
            else:
                pnl = (entry_price - current_price) * position_size
            
            cost = entry_price * position_size * total_cost / 100
            pnl -= cost
            
            equity += pnl
            
            self.trades.append(TradeResult(
                entry_time=entry_time,
                exit_time=df.iloc[-1].name,
                direction=position,
                entry_price=entry_price,
                exit_price=current_price,
                size=position_size,
                pnl=pnl,
                pnl_pct=pnl / (equity - pnl) * 100,
                confidence=entry_confidence,
                regime=entry_regime,
                exit_reason="END_OF_DATA"
            ))
        
        return self._calculate_metrics(equity_curve)
    
    def _calculate_metrics(self, equity_curve: List[float]) -> BacktestMetrics:
        """Calculate backtest metrics."""
        metrics = BacktestMetrics()
        
        if not self.trades:
            return metrics
        
        metrics.total_trades = len(self.trades)
        
        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl <= 0]
        
        metrics.winning_trades = len(wins)
        metrics.losing_trades = len(losses)
        metrics.win_rate = len(wins) / len(self.trades) if self.trades else 0
        
        metrics.total_pnl = sum(t.pnl for t in self.trades)
        metrics.total_pnl_pct = (equity_curve[-1] - self.initial_capital) / self.initial_capital * 100
        
        metrics.avg_win = np.mean([t.pnl for t in wins]) if wins else 0
        metrics.avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
        
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        metrics.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        metrics.expectancy = metrics.total_pnl / len(self.trades) if self.trades else 0
        
        # Drawdown
        equity_arr = np.array(equity_curve)
        peak = np.maximum.accumulate(equity_arr)
        drawdown = peak - equity_arr
        metrics.max_drawdown = np.max(drawdown)
        metrics.max_drawdown_pct = np.max(drawdown / peak) * 100
        
        # Sharpe and Sortino
        returns = np.diff(equity_arr) / equity_arr[:-1]
        if len(returns) > 0 and np.std(returns) > 0:
            metrics.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
            
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0 and np.std(downside_returns) > 0:
                metrics.sortino_ratio = np.mean(returns) / np.std(downside_returns) * np.sqrt(252)
        
        # Calmar
        annual_return = metrics.total_pnl_pct / (len(equity_curve) / 252)
        if metrics.max_drawdown_pct > 0:
            metrics.calmar_ratio = annual_return / metrics.max_drawdown_pct
        
        return metrics
    
    def walk_forward(self, df: pd.DataFrame, 
                     n_splits: int = 5,
                     train_pct: float = 0.6,
                     purge_bars: int = 10) -> List[BacktestMetrics]:
        """Run purged walk-forward validation."""
        results = []
        split_size = len(df) // n_splits
        
        for i in range(n_splits):
            start_idx = i * split_size
            end_idx = (i + 1) * split_size if i < n_splits - 1 else len(df)
            
            split_data = df.iloc[start_idx:end_idx]
            train_size = int(len(split_data) * train_pct)
            
            # Purge gap between train and test
            test_start = train_size + purge_bars
            if test_start >= len(split_data):
                continue
            
            test_data = split_data.iloc[test_start:]
            
            if len(test_data) < 50:
                continue
            
            metrics = self.run(test_data)
            results.append(metrics)
        
        return results
    
    def regime_slice(self, df: pd.DataFrame) -> Dict[str, BacktestMetrics]:
        """Run backtest sliced by regime."""
        df = self.engine.calculate_indicators(df)
        
        results = {}
        
        # Trending periods (ADX > 25)
        trending_mask = df['adx'] > self.engine.params.adx_threshold
        if trending_mask.sum() > 100:
            trending_df = df[trending_mask].copy()
            results['trending'] = self.run(trending_df)
        
        # Ranging periods (ADX < 20)
        ranging_mask = df['adx'] < 20
        if ranging_mask.sum() > 100:
            ranging_df = df[ranging_mask].copy()
            results['ranging'] = self.run(ranging_df)
        
        # High volatility periods (ATR ratio > 1.2)
        high_vol_mask = df['atr_ratio'] > 1.2
        if high_vol_mask.sum() > 100:
            high_vol_df = df[high_vol_mask].copy()
            results['high_vol'] = self.run(high_vol_df)
        
        return results
    
    def stress_test(self, df: pd.DataFrame) -> Dict[str, BacktestMetrics]:
        """Run stress tests with adverse conditions."""
        results = {}
        
        # Normal conditions
        results['normal'] = self.run(df)
        
        # 2x costs
        results['2x_costs'] = self.run(df, cost_multiplier=2.0)
        
        # 2x slippage
        results['2x_slippage'] = self.run(df, slippage_multiplier=2.0)
        
        # Both 2x
        results['2x_both'] = self.run(df, cost_multiplier=2.0, slippage_multiplier=2.0)
        
        return results


# ============================================================================
# EVALUATION
# ============================================================================

def evaluate_results(metrics: BacktestMetrics, params: Parameters) -> Dict[str, bool]:
    """Evaluate if results pass the promotion gates."""
    gates = {
        'expectancy_positive': metrics.expectancy > 0,
        'win_rate_above_40': metrics.win_rate > 0.40,
        'profit_factor_above_1_2': metrics.profit_factor > 1.2,
        'max_dd_below_limit': metrics.max_drawdown_pct < params.max_drawdown,
        'sharpe_above_0_5': metrics.sharpe_ratio > 0.5,
        'sufficient_trades': metrics.total_trades >= 30,
    }
    
    gates['all_passed'] = all(gates.values())
    return gates


def generate_report(metrics: BacktestMetrics, 
                   walk_forward_results: List[BacktestMetrics],
                   regime_results: Dict[str, BacktestMetrics],
                   stress_results: Dict[str, BacktestMetrics],
                   params: Parameters) -> Dict:
    """Generate comprehensive backtest report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'parameters': params.to_dict(),
        'main_results': metrics.to_dict(),
        'evaluation_gates': evaluate_results(metrics, params),
    }
    
    # Walk-forward results
    if walk_forward_results:
        wf_metrics = {
            'n_splits': len(walk_forward_results),
            'avg_expectancy': np.mean([m.expectancy for m in walk_forward_results]),
            'avg_win_rate': np.mean([m.win_rate for m in walk_forward_results]),
            'avg_profit_factor': np.mean([m.profit_factor for m in walk_forward_results]),
            'avg_sharpe': np.mean([m.sharpe_ratio for m in walk_forward_results]),
            'splits': [m.to_dict() for m in walk_forward_results]
        }
        report['walk_forward'] = wf_metrics
    
    # Regime results
    if regime_results:
        report['regime_slicing'] = {k: v.to_dict() for k, v in regime_results.items()}
        
        # Check regime survival
        profitable_regimes = sum(1 for m in regime_results.values() if m.expectancy > 0)
        report['regime_survival'] = profitable_regimes >= 2
    
    # Stress test results
    if stress_results:
        report['stress_tests'] = {k: v.to_dict() for k, v in stress_results.items()}
        
        # Check stress survival
        report['stress_survival'] = stress_results.get('2x_both', BacktestMetrics()).expectancy > 0
    
    return report


# ============================================================================
# MAIN
# ============================================================================

def load_data(filepath: str) -> pd.DataFrame:
    """Load OHLCV data from CSV."""
    df = pd.read_csv(filepath, parse_dates=['timestamp'] if 'timestamp' in pd.read_csv(filepath, nrows=1).columns else [0])
    
    # Standardize column names
    df.columns = df.columns.str.lower()
    
    # Rename common variations
    rename_map = {
        'date': 'timestamp',
        'datetime': 'timestamp',
        'time': 'timestamp',
        'o': 'open',
        'h': 'high',
        'l': 'low',
        'c': 'close',
        'v': 'volume',
        'vol': 'volume'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    # Set index
    if 'timestamp' in df.columns:
        df = df.set_index('timestamp')
    
    # Ensure required columns
    required = ['open', 'high', 'low', 'close']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Add volume if missing
    if 'volume' not in df.columns:
        df['volume'] = 1.0
    
    return df


def main():
    parser = argparse.ArgumentParser(description='QUANT-OMEGA Backtest Harness')
    parser.add_argument('--data', type=str, required=True, help='Path to OHLCV CSV file')
    parser.add_argument('--output', type=str, default='results', help='Output directory')
    parser.add_argument('--walk-forward', action='store_true', help='Run walk-forward validation')
    parser.add_argument('--regime-slice', action='store_true', help='Run regime slicing')
    parser.add_argument('--stress-test', action='store_true', help='Run stress tests')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"Loading data from {args.data}...")
    df = load_data(args.data)
    print(f"Loaded {len(df)} bars")
    
    # Initialize engine
    params = Parameters()
    engine = QuantOmegaEngine(params)
    backtester = Backtester(engine, initial_capital=args.capital)
    
    # Run main backtest
    print("Running main backtest...")
    metrics = backtester.run(df)
    print(f"Total trades: {metrics.total_trades}")
    print(f"Win rate: {metrics.win_rate:.2%}")
    print(f"Profit factor: {metrics.profit_factor:.2f}")
    print(f"Expectancy: ${metrics.expectancy:.2f}")
    print(f"Max drawdown: {metrics.max_drawdown_pct:.2f}%")
    print(f"Sharpe ratio: {metrics.sharpe_ratio:.2f}")
    
    # Walk-forward validation
    wf_results = []
    if args.walk_forward:
        print("\nRunning walk-forward validation...")
        wf_results = backtester.walk_forward(df)
        if wf_results:
            avg_exp = np.mean([m.expectancy for m in wf_results])
            print(f"Walk-forward avg expectancy: ${avg_exp:.2f}")
    
    # Regime slicing
    regime_results = {}
    if args.regime_slice:
        print("\nRunning regime slicing...")
        regime_results = backtester.regime_slice(df)
        for regime, m in regime_results.items():
            print(f"  {regime}: {m.total_trades} trades, {m.win_rate:.2%} win rate, ${m.expectancy:.2f} expectancy")
    
    # Stress tests
    stress_results = {}
    if args.stress_test:
        print("\nRunning stress tests...")
        stress_results = backtester.stress_test(df)
        for test, m in stress_results.items():
            print(f"  {test}: ${m.expectancy:.2f} expectancy")
    
    # Generate report
    report = generate_report(metrics, wf_results, regime_results, stress_results, params)
    
    # Evaluation
    gates = report['evaluation_gates']
    print("\n=== EVALUATION GATES ===")
    for gate, passed in gates.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {gate}: {status}")
    
    # Save report
    report_path = output_dir / 'backtest_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport saved to {report_path}")
    
    # Save champion if all gates passed
    if gates['all_passed']:
        champion = {
            'version': '1.0.0',
            'created': datetime.now().isoformat(),
            'parameters': params.to_dict(),
            'performance': metrics.to_dict()
        }
        if regime_results:
            champion['regime_performance'] = {k: v.to_dict() for k, v in regime_results.items()}
        
        champion_path = output_dir / 'champion.json'
        with open(champion_path, 'w') as f:
            json.dump(champion, f, indent=2, default=str)
        print(f"Champion saved to {champion_path}")
    
    return report


if __name__ == '__main__':
    main()
