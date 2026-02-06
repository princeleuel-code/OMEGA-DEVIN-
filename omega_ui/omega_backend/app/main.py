from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json
import sys
import os
import numpy as np

# Add omega_devin to path
sys.path.insert(0, '/home/ubuntu/omega_devin')

# Import Provenance System
from app.provenance import (
    DataTier,
    ProvenanceFirewall,
    ProvenanceTag,
    TaggedFeature,
    create_tagged_feature,
    FEATURE_PROVENANCE_TABLE
)
from app.provenance.weave_packet import (
    WeavePacket,
    WeavePacketStore,
    DecisionType,
    ReasonCode,
    RenderAnchor,
    FeatureValue,
    ConflictInfo,
    create_wait_packet,
    packet_store
)
from app.provenance.real_dom import (
    RealDOMManager,
    BinanceL2Feed,
    RealDOMSnapshot,
    dom_manager,
    get_synthetic_dom_watermarked
)

# Global provenance firewall
provenance_firewall = ProvenanceFirewall()

app = FastAPI(title="OMEGA-DEVIN Trading Dashboard API")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# In-memory storage for demo
class TradingState:
    def __init__(self):
        self.capital = 10000.0
        self.equity = 10000.0
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.open_positions = []
        self.closed_trades = []
        self.signals = []
        self.price_history = {}
        self.current_prices = {}
        self.regime = "NEUTRAL"
        self.confluence_score = 0.0
        self.kill_switch_active = False
        self.volume_profiles = {}
        self.vwap_data = {}

state = TradingState()

def calculate_volume_profile(bars: List[dict], num_levels: int = 50) -> dict:
    """Calculate Volume Profile with HVN, LVN, POC, and Value Area"""
    if not bars or len(bars) < 10:
        return {}
    
    # Get price range
    all_highs = [b["high"] for b in bars]
    all_lows = [b["low"] for b in bars]
    price_high = max(all_highs)
    price_low = min(all_lows)
    price_range = price_high - price_low
    
    if price_range <= 0:
        return {}
    
    # Create price levels
    level_size = price_range / num_levels
    levels = []
    for i in range(num_levels):
        level_low = price_low + (i * level_size)
        level_high = level_low + level_size
        levels.append({
            "price_low": level_low,
            "price_high": level_high,
            "price_mid": (level_low + level_high) / 2,
            "volume": 0,
            "buy_volume": 0,
            "sell_volume": 0,
            "delta": 0
        })
    
    # Distribute volume across levels
    total_volume = 0
    for bar in bars:
        bar_range = bar["high"] - bar["low"]
        bar_volume = bar.get("volume", 1000)
        
        # Determine if bar is bullish or bearish for delta
        is_bullish = bar["close"] >= bar["open"]
        
        for level in levels:
            # Check overlap between bar and level
            overlap_low = max(bar["low"], level["price_low"])
            overlap_high = min(bar["high"], level["price_high"])
            
            if overlap_high > overlap_low:
                # Calculate volume proportion for this level
                if bar_range > 0:
                    overlap_ratio = (overlap_high - overlap_low) / bar_range
                else:
                    overlap_ratio = 1.0 / num_levels
                
                vol_contribution = bar_volume * overlap_ratio
                level["volume"] += vol_contribution
                total_volume += vol_contribution
                
                # Delta calculation (simplified - bullish bars add to buy, bearish to sell)
                if is_bullish:
                    level["buy_volume"] += vol_contribution * 0.6
                    level["sell_volume"] += vol_contribution * 0.4
                else:
                    level["buy_volume"] += vol_contribution * 0.4
                    level["sell_volume"] += vol_contribution * 0.6
                
                level["delta"] = level["buy_volume"] - level["sell_volume"]
    
    # Find POC (Point of Control) - level with highest volume
    poc_level = max(levels, key=lambda x: x["volume"])
    poc_price = poc_level["price_mid"]
    
    # Calculate Value Area (70% of volume around POC)
    sorted_levels = sorted(levels, key=lambda x: x["volume"], reverse=True)
    value_area_volume = 0
    value_area_target = total_volume * 0.70
    value_area_levels = []
    
    for level in sorted_levels:
        if value_area_volume < value_area_target:
            value_area_levels.append(level)
            value_area_volume += level["volume"]
        else:
            break
    
    if value_area_levels:
        vah = max(l["price_high"] for l in value_area_levels)
        val = min(l["price_low"] for l in value_area_levels)
    else:
        vah = price_high
        val = price_low
    
    # Identify HVN and LVN
    avg_volume = total_volume / num_levels if num_levels > 0 else 0
    hvn_threshold = avg_volume * 1.5
    lvn_threshold = avg_volume * 0.5
    
    hvn_levels = [l for l in levels if l["volume"] > hvn_threshold]
    lvn_levels = [l for l in levels if l["volume"] < lvn_threshold and l["volume"] > 0]
    
    # Normalize volumes for display (0-100 scale)
    max_vol = max(l["volume"] for l in levels) if levels else 1
    for level in levels:
        level["volume_pct"] = (level["volume"] / max_vol * 100) if max_vol > 0 else 0
        level["is_value_area"] = val <= level["price_mid"] <= vah
        level["is_hvn"] = level["volume"] > hvn_threshold
        level["is_lvn"] = level["volume"] < lvn_threshold
    
    return {
        "levels": levels,
        "poc": poc_price,
        "vah": vah,
        "val": val,
        "price_high": price_high,
        "price_low": price_low,
        "total_volume": total_volume,
        "hvn_prices": [l["price_mid"] for l in hvn_levels],
        "lvn_prices": [l["price_mid"] for l in lvn_levels]
    }

def calculate_vwap(bars: List[dict]) -> List[dict]:
    """Calculate VWAP (Volume Weighted Average Price)"""
    if not bars:
        return []
    
    vwap_data = []
    cumulative_tpv = 0  # Total Price * Volume
    cumulative_volume = 0
    
    for i, bar in enumerate(bars):
        typical_price = (bar["high"] + bar["low"] + bar["close"]) / 3
        volume = bar.get("volume", 1000)
        
        cumulative_tpv += typical_price * volume
        cumulative_volume += volume
        
        vwap = cumulative_tpv / cumulative_volume if cumulative_volume > 0 else typical_price
        
        # Calculate standard deviation bands
        if i > 0:
            prices = [(b["high"] + b["low"] + b["close"]) / 3 for b in bars[:i+1]]
            std_dev = np.std(prices) if len(prices) > 1 else 0
        else:
            std_dev = 0
        
        vwap_data.append({
            "timestamp": bar["timestamp"],
            "vwap": vwap,
            "upper_band_1": vwap + std_dev,
            "lower_band_1": vwap - std_dev,
            "upper_band_2": vwap + 2 * std_dev,
            "lower_band_2": vwap - 2 * std_dev
        })
    
    return vwap_data

def calculate_cumulative_delta(bars: List[dict]) -> List[dict]:
    """Calculate Cumulative Delta (buying vs selling pressure)"""
    if not bars:
        return []
    
    delta_data = []
    cumulative_delta = 0
    
    for bar in bars:
        # Simplified delta calculation based on candle direction and volume
        volume = bar.get("volume", 1000)
        is_bullish = bar["close"] >= bar["open"]
        
        # Calculate delta based on candle body vs wick ratio
        body = abs(bar["close"] - bar["open"])
        total_range = bar["high"] - bar["low"]
        
        if total_range > 0:
            body_ratio = body / total_range
        else:
            body_ratio = 0.5
        
        # Strong candles have more delta in their direction
        if is_bullish:
            bar_delta = volume * (0.3 + 0.4 * body_ratio)
        else:
            bar_delta = -volume * (0.3 + 0.4 * body_ratio)
        
        cumulative_delta += bar_delta
        
        delta_data.append({
            "timestamp": bar["timestamp"],
            "delta": bar_delta,
            "cumulative_delta": cumulative_delta,
            "is_bullish": is_bullish
        })
    
    return delta_data

# ============================================================================
# BREAKTHROUGH INSTITUTIONAL-GRADE ANALYTICS
# ============================================================================

def calculate_order_flow_imbalance(bars: List[dict], lookback: int = 20) -> dict:
    """
    Calculate Order Flow Imbalance (OFI) - measures aggressive buying vs selling
    OFI > 0 indicates buying pressure, OFI < 0 indicates selling pressure
    """
    if not bars or len(bars) < lookback:
        return {"ofi": 0, "ofi_normalized": 0, "signal": "NEUTRAL", "strength": 0}
    
    recent_bars = bars[-lookback:]
    ofi_values = []
    
    for i, bar in enumerate(recent_bars):
        volume = bar.get("volume", 1000)
        
        # Calculate bid/ask imbalance proxy using price action
        mid_price = (bar["high"] + bar["low"]) / 2
        close_position = (bar["close"] - bar["low"]) / (bar["high"] - bar["low"]) if bar["high"] != bar["low"] else 0.5
        
        # OFI calculation: positive when close is above mid (buying pressure)
        bar_ofi = volume * (close_position - 0.5) * 2
        ofi_values.append(bar_ofi)
    
    total_ofi = sum(ofi_values)
    avg_volume = np.mean([b.get("volume", 1000) for b in recent_bars])
    ofi_normalized = total_ofi / (avg_volume * lookback) if avg_volume > 0 else 0
    
    # Determine signal
    if ofi_normalized > 0.3:
        signal = "STRONG_BUY"
        strength = min(1.0, ofi_normalized / 0.5)
    elif ofi_normalized > 0.1:
        signal = "BUY"
        strength = ofi_normalized / 0.3
    elif ofi_normalized < -0.3:
        signal = "STRONG_SELL"
        strength = min(1.0, abs(ofi_normalized) / 0.5)
    elif ofi_normalized < -0.1:
        signal = "SELL"
        strength = abs(ofi_normalized) / 0.3
    else:
        signal = "NEUTRAL"
        strength = abs(ofi_normalized) / 0.1
    
    return {
        "ofi": total_ofi,
        "ofi_normalized": ofi_normalized,
        "signal": signal,
        "strength": min(1.0, strength),
        "lookback": lookback
    }

