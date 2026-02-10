"""
Session & Trade Management Intelligence Module

This module implements concepts from the 4th YouTube Trader Transcript:
1. Session-Based Trading - NY, London, Asia session awareness
2. Partial Close Management - Automated partial profit taking
3. Break Even Management - Moving SL to BE after partials
4. News Event Awareness - Avoiding high-impact news times
5. Trading Psychology Detection - Revenge trading prevention
6. Single Pair Focus - Specialization optimization

Key Concepts from Transcript:
- "New York session has the best trading conditions" (line 144)
- "Higher timeframe gives you better view of market" (line 146)
- "Partial close at previous high, secure deposit" (line 420-426)
- "One trade per day maximum" rule (line 358)
- "Protect your account is the #1 rule" (lines 337-342)
- "1-5% risk depending on account size" (lines 312-316)
- "Avoid entering trades specifically for news" (lines 377-382)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, time, timedelta
import math


class TradingSession(Enum):
    """Trading sessions"""
    ASIA = "asia"
    LONDON = "london"
    NEW_YORK = "new_york"
    LONDON_NY_OVERLAP = "london_ny_overlap"
    OFF_HOURS = "off_hours"


class SessionQuality(Enum):
    """Session quality for trading"""
    EXCELLENT = "excellent"  # London-NY overlap
    GOOD = "good"  # NY session, London session
    MODERATE = "moderate"  # Asia session
    POOR = "poor"  # Off hours, low liquidity


class NewsImpact(Enum):
    """News event impact level"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class TradeManagementAction(Enum):
    """Trade management actions"""
    HOLD = "hold"
    PARTIAL_CLOSE = "partial_close"
    MOVE_TO_BE = "move_to_be"
    TRAIL_STOP = "trail_stop"
    CLOSE_ALL = "close_all"
    WAIT = "wait"


class PsychologyState(Enum):
    """Trading psychology state"""
    OPTIMAL = "optimal"
    CAUTIOUS = "cautious"
    REVENGE_RISK = "revenge_risk"
    OVERTRADING = "overtrading"
    TILT = "tilt"


@dataclass
class SessionInfo:
    """Current session information"""
    current_session: TradingSession
    session_quality: SessionQuality
    time_until_next_session: int  # minutes
    next_session: TradingSession
    is_overlap: bool
    session_progress: float  # 0-1, how far into session
    recommended_action: str


@dataclass
class NewsEvent:
    """News event information"""
    name: str
    currency: str
    impact: NewsImpact
    time: datetime
    minutes_until: int


@dataclass
class PartialCloseLevel:
    """Partial close level"""
    price: float
    percentage: float  # % of position to close
    reason: str
    triggered: bool = False


@dataclass
class TradeManagementPlan:
    """Complete trade management plan"""
    # Partial close levels
    partial_levels: List[PartialCloseLevel]
    
    # Break even
    move_to_be_price: float
    be_triggered: bool
    
    # Trailing stop
    trail_stop_enabled: bool
    trail_stop_distance: float
    current_trail_stop: float
    
    # Risk management
    max_daily_loss: float
    max_daily_trades: int
    current_daily_pnl: float
    trades_today: int
    
    # Psychology
    psychology_state: PsychologyState
    can_trade: bool
    wait_until: Optional[datetime]
    
    # Reasoning
    reasoning: List[str]


@dataclass
class SessionTradeAnalysis:
    """Complete session and trade management analysis"""
    # Session info
    session_info: SessionInfo
    
    # News awareness
    upcoming_news: List[NewsEvent]
    news_warning: bool
    avoid_trading_until: Optional[datetime]
    
    # Trade management
    management_plan: TradeManagementPlan
    recommended_action: TradeManagementAction
    
    # Signal
    signal: str  # "TRADE", "WAIT", "CLOSE", "MANAGE"
    confidence: float
    
    # Reasoning
    reasoning: List[str]


