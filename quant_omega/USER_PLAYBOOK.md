# QUANT-OMEGA User Playbook

## How to Read the Indicator

### 1. Regime Label (Top-Left)
The regime label shows the current market state:
- **TRENDING** (Green): Strong directional movement, ADX > 25
- **RANGING** (Gray): Sideways consolidation, ADX < 20
- **BREAKOUT** (Orange): Volatility expansion, potential new trend
- **SQUEEZE** (Yellow): Compression before expansion, wait for release

### 2. Confidence Meter (Top-Right)
The confidence score (0-100) determines action:
- **86-100 (Green)**: STRONG entry - use 1.5x normal size
- **71-85 (Lime)**: NORMAL entry - use standard size
- **51-70 (Yellow)**: SMALL entry - use 0.5x size
- **31-50 (Orange)**: WATCH only - no entry
- **0-30 (Red)**: NO TRADE - stay flat

### 3. Entry Markers
- **Green Triangle Up**: Long entry signal
- **Red Triangle Down**: Short entry signal
- Marker size indicates confidence level

### 4. No-Trade Zone Shading
Gray background indicates unfavorable conditions:
- ADX < 15 (dead market)
- ATR ratio < 0.5 (extremely low volatility)
- Volume < 50% of average (no participation)

### 5. Moving Averages
- **Blue Line (EMA 8)**: Fast trend
- **Orange Line (EMA 21)**: Slow trend
- **Purple Line (EMA 50)**: Major trend

### 6. Bollinger Bands
- **Gray Lines**: Upper and lower bands
- **Gray Circles**: Middle band (SMA 20)
- Price outside bands = potential mean reversion

### 7. Donchian Channels
- **Teal Lines**: 20-period high/low
- Breakout above/below = potential trend start

---

## Signal Types

### Trend Following Signals
**When to expect:** TRENDING regime, ADX > 25
**Entry logic:**
- EMA fast > EMA slow (long) or EMA fast < EMA slow (short)
- Price above/below EMA trend
- Price pulls back to fast EMA
- RSI between 40-70 (long) or 30-60 (short)

**Best conditions:**
- Clear directional bias on higher timeframes
- Volume confirming the move
- No momentum exhaustion

### Mean Reversion Signals
**When to expect:** RANGING regime, ADX < 25
**Entry logic:**
- Price outside Bollinger Bands
- RSI < 30 (long) or RSI > 70 (short)
- Volume spike (capitulation/euphoria)
- No strong trend (EMA slope near zero)

**Best conditions:**
- Clear support/resistance levels
- Multiple touches of range boundaries
- Divergence on oscillators

### Breakout Signals
**When to expect:** BREAKOUT regime, squeeze release
**Entry logic:**
- Price breaks Donchian channel
- Squeeze just released (BB inside KC → BB outside KC)
- Volume spike (1.5x average)
- ATR ratio > 1.0 (volatility expanding)

**Best conditions:**
- Prior consolidation (squeeze)
- Volume confirmation
- Clean break with momentum

---

## Risk Management Rules

### Position Sizing
| Confidence | Risk % | Example ($100k account) |
|------------|--------|-------------------------|
| 86-100 | 1.5% | $1,500 risk |
| 71-85 | 1.0% | $1,000 risk |
| 51-70 | 0.5% | $500 risk |
| 0-50 | 0% | No trade |

### Stop Loss
- Default: 2x ATR from entry
- Placed at logical structure (swing high/low)
- Never move stop further from entry

### Take Profit
- Default: 3x ATR from entry (1.5 R:R)
- Scale out at 1R, 2R, 3R
- Trail stop after 1R profit

### Kill Switch Rules
| Condition | Action |
|-----------|--------|
| Daily loss > 3% | Stop trading today |
| Weekly loss > 7% | Stop trading this week |
| Max drawdown > 15% | Stop and review |
| 5 consecutive losses | Reduce size 50% |
| Win rate < 30% (20 trades) | Stop and review |

---

## Best Practices

### DO:
1. **Wait for confluence** - Multiple signals agreeing
2. **Respect no-trade zones** - The best trade is often no trade
3. **Follow position sizing** - Never exceed recommended size
4. **Honor kill-switches** - They exist to protect you
5. **Review weekly** - Compare live vs backtest performance
6. **Journal every trade** - Entry reason, exit reason, lessons
7. **Trade the regime** - Trend-follow in trends, mean-revert in ranges

### DON'T:
1. **Override signals** - "I think it will go up anyway"
2. **Ignore regime** - Trading trend-following in chop
3. **Revenge trade** - After losses, wanting to "make it back"
4. **Size creep** - Gradually increasing position sizes
5. **Curve-fit** - Optimizing on recent data only
6. **Chase entries** - If you missed it, wait for next setup
7. **Move stops** - Once set, only move in your favor

---

## Common Traps and How to Avoid Them

### Trap 1: Overtrading
**Symptom:** Taking every signal, even low confidence
**Solution:** Only trade confidence > 70, max 5 trades/day

### Trap 2: Regime Mismatch
**Symptom:** Losing streaks when market changes
**Solution:** Check regime FIRST, only use matching strategy

### Trap 3: Confirmation Bias
**Symptom:** Seeing signals that aren't there
**Solution:** Write down entry criteria BEFORE looking at chart

### Trap 4: Recency Bias
**Symptom:** Overweighting recent trades in decisions
**Solution:** Track 100+ trade statistics, not last 5

### Trap 5: Revenge Trading
**Symptom:** Increasing size after losses
**Solution:** Strict kill-switch rules, walk away after limit

---

## Weekly Review Checklist

### Performance Review
- [ ] Total trades this week
- [ ] Win rate vs expected (target: 50%+)
- [ ] Average R:R vs expected (target: 1.5+)
- [ ] Max drawdown vs limit (target: <15%)
- [ ] Profit factor vs expected (target: 1.5+)

### Process Review
- [ ] Did I follow entry rules?
- [ ] Did I follow exit rules?
- [ ] Did I respect position sizing?
- [ ] Did I honor kill-switches?
- [ ] Did I trade the correct regime?

### Improvement Questions
- What worked well this week?
- What didn't work?
- What will I do differently next week?
- What did I learn that reduces self-deception?

---

## Troubleshooting

### "No signals appearing"
1. Check if in no-trade zone (gray shading)
2. Check ADX - may be too low (<15)
3. Check volume - may be too low
4. Check ATR ratio - may be too low

### "Too many false signals"
1. Increase confidence threshold
2. Add higher timeframe filter
3. Check if regime is transitioning
4. Reduce trading during news events

### "Stops getting hit too often"
1. Check if stop multiplier is too tight
2. Check if entering at poor locations
3. Consider wider stops with smaller size
4. Review entry timing (not chasing)

### "Missing good moves"
1. Check if confidence threshold too high
2. Check if no-trade filters too strict
3. Consider adding to winners
4. Review if waiting too long for confirmation

---

## Quick Reference Card

```
REGIME → STRATEGY
TRENDING → Trend Following (pullback entries)
RANGING → Mean Reversion (band touches)
BREAKOUT → Breakout (channel breaks)
SQUEEZE → Wait for release

CONFIDENCE → ACTION
86-100 → Strong entry (1.5x size)
71-85 → Normal entry (1x size)
51-70 → Small entry (0.5x size)
31-50 → Watch only
0-30 → No trade

RISK RULES
Max risk/trade: 1.5%
Max daily loss: 3%
Max drawdown: 15%
Max trades/day: 5

STOP/TARGET
Stop: 2x ATR
Target: 3x ATR
R:R minimum: 1.5
```