def calculate_footprint_analysis(bars: List[dict]) -> dict:
    """
    Footprint Chart Analysis - identifies stacked imbalances, absorption, and exhaustion
    """
    if not bars or len(bars) < 10:
        return {"imbalances": [], "absorption_zones": [], "exhaustion_signals": []}
    
    imbalances = []
    absorption_zones = []
    exhaustion_signals = []
    
    for i, bar in enumerate(bars):
        volume = bar.get("volume", 1000)
        body = abs(bar["close"] - bar["open"])
        total_range = bar["high"] - bar["low"]
        is_bullish = bar["close"] >= bar["open"]
        
        if total_range == 0:
            continue
        
        body_ratio = body / total_range
        upper_wick = bar["high"] - max(bar["open"], bar["close"])
        lower_wick = min(bar["open"], bar["close"]) - bar["low"]
        
        # Stacked Imbalance Detection (3+ consecutive same-direction strong candles)
        if i >= 2:
            prev_bars = bars[i-2:i+1]
            same_direction = all(b["close"] >= b["open"] for b in prev_bars) or all(b["close"] < b["open"] for b in prev_bars)
            strong_bodies = all(abs(b["close"] - b["open"]) / max(b["high"] - b["low"], 0.0001) > 0.6 for b in prev_bars)
            
            if same_direction and strong_bodies:
                imbalances.append({
                    "index": i,
                    "timestamp": bar["timestamp"],
                    "type": "BULLISH_STACK" if is_bullish else "BEARISH_STACK",
                    "strength": body_ratio,
                    "price": bar["close"]
                })
        
        # Absorption Detection (high volume with small body = orders being absorbed)
        if i > 0:
            prev_volume = bars[i-1].get("volume", 1000)
            if volume > prev_volume * 1.5 and body_ratio < 0.3:
                absorption_zones.append({
                    "index": i,
                    "timestamp": bar["timestamp"],
                    "type": "ABSORPTION",
                    "volume_ratio": volume / prev_volume,
                    "price_high": bar["high"],
                    "price_low": bar["low"]
                })
        
        # Exhaustion Detection (long wick in direction of move = exhaustion)
        if is_bullish and upper_wick > body * 2:
            exhaustion_signals.append({
                "index": i,
                "timestamp": bar["timestamp"],
                "type": "BUYING_EXHAUSTION",
                "wick_ratio": upper_wick / max(body, 0.0001),
                "price": bar["high"]
            })
        elif not is_bullish and lower_wick > body * 2:
            exhaustion_signals.append({
                "index": i,
                "timestamp": bar["timestamp"],
                "type": "SELLING_EXHAUSTION",
                "wick_ratio": lower_wick / max(body, 0.0001),
                "price": bar["low"]
            })
    
    return {
        "imbalances": imbalances[-10:],  # Last 10 imbalances
        "absorption_zones": absorption_zones[-5:],  # Last 5 absorption zones
        "exhaustion_signals": exhaustion_signals[-5:]  # Last 5 exhaustion signals
    }

def detect_liquidity_sweeps(bars: List[dict], lookback: int = 50) -> List[dict]:
    """
    Detect Liquidity Sweeps - when price takes out highs/lows and reverses
    This is a key institutional trading concept
    """
    if not bars or len(bars) < lookback:
        return []
    
    sweeps = []
    recent_bars = bars[-lookback:]
    
    # Find swing highs and lows
    swing_highs = []
    swing_lows = []
    
    for i in range(2, len(recent_bars) - 2):
        # Swing high: higher than 2 bars on each side
        if (recent_bars[i]["high"] > recent_bars[i-1]["high"] and 
            recent_bars[i]["high"] > recent_bars[i-2]["high"] and
            recent_bars[i]["high"] > recent_bars[i+1]["high"] and 
            recent_bars[i]["high"] > recent_bars[i+2]["high"]):
            swing_highs.append({"index": i, "price": recent_bars[i]["high"], "timestamp": recent_bars[i]["timestamp"]})
        
        # Swing low: lower than 2 bars on each side
        if (recent_bars[i]["low"] < recent_bars[i-1]["low"] and 
            recent_bars[i]["low"] < recent_bars[i-2]["low"] and
            recent_bars[i]["low"] < recent_bars[i+1]["low"] and 
            recent_bars[i]["low"] < recent_bars[i+2]["low"]):
            swing_lows.append({"index": i, "price": recent_bars[i]["low"], "timestamp": recent_bars[i]["timestamp"]})
    
    # Check for sweeps in recent bars
    for i in range(len(recent_bars) - 5, len(recent_bars)):
        bar = recent_bars[i]
        
        # Check for high sweep (price goes above swing high then closes below)
        for sh in swing_highs:
            if sh["index"] < i - 2:  # Must be at least 3 bars ago
                if bar["high"] > sh["price"] and bar["close"] < sh["price"]:
                    sweeps.append({
                        "type": "LIQUIDITY_SWEEP_HIGH",
                        "sweep_price": sh["price"],
                        "bar_high": bar["high"],
                        "bar_close": bar["close"],
                        "timestamp": bar["timestamp"],
                        "signal": "BEARISH"
                    })
        
        # Check for low sweep (price goes below swing low then closes above)
        for sl in swing_lows:
            if sl["index"] < i - 2:
                if bar["low"] < sl["price"] and bar["close"] > sl["price"]:
                    sweeps.append({
                        "type": "LIQUIDITY_SWEEP_LOW",
                        "sweep_price": sl["price"],
                        "bar_low": bar["low"],
                        "bar_close": bar["close"],
                        "timestamp": bar["timestamp"],
                        "signal": "BULLISH"
                    })
    
    return sweeps[-5:]  # Return last 5 sweeps

def calculate_market_structure(bars: List[dict]) -> dict:
    """
    Analyze Market Structure - Break of Structure (BOS) and Change of Character (CHoCH)
    """
    if not bars or len(bars) < 20:
        return {"structure": "UNKNOWN", "bos_signals": [], "choch_signals": [], "trend": "NEUTRAL"}
    
    # Find swing points
    swing_highs = []
    swing_lows = []
    
    for i in range(2, len(bars) - 2):
        if (bars[i]["high"] > bars[i-1]["high"] and bars[i]["high"] > bars[i-2]["high"] and
            bars[i]["high"] > bars[i+1]["high"] and bars[i]["high"] > bars[i+2]["high"]):
            swing_highs.append({"index": i, "price": bars[i]["high"]})
        
        if (bars[i]["low"] < bars[i-1]["low"] and bars[i]["low"] < bars[i-2]["low"] and
            bars[i]["low"] < bars[i+1]["low"] and bars[i]["low"] < bars[i+2]["low"]):
            swing_lows.append({"index": i, "price": bars[i]["low"]})
    
    bos_signals = []
    choch_signals = []
    
    # Determine trend based on higher highs/higher lows or lower highs/lower lows
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        recent_highs = swing_highs[-3:]
        recent_lows = swing_lows[-3:]
        
        # Check for uptrend (higher highs and higher lows)
        hh = all(recent_highs[i]["price"] > recent_highs[i-1]["price"] for i in range(1, len(recent_highs)))
        hl = all(recent_lows[i]["price"] > recent_lows[i-1]["price"] for i in range(1, len(recent_lows)))
        
        # Check for downtrend (lower highs and lower lows)
        lh = all(recent_highs[i]["price"] < recent_highs[i-1]["price"] for i in range(1, len(recent_highs)))
        ll = all(recent_lows[i]["price"] < recent_lows[i-1]["price"] for i in range(1, len(recent_lows)))
        
        if hh and hl:
            structure = "BULLISH"
            trend = "UPTREND"
        elif lh and ll:
            structure = "BEARISH"
            trend = "DOWNTREND"
        else:
            structure = "RANGING"
            trend = "SIDEWAYS"
        
        # Check for BOS (Break of Structure)
        current_price = bars[-1]["close"]
        if swing_highs and current_price > swing_highs[-1]["price"]:
            bos_signals.append({
                "type": "BOS_BULLISH",
                "broken_level": swing_highs[-1]["price"],
                "current_price": current_price
            })
        if swing_lows and current_price < swing_lows[-1]["price"]:
            bos_signals.append({
                "type": "BOS_BEARISH",
                "broken_level": swing_lows[-1]["price"],
                "current_price": current_price
            })
    else:
        structure = "UNKNOWN"
        trend = "NEUTRAL"
    
    return {
        "structure": structure,
        "trend": trend,
        "swing_highs": [{"price": sh["price"], "index": sh["index"]} for sh in swing_highs[-5:]],
        "swing_lows": [{"price": sl["price"], "index": sl["index"]} for sl in swing_lows[-5:]],
        "bos_signals": bos_signals,
        "choch_signals": choch_signals
    }