class SessionTradeManagementIntelligence:
    """
    Session & Trade Management Intelligence
    
    Implements practical trade management concepts from the 4th YouTube transcript:
    - Session timing awareness
    - Partial close automation
    - Break even management
    - News event awareness
    - Trading psychology detection
    """
    
    # Session times (UTC)
    SESSION_TIMES = {
        TradingSession.ASIA: (time(0, 0), time(9, 0)),
        TradingSession.LONDON: (time(7, 0), time(16, 0)),
        TradingSession.NEW_YORK: (time(12, 0), time(21, 0)),
        TradingSession.LONDON_NY_OVERLAP: (time(12, 0), time(16, 0)),
    }
    
    # Session quality ratings
    SESSION_QUALITY = {
        TradingSession.LONDON_NY_OVERLAP: SessionQuality.EXCELLENT,
        TradingSession.NEW_YORK: SessionQuality.GOOD,
        TradingSession.LONDON: SessionQuality.GOOD,
        TradingSession.ASIA: SessionQuality.MODERATE,
        TradingSession.OFF_HOURS: SessionQuality.POOR,
    }
    
    # Default partial close levels (from transcript)
    DEFAULT_PARTIAL_LEVELS = [
        (0.5, 0.35),  # At 50% to TP, close 35%
        (0.75, 0.35),  # At 75% to TP, close another 35%
        (1.0, 0.30),  # At TP, close remaining 30%
    ]
    
    # Risk management rules (from transcript)
    MAX_DAILY_TRADES = 2  # "One trade per day maximum, at most two" (line 358)
    MAX_DAILY_LOSS_PERCENT = 0.05  # 5% max daily loss
    MIN_ACCOUNT_SIZE_FOR_PERCENT_RISK = 1000  # Below this, use fixed risk
    
    def __init__(
        self,
        account_balance: float = 10000,
        risk_per_trade: float = 0.02,
        max_daily_trades: int = 2
    ):
        """
        Initialize Session Trade Management Intelligence
        
        Args:
            account_balance: Trading account balance
            risk_per_trade: Risk per trade as decimal (0.02 = 2%)
            max_daily_trades: Maximum trades per day
        """
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self.max_daily_trades = max_daily_trades
        
        # Daily tracking
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.losses_today = 0
        self.last_trade_result = None  # "win" or "loss"
        self.consecutive_losses = 0
        
    def analyze(
        self,
        bars: List[Dict[str, Any]],
        current_time: Optional[datetime] = None,
        open_position: Optional[Dict[str, Any]] = None,
        daily_trades: int = 0,
        daily_pnl: float = 0.0,
        last_trade_result: Optional[str] = None
    ) -> SessionTradeAnalysis:
        """
        Perform complete session and trade management analysis
        
        Args:
            bars: OHLCV bars
            current_time: Current time (defaults to now)
            open_position: Current open position info (if any)
            daily_trades: Number of trades taken today
            daily_pnl: Today's P&L
            last_trade_result: Result of last trade ("win" or "loss")
            
        Returns:
            SessionTradeAnalysis with complete management plan
        """
        if current_time is None:
            current_time = datetime.utcnow()
            
        reasoning = []
        
        # Update tracking
        self.trades_today = daily_trades
        self.daily_pnl = daily_pnl
        self.last_trade_result = last_trade_result
        
        # 1. Analyze current session
        session_info = self._analyze_session(current_time)
        reasoning.append(f"Session: {session_info.current_session.value} ({session_info.session_quality.value} quality)")
        
        # 2. Check for upcoming news events
        upcoming_news = self._get_upcoming_news(current_time)
        news_warning = any(n.impact == NewsImpact.HIGH and n.minutes_until < 30 for n in upcoming_news)
        avoid_until = None
        
        if news_warning:
            high_impact_news = [n for n in upcoming_news if n.impact == NewsImpact.HIGH]
            if high_impact_news:
                avoid_until = high_impact_news[0].time + timedelta(minutes=30)
                reasoning.append(f"WARNING: High impact news in {high_impact_news[0].minutes_until} minutes - avoid trading")
        
        # 3. Analyze psychology state
        psychology_state = self._analyze_psychology(daily_trades, daily_pnl, last_trade_result)
        reasoning.append(f"Psychology: {psychology_state.value}")
        
        # 4. Create trade management plan
        management_plan = self._create_management_plan(
            bars, open_position, psychology_state, daily_trades, daily_pnl
        )
        
        # 5. Determine recommended action
        recommended_action, action_reasoning = self._determine_action(
            session_info, news_warning, psychology_state, open_position, management_plan
        )
        reasoning.extend(action_reasoning)
        
        # 6. Determine overall signal
        signal, confidence = self._determine_signal(
            session_info, news_warning, psychology_state, management_plan
        )
        
        return SessionTradeAnalysis(
            session_info=session_info,
            upcoming_news=upcoming_news,
            news_warning=news_warning,
            avoid_trading_until=avoid_until,
            management_plan=management_plan,
            recommended_action=recommended_action,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _analyze_session(self, current_time: datetime) -> SessionInfo:
        """Analyze current trading session"""
        current_utc_time = current_time.time()
        
        # Check for London-NY overlap first (highest priority)
        overlap_start, overlap_end = self.SESSION_TIMES[TradingSession.LONDON_NY_OVERLAP]
        if overlap_start <= current_utc_time <= overlap_end:
            current_session = TradingSession.LONDON_NY_OVERLAP
            session_quality = SessionQuality.EXCELLENT
            is_overlap = True
            
            # Calculate progress through overlap
            overlap_duration = (datetime.combine(datetime.today(), overlap_end) - 
                              datetime.combine(datetime.today(), overlap_start)).seconds / 60
            elapsed = (datetime.combine(datetime.today(), current_utc_time) - 
                      datetime.combine(datetime.today(), overlap_start)).seconds / 60
            session_progress = elapsed / overlap_duration
            
            # Next session is pure NY
            next_session = TradingSession.NEW_YORK
            time_until_next = int(overlap_duration - elapsed)
            
        else:
            is_overlap = False
            current_session = TradingSession.OFF_HOURS
            session_quality = SessionQuality.POOR
            
            # Check each session
            for session, (start, end) in self.SESSION_TIMES.items():
                if session == TradingSession.LONDON_NY_OVERLAP:
                    continue
                if start <= current_utc_time <= end:
                    current_session = session
                    session_quality = self.SESSION_QUALITY[session]
                    
                    # Calculate progress
                    duration = (datetime.combine(datetime.today(), end) - 
                               datetime.combine(datetime.today(), start)).seconds / 60
                    elapsed = (datetime.combine(datetime.today(), current_utc_time) - 
                              datetime.combine(datetime.today(), start)).seconds / 60
                    session_progress = elapsed / duration
                    break
            else:
                session_progress = 0.0
            
            # Determine next session
            next_session, time_until_next = self._get_next_session(current_utc_time)
        
        # Determine recommended action based on session
        if session_quality == SessionQuality.EXCELLENT:
            recommended_action = "TRADE - Best session for entries"
        elif session_quality == SessionQuality.GOOD:
            recommended_action = "TRADE - Good session conditions"
        elif session_quality == SessionQuality.MODERATE:
            recommended_action = "CAUTION - Lower liquidity, wider spreads possible"
        else:
            recommended_action = "WAIT - Off hours, avoid new entries"
        
        return SessionInfo(
            current_session=current_session,
            session_quality=session_quality,
            time_until_next_session=time_until_next,
            next_session=next_session,
            is_overlap=is_overlap,
            session_progress=session_progress,
            recommended_action=recommended_action
        )
    
    def _get_next_session(self, current_time: time) -> Tuple[TradingSession, int]:
        """Get next trading session and time until it starts"""
        sessions_order = [
            (TradingSession.ASIA, time(0, 0)),
            (TradingSession.LONDON, time(7, 0)),
            (TradingSession.LONDON_NY_OVERLAP, time(12, 0)),
            (TradingSession.NEW_YORK, time(12, 0)),
        ]
        
        current_minutes = current_time.hour * 60 + current_time.minute
        
        for session, start_time in sessions_order:
            start_minutes = start_time.hour * 60 + start_time.minute
            if start_minutes > current_minutes:
                return session, start_minutes - current_minutes
        
        # Wrap to next day's Asia session
        return TradingSession.ASIA, (24 * 60 - current_minutes)
    
    def _get_upcoming_news(self, current_time: datetime) -> List[NewsEvent]:
        """Get upcoming news events (simulated for now)"""
        # In production, this would fetch from a news calendar API
        # For now, return empty list - can be extended with real news data
        return []
    
    def _analyze_psychology(
        self,
        daily_trades: int,
        daily_pnl: float,
        last_trade_result: Optional[str]
    ) -> PsychologyState:
        """
        Analyze trading psychology state
        
        Based on transcript concepts:
        - "Revenge trading is the biggest enemy" (lines 349-365)
        - "One trade per day maximum" rule (line 358)
        - "Emotions affect strategy execution" (lines 238-240)
        """
        # Check for overtrading
        if daily_trades >= self.max_daily_trades:
            return PsychologyState.OVERTRADING
        
        # Check for tilt (large daily loss)
        max_daily_loss = self.account_balance * self.MAX_DAILY_LOSS_PERCENT
        if daily_pnl < -max_daily_loss:
            return PsychologyState.TILT
        
        # Check for revenge trading risk
        if last_trade_result == "loss":
            self.consecutive_losses += 1
            if self.consecutive_losses >= 2:
                return PsychologyState.REVENGE_RISK
            return PsychologyState.CAUTIOUS
        elif last_trade_result == "win":
            self.consecutive_losses = 0
        
        # Check for moderate loss
        if daily_pnl < -max_daily_loss * 0.5:
            return PsychologyState.CAUTIOUS
        
        return PsychologyState.OPTIMAL
    
    def _create_management_plan(
        self,
        bars: List[Dict[str, Any]],
        open_position: Optional[Dict[str, Any]],
        psychology_state: PsychologyState,
        daily_trades: int,
        daily_pnl: float
    ) -> TradeManagementPlan:
        """
        Create trade management plan
        
        Based on transcript concepts:
        - "Partial close at previous high, secure deposit" (line 420-426)
        - "Move stop loss to break even after partial" (line 426)
        - "Protect your account is the #1 rule" (lines 337-342)
        """
        reasoning = []
        
        # Calculate partial close levels
        partial_levels = []
        if open_position:
            entry = open_position.get("entry_price", 0)
            tp = open_position.get("take_profit", 0)
            sl = open_position.get("stop_loss", 0)
            direction = open_position.get("direction", "LONG")
            
            if entry > 0 and tp > 0:
                total_distance = abs(tp - entry)
                
                for progress, close_pct in self.DEFAULT_PARTIAL_LEVELS:
                    if direction == "LONG":
                        partial_price = entry + (total_distance * progress)
                    else:
                        partial_price = entry - (total_distance * progress)
                    
                    partial_levels.append(PartialCloseLevel(
                        price=partial_price,
                        percentage=close_pct,
                        reason=f"Partial at {progress:.0%} to TP",
                        triggered=False
                    ))
                
                # Move to BE price (after first partial)
                if direction == "LONG":
                    move_to_be_price = entry + (total_distance * 0.5)
                else:
                    move_to_be_price = entry - (total_distance * 0.5)
                    
                reasoning.append(f"Partial close plan: 35% at 50%, 35% at 75%, 30% at TP")
                reasoning.append(f"Move to BE after first partial at {move_to_be_price:.5f}")
        else:
            move_to_be_price = 0.0
        
        # Determine if can trade based on psychology
        can_trade = psychology_state in [PsychologyState.OPTIMAL, PsychologyState.CAUTIOUS]
        wait_until = None
        
        if psychology_state == PsychologyState.OVERTRADING:
            reasoning.append("STOP: Maximum daily trades reached")
            can_trade = False
        elif psychology_state == PsychologyState.TILT:
            reasoning.append("STOP: Daily loss limit reached - no more trading today")
            can_trade = False
        elif psychology_state == PsychologyState.REVENGE_RISK:
            reasoning.append("WARNING: Revenge trading risk - wait 30 minutes before next trade")
            wait_until = datetime.utcnow() + timedelta(minutes=30)
            can_trade = False
        
        # Calculate max daily loss
        max_daily_loss = self.account_balance * self.MAX_DAILY_LOSS_PERCENT
        
        return TradeManagementPlan(
            partial_levels=partial_levels,
            move_to_be_price=move_to_be_price,
            be_triggered=False,
            trail_stop_enabled=True,
            trail_stop_distance=0.0,
            current_trail_stop=0.0,
            max_daily_loss=max_daily_loss,
            max_daily_trades=self.max_daily_trades,
            current_daily_pnl=daily_pnl,
            trades_today=daily_trades,
            psychology_state=psychology_state,
            can_trade=can_trade,
            wait_until=wait_until,
            reasoning=reasoning
        )
    
    def _determine_action(
        self,
        session_info: SessionInfo,
        news_warning: bool,
        psychology_state: PsychologyState,
        open_position: Optional[Dict[str, Any]],
        management_plan: TradeManagementPlan
    ) -> Tuple[TradeManagementAction, List[str]]:
        """Determine recommended trade management action"""
        reasoning = []
        
        # If news warning, close or wait
        if news_warning:
            if open_position:
                reasoning.append("High impact news approaching - consider closing position")
                return TradeManagementAction.CLOSE_ALL, reasoning
            else:
                reasoning.append("High impact news approaching - wait before entering")
                return TradeManagementAction.WAIT, reasoning
        
        # If psychology not optimal, wait
        if not management_plan.can_trade:
            reasoning.append(f"Psychology state: {psychology_state.value} - wait before trading")
            return TradeManagementAction.WAIT, reasoning
        
        # If poor session quality, wait
        if session_info.session_quality == SessionQuality.POOR:
            reasoning.append("Off hours - wait for better session")
            return TradeManagementAction.WAIT, reasoning
        
        # If position open, manage it
        if open_position:
            current_price = open_position.get("current_price", 0)
            entry = open_position.get("entry_price", 0)
            direction = open_position.get("direction", "LONG")
            
            # Check partial close levels
            for level in management_plan.partial_levels:
                if not level.triggered:
                    if direction == "LONG" and current_price >= level.price:
                        reasoning.append(f"Price reached partial level {level.price:.5f} - take {level.percentage:.0%} profit")
                        return TradeManagementAction.PARTIAL_CLOSE, reasoning
                    elif direction == "SHORT" and current_price <= level.price:
                        reasoning.append(f"Price reached partial level {level.price:.5f} - take {level.percentage:.0%} profit")
                        return TradeManagementAction.PARTIAL_CLOSE, reasoning
            
            # Check move to BE
            if not management_plan.be_triggered:
                if direction == "LONG" and current_price >= management_plan.move_to_be_price:
                    reasoning.append(f"Price above BE level - move stop to break even")
                    return TradeManagementAction.MOVE_TO_BE, reasoning
                elif direction == "SHORT" and current_price <= management_plan.move_to_be_price:
                    reasoning.append(f"Price below BE level - move stop to break even")
                    return TradeManagementAction.MOVE_TO_BE, reasoning
            
            reasoning.append("Position in profit - hold and manage")
            return TradeManagementAction.HOLD, reasoning
        
        # No position, good conditions
        reasoning.append(f"Session: {session_info.session_quality.value} - ready for entries")
        return TradeManagementAction.HOLD, reasoning
    
    def _determine_signal(
        self,
        session_info: SessionInfo,
        news_warning: bool,
        psychology_state: PsychologyState,
        management_plan: TradeManagementPlan
    ) -> Tuple[str, float]:
        """Determine overall signal and confidence"""
        # Base confidence on session quality
        session_confidence = {
            SessionQuality.EXCELLENT: 0.95,
            SessionQuality.GOOD: 0.80,
            SessionQuality.MODERATE: 0.60,
            SessionQuality.POOR: 0.30,
        }
        
        confidence = session_confidence.get(session_info.session_quality, 0.5)
        
        # Reduce confidence for news warning
        if news_warning:
            confidence *= 0.5
            return "WAIT", confidence
        
        # Reduce confidence for psychology issues
        if psychology_state == PsychologyState.TILT:
            return "CLOSE", 0.1
        elif psychology_state == PsychologyState.OVERTRADING:
            return "WAIT", 0.2
        elif psychology_state == PsychologyState.REVENGE_RISK:
            confidence *= 0.6
            return "WAIT", confidence
        elif psychology_state == PsychologyState.CAUTIOUS:
            confidence *= 0.8
        
        # Check if can trade
        if not management_plan.can_trade:
            return "WAIT", confidence * 0.5
        
        # Good conditions
        if session_info.session_quality in [SessionQuality.EXCELLENT, SessionQuality.GOOD]:
            return "TRADE", confidence
        elif session_info.session_quality == SessionQuality.MODERATE:
            return "TRADE", confidence
        else:
            return "WAIT", confidence
    
    def get_optimal_risk_percent(self, account_balance: float) -> float:
        """
        Get optimal risk percent based on account size
        
        From transcript: "1-5% risk depending on account size" (lines 312-316)
        """
        if account_balance < 100:
            # Very small account - use fixed dollar risk
            return 0.10  # 10% for tiny accounts
        elif account_balance < 500:
            return 0.05  # 5% for small accounts
        elif account_balance < 1000:
            return 0.03  # 3% for medium-small accounts
        elif account_balance < 5000:
            return 0.02  # 2% for medium accounts
        else:
            return 0.01  # 1% for larger accounts
    
    def should_trade_now(
        self,
        current_time: Optional[datetime] = None,
        daily_trades: int = 0,
        daily_pnl: float = 0.0,
        last_trade_result: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Quick check if trading is recommended now
        
        Returns:
            Tuple of (should_trade, reason)
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Check session
        session_info = self._analyze_session(current_time)
        if session_info.session_quality == SessionQuality.POOR:
            return False, f"Off hours - wait for {session_info.next_session.value} session"
        
        # Check psychology
        psychology = self._analyze_psychology(daily_trades, daily_pnl, last_trade_result)
        if psychology == PsychologyState.TILT:
            return False, "Daily loss limit reached - no more trading today"
        elif psychology == PsychologyState.OVERTRADING:
            return False, "Maximum daily trades reached"
        elif psychology == PsychologyState.REVENGE_RISK:
            return False, "Revenge trading risk - wait 30 minutes"
        
        # Good to trade
        return True, f"Good conditions - {session_info.current_session.value} session ({session_info.session_quality.value})"
    
    def update_account(self, new_balance: float) -> None:
        """Update account balance"""
        self.account_balance = new_balance
    
    def reset_daily_stats(self) -> None:
        """Reset daily statistics (call at start of new trading day)"""
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.losses_today = 0
        self.consecutive_losses = 0
        self.last_trade_result = None


def test_session_trade_management():
    """Test the Session Trade Management Intelligence"""
    print("Testing Session Trade Management Intelligence...")
    
    # Create test bars
    bars = []
    base_price = 1.1000
    for i in range(100):
        bars.append({
            "open": base_price + i * 0.0001,
            "high": base_price + i * 0.0001 + 0.0005,
            "low": base_price + i * 0.0001 - 0.0003,
            "close": base_price + i * 0.0001 + 0.0002,
            "volume": 1000 + i * 10
        })
    
    # Initialize intelligence
    stm = SessionTradeManagementIntelligence(
        account_balance=10000,
        risk_per_trade=0.02,
        max_daily_trades=2
    )
    
    # Test 1: Normal conditions
    print("\n1. Testing normal conditions...")
    analysis = stm.analyze(bars, daily_trades=0, daily_pnl=0.0)
    print(f"   Session: {analysis.session_info.current_session.value}")
    print(f"   Quality: {analysis.session_info.session_quality.value}")
    print(f"   Signal: {analysis.signal}")
    print(f"   Confidence: {analysis.confidence:.2%}")
    print(f"   Can Trade: {analysis.management_plan.can_trade}")
    
    # Test 2: After a loss
    print("\n2. Testing after a loss...")
    analysis = stm.analyze(bars, daily_trades=1, daily_pnl=-100, last_trade_result="loss")
    print(f"   Psychology: {analysis.management_plan.psychology_state.value}")
    print(f"   Signal: {analysis.signal}")
    print(f"   Can Trade: {analysis.management_plan.can_trade}")
    
    # Test 3: Overtrading check
    print("\n3. Testing overtrading...")
    analysis = stm.analyze(bars, daily_trades=3, daily_pnl=50)
    print(f"   Psychology: {analysis.management_plan.psychology_state.value}")
    print(f"   Signal: {analysis.signal}")
    print(f"   Can Trade: {analysis.management_plan.can_trade}")
    
    # Test 4: With open position
    print("\n4. Testing with open position...")
    open_position = {
        "entry_price": 1.1000,
        "take_profit": 1.1100,
        "stop_loss": 1.0950,
        "direction": "LONG",
        "current_price": 1.1060
    }
    analysis = stm.analyze(bars, open_position=open_position)
    print(f"   Recommended Action: {analysis.recommended_action.value}")
    print(f"   Partial Levels: {len(analysis.management_plan.partial_levels)}")
    for level in analysis.management_plan.partial_levels:
        print(f"      - {level.price:.5f}: {level.percentage:.0%} ({level.reason})")
    
    # Test 5: Optimal risk calculation
    print("\n5. Testing optimal risk calculation...")
    for balance in [50, 200, 500, 1000, 5000, 10000]:
        risk = stm.get_optimal_risk_percent(balance)
        print(f"   ${balance}: {risk:.1%} risk")
    
    print("\nSession Trade Management Intelligence tests passed!")


if __name__ == "__main__":
    test_session_trade_management()
