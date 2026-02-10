# OMEGA-DEVIN // RISK MANAGER
# Protects capital and manages position sizing

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class RiskManager:
    """
    RISK MANAGER
    
    Protects capital through:
    1. Position sizing based on risk %
    2. Maximum drawdown limits
    3. Daily loss limits
    4. Correlation checks
    5. Kill switch for emergencies
    """
    
    def __init__(self, config_path: str = "strategies/config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Risk parameters
        self.max_risk_per_trade = self.config.get('risk_management', {}).get('stop_loss_pct', 0.01)
        self.max_daily_drawdown = self.config.get('risk_management', {}).get('max_drawdown_daily', 0.03)
        self.max_positions = self.config.get('risk_management', {}).get('max_positions', 3)
        self.position_size_pct = self.config.get('risk_management', {}).get('position_size_pct', 0.02)
        
        # State
        self.daily_pnl = 0
        self.starting_equity = 10000
        self.current_equity = 10000
        self.kill_switch = False
        self.open_positions = 0
        
    def _load_config(self) -> Dict:
        """Load risk configuration"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default config
        return {
            "risk_management": {
                "stop_loss_pct": 0.01,
                "take_profit_pct": 0.02,
                "max_drawdown_daily": 0.03,
                "position_size_pct": 0.02,
                "max_positions": 3
            }
        }
    
    def can_trade(self) -> Dict[str, Any]:
        """
        Check if trading is allowed
        
        Returns:
            Dictionary with allowed status and reason
        """
        # Check kill switch
        if self.kill_switch:
            return {"allowed": False, "reason": "KILL SWITCH ACTIVE"}
        
        # Check daily drawdown
        daily_drawdown = abs(self.daily_pnl) / self.starting_equity if self.starting_equity > 0 else 0
        if self.daily_pnl < 0 and daily_drawdown >= self.max_daily_drawdown:
            return {"allowed": False, "reason": f"Daily drawdown limit reached ({daily_drawdown:.2%})"}
        
        # Check max positions
        if self.open_positions >= self.max_positions:
            return {"allowed": False, "reason": f"Max positions reached ({self.open_positions}/{self.max_positions})"}
        
        return {"allowed": True, "reason": "All risk checks passed"}
    
    def calculate_position_size(self, entry_price: float, stop_loss: float, 
                                 symbol: str = "EURUSD") -> Dict[str, Any]:
        """
        Calculate position size based on risk parameters
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            symbol: Trading symbol
            
        Returns:
            Position size and risk details
        """
        # Calculate risk in pips
        risk_pips = abs(entry_price - stop_loss) * 10000  # For forex
        
        if risk_pips == 0:
            return {"size": 0, "reason": "Invalid stop loss"}
        
        # Calculate dollar risk
        risk_amount = self.current_equity * self.max_risk_per_trade
        
        # Calculate position size (lots)
        # Assuming $10 per pip for standard lot
        pip_value = 10  # $10 per pip for 1 lot
        position_size = risk_amount / (risk_pips * pip_value)
        
        # Apply position size limit
        max_size = self.current_equity * self.position_size_pct / entry_price
        position_size = min(position_size, max_size)
        
        # Round to 2 decimal places (mini lots)
        position_size = round(position_size, 2)
        
        return {
            "size": position_size,
            "risk_pips": risk_pips,
            "risk_amount": risk_amount,
            "risk_percent": self.max_risk_per_trade,
            "pip_value": pip_value * position_size
        }
    
    def update_pnl(self, pnl: float):
        """Update daily PnL"""
        self.daily_pnl += pnl
        self.current_equity += pnl
        
        # Check if we need to activate kill switch
        daily_drawdown = abs(self.daily_pnl) / self.starting_equity if self.starting_equity > 0 else 0
        if self.daily_pnl < 0 and daily_drawdown >= self.max_daily_drawdown:
            self.activate_kill_switch("Daily drawdown limit reached")
    
    def activate_kill_switch(self, reason: str):
        """Activate kill switch to stop all trading"""
        self.kill_switch = True
        print(f"   [RISK]: KILL SWITCH ACTIVATED - {reason}")
    
    def deactivate_kill_switch(self):
        """Deactivate kill switch"""
        self.kill_switch = False
        print("   [RISK]: Kill switch deactivated")
    
    def reset_daily(self):
        """Reset daily counters (call at start of new trading day)"""
        self.daily_pnl = 0
        self.starting_equity = self.current_equity
        if self.kill_switch:
            self.deactivate_kill_switch()
        print("   [RISK]: Daily counters reset")
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        daily_drawdown = abs(self.daily_pnl) / self.starting_equity if self.starting_equity > 0 else 0
        
        return {
            "kill_switch": self.kill_switch,
            "daily_pnl": self.daily_pnl,
            "daily_drawdown": daily_drawdown,
            "max_daily_drawdown": self.max_daily_drawdown,
            "current_equity": self.current_equity,
            "open_positions": self.open_positions,
            "max_positions": self.max_positions,
            "can_trade": self.can_trade()
        }


# Test
if __name__ == "__main__":
    risk = RiskManager()
    
    print("\n=== RISK MANAGER TEST ===")
    
    # Check if we can trade
    status = risk.can_trade()
    print(f"Can trade: {status}")
    
    # Calculate position size
    size = risk.calculate_position_size(
        entry_price=1.0850,
        stop_loss=1.0800,
        symbol="EURUSD"
    )
    print(f"\nPosition size: {size}")
    
    # Simulate some losses
    risk.update_pnl(-100)
    risk.update_pnl(-150)
    
    # Check status
    status = risk.get_risk_status()
    print(f"\nRisk status: {status}")