def calculate_session_profiles(bars: List[dict]) -> dict:
    """
    Calculate Session-based Volume Profiles (Asian, London, NY sessions)
    """
    if not bars:
        return {"asian": None, "london": None, "ny": None}
    
    # Session times (UTC)
    # Asian: 00:00 - 08:00
    # London: 08:00 - 16:00
    # NY: 13:00 - 21:00
    
    asian_bars = []
    london_bars = []
    ny_bars = []
    
    for bar in bars:
        try:
            timestamp = bar["timestamp"]
            if isinstance(timestamp, str):
                # Parse hour from timestamp
                parts = timestamp.split(" ")
                if len(parts) >= 2:
                    time_part = parts[1]
                    hour = int(time_part.split(":")[0])
                else:
                    continue
            else:
                continue
            
            if 0 <= hour < 8:
                asian_bars.append(bar)
            elif 8 <= hour < 16:
                london_bars.append(bar)
            elif 13 <= hour < 21:
                ny_bars.append(bar)
        except:
            continue
    
    return {
        "asian": calculate_volume_profile(asian_bars, 20) if len(asian_bars) >= 10 else None,
        "london": calculate_volume_profile(london_bars, 20) if len(london_bars) >= 10 else None,
        "ny": calculate_volume_profile(ny_bars, 20) if len(ny_bars) >= 10 else None,
        "asian_bars": len(asian_bars),
        "london_bars": len(london_bars),
        "ny_bars": len(ny_bars)
    }

def calculate_institutional_levels(bars: List[dict], volume_profile: dict) -> dict:
    """
    Calculate Institutional Trading Levels based on Volume Profile and Price Action
    """
    if not bars or not volume_profile:
        return {"levels": [], "zones": []}
    
    levels = []
    zones = []
    
    # POC is a key institutional level
    if "poc" in volume_profile:
        levels.append({
            "price": volume_profile["poc"],
            "type": "POC",
            "strength": 1.0,
            "description": "Point of Control - Highest volume level"
        })
    
    # VAH and VAL are key levels
    if "vah" in volume_profile:
        levels.append({
            "price": volume_profile["vah"],
            "type": "VAH",
            "strength": 0.8,
            "description": "Value Area High - Upper bound of 70% volume"
        })
    
    if "val" in volume_profile:
        levels.append({
            "price": volume_profile["val"],
            "type": "VAL",
            "strength": 0.8,
            "description": "Value Area Low - Lower bound of 70% volume"
        })
    
    # HVN levels are support/resistance
    for hvn_price in volume_profile.get("hvn_prices", [])[:3]:
        levels.append({
            "price": hvn_price,
            "type": "HVN",
            "strength": 0.7,
            "description": "High Volume Node - Strong support/resistance"
        })
    
    # LVN levels are breakout zones
    for lvn_price in volume_profile.get("lvn_prices", [])[:3]:
        levels.append({
            "price": lvn_price,
            "type": "LVN",
            "strength": 0.5,
            "description": "Low Volume Node - Potential breakout zone"
        })
    
    # Value Area Zone
    if "vah" in volume_profile and "val" in volume_profile:
        zones.append({
            "high": volume_profile["vah"],
            "low": volume_profile["val"],
            "type": "VALUE_AREA",
            "description": "70% of trading activity occurred here"
        })
    
    return {
        "levels": sorted(levels, key=lambda x: x["price"], reverse=True),
        "zones": zones
    }

def calculate_risk_metrics(bars: List[dict], trades: List[dict]) -> dict:
    """
    Calculate Advanced Risk Metrics - VaR, Expected Shortfall, etc.
    """
    if not bars or len(bars) < 20:
        return {
            "var_95": 0, "var_99": 0, "expected_shortfall": 0,
            "volatility": 0, "sharpe_estimate": 0, "max_drawdown": 0
        }
    
    # Calculate returns
    returns = []
    for i in range(1, len(bars)):
        if bars[i-1]["close"] > 0:
            ret = (bars[i]["close"] - bars[i-1]["close"]) / bars[i-1]["close"]
            returns.append(ret)
    
    if not returns:
        return {
            "var_95": 0, "var_99": 0, "expected_shortfall": 0,
            "volatility": 0, "sharpe_estimate": 0, "max_drawdown": 0
        }
    
    returns = np.array(returns)
    
    # Value at Risk (VaR) - 95% and 99% confidence
    var_95 = np.percentile(returns, 5)  # 5th percentile for 95% VaR
    var_99 = np.percentile(returns, 1)  # 1st percentile for 99% VaR
    
    # Expected Shortfall (CVaR) - average of returns below VaR
    es_returns = returns[returns <= var_95]
    expected_shortfall = np.mean(es_returns) if len(es_returns) > 0 else var_95
    
    # Volatility (annualized)
    volatility = np.std(returns) * np.sqrt(252 * 24)  # Hourly data
    
    # Sharpe Ratio estimate (assuming 0 risk-free rate)
    mean_return = np.mean(returns) * 252 * 24
    sharpe_estimate = mean_return / volatility if volatility > 0 else 0
    
    # Max Drawdown
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_drawdown = np.min(drawdowns)
    
    return {
        "var_95": float(var_95 * 100),  # As percentage
        "var_99": float(var_99 * 100),
        "expected_shortfall": float(expected_shortfall * 100),
        "volatility": float(volatility * 100),
        "sharpe_estimate": float(sharpe_estimate),
        "max_drawdown": float(max_drawdown * 100)
    }

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/api/state")
async def get_state():
    return {
        "capital": state.capital,
        "equity": state.equity,
        "total_pnl": state.total_pnl,
        "total_pnl_pct": (state.total_pnl / 10000) * 100,
        "daily_pnl": state.daily_pnl,
        "open_positions": state.open_positions,
        "closed_trades": state.closed_trades[-50:],
        "regime": state.regime,
        "confluence_score": state.confluence_score,
        "kill_switch_active": state.kill_switch_active,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/prices")
async def get_prices():
    return state.current_prices

@app.get("/api/prices/{symbol}")
async def get_price_history(symbol: str, bars: int = 200):
    history = state.price_history.get(symbol, [])
    return history[-bars:] if history else []

@app.get("/api/volume-profile/{symbol}")
async def get_volume_profile(symbol: str, bars: int = 100, levels: int = 40):
    """Get Volume Profile data for a symbol"""
    history = state.price_history.get(symbol, [])
    if not history:
        return {"error": "No data available"}
    
    recent_bars = history[-bars:]
    profile = calculate_volume_profile(recent_bars, levels)
    return profile

@app.get("/api/vwap/{symbol}")
async def get_vwap(symbol: str, bars: int = 100):
    """Get VWAP data for a symbol"""
    history = state.price_history.get(symbol, [])
    if not history:
        return {"error": "No data available"}
    
    recent_bars = history[-bars:]
    vwap = calculate_vwap(recent_bars)
    return vwap

@app.get("/api/delta/{symbol}")
async def get_delta(symbol: str, bars: int = 100):
    """Get Cumulative Delta data for a symbol"""
    history = state.price_history.get(symbol, [])
    if not history:
        return {"error": "No data available"}
    
    recent_bars = history[-bars:]
    delta = calculate_cumulative_delta(recent_bars)
    return delta

@app.get("/api/chart-data/{symbol}")
async def get_chart_data(symbol: str, bars: int = 100):
    """Get all chart data in one call - OHLCV, Volume Profile, VWAP, Delta, and Institutional Analytics"""
    history = state.price_history.get(symbol, [])
    if not history:
        return {"error": "No data available"}
    
    recent_bars = history[-bars:]
    volume_profile = calculate_volume_profile(recent_bars, 40)
    
    return {
        "candles": recent_bars,
        "volume_profile": volume_profile,
        "vwap": calculate_vwap(recent_bars),
        "delta": calculate_cumulative_delta(recent_bars),
        "current_price": recent_bars[-1]["close"] if recent_bars else 0,
        "order_flow_imbalance": calculate_order_flow_imbalance(recent_bars),
        "footprint": calculate_footprint_analysis(recent_bars),
        "liquidity_sweeps": detect_liquidity_sweeps(recent_bars),
        "market_structure": calculate_market_structure(recent_bars),
        "institutional_levels": calculate_institutional_levels(recent_bars, volume_profile),
        "risk_metrics": calculate_risk_metrics(recent_bars, state.closed_trades)
    }

@app.get("/api/institutional/{symbol}")
async def get_institutional_analysis(symbol: str, bars: int = 200):
    """Get comprehensive institutional-grade analysis"""
    history = state.price_history.get(symbol, [])
    if not history:
        return {"error": "No data available"}
    
    recent_bars = history[-bars:]
    volume_profile = calculate_volume_profile(recent_bars, 50)
    
    return {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "order_flow": {
            "imbalance": calculate_order_flow_imbalance(recent_bars),
            "footprint": calculate_footprint_analysis(recent_bars),
            "liquidity_sweeps": detect_liquidity_sweeps(recent_bars)
        },
        "market_structure": calculate_market_structure(recent_bars),
        "volume_analysis": {
            "profile": volume_profile,
            "session_profiles": calculate_session_profiles(recent_bars)
        },
        "institutional_levels": calculate_institutional_levels(recent_bars, volume_profile),
        "risk_metrics": calculate_risk_metrics(recent_bars, state.closed_trades)
    }

@app.get("/api/risk/{symbol}")
async def get_risk_analysis(symbol: str, bars: int = 200):
    """Get risk metrics for a symbol"""
    history = state.price_history.get(symbol, [])
    if not history:
        return {"error": "No data available"}
    
    recent_bars = history[-bars:]
    return calculate_risk_metrics(recent_bars, state.closed_trades)

@app.get("/api/signals")
async def get_signals():
    return state.signals[-100:]

@app.get("/api/trades")
async def get_trades():
    return state.closed_trades

@app.get("/api/positions")
async def get_positions():
    return state.open_positions

@app.get("/api/performance")
async def get_performance():
    if not state.closed_trades:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "avg_trade": 0,
            "best_trade": 0,
            "worst_trade": 0,
        }
    
    wins = [t for t in state.closed_trades if t.get("pnl", 0) > 0]
    losses = [t for t in state.closed_trades if t.get("pnl", 0) <= 0]
    
    gross_profit = sum(t.get("pnl", 0) for t in wins)
    gross_loss = abs(sum(t.get("pnl", 0) for t in losses))
    
    pnls = [t.get("pnl", 0) for t in state.closed_trades]
    
    return {
        "total_trades": len(state.closed_trades),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": len(wins) / len(state.closed_trades) if state.closed_trades else 0,
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else 0,
        "total_pnl": state.total_pnl,
        "avg_trade": sum(pnls) / len(pnls) if pnls else 0,
        "best_trade": max(pnls) if pnls else 0,
        "worst_trade": min(pnls) if pnls else 0,
    }

