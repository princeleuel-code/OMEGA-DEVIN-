# OMEGA-DEVIN // TRADE EXECUTION ENGINE
# Handles order placement and management

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class TradeExecutor:
    """
    TRADE EXECUTION ENGINE
    
    Handles:
    1. Order placement (market, limit, stop)
    2. Position management
    3. Order tracking
    4. Trade logging
    
    Supports multiple execution modes:
    - PAPER: Simulated trading (no real money)
    - LIVE: Real trading (requires broker API)
    """
    
    def __init__(self, mode: str = "PAPER", logs_dir: str = "logs"):
        self.mode = mode
        self.logs_dir = logs_dir
        self.positions = {}
        self.orders = {}
        self.trade_history = []
        self.order_counter = 0
        
        # Load existing trade history
        self._load_trade_history()
        
    def place_order(self, symbol: str, side: str, quantity: float, 
                    order_type: str = "MARKET", price: float = None,
                    stop_loss: float = None, take_profit: float = None,
                    reason: str = "") -> Dict[str, Any]:
        """
        Place a new order
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            side: "BUY" or "SELL"
            quantity: Position size
            order_type: "MARKET", "LIMIT", "STOP"
            price: Limit/stop price (required for non-market orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            reason: Reason for the trade
            
        Returns:
            Order confirmation with order_id
        """
        self.order_counter += 1
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.order_counter}"
        
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
            "price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "reason": reason,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "filled_at": None,
            "fill_price": None
        }
        
        self.orders[order_id] = order
        
        if self.mode == "PAPER":
            # Simulate immediate fill for market orders
            if order_type == "MARKET":
                return self._simulate_fill(order_id)
            else:
                print(f"   [EXECUTOR]: Order {order_id} placed - waiting for fill")
                return order
        else:
            # LIVE mode - would connect to broker API
            print(f"   [EXECUTOR]: LIVE mode not implemented - order {order_id} simulated")
            return self._simulate_fill(order_id)
    
    def _simulate_fill(self, order_id: str) -> Dict[str, Any]:
        """Simulate order fill for paper trading"""
        order = self.orders[order_id]
        
        # Simulate fill price (market price or limit price)
        fill_price = order['price'] if order['price'] else self._get_current_price(order['symbol'])
        
        order['status'] = "FILLED"
        order['filled_at'] = datetime.now().isoformat()
        order['fill_price'] = fill_price
        
        # Update position
        self._update_position(order)
        
        print(f"   [EXECUTOR]: Order {order_id} FILLED at {fill_price:.5f}")
        
        return order
    
    def _update_position(self, order: Dict):
        """Update position after order fill"""
        symbol = order['symbol']
        
        if symbol not in self.positions:
            self.positions[symbol] = {
                "symbol": symbol,
                "quantity": 0,
                "avg_price": 0,
                "unrealized_pnl": 0,
                "stop_loss": None,
                "take_profit": None
            }
        
        position = self.positions[symbol]
        
        if order['side'] == "BUY":
            # Add to long position
            new_quantity = position['quantity'] + order['quantity']
            if new_quantity != 0:
                position['avg_price'] = (
                    (position['avg_price'] * position['quantity'] + order['fill_price'] * order['quantity'])
                    / new_quantity
                )
            position['quantity'] = new_quantity
        else:
            # Add to short position (or close long)
            new_quantity = position['quantity'] - order['quantity']
            if new_quantity != 0 and position['quantity'] != 0:
                position['avg_price'] = (
                    (position['avg_price'] * abs(position['quantity']) + order['fill_price'] * order['quantity'])
                    / abs(new_quantity)
                )
            position['quantity'] = new_quantity
        
        # Update stop loss and take profit
        if order['stop_loss']:
            position['stop_loss'] = order['stop_loss']
        if order['take_profit']:
            position['take_profit'] = order['take_profit']
        
        # If position is closed, log the trade
        if position['quantity'] == 0:
            self._log_closed_trade(order)
    
    def _log_closed_trade(self, closing_order: Dict):
        """Log a closed trade to history"""
        trade = {
            "symbol": closing_order['symbol'],
            "side": "LONG" if closing_order['side'] == "SELL" else "SHORT",
            "entry": self.positions[closing_order['symbol']]['avg_price'],
            "exit": closing_order['fill_price'],
            "quantity": closing_order['quantity'],
            "pnl": self._calculate_pnl(closing_order),
            "reason": closing_order['reason'],
            "closed_at": datetime.now().isoformat()
        }
        
        self.trade_history.append(trade)
        self._save_trade_history()
        
        print(f"   [EXECUTOR]: Trade closed - PnL: ${trade['pnl']:.2f}")
    
    def _calculate_pnl(self, order: Dict) -> float:
        """Calculate PnL for a closed trade"""
        position = self.positions.get(order['symbol'], {})
        entry_price = position.get('avg_price', order['fill_price'])
        exit_price = order['fill_price']
        quantity = order['quantity']
        
        if order['side'] == "SELL":
            # Closing a long position
            pnl = (exit_price - entry_price) * quantity * 10000  # Simplified for forex
        else:
            # Closing a short position
            pnl = (entry_price - exit_price) * quantity * 10000
        
        return round(pnl, 2)
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        # Default prices for simulation
        prices = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 154.50,
            "AUDUSD": 0.6280,
            "XAUUSD": 2045.00
        }
        return prices.get(symbol, 1.0)
    
    def close_position(self, symbol: str, reason: str = "Manual close") -> Optional[Dict]:
        """Close an existing position"""
        if symbol not in self.positions or self.positions[symbol]['quantity'] == 0:
            print(f"   [EXECUTOR]: No position to close for {symbol}")
            return None
        
        position = self.positions[symbol]
        side = "SELL" if position['quantity'] > 0 else "BUY"
        quantity = abs(position['quantity'])
        
        return self.place_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type="MARKET",
            reason=reason
        )
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position for a symbol"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Dict]:
        """Get all open positions"""
        return {k: v for k, v in self.positions.items() if v['quantity'] != 0}
    
    def get_trade_history(self) -> List[Dict]:
        """Get trade history"""
        return self.trade_history
    
    def _load_trade_history(self):
        """Load trade history from file"""
        history_file = os.path.join(self.logs_dir, "trade_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    self.trade_history = json.load(f)
            except:
                self.trade_history = []
    
    def _save_trade_history(self):
        """Save trade history to file"""
        os.makedirs(self.logs_dir, exist_ok=True)
        history_file = os.path.join(self.logs_dir, "trade_history.json")
        with open(history_file, 'w') as f:
            json.dump(self.trade_history, f, indent=2)


# Test
if __name__ == "__main__":
    executor = TradeExecutor(mode="PAPER")
    
    print("\n=== TRADE EXECUTOR TEST ===")
    
    # Place a buy order
    order = executor.place_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.1,
        order_type="MARKET",
        stop_loss=1.0800,
        take_profit=1.0900,
        reason="Test trade"
    )
    print(f"\nOrder placed: {order['order_id']}")
    
    # Check position
    position = executor.get_position("EURUSD")
    print(f"Position: {position}")
    
    # Close position
    close_order = executor.close_position("EURUSD", "Test close")
    print(f"\nPosition closed: {close_order['order_id']}")
    
    # Check trade history
    history = executor.get_trade_history()
    print(f"\nTrade history: {len(history)} trades")
