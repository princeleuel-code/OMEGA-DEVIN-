# QUANT-OMEGA: Adaptive Regime + Ensemble Signal System

## 1. ASSUMPTIONS

### Markets
- Primary: BTC/USDT, ETH/USDT (crypto perpetuals)
- Secondary: ES (S&P 500 futures), NQ (Nasdaq futures)
- Tertiary: EUR/USD, GBP/USD (major forex)

### Timeframes
- Primary execution: 15m, 1h
- Regime context: 4h, 1D
- Scalp mode: 5m (optional)

### Trading Style
- Intraday to swing (holding 1 hour to 3 days)
- NOT high-frequency (no sub-minute)

### Data Availability
- TradingView OHLCV only (default assumption)
- Volume data available
- NO order book, NO funding rates, NO options data assumed

### Costs (Conservative)
- Fees: 0.1% round-trip (0.05% entry + 0.05% exit)
- Slippage: 0.05% per trade (market orders)
- Total cost per trade: 0.15%

### Risk Limits
- Max drawdown target: 15%
- Daily loss limit: 3%
- Risk per trade: 1% of equity
- Max concurrent positions: 3
- Max leverage: 5x (regardless of what exchange allows)

---

## 2. THE INDICATOR CONCEPT

### What It Detects
QUANT-OMEGA detects the current market regime and generates ensemble signals from 3 independent alpha families, producing a unified confidence score that determines:
- When to trade (high confidence)
- When to stay out (low confidence / choppy)
- Entry/exit levels with mathematical justification

### Why It Works
Markets exhibit regime persistence - trending markets tend to continue trending, mean-reverting markets tend to continue mean-reverting. By:
1. Detecting the current regime FIRST
2. Selecting the appropriate alpha family for that regime
3. Requiring multi-signal confluence
We avoid the #1 killer of trading systems: applying trend-following in choppy markets or mean-reversion in trending markets.

### When It Fails
- Regime transitions (the moment trend becomes chop or vice versa)
- Black swan events (news-driven gaps)
- Low liquidity periods (weekends, holidays)
- When volatility regime shifts faster than detection lag

### Edge Decay Expectation
- Alpha families have ~6-12 month half-life
- Regime detection is more stable (~2-3 year half-life)
- System requires quarterly review and annual recalibration

---

## 3. SIGNAL ENGINE (Math/Logic)

### A) Regime Detection Module

#### 3.1 Trend Regime (ADX-based)
```
ADX = Average Directional Index (14 periods)
DI+ = Positive Directional Indicator
DI- = Negative Directional Indicator

trend_strength = ADX
trend_direction = sign(DI+ - DI-)

TRENDING if ADX > 25
WEAK_TREND if 20 < ADX <= 25
RANGING if ADX <= 20
```

#### 3.2 Volatility Regime (ATR-based)
```
ATR_fast = ATR(14)
ATR_slow = ATR(50)
ATR_ratio = ATR_fast / ATR_slow

LOW_VOL if ATR_ratio < 0.8
NORMAL_VOL if 0.8 <= ATR_ratio <= 1.2
HIGH_VOL if ATR_ratio > 1.2
EXPANDING if ATR_ratio > 1.2 AND ATR_fast > ATR_fast[5]
CONTRACTING if ATR_ratio < 0.8 AND ATR_fast < ATR_fast[5]
```

#### 3.3 Momentum Regime (RSI + Stochastic)
```
RSI = RSI(14)
Stoch_K = Stochastic %K(14, 3, 3)

OVERBOUGHT if RSI > 70 AND Stoch_K > 80
OVERSOLD if RSI < 30 AND Stoch_K < 20
NEUTRAL otherwise

momentum_exhaustion = (RSI > 70 AND RSI < RSI[3]) OR (RSI < 30 AND RSI > RSI[3])
```

#### 3.4 Squeeze Detection (Bollinger + Keltner)
```
BB_upper = SMA(20) + 2 * StdDev(20)
BB_lower = SMA(20) - 2 * StdDev(20)
KC_upper = EMA(20) + 1.5 * ATR(20)
KC_lower = EMA(20) - 1.5 * ATR(20)

SQUEEZE_ON if BB_lower > KC_lower AND BB_upper < KC_upper
SQUEEZE_OFF otherwise
squeeze_momentum = close - (highest(20) + lowest(20)) / 2
```