@app.get("/api/analysis/{symbol}")
async def get_analysis(symbol: str):
    return {
        "symbol": symbol,
        "regime": state.regime,
        "trend_direction": "BULLISH",
        "trend_strength": 0.75,
        "confluence_score": state.confluence_score,
        "htf_bias": "BULLISH",
        "ltf_signal": "LONG",
        "order_blocks": [
            {"type": "BULLISH", "high": 1.0850, "low": 1.0830, "strength": 0.8},
            {"type": "BEARISH", "high": 1.0920, "low": 1.0900, "strength": 0.6}
        ],
        "fair_value_gaps": [
            {"type": "BULLISH", "high": 1.0870, "low": 1.0860, "fill_pct": 0.3}
        ],
        "liquidity_pools": [
            {"price": 1.0800, "type": "BELOW", "strength": 0.7},
            {"price": 1.0950, "type": "ABOVE", "strength": 0.5}
        ],
        "support_levels": [1.0800, 1.0750, 1.0700],
        "resistance_levels": [1.0900, 1.0950, 1.1000],
        "recommended_action": "WAIT" if state.confluence_score < 0.5 else "LONG",
        "reason_codes": ["MTF_BULLISH_CONFLUENCE", "SMC_BULLISH_BIAS", "REGIME_TRENDING"]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.send_json({
                "type": "state_update",
                "data": {
                    "capital": state.capital,
                    "equity": state.equity,
                    "total_pnl": state.total_pnl,
                    "daily_pnl": state.daily_pnl,
                    "open_positions": len(state.open_positions),
                    "regime": state.regime,
                    "confluence_score": state.confluence_score,
                    "prices": state.current_prices,
                    "timestamp": datetime.now().isoformat()
                }
            })
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.on_event("startup")
async def load_sample_data():
    try:
        import pandas as pd
        
        # Load all symbols
        symbols_files = {
            "EURUSD": "/home/ubuntu/omega_devin/data/eurusd_hourly_2y.csv",
            "GBPUSD": "/home/ubuntu/omega_devin/data/gbpusd_hourly_2y.csv",
            "USDJPY": "/home/ubuntu/omega_devin/data/usdjpy_hourly_2y.csv",
            "AUDUSD": "/home/ubuntu/omega_devin/data/audusd_hourly_2y.csv",
            "XAUUSD": "/home/ubuntu/omega_devin/data/xauusd_hourly_2y.csv"
        }
        
        for symbol, data_file in symbols_files.items():
            if os.path.exists(data_file):
                df = pd.read_csv(data_file)
                bars = []
                # Load more data for better volume profile
                for _, row in df.tail(500).iterrows():
                    # Generate realistic volume if not present
                    vol = float(row["Volume"]) if row["Volume"] > 0 else np.random.randint(500, 5000)
                    bars.append({
                        "timestamp": row["Datetime"],
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": vol
                    })
                state.price_history[symbol] = bars
                state.current_prices[symbol] = bars[-1]["close"] if bars else 1.08
                print(f"Loaded {len(bars)} bars for {symbol}")
        
        # Set default prices if files don't exist
        if not state.current_prices:
            state.current_prices = {
                "EURUSD": 1.0850,
                "GBPUSD": 1.2650,
                "USDJPY": 154.50,
                "AUDUSD": 0.6280,
                "XAUUSD": 2045.00
            }
        
        state.regime = "TRENDING"
        state.confluence_score = 0.72
        
        state.closed_trades = [
            {"symbol": "EURUSD", "side": "LONG", "entry": 1.0820, "exit": 1.0850, "pnl": 30.0, "pnl_pct": 0.3, "exit_reason": "TP1", "timestamp": "2026-01-28 10:00"},
            {"symbol": "GBPUSD", "side": "LONG", "entry": 1.2600, "exit": 1.2650, "pnl": 50.0, "pnl_pct": 0.5, "exit_reason": "TP2", "timestamp": "2026-01-28 11:00"},
            {"symbol": "USDJPY", "side": "SHORT", "entry": 155.00, "exit": 154.50, "pnl": 32.0, "pnl_pct": 0.32, "exit_reason": "TP1", "timestamp": "2026-01-28 12:00"},
            {"symbol": "EURUSD", "side": "LONG", "entry": 1.0840, "exit": 1.0820, "pnl": -20.0, "pnl_pct": -0.2, "exit_reason": "SL", "timestamp": "2026-01-28 13:00"},
            {"symbol": "XAUUSD", "side": "LONG", "entry": 2030.0, "exit": 2045.0, "pnl": 75.0, "pnl_pct": 0.75, "exit_reason": "TP1", "timestamp": "2026-01-28 14:00"},
            {"symbol": "EURUSD", "side": "SHORT", "entry": 1.0870, "exit": 1.0840, "pnl": 30.0, "pnl_pct": 0.3, "exit_reason": "TP1", "timestamp": "2026-01-28 15:00"},
            {"symbol": "GBPUSD", "side": "SHORT", "entry": 1.2680, "exit": 1.2700, "pnl": -20.0, "pnl_pct": -0.2, "exit_reason": "SL", "timestamp": "2026-01-28 16:00"},
            {"symbol": "XAUUSD", "side": "LONG", "entry": 2040.0, "exit": 2065.0, "pnl": 125.0, "pnl_pct": 1.25, "exit_reason": "TP2", "timestamp": "2026-01-28 17:00"},
        ]
        state.total_pnl = sum(t["pnl"] for t in state.closed_trades)
        state.capital = 10000 + state.total_pnl
        state.equity = state.capital
        
        print("Sample data loaded successfully")
    except Exception as e:
        print(f"Error loading sample data: {e}")
        import traceback
        traceback.print_exc()

# ============================================================================
# DEEPCHARTS-STYLE ADVANCED ORDER FLOW ANALYSIS
# Surpassing MMT PRO with institutional-grade features
# ============================================================================

def detect_absorption_patterns(bars: List[dict], window: int = 5) -> List[dict]:
    """
    Detect Absorption patterns - when aggressive orders are absorbed by passive limit orders
    Key signal: High delta (aggression) but price doesn't move = absorption
    """
    if len(bars) < window:
        return []
    
    absorptions = []
    
    for i in range(window, len(bars)):
        recent_bars = bars[i-window:i+1]
        current_bar = bars[i]
        
        # Calculate delta for recent bars
        deltas = []
        for bar in recent_bars:
            is_bullish = bar["close"] >= bar["open"]
            vol = bar.get("volume", 1000)
            delta = vol * 0.2 if is_bullish else -vol * 0.2
            deltas.append(delta)
        
        total_delta = sum(deltas)
        price_change = current_bar["close"] - recent_bars[0]["open"]
        bar_range = max(b["high"] for b in recent_bars) - min(b["low"] for b in recent_bars)
        
        # Absorption: High delta but price doesn't move proportionally
        if bar_range > 0:
            delta_magnitude = abs(total_delta)
            price_movement_ratio = abs(price_change) / bar_range
            
            # Strong delta but weak price movement = absorption
            if delta_magnitude > 500 and price_movement_ratio < 0.3:
                absorption_type = "BULLISH" if total_delta < 0 else "BEARISH"
                # Negative delta + price holds = bullish absorption (buyers absorbing sellers)
                # Positive delta + price holds = bearish absorption (sellers absorbing buyers)
                
                absorptions.append({
                    "bar_index": i,
                    "timestamp": current_bar.get("timestamp", ""),
                    "price": current_bar["close"],
                    "type": absorption_type,
                    "delta": total_delta,
                    "price_change": price_change,
                    "strength": min(100, int(delta_magnitude / 10)),
                    "description": f"{'Buyers' if absorption_type == 'BULLISH' else 'Sellers'} absorbing {'selling' if absorption_type == 'BULLISH' else 'buying'} pressure"
                })
    
    return absorptions


def detect_cvd_divergence(bars: List[dict], lookback: int = 10) -> List[dict]:
    """
    Detect CVD Divergence patterns
    - Bullish: Price makes lower low, CVD makes higher low (sellers exhausted)
    - Bearish: Price makes higher high, CVD makes lower high (buyers exhausted)
    """
    if len(bars) < lookback * 2:
        return []
    
    divergences = []
    cvd = 0
    cvd_values = []
    
    # Calculate CVD for all bars
    for bar in bars:
        is_bullish = bar["close"] >= bar["open"]
        vol = bar.get("volume", 1000)
        delta = vol * 0.2 if is_bullish else -vol * 0.2
        cvd += delta
        cvd_values.append(cvd)
    
    # Look for divergences
    for i in range(lookback * 2, len(bars)):
        # Find local price lows/highs
        recent_prices = [b["low"] for b in bars[i-lookback:i+1]]
        recent_highs = [b["high"] for b in bars[i-lookback:i+1]]
        recent_cvd = cvd_values[i-lookback:i+1]
        
        current_low = bars[i]["low"]
        current_high = bars[i]["high"]
        current_cvd = cvd_values[i]
        
        prev_low = min(recent_prices[:-1])
        prev_high = max(recent_highs[:-1])
        prev_cvd_at_low = min(recent_cvd[:-1])
        prev_cvd_at_high = max(recent_cvd[:-1])
        
        # Bullish divergence: Price lower low, CVD higher low
        if current_low < prev_low and current_cvd > prev_cvd_at_low:
            divergences.append({
                "bar_index": i,
                "timestamp": bars[i].get("timestamp", ""),
                "price": current_low,
                "type": "BULLISH",
                "cvd": current_cvd,
                "description": "Price lower low but CVD higher low - sellers exhausted (Bear Trap)"
            })
        
        # Bearish divergence: Price higher high, CVD lower high
        if current_high > prev_high and current_cvd < prev_cvd_at_high:
            divergences.append({
                "bar_index": i,
                "timestamp": bars[i].get("timestamp", ""),
                "price": current_high,
                "type": "BEARISH",
                "cvd": current_cvd,
                "description": "Price higher high but CVD lower high - buyers exhausted (Bull Trap)"
            })
    
    return divergences


def detect_deep_trades(bars: List[dict], threshold_multiplier: float = 3.0) -> List[dict]:
    """
    Detect Deep Trades (Volume Bubbles) - Large institutional trades
    These are trades significantly larger than average, indicating whale activity
    """
    if len(bars) < 10:
        return []
    
    # Calculate average volume
    volumes = [b.get("volume", 1000) for b in bars]
    avg_volume = sum(volumes) / len(volumes)
    threshold = avg_volume * threshold_multiplier
    
    deep_trades = []
    
    for i, bar in enumerate(bars):
        vol = bar.get("volume", 1000)
        
        if vol > threshold:
            is_bullish = bar["close"] >= bar["open"]
            
            # Size of bubble proportional to volume
            size = min(100, int((vol / threshold) * 30))
            
            deep_trades.append({
                "bar_index": i,
                "timestamp": bar.get("timestamp", ""),
                "price": (bar["high"] + bar["low"]) / 2,
                "volume": vol,
                "type": "BUY" if is_bullish else "SELL",
                "size": size,
                "multiplier": round(vol / avg_volume, 1),
                "description": f"{'Aggressive Buyer' if is_bullish else 'Aggressive Seller'} - {round(vol / avg_volume, 1)}x avg volume"
            })
    
    return deep_trades


def generate_liquidity_heatmap(bars: List[dict], num_price_levels: int = 30) -> dict:
    """
    Generate Liquidity Heatmap data
    Shows where volume has accumulated over time at each price level
    Hot colors = high liquidity, Cold colors = low liquidity
    """
    if len(bars) < 5:
        return {"levels": [], "max_liquidity": 0}
    
    # Get price range
    all_highs = [b["high"] for b in bars]
    all_lows = [b["low"] for b in bars]
    price_high = max(all_highs)
    price_low = min(all_lows)
    price_range = price_high - price_low
    
    if price_range <= 0:
        return {"levels": [], "max_liquidity": 0}
    
    level_size = price_range / num_price_levels
    
    # Initialize heatmap grid: [time_index][price_level] = liquidity
    heatmap = []
    
    for i, bar in enumerate(bars):
        bar_liquidity = []
        vol = bar.get("volume", 1000)
        
        for j in range(num_price_levels):
            level_low = price_low + (j * level_size)
            level_high = level_low + level_size
            
            # Check if bar overlaps with this level
            overlap_low = max(bar["low"], level_low)
            overlap_high = min(bar["high"], level_high)
            
            if overlap_high > overlap_low:
                bar_range = bar["high"] - bar["low"]
                if bar_range > 0:
                    overlap_ratio = (overlap_high - overlap_low) / bar_range
                else:
                    overlap_ratio = 1.0 / num_price_levels
                
                liquidity = vol * overlap_ratio
            else:
                liquidity = 0
            
            bar_liquidity.append({
                "price_low": round(level_low, 5),
                "price_high": round(level_high, 5),
                "price_mid": round((level_low + level_high) / 2, 5),
                "liquidity": int(liquidity)
            })
        
        heatmap.append({
            "bar_index": i,
            "timestamp": bar.get("timestamp", ""),
            "levels": bar_liquidity
        })
    
    # Find max liquidity for color scaling
    max_liquidity = max(
        level["liquidity"] 
        for bar_data in heatmap 
        for level in bar_data["levels"]
    ) if heatmap else 1
    
    # Add normalized values (0-1) for color mapping
    for bar_data in heatmap:
        for level in bar_data["levels"]:
            level["intensity"] = level["liquidity"] / max_liquidity if max_liquidity > 0 else 0
    
    return {
        "heatmap": heatmap,
        "price_high": price_high,
        "price_low": price_low,
        "max_liquidity": max_liquidity,
        "num_levels": num_price_levels
    }


def detect_delta_divergence(bars: List[dict]) -> List[dict]:
    """
    Detect Delta Divergence within candles
    - Negative delta with bullish price = limit buyers absorbing (reversal signal)
    - Positive delta with bearish price = limit sellers absorbing (reversal signal)
    """
    divergences = []
    
    for i, bar in enumerate(bars):
        is_bullish = bar["close"] >= bar["open"]
        vol = bar.get("volume", 1000)
        
        # Estimate delta based on candle structure
        body_size = abs(bar["close"] - bar["open"])
        bar_range = bar["high"] - bar["low"]
        
        if bar_range > 0:
            body_ratio = body_size / bar_range
            
            # Strong body = delta follows price
            # Weak body with wicks = potential absorption
            if body_ratio < 0.3:  # Doji-like candle
                # Check wick direction
                upper_wick = bar["high"] - max(bar["open"], bar["close"])
                lower_wick = min(bar["open"], bar["close"]) - bar["low"]
                
                if upper_wick > lower_wick * 2:
                    # Long upper wick = selling pressure absorbed
                    divergences.append({
                        "bar_index": i,
                        "timestamp": bar.get("timestamp", ""),
                        "price": bar["close"],
                        "type": "BEARISH_ABSORPTION",
                        "description": "Long upper wick - selling pressure being absorbed by limit buyers"
                    })
                elif lower_wick > upper_wick * 2:
                    # Long lower wick = buying pressure absorbed
                    divergences.append({
                        "bar_index": i,
                        "timestamp": bar.get("timestamp", ""),
                        "price": bar["close"],
                        "type": "BULLISH_ABSORPTION",
                        "description": "Long lower wick - buying pressure being absorbed by limit sellers"
                    })
    
    return divergences


def find_real_fvg(bars: List[dict], volume_profile: dict) -> List[dict]:
    """
    Find Real Fair Value Gaps using Fixed Volume Profile
    The real FVG is the specific low-volume node where price will reject
    """
    if not volume_profile or "levels" not in volume_profile:
        return []
    
    fvgs = []
    levels = volume_profile["levels"]
    
    # Find LVN (Low Volume Nodes) - these are the real FVGs
    avg_volume = sum(l["volume"] for l in levels) / len(levels) if levels else 0
    lvn_threshold = avg_volume * 0.3
    
    for level in levels:
        if level["volume"] < lvn_threshold and level["volume"] > 0:
            fvgs.append({
                "price_low": level["price_low"],
                "price_high": level["price_high"],
                "price_mid": level["price_mid"],
                "volume": level["volume"],
                "type": "REAL_FVG",
                "description": f"Low volume node - precise rejection level at {level['price_mid']:.5f}"
            })
    
    return fvgs


def generate_footprint_data(bars: List[dict], tick_size: float = 0.0001) -> List[dict]:
    """
    Generate MMT PRO-style footprint chart data
    Shows volume at each price level within each candle with delta (buy/sell)
    """
    if not bars or len(bars) < 5:
        return []
    
    footprint_candles = []
    
    for i, bar in enumerate(bars):
        volume = bar.get("volume", 1000)
        bar_range = bar["high"] - bar["low"]
        is_bullish = bar["close"] >= bar["open"]
        
        if bar_range <= 0:
            continue
        
        # Determine number of price levels based on range
        # For FX pairs, use appropriate tick sizes
        if bar_range > 1:  # Gold or large moves
            num_levels = min(20, max(5, int(bar_range / 0.5)))
            level_size = bar_range / num_levels
        else:
            num_levels = min(15, max(5, int(bar_range / tick_size / 10)))
            level_size = bar_range / num_levels
        
        price_levels = []
        
        for j in range(num_levels):
            level_low = bar["low"] + (j * level_size)
            level_high = level_low + level_size
            level_mid = (level_low + level_high) / 2
            
            # Distribute volume across levels (more at close, less at extremes)
            close_distance = abs(level_mid - bar["close"]) / bar_range
            open_distance = abs(level_mid - bar["open"]) / bar_range
            
            # Volume distribution: more volume near close and open
            base_vol = volume / num_levels
            vol_multiplier = 1.0 + (1.0 - min(close_distance, open_distance)) * 0.5
            level_volume = base_vol * vol_multiplier
            
            # Delta calculation: estimate buy vs sell based on candle structure
            # Bullish candles have more buying at lower prices, selling at higher
            # Bearish candles have more selling at lower prices, buying at higher
            position_in_candle = (level_mid - bar["low"]) / bar_range
            
            if is_bullish:
                # Bullish: more buying at bottom, more selling at top
                buy_ratio = 0.6 - (position_in_candle * 0.3)
                sell_ratio = 0.4 + (position_in_candle * 0.3)
            else:
                # Bearish: more selling at bottom, more buying at top
                buy_ratio = 0.4 + (position_in_candle * 0.3)
                sell_ratio = 0.6 - (position_in_candle * 0.3)
            
            buy_volume = int(level_volume * buy_ratio)
            sell_volume = int(level_volume * sell_ratio)
            delta = buy_volume - sell_volume
            
            # Detect imbalance (3:1 ratio or more)
            is_imbalance = False
            imbalance_type = None
            if buy_volume > 0 and sell_volume > 0:
                ratio = max(buy_volume, sell_volume) / min(buy_volume, sell_volume)
                if ratio >= 3:
                    is_imbalance = True
                    imbalance_type = "BUY" if buy_volume > sell_volume else "SELL"
            
            price_levels.append({
                "price_low": round(level_low, 5),
                "price_high": round(level_high, 5),
                "price_mid": round(level_mid, 5),
                "buy_volume": buy_volume,
                "sell_volume": sell_volume,
                "delta": delta,
                "total_volume": buy_volume + sell_volume,
                "is_imbalance": is_imbalance,
                "imbalance_type": imbalance_type
            })
        
        # Calculate candle-level metrics
        total_buy = sum(l["buy_volume"] for l in price_levels)
        total_sell = sum(l["sell_volume"] for l in price_levels)
        candle_delta = total_buy - total_sell
        
        # Detect stacked imbalances (3+ consecutive same-direction imbalances)
        stacked_imbalances = []
        current_stack = []
        for level in price_levels:
            if level["is_imbalance"]:
                if not current_stack or current_stack[-1]["imbalance_type"] == level["imbalance_type"]:
                    current_stack.append(level)
                else:
                    if len(current_stack) >= 3:
                        stacked_imbalances.append({
                            "type": current_stack[0]["imbalance_type"],
                            "count": len(current_stack),
                            "price_start": current_stack[0]["price_mid"],
                            "price_end": current_stack[-1]["price_mid"]
                        })
                    current_stack = [level]
            else:
                if len(current_stack) >= 3:
                    stacked_imbalances.append({
                        "type": current_stack[0]["imbalance_type"],
                        "count": len(current_stack),
                        "price_start": current_stack[0]["price_mid"],
                        "price_end": current_stack[-1]["price_mid"]
                    })
                current_stack = []
        
        # Check final stack
        if len(current_stack) >= 3:
            stacked_imbalances.append({
                "type": current_stack[0]["imbalance_type"],
                "count": len(current_stack),
                "price_start": current_stack[0]["price_mid"],
                "price_end": current_stack[-1]["price_mid"]
            })
        
        footprint_candles.append({
            "timestamp": bar.get("timestamp", bar.get("time", "")),
            "open": bar["open"],
            "high": bar["high"],
            "low": bar["low"],
            "close": bar["close"],
            "is_bullish": is_bullish,
            "total_volume": int(volume),
            "total_buy": total_buy,
            "total_sell": total_sell,
            "delta": candle_delta,
            "price_levels": price_levels,
            "stacked_imbalances": stacked_imbalances,
            "has_buy_imbalance": any(l["imbalance_type"] == "BUY" for l in price_levels if l["is_imbalance"]),
            "has_sell_imbalance": any(l["imbalance_type"] == "SELL" for l in price_levels if l["is_imbalance"])
        })
    
    return footprint_candles


def generate_dom_ladder(bars: List[dict], num_levels: int = 10) -> dict:
    """
    Generate simulated DOM (Depth of Market) Ladder
    Shows bid/ask levels with liquidity - BEST IN WORLD feature
    """
    if not bars or len(bars) < 1:
        return {"bids": [], "asks": [], "spread": 0}
    
    current_bar = bars[-1]
    current_price = current_bar["close"]
    
    # Estimate spread based on symbol (tighter for majors)
    avg_range = sum(b["high"] - b["low"] for b in bars[-10:]) / min(10, len(bars))
    spread = avg_range * 0.01  # 1% of average range
    
    bid_price = current_price - spread / 2
    ask_price = current_price + spread / 2
    
    # Generate bid levels (below current price)
    bids = []
    for i in range(num_levels):
        level_price = bid_price - (i * spread * 2)
        # Simulate liquidity - more at round numbers, less at random levels
        base_liquidity = 1000 + (i * 200)
        # Add extra liquidity at "round" levels
        if abs(level_price * 10000) % 10 < 1:
            base_liquidity *= 2.5
        bids.append({
            "price": round(level_price, 5),
            "size": int(base_liquidity * (0.8 + 0.4 * np.random.random())),
            "is_large": base_liquidity > 2000
        })
    
    # Generate ask levels (above current price)
    asks = []
    for i in range(num_levels):
        level_price = ask_price + (i * spread * 2)
        base_liquidity = 1000 + (i * 200)
        if abs(level_price * 10000) % 10 < 1:
            base_liquidity *= 2.5
        asks.append({
            "price": round(level_price, 5),
            "size": int(base_liquidity * (0.8 + 0.4 * np.random.random())),
            "is_large": base_liquidity > 2000
        })
    
    # Find liquidity walls (large orders)
    all_levels = bids + asks
    max_size = max(l["size"] for l in all_levels) if all_levels else 1
    liquidity_walls = [l for l in all_levels if l["size"] > max_size * 0.7]
    
    return {
        "bids": bids,
        "asks": asks,
        "spread": round(spread, 6),
        "mid_price": round(current_price, 5),
        "liquidity_walls": liquidity_walls,
        "total_bid_liquidity": sum(b["size"] for b in bids),
        "total_ask_liquidity": sum(a["size"] for a in asks),
        "imbalance": round((sum(b["size"] for b in bids) - sum(a["size"] for a in asks)) / max(1, sum(b["size"] for b in bids) + sum(a["size"] for a in asks)), 2)
    }


def detect_footprint_patterns(candles: List[dict]) -> List[dict]:
    """
    Detect advanced footprint patterns - BEST IN WORLD feature
    - Finished Auction: Strong close at high/low with volume
    - Unfinished Auction: Weak close, price likely to return
    - Poor High/Low: Rejection at extremes
    - Single Prints: Low volume gaps
    - Excess: Strong rejection with high volume
    """
    if not candles or len(candles) < 3:
        return []
    
    patterns = []
    
    for i, candle in enumerate(candles):
        bar_range = candle["high"] - candle["low"]
        if bar_range <= 0:
            continue
            
        body_size = abs(candle["close"] - candle["open"])
        body_ratio = body_size / bar_range
        close_position = (candle["close"] - candle["low"]) / bar_range
        
        # Finished Auction (Strong close at extreme)
        if body_ratio > 0.7 and (close_position > 0.85 or close_position < 0.15):
            patterns.append({
                "bar_index": i,
                "type": "FINISHED_AUCTION",
                "direction": "BULLISH" if close_position > 0.5 else "BEARISH",
                "price": candle["close"],
                "description": f"Strong {'bullish' if close_position > 0.5 else 'bearish'} close - auction complete, trend likely to continue"
            })
        
        # Unfinished Auction (Weak close, doji-like)
        elif body_ratio < 0.3 and 0.3 < close_position < 0.7:
            patterns.append({
                "bar_index": i,
                "type": "UNFINISHED_AUCTION",
                "direction": "NEUTRAL",
                "price": candle["close"],
                "description": "Weak close - unfinished business, price likely to return to this level"
            })
        
        # Poor High (Rejection at top)
        upper_wick = candle["high"] - max(candle["open"], candle["close"])
        if upper_wick > bar_range * 0.4 and candle.get("delta", 0) < 0:
            patterns.append({
                "bar_index": i,
                "type": "POOR_HIGH",
                "direction": "BEARISH",
                "price": candle["high"],
                "description": "Rejection at high - sellers absorbed buyers, potential reversal"
            })
        
        # Poor Low (Rejection at bottom)
        lower_wick = min(candle["open"], candle["close"]) - candle["low"]
        if lower_wick > bar_range * 0.4 and candle.get("delta", 0) > 0:
            patterns.append({
                "bar_index": i,
                "type": "POOR_LOW",
                "direction": "BULLISH",
                "price": candle["low"],
                "description": "Rejection at low - buyers absorbed sellers, potential reversal"
            })
        
        # Excess (Strong rejection with high volume)
        if i > 0:
            prev_vol = candles[i-1].get("total_volume", 1000)
            curr_vol = candle.get("total_volume", 1000)
            if curr_vol > prev_vol * 1.5:
                if upper_wick > bar_range * 0.5:
                    patterns.append({
                        "bar_index": i,
                        "type": "EXCESS_HIGH",
                        "direction": "BEARISH",
                        "price": candle["high"],
                        "description": "Excess at high - massive rejection with high volume, strong resistance"
                    })
                elif lower_wick > bar_range * 0.5:
                    patterns.append({
                        "bar_index": i,
                        "type": "EXCESS_LOW",
                        "direction": "BULLISH",
                        "price": candle["low"],
                        "description": "Excess at low - massive rejection with high volume, strong support"
                    })
    
    return patterns


def calculate_market_profile_tpo(bars: List[dict], tpo_size: int = 30) -> dict:
    """
    Calculate Market Profile TPO (Time Price Opportunity) - BEST IN WORLD feature
    Shows time spent at each price level, not just volume
    """
    if not bars or len(bars) < 5:
        return {"tpo_levels": [], "poc": 0, "value_area_high": 0, "value_area_low": 0}
    
    # Get price range
    all_highs = [b["high"] for b in bars]
    all_lows = [b["low"] for b in bars]
    price_high = max(all_highs)
    price_low = min(all_lows)
    price_range = price_high - price_low
    
    if price_range <= 0:
        return {"tpo_levels": [], "poc": 0, "value_area_high": 0, "value_area_low": 0}
    
    # Create TPO levels
    num_levels = tpo_size
    level_size = price_range / num_levels
    tpo_counts = [0] * num_levels
    
    # Count time (bars) at each level
    for bar in bars:
        for i in range(num_levels):
            level_low = price_low + (i * level_size)
            level_high = level_low + level_size
            
            # Check if bar touched this level
            if bar["low"] <= level_high and bar["high"] >= level_low:
                tpo_counts[i] += 1
    
    # Find POC (level with most time)
    max_tpo = max(tpo_counts)
    poc_idx = tpo_counts.index(max_tpo)
    poc_price = price_low + (poc_idx + 0.5) * level_size
    
    # Calculate Value Area (70% of TPOs)
    total_tpo = sum(tpo_counts)
    target_tpo = total_tpo * 0.70
    
    # Expand from POC
    va_low_idx = poc_idx
    va_high_idx = poc_idx
    current_tpo = tpo_counts[poc_idx]
    
    while current_tpo < target_tpo and (va_low_idx > 0 or va_high_idx < num_levels - 1):
        expand_low = tpo_counts[va_low_idx - 1] if va_low_idx > 0 else 0
        expand_high = tpo_counts[va_high_idx + 1] if va_high_idx < num_levels - 1 else 0
        
        if expand_low >= expand_high and va_low_idx > 0:
            va_low_idx -= 1
            current_tpo += expand_low
        elif va_high_idx < num_levels - 1:
            va_high_idx += 1
            current_tpo += expand_high
        else:
            break
    
    va_low = price_low + va_low_idx * level_size
    va_high = price_low + (va_high_idx + 1) * level_size
    
    # Build TPO levels with letters
    tpo_levels = []
    for i in range(num_levels):
        level_low = price_low + (i * level_size)
        level_high = level_low + level_size
        tpo_levels.append({
            "price_low": round(level_low, 5),
            "price_high": round(level_high, 5),
            "price_mid": round((level_low + level_high) / 2, 5),
            "tpo_count": tpo_counts[i],
            "is_poc": i == poc_idx,
            "is_value_area": va_low_idx <= i <= va_high_idx,
            "intensity": tpo_counts[i] / max_tpo if max_tpo > 0 else 0
        })
    
    return {
        "tpo_levels": tpo_levels,
        "poc": round(poc_price, 5),
        "value_area_high": round(va_high, 5),
        "value_area_low": round(va_low, 5),
        "total_tpo": total_tpo,
        "price_high": price_high,
        "price_low": price_low
    }


@app.get("/api/footprint/{symbol}")
def get_footprint_data(symbol: str):
    """Get DeepCharts-style advanced footprint chart data with all order flow analysis"""
    bars = state.price_history.get(symbol, [])
    if not bars:
        return {"candles": [], "cumulative_delta": 0}
    
    # Determine tick size based on symbol
    tick_size = 0.5 if symbol == "XAUUSD" else 0.01 if symbol == "USDJPY" else 0.0001
    
    # Get last 50 candles for footprint
    recent_bars = bars[-50:]
    
    # Generate all advanced analysis
    footprint_candles = generate_footprint_data(recent_bars, tick_size)
    absorptions = detect_absorption_patterns(recent_bars)
    cvd_divergences = detect_cvd_divergence(recent_bars)
    deep_trades = detect_deep_trades(recent_bars)
    heatmap_data = generate_liquidity_heatmap(recent_bars)
    delta_divergences = detect_delta_divergence(recent_bars)
    
    # Calculate volume profile for Real FVG detection
    volume_profile = calculate_volume_profile(recent_bars)
    real_fvgs = find_real_fvg(recent_bars, volume_profile)
    
    # BEST IN WORLD: DOM Ladder
    dom_ladder = generate_dom_ladder(recent_bars)
    
    # BEST IN WORLD: Footprint Patterns
    footprint_patterns = detect_footprint_patterns(footprint_candles)
    
    # BEST IN WORLD: Market Profile TPO
    market_profile = calculate_market_profile_tpo(recent_bars)
    
    # Calculate cumulative delta
    cumulative_delta = sum(c["delta"] for c in footprint_candles)
    
    # Calculate CVD values for chart
    cvd_values = []
    running_cvd = 0
    for c in footprint_candles:
        running_cvd += c["delta"]
        cvd_values.append({
            "timestamp": c["timestamp"],
            "cvd": running_cvd,
            "delta": c["delta"]
        })
    
    return {
        "candles": footprint_candles,
        "cumulative_delta": cumulative_delta,
        "total_candles": len(footprint_candles),
        # DeepCharts Advanced Features
        "absorptions": absorptions,
        "cvd_divergences": cvd_divergences,
        "deep_trades": deep_trades,
        "heatmap": heatmap_data,
        "delta_divergences": delta_divergences,
        "real_fvgs": real_fvgs,
        "cvd_values": cvd_values,
        "volume_profile": volume_profile,
        # BEST IN WORLD Features
        "dom_ladder": dom_ladder,
        "footprint_patterns": footprint_patterns,
        "market_profile": market_profile
    }


# ============================================================================
# PROVENANCE API ENDPOINTS - Data Provenance Firewall
# ============================================================================

@app.get("/api/provenance/status")
def get_provenance_status():
    """Get current provenance status including real DOM connection state"""
    return {
        "real_dom_enabled": dom_manager.real_dom_enabled,
        "dom_status": dom_manager.get_status(),
        "firewall_report": provenance_firewall.get_provenance_report(),
        "blocked_features": provenance_firewall.blocked_features
    }


@app.get("/api/provenance/report")
def get_provenance_report():
    """Get full provenance report for audit"""
    return {
        "provenance_table": {
            name: tier.value for name, tier in FEATURE_PROVENANCE_TABLE.items()
        },
        "firewall_report": provenance_firewall.get_provenance_report(),
        "decision_trace": provenance_firewall.decision_trace[-100:]  # Last 100 traces
    }


@app.get("/api/weave-packet/{symbol}")
def get_weave_packet(symbol: str):
    """
    Get the latest WEAVE_PACKET for a symbol.
    Contains all feature values with provenance tags, decision, and evidence pins.
    """
    bars = state.price_history.get(symbol, [])
    if not bars:
        return {"error": "No data for symbol", "packet": None}
    
    # Get latest bar index
    bar_index = len(bars) - 1
    
    # Check for existing packet
    existing_packet = packet_store.get_by_bar(symbol, bar_index)
    if existing_packet:
        return {"packet": existing_packet.to_dict()}
    
    # Generate new packet with current analysis
    recent_bars = bars[-50:]
    
    # Build features with provenance
    features = {}
    
    # Volume Profile (SYNTHETIC - from candles)
    vp = calculate_volume_profile(recent_bars)
    features["estimated_volume_profile"] = FeatureValue(
        name="estimated_volume_profile",
        value=vp,
        tier="SYNTHETIC",
        source="candle_estimation",
        can_affect_decisions=False,
        render_anchors=[
            RenderAnchor(
                anchor_type="zone",
                price_low=vp.get("value_area_low", 0),
                price_high=vp.get("value_area_high", 0),
                description="Value Area (estimated from candles)"
            )
        ] if vp else []
    )
    
    # Delta (SYNTHETIC - from candles)
    delta_data = calculate_cumulative_delta(recent_bars)
    features["estimated_delta"] = FeatureValue(
        name="estimated_delta",
        value=delta_data,
        tier="SYNTHETIC",
        source="candle_estimation",
        can_affect_decisions=False,
        render_anchors=[
            RenderAnchor(
                anchor_type="candle",
                bar_index=i,
                description=f"Delta: {d.get('delta', 0)}"
            ) for i, d in enumerate(delta_data[-10:])
        ] if delta_data else []
    )
    
    # DOM (check if real or synthetic)
    if dom_manager.is_real_dom_available(symbol):
        real_dom = dom_manager.get_snapshot(symbol)
        if real_dom:
            features["real_dom_bids"] = FeatureValue(
                name="real_dom_bids",
                value=real_dom.bids,
                tier="REAL",
                source="binance_l2_feed",
                can_affect_decisions=True,
                render_anchors=[]
            )
            features["real_dom_asks"] = FeatureValue(
                name="real_dom_asks",
                value=real_dom.asks,
                tier="REAL",
                source="binance_l2_feed",
                can_affect_decisions=True,
                render_anchors=[]
            )
    else:
        # Synthetic DOM - CANNOT affect decisions
        synthetic_dom = get_synthetic_dom_watermarked(symbol, recent_bars)
        features["simulated_dom"] = FeatureValue(
            name="simulated_dom",
            value=synthetic_dom,
            tier="SYNTHETIC",
            source="candle_estimation",
            can_affect_decisions=False,
            render_anchors=[]
        )
    
    # Determine decision based on real data availability
    real_features = {k: v for k, v in features.items() if v.can_affect_decisions}
    has_real_data = len(real_features) > 0
    
    # Check for conflicts
    conflict_info = None
    reason_codes = []
    evidence_pins = []
    resolution_conditions = []
    
    if not has_real_data:
        reason_codes.append(ReasonCode.NO_REAL_DATA)
        evidence_pins.append({
            "pin_id": "no_real_data",
            "text": "No real order flow data available",
            "type": "warning",
            "bar_index": bar_index,
            "price": bars[-1]["close"]
        })
        resolution_conditions.append({
            "condition": "Connect to real L2 feed (REAL_DOM=true)",
            "type": "requirement",
            "anchors": []
        })
    
    # Check for signal conflicts (Volume vs Delta)
    vp_signal = "BULLISH" if vp.get("poc", 0) < bars[-1]["close"] else "BEARISH"
    delta_signal = "BULLISH" if delta_data and delta_data[-1].get("cumulative_delta", 0) > 0 else "BEARISH"
    
    if vp_signal != delta_signal:
        conflict_info = ConflictInfo(
            conflict_type="VOLUME_DELTA_CONFLICT",
            signals_in_conflict=["Volume Profile", "Delta Flow"],
            resolution_conditions=[
                f"WAIT until Volume Profile and Delta align",
                f"Volume says {vp_signal}, Delta says {delta_signal}"
            ],
            resolution_anchors=[
                RenderAnchor(
                    anchor_type="level",
                    price_low=vp.get("poc", 0),
                    price_high=vp.get("poc", 0),
                    description="POC level - watch for acceptance"
                )
            ]
        )
        reason_codes.append(ReasonCode.CONFLICTING_SIGNALS)
        evidence_pins.append({
            "pin_id": "conflict_vp_delta",
            "text": f"CONFLICT: Volume={vp_signal}, Delta={delta_signal}",
            "type": "conflict",
            "bar_index": bar_index,
            "price": vp.get("poc", bars[-1]["close"])
        })
        resolution_conditions.append({
            "condition": f"Wait for {vp_signal} confirmation above POC" if vp_signal == "BULLISH" else f"Wait for {vp_signal} confirmation below POC",
            "type": "resolution",
            "anchors": [{"price": vp.get("poc", 0), "type": "level"}]
        })
    
    # Create packet
    decision = DecisionType.CONFLICT if conflict_info else (
        DecisionType.WAIT if not has_real_data else DecisionType.TRADE
    )
    
    confidence = len(real_features) / max(len(features), 1) * 100
    
    reason_text = "WAIT: " + ", ".join([r.value for r in reason_codes]) if reason_codes else "Ready to trade"
    
    packet = WeavePacket(
        packet_id="",
        timestamp=datetime.utcnow(),
        symbol=symbol,
        timeframe="1H",
        bar_index=bar_index,
        features=features,
        decision=decision,
        confidence=confidence,
        reason_codes=reason_codes,
        reason_text=reason_text,
        invalidation_conditions=[],
        invalidation_anchors=[],
        conflict_info=conflict_info,
        evidence_pins=evidence_pins,
        resolution_conditions=resolution_conditions
    )
    
    # Store packet
    packet_store.store(packet)
    
    return {"packet": packet.to_dict()}


@app.get("/api/replay/{symbol}")
def get_replay_data(symbol: str):
    """Get replay data for timeline scrubbing"""
    packets = packet_store.export_for_replay(symbol)
    return {
        "symbol": symbol,
        "total_frames": len(packets),
        "packets": packets
    }


@app.get("/api/replay/{symbol}/{bar_index}")
def get_replay_frame(symbol: str, bar_index: int):
    """Get a specific replay frame for a bar"""
    packet = packet_store.get_by_bar(symbol, bar_index)
    if packet:
        return {"packet": packet.to_dict()}
    return {"error": "No packet for this bar", "packet": None}


@app.get("/api/dom/{symbol}")
def get_dom_data(symbol: str):
    """
    Get DOM data with provenance.
    Returns REAL DOM if connected, otherwise SYNTHETIC with watermark.
    """
    bars = state.price_history.get(symbol, [])
    
    # Check for real DOM
    if dom_manager.is_real_dom_available(symbol):
        real_dom = dom_manager.get_snapshot(symbol)
        if real_dom:
            return {
                "dom": real_dom.to_dict(),
                "is_real": True,
                "provenance_tier": "REAL",
                "watermark": None,
                "can_affect_decisions": True
            }
    
    # Return synthetic DOM with watermark
    synthetic_dom = get_synthetic_dom_watermarked(symbol, bars[-50:] if bars else [])
    return {
        "dom": synthetic_dom,
        "is_real": False,
        "provenance_tier": "SYNTHETIC",
        "watermark": "SYNTHETIC / EDUCATIONAL ONLY",
        "can_affect_decisions": False,
        "warning": "This DOM is simulated from OHLCV data. DO NOT use for trading decisions."
    }


@app.post("/api/real-dom/start/{symbol}")
async def start_real_dom(symbol: str):
    """Start real DOM feed for a symbol (requires REAL_DOM=true)"""
    if not dom_manager.real_dom_enabled:
        return {
            "success": False,
            "error": "REAL_DOM not enabled. Set REAL_DOM=true environment variable."
        }
    
    success = await dom_manager.start_feed(symbol)
    return {
        "success": success,
        "symbol": symbol,
        "status": dom_manager.get_status()
    }


@app.get("/api/decision/{symbol}")
def get_decision(symbol: str):
    """
    Get current trading decision with full provenance.
    CRITICAL: Only Tier A/B features can affect this decision.
    """
    bars = state.price_history.get(symbol, [])
    if not bars:
        return {
            "decision": "SKIP",
            "confidence": 0,
            "reason": "No data available",
            "can_trade": False,
            "provenance_check": "FAILED - No data"
        }
    
    # Get weave packet (generates decision)
    packet_response = get_weave_packet(symbol)
    packet_data = packet_response.get("packet", {})
    
    if not packet_data:
        return {
            "decision": "SKIP",
            "confidence": 0,
            "reason": "Failed to generate decision packet",
            "can_trade": False,
            "provenance_check": "FAILED"
        }
    
    # Check if we can trade (fail-closed)
    can_trade = dom_manager.fail_closed_check(symbol) if dom_manager.real_dom_enabled else False
    
    return {
        "decision": packet_data.get("decision", "WAIT"),
        "confidence": packet_data.get("confidence", 0),
        "reason": packet_data.get("reason_text", ""),
        "can_trade": can_trade,
        "provenance_check": "PASSED" if can_trade else "FAILED - No real data",
        "evidence_pins": packet_data.get("evidence_pins", []),
        "resolution_conditions": packet_data.get("resolution_conditions", []),
        "conflict_info": packet_data.get("conflict_info"),
        "features_used": {
            k: {
                "tier": v.get("tier"),
                "can_affect_decisions": v.get("can_affect_decisions")
            }
            for k, v in packet_data.get("features", {}).items()
        }
    }