### B) Alpha Family 1: Trend Following

#### Entry Logic
```
ema_fast = EMA(8)
ema_slow = EMA(21)
ema_trend = EMA(50)

LONG_TREND_SIGNAL:
  - ema_fast > ema_slow
  - close > ema_trend
  - ADX > 25
  - close pulls back to ema_fast (within 0.5 * ATR)
  - RSI > 40 AND RSI < 70

SHORT_TREND_SIGNAL:
  - ema_fast < ema_slow
  - close < ema_trend
  - ADX > 25
  - close pulls back to ema_fast (within 0.5 * ATR)
  - RSI < 60 AND RSI > 30
```

#### Exit Logic
```
TREND_EXIT:
  - ema_fast crosses ema_slow against position
  - OR close crosses ema_trend against position
  - OR ADX drops below 20
  - OR trailing stop hit (2 * ATR from swing high/low)
```

### C) Alpha Family 2: Mean Reversion

#### Entry Logic
```
bb_mid = SMA(20)
bb_upper = bb_mid + 2 * StdDev(20)
bb_lower = bb_mid - 2 * StdDev(20)
bb_width = (bb_upper - bb_lower) / bb_mid

LONG_REVERSION_SIGNAL:
  - close < bb_lower
  - ADX < 25 (not trending)
  - RSI < 30
  - volume > SMA(volume, 20) (capitulation)
  - NOT in downtrend (ema_50 slope > -0.001)

SHORT_REVERSION_SIGNAL:
  - close > bb_upper
  - ADX < 25 (not trending)
  - RSI > 70
  - volume > SMA(volume, 20) (euphoria)
  - NOT in uptrend (ema_50 slope < 0.001)
```

#### Exit Logic
```
REVERSION_EXIT:
  - close crosses bb_mid (target reached)
  - OR RSI crosses 50 (momentum neutralized)
  - OR time stop: 10 bars without progress
  - OR stop loss: 1.5 * ATR from entry
```

### D) Alpha Family 3: Breakout / Volatility Expansion

#### Entry Logic
```
donchian_high = highest(high, 20)
donchian_low = lowest(low, 20)
range_width = donchian_high - donchian_low

LONG_BREAKOUT_SIGNAL:
  - close > donchian_high[1] (breakout)
  - SQUEEZE_OFF (squeeze just released)
  - squeeze_momentum > 0 (momentum positive)
  - volume > 1.5 * SMA(volume, 20) (volume confirmation)
  - ATR_ratio > 1.0 (volatility expanding)

SHORT_BREAKOUT_SIGNAL:
  - close < donchian_low[1] (breakdown)
  - SQUEEZE_OFF (squeeze just released)
  - squeeze_momentum < 0 (momentum negative)
  - volume > 1.5 * SMA(volume, 20) (volume confirmation)
  - ATR_ratio > 1.0 (volatility expanding)
```

#### Exit Logic
```
BREAKOUT_EXIT:
  - close re-enters previous range (failed breakout)
  - OR trailing stop: 1.5 * ATR from breakout high/low
  - OR target: 2 * range_width from breakout point
```

---

## 4. CONFIDENCE SCORE + NO-TRADE FILTERS

### Confidence Calculation (0-100)

```python
def calculate_confidence(regime, signals, market_conditions):
    base_score = 0
    
    # Regime alignment (0-30 points)
    if regime.trend_strength == 'TRENDING' and signals.trend_signal:
        base_score += 30
    elif regime.trend_strength == 'RANGING' and signals.reversion_signal:
        base_score += 30
    elif regime.volatility == 'EXPANDING' and signals.breakout_signal:
        base_score += 30
    else:
        base_score += 10  # Regime mismatch penalty
    
    # Signal agreement (0-30 points)
    signal_count = sum([signals.trend_signal, signals.reversion_signal, signals.breakout_signal])
    if signal_count >= 2:
        base_score += 30
    elif signal_count == 1:
        base_score += 15
    
    # Volume confirmation (0-15 points)
    if market_conditions.volume > market_conditions.avg_volume * 1.2:
        base_score += 15
    elif market_conditions.volume > market_conditions.avg_volume:
        base_score += 10
    
    # Momentum alignment (0-15 points)
    if not regime.momentum_exhaustion:
        base_score += 15
    
    # Time filter (0-10 points)
    if market_conditions.is_active_session:
        base_score += 10
    
    return min(100, base_score)
```

### Confidence Thresholds

| Confidence | Action | Position Size |
|------------|--------|---------------|
| 0-30 | NO TRADE | 0% |
| 31-50 | WATCH ONLY | 0% |
| 51-70 | SMALL ENTRY | 0.5% risk |
| 71-85 | NORMAL ENTRY | 1.0% risk |
| 86-100 | STRONG ENTRY | 1.5% risk (max) |

### No-Trade Filters (Hard Blocks)

```python
NO_TRADE_CONDITIONS = [
    ADX < 15,  # Dead market
    ATR_ratio < 0.5,  # Extremely low volatility
    volume < 0.5 * avg_volume,  # No participation
    spread > 0.1%,  # Wide spread
    is_weekend,  # Crypto weekend gaps
    is_major_news_event,  # Manual flag
    daily_loss_limit_hit,  # Risk management
    max_drawdown_exceeded,  # Risk management
]

if any(NO_TRADE_CONDITIONS):
    confidence = 0
    action = "NO TRADE"
```

---

## 5. RISK + POSITIONING

### Position Sizing Formula

```python
def calculate_position_size(equity, confidence, stop_distance, max_leverage=5):
    # Base risk per trade
    if confidence >= 86:
        risk_pct = 0.015  # 1.5%
    elif confidence >= 71:
        risk_pct = 0.010  # 1.0%
    elif confidence >= 51:
        risk_pct = 0.005  # 0.5%
    else:
        return 0  # No trade
    
    # Calculate position size
    risk_amount = equity * risk_pct
    position_size = risk_amount / stop_distance
    
    # Leverage check
    notional_value = position_size * current_price
    implied_leverage = notional_value / equity
    
    if implied_leverage > max_leverage:
        position_size = (equity * max_leverage) / current_price
    
    return position_size
```

### Kill-Switch Rules

```python
KILL_SWITCH_TRIGGERS = {
    'daily_loss': -0.03,  # -3% daily loss
    'weekly_loss': -0.07,  # -7% weekly loss
    'max_drawdown': -0.15,  # -15% from peak
    'consecutive_losses': 5,  # 5 losses in a row
    'win_rate_collapse': 0.30,  # Win rate drops below 30% over 20 trades
}

def check_kill_switch(account_state):
    if account_state.daily_pnl <= KILL_SWITCH_TRIGGERS['daily_loss']:
        return "STOP_TRADING_TODAY"
    if account_state.weekly_pnl <= KILL_SWITCH_TRIGGERS['weekly_loss']:
        return "STOP_TRADING_WEEK"
    if account_state.drawdown <= KILL_SWITCH_TRIGGERS['max_drawdown']:
        return "STOP_TRADING_REVIEW"
    if account_state.consecutive_losses >= KILL_SWITCH_TRIGGERS['consecutive_losses']:
        return "REDUCE_SIZE_50%"
    return "CONTINUE"
```

### Leverage Sanity

```
MAX_LEVERAGE = 5x (hard cap)
RECOMMENDED_LEVERAGE = 2-3x

Leverage adjustment by volatility:
- LOW_VOL: up to 5x allowed
- NORMAL_VOL: up to 3x allowed
- HIGH_VOL: up to 2x allowed
- EXTREME_VOL (ATR_ratio > 2): 1x only (no leverage)
```

---

## 6. EVALUATION PROTOCOL

### Pass/Fail Gates

| Metric | Minimum Requirement | Target |
|--------|---------------------|--------|
| Out-of-sample expectancy | > 0 after costs | > 0.5% per trade |
| Win rate | > 40% | > 50% |
| Profit factor | > 1.2 | > 1.5 |
| Max drawdown | < 15% | < 10% |
| Sharpe ratio | > 0.5 | > 1.0 |
| Sortino ratio | > 0.7 | > 1.5 |
| Regime survival | 2+ regimes | All 3 regimes |
| Parameter sensitivity | ±20% stable | ±30% stable |

### Test Protocol

1. **In-Sample Training** (60% of data)
   - Optimize parameters
   - Develop signal logic

2. **Validation** (20% of data)
   - Test parameter stability
   - Adjust if needed (max 1 iteration)

3. **Out-of-Sample Test** (20% of data)
   - NO changes allowed
   - Must pass all gates

4. **Regime Slicing**
   - Test separately on: trending periods, ranging periods, high-vol periods
   - Must be profitable in at least 2 of 3

5. **Stress Tests**
   - 2x costs
   - 2x slippage
   - Random 1-bar delay on entries
   - Must remain profitable

### Repaint Audit Checklist

- [ ] No future data in calculations
- [ ] security() calls use barmerge.lookahead_off
- [ ] No request.security() on lower timeframes
- [ ] Signals only trigger on bar close
- [ ] Historical signals match real-time signals
- [ ] Alerts fire at same time as visual signals

---

## 7. RECURSIVE IMPROVEMENT LOOP

### Champion.json Structure

```json
{
  "version": "1.0.0",
  "created": "2026-02-20",
  "parameters": {
    "ema_fast": 8,
    "ema_slow": 21,
    "ema_trend": 50,
    "adx_period": 14,
    "adx_threshold": 25,
    "atr_period": 14,
    "bb_period": 20,
    "bb_std": 2.0,
    "donchian_period": 20,
    "confidence_threshold": 51
  },
  "performance": {
    "expectancy": 0.0052,
    "win_rate": 0.54,
    "profit_factor": 1.67,
    "max_drawdown": -0.089,
    "sharpe": 1.23,
    "total_trades": 847
  },
  "regime_performance": {
    "trending": {"expectancy": 0.0078, "trades": 312},
    "ranging": {"expectancy": 0.0031, "trades": 298},
    "high_vol": {"expectancy": 0.0045, "trades": 237}
  }
}
```

### Weekly Experiment Cycle

1. **Monday**: Review last week's live performance vs backtest
2. **Tuesday**: Propose 3 variants (parameter tweaks or logic changes)
3. **Wednesday**: Run cheap tests (1-year backtest, no walk-forward)
4. **Thursday**: Full evaluation on promising variants
5. **Friday**: Promote winner to champion if it beats current

### Adversarial Replay

Every month, run the champion against:
- Worst 10 drawdown periods in history
- Flash crash scenarios
- Low liquidity periods
- News event periods

If champion fails adversarial replay, demote and investigate.

### Weekly Question

"What did we learn this week that reduces self-deception in evaluation?"

Document answers in improvement_log.md

---

## 8. USER PLAYBOOK

### How to Read the Indicator

1. **Regime Label** (top-left)
   - Shows current market state: TRENDING/RANGING/BREAKOUT
   - Color: Green = favorable, Yellow = caution, Red = avoid

2. **Confidence Meter** (top-right)
   - 0-100 scale
   - Green zone (51+): Trade allowed
   - Yellow zone (31-50): Watch only
   - Red zone (0-30): No trade

3. **Entry Markers**
   - Green triangle up: Long entry
   - Red triangle down: Short entry
   - Size indicates confidence level

4. **Exit Markers**
   - X marker: Stop loss hit
   - Star marker: Take profit hit
   - Circle marker: Signal exit

5. **No-Trade Shading**
   - Gray background: No trade zone
   - Indicates choppy/unfavorable conditions

### Best Practices

1. **Wait for confluence**: Don't trade on single signals
2. **Respect no-trade zones**: The best trade is often no trade
3. **Follow position sizing**: Never exceed recommended size
4. **Honor kill-switches**: They exist to protect you
5. **Review weekly**: Compare live vs backtest performance

### Common Traps

1. **Overriding signals**: "I think it will go up anyway"
2. **Ignoring regime**: Trading trend-following in chop
3. **Revenge trading**: After losses, wanting to "make it back"
4. **Size creep**: Gradually increasing position sizes
5. **Curve-fitting**: Optimizing on recent data only
