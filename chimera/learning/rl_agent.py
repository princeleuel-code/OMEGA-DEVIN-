"""
Reinforcement Learning Agent for Trading

This module implements a deep RL agent that learns optimal trading decisions
by interacting with a simulated market environment. The agent can serve as
a meta-controller for strategy selection and position sizing.

Key Features:
- OpenAI Gym-compatible trading environment
- PPO-based policy learning (can be swapped for other algorithms)
- Abstention-first reward design (penalizes bad trades heavily)
- Integration with existing veto cascade and reason codes
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from chimera.core.reason_codes import ReasonCode
from chimera.data.loader import OHLCV

logger = logging.getLogger(__name__)


class RLAction(Enum):
    """Possible actions for the RL agent."""
    HOLD = 0      # Do nothing
    LONG = 1      # Open/hold long position
    SHORT = 2     # Open/hold short position
    CLOSE = 3     # Close any open position


@dataclass
class RLConfig:
    """Configuration for the RL agent."""
    # State space
    lookback_bars: int = 20
    feature_dim: int = 10  # Number of features per bar
    
    # Action space
    n_actions: int = 4  # HOLD, LONG, SHORT, CLOSE
    
    # Reward shaping
    profit_reward_scale: float = 1.0
    loss_penalty_scale: float = 2.0  # Penalize losses more than reward profits
    abstention_reward: float = 0.01  # Small reward for not trading in uncertain conditions
    veto_penalty: float = -0.5  # Penalty for proposing vetoed trades
    
    # Training parameters
    learning_rate: float = 3e-4
    gamma: float = 0.99  # Discount factor
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay: float = 0.995
    batch_size: int = 64
    memory_size: int = 10000
    
    # Risk constraints (built into reward)
    max_drawdown_penalty: float = -10.0
    max_consecutive_losses: int = 3
    
    # Model architecture
    hidden_layers: List[int] = field(default_factory=lambda: [128, 64, 32])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lookback_bars": self.lookback_bars,
            "feature_dim": self.feature_dim,
            "n_actions": self.n_actions,
            "profit_reward_scale": self.profit_reward_scale,
            "loss_penalty_scale": self.loss_penalty_scale,
            "abstention_reward": self.abstention_reward,
            "veto_penalty": self.veto_penalty,
            "learning_rate": self.learning_rate,
            "gamma": self.gamma,
            "epsilon_start": self.epsilon_start,
            "epsilon_end": self.epsilon_end,
            "epsilon_decay": self.epsilon_decay,
            "batch_size": self.batch_size,
            "memory_size": self.memory_size,
            "max_drawdown_penalty": self.max_drawdown_penalty,
            "max_consecutive_losses": self.max_consecutive_losses,
            "hidden_layers": self.hidden_layers,
        }


def create_default_rl_config() -> RLConfig:
    """Create a default RL configuration with conservative settings."""
    return RLConfig()


@dataclass
class TradingState:
    """Current state of the trading environment."""
    position: int = 0  # -1 short, 0 flat, 1 long
    entry_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    equity: float = 10000.0
    peak_equity: float = 10000.0
    drawdown: float = 0.0
    consecutive_losses: int = 0
    trades_today: int = 0
    step: int = 0


class TradingEnvironment:
    """
    OpenAI Gym-compatible trading environment.
    
    The environment simulates trading on historical OHLCV data.
    States are feature vectors derived from price/volume data.
    Actions are trading decisions (hold, long, short, close).
    Rewards are shaped to encourage abstention-first behavior.
    """
    
    def __init__(
        self,
        bars: List[OHLCV],
        config: RLConfig,
        initial_capital: float = 10000.0,
        spread_pips: float = 1.0,
        pip_size: float = 0.0001,
    ):
        self.bars = bars
        self.config = config
        self.initial_capital = initial_capital
        self.spread_pips = spread_pips
        self.pip_size = pip_size
        
        # State dimensions
        self.state_dim = config.lookback_bars * config.feature_dim + 5  # +5 for position info
        self.action_dim = config.n_actions
        
        # Initialize state
        self.state = TradingState(equity=initial_capital, peak_equity=initial_capital)
        self.current_idx = config.lookback_bars
        
        # Feature cache
        self._feature_cache: Dict[int, np.ndarray] = {}
        
        # Episode tracking
        self.episode_rewards: List[float] = []
        self.episode_trades: List[Dict[str, Any]] = []
        
    def reset(self) -> np.ndarray:
        """Reset the environment to initial state."""
        self.state = TradingState(
            equity=self.initial_capital,
            peak_equity=self.initial_capital,
        )
        self.current_idx = self.config.lookback_bars
        self.episode_rewards = []
        self.episode_trades = []
        self._feature_cache = {}
        
        return self._get_observation()
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            action: The action to take (0=HOLD, 1=LONG, 2=SHORT, 3=CLOSE)
            
        Returns:
            observation: New state observation
            reward: Reward for the action
            done: Whether episode is finished
            info: Additional information
        """
        if self.current_idx >= len(self.bars) - 1:
            return self._get_observation(), 0.0, True, {"reason": "end_of_data"}
        
        current_bar = self.bars[self.current_idx]
        next_bar = self.bars[self.current_idx + 1]
        
        # Calculate reward based on action and market movement
        reward, info = self._calculate_reward(action, current_bar, next_bar)
        
        # Update state
        self._update_state(action, current_bar, next_bar)
        
        # Move to next bar
        self.current_idx += 1
        self.state.step += 1
        
        # Check termination conditions
        done = self._check_done()
        
        # Get new observation
        obs = self._get_observation()
        
        # Track episode
        self.episode_rewards.append(reward)
        
        return obs, reward, done, info
    
    def _get_observation(self) -> np.ndarray:
        """Get the current observation (state) vector."""
        # Get bar features for lookback window
        bar_features = []
        for i in range(self.config.lookback_bars):
            idx = self.current_idx - self.config.lookback_bars + i
            if idx >= 0 and idx < len(self.bars):
                features = self._extract_bar_features(idx)
                bar_features.append(features)
            else:
                bar_features.append(np.zeros(self.config.feature_dim))
        
        # Flatten bar features
        bar_obs = np.concatenate(bar_features)
        
        # Add position information
        position_obs = np.array([
            self.state.position,
            self.state.unrealized_pnl / self.initial_capital,
            self.state.drawdown,
            self.state.consecutive_losses / self.config.max_consecutive_losses,
            self.state.trades_today / 10.0,  # Normalize
        ])
        
        # Combine
        obs = np.concatenate([bar_obs, position_obs])
        
        return obs.astype(np.float32)
    
    def _extract_bar_features(self, idx: int) -> np.ndarray:
        """Extract normalized features from a single bar."""
        if idx in self._feature_cache:
            return self._feature_cache[idx]
        
        bar = self.bars[idx]
        
        # Calculate basic features
        range_size = bar.high - bar.low
        body_size = abs(bar.close - bar.open)
        
        # Normalize by recent average
        lookback = min(20, idx)
        if lookback > 0:
            recent_bars = self.bars[idx - lookback:idx]
            avg_range = np.mean([b.high - b.low for b in recent_bars])
            avg_volume = np.mean([b.volume for b in recent_bars])
        else:
            avg_range = range_size if range_size > 0 else 1.0
            avg_volume = bar.volume if bar.volume > 0 else 1.0
        
        # Prevent division by zero
        avg_range = max(avg_range, 1e-8)
        avg_volume = max(avg_volume, 1.0)
        
        # Calculate returns
        if idx > 0:
            prev_close = self.bars[idx - 1].close
            returns = (bar.close - prev_close) / prev_close if prev_close > 0 else 0.0
        else:
            returns = 0.0
        
        features = np.array([
            returns,  # Price return
            (bar.close - bar.open) / avg_range,  # Normalized body
            (bar.high - max(bar.open, bar.close)) / avg_range,  # Upper wick
            (min(bar.open, bar.close) - bar.low) / avg_range,  # Lower wick
            range_size / avg_range,  # Normalized range
            bar.volume / avg_volume,  # Normalized volume
            1.0 if bar.close > bar.open else -1.0,  # Candle direction
            body_size / range_size if range_size > 0 else 0.0,  # Body ratio
            (bar.close - bar.low) / range_size if range_size > 0 else 0.5,  # Close position in range
            0.0,  # Placeholder for additional features
        ])
        
        # Clip to prevent extreme values
        features = np.clip(features, -10.0, 10.0)
        
        self._feature_cache[idx] = features
        return features
    
    def _calculate_reward(
        self,
        action: int,
        current_bar: OHLCVBar,
        next_bar: OHLCVBar,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate reward for the action taken.
        
        Reward design follows abstention-first principle:
        - Small positive reward for holding when uncertain
        - Larger reward for profitable trades
        - Heavy penalty for losses (asymmetric)
        - Penalty for excessive trading
        """
        reward = 0.0
        info = {"action": RLAction(action).name, "reason_codes": []}
        
        price_change = next_bar.close - current_bar.close
        spread_cost = self.spread_pips * self.pip_size
        
        # Handle different actions
        if action == RLAction.HOLD.value:
            # Reward for abstention when flat
            if self.state.position == 0:
                reward = self.config.abstention_reward
                info["reason_codes"].append("ABSTAIN_FLAT")
            else:
                # Holding an existing position - reward based on unrealized P&L change
                if self.state.position == 1:  # Long
                    reward = price_change * self.config.profit_reward_scale
                else:  # Short
                    reward = -price_change * self.config.profit_reward_scale
                info["reason_codes"].append("HOLD_POSITION")
                
        elif action == RLAction.LONG.value:
            if self.state.position == 0:
                # Opening new long
                info["reason_codes"].append("OPEN_LONG")
                # Immediate cost of spread
                reward = -spread_cost * self.config.loss_penalty_scale
            elif self.state.position == 1:
                # Already long, treat as hold
                reward = price_change * self.config.profit_reward_scale
                info["reason_codes"].append("HOLD_LONG")
            else:
                # Closing short and going long (reversal)
                close_pnl = self.state.entry_price - current_bar.close - spread_cost
                reward = close_pnl * (self.config.profit_reward_scale if close_pnl > 0 else self.config.loss_penalty_scale)
                info["reason_codes"].append("REVERSE_TO_LONG")
                
        elif action == RLAction.SHORT.value:
            if self.state.position == 0:
                # Opening new short
                info["reason_codes"].append("OPEN_SHORT")
                reward = -spread_cost * self.config.loss_penalty_scale
            elif self.state.position == -1:
                # Already short, treat as hold
                reward = -price_change * self.config.profit_reward_scale
                info["reason_codes"].append("HOLD_SHORT")
            else:
                # Closing long and going short (reversal)
                close_pnl = current_bar.close - self.state.entry_price - spread_cost
                reward = close_pnl * (self.config.profit_reward_scale if close_pnl > 0 else self.config.loss_penalty_scale)
                info["reason_codes"].append("REVERSE_TO_SHORT")
                
        elif action == RLAction.CLOSE.value:
            if self.state.position != 0:
                # Calculate P&L
                if self.state.position == 1:
                    pnl = current_bar.close - self.state.entry_price - spread_cost
                else:
                    pnl = self.state.entry_price - current_bar.close - spread_cost
                
                # Asymmetric reward
                if pnl > 0:
                    reward = pnl * self.config.profit_reward_scale
                    info["reason_codes"].append("CLOSE_PROFIT")
                else:
                    reward = pnl * self.config.loss_penalty_scale
                    info["reason_codes"].append("CLOSE_LOSS")
            else:
                # Closing when flat - small penalty for unnecessary action
                reward = -0.01
                info["reason_codes"].append("CLOSE_FLAT")
        
        # Drawdown penalty
        if self.state.drawdown > 0.1:  # 10% drawdown
            reward += self.config.max_drawdown_penalty * self.state.drawdown
            info["reason_codes"].append("DRAWDOWN_PENALTY")
        
        # Consecutive loss penalty
        if self.state.consecutive_losses >= self.config.max_consecutive_losses:
            reward -= 0.5
            info["reason_codes"].append("CONSECUTIVE_LOSS_PENALTY")
        
        info["reward"] = reward
        return reward, info
    
    def _update_state(
        self,
        action: int,
        current_bar: OHLCVBar,
        next_bar: OHLCVBar,
    ) -> None:
        """Update the trading state based on action."""
        spread_cost = self.spread_pips * self.pip_size
        
        # Handle position changes
        if action == RLAction.LONG.value:
            if self.state.position <= 0:
                # Close any short position first
                if self.state.position == -1:
                    pnl = self.state.entry_price - current_bar.close - spread_cost
                    self.state.realized_pnl += pnl
                    self.state.equity += pnl * 10000  # Assuming 1 lot = 10000 units
                    if pnl < 0:
                        self.state.consecutive_losses += 1
                    else:
                        self.state.consecutive_losses = 0
                    self.episode_trades.append({
                        "type": "close_short",
                        "pnl": pnl,
                        "step": self.state.step,
                    })
                
                # Open long
                self.state.position = 1
                self.state.entry_price = current_bar.close + spread_cost / 2
                self.state.trades_today += 1
                
        elif action == RLAction.SHORT.value:
            if self.state.position >= 0:
                # Close any long position first
                if self.state.position == 1:
                    pnl = current_bar.close - self.state.entry_price - spread_cost
                    self.state.realized_pnl += pnl
                    self.state.equity += pnl * 10000
                    if pnl < 0:
                        self.state.consecutive_losses += 1
                    else:
                        self.state.consecutive_losses = 0
                    self.episode_trades.append({
                        "type": "close_long",
                        "pnl": pnl,
                        "step": self.state.step,
                    })
                
                # Open short
                self.state.position = -1
                self.state.entry_price = current_bar.close - spread_cost / 2
                self.state.trades_today += 1
                
        elif action == RLAction.CLOSE.value:
            if self.state.position == 1:
                pnl = current_bar.close - self.state.entry_price - spread_cost
                self.state.realized_pnl += pnl
                self.state.equity += pnl * 10000
                if pnl < 0:
                    self.state.consecutive_losses += 1
                else:
                    self.state.consecutive_losses = 0
                self.episode_trades.append({
                    "type": "close_long",
                    "pnl": pnl,
                    "step": self.state.step,
                })
            elif self.state.position == -1:
                pnl = self.state.entry_price - current_bar.close - spread_cost
                self.state.realized_pnl += pnl
                self.state.equity += pnl * 10000
                if pnl < 0:
                    self.state.consecutive_losses += 1
                else:
                    self.state.consecutive_losses = 0
                self.episode_trades.append({
                    "type": "close_short",
                    "pnl": pnl,
                    "step": self.state.step,
                })
            
            self.state.position = 0
            self.state.entry_price = 0.0
        
        # Update unrealized P&L
        if self.state.position == 1:
            self.state.unrealized_pnl = next_bar.close - self.state.entry_price
        elif self.state.position == -1:
            self.state.unrealized_pnl = self.state.entry_price - next_bar.close
        else:
            self.state.unrealized_pnl = 0.0
        
        # Update peak equity and drawdown
        current_equity = self.state.equity + self.state.unrealized_pnl * 10000
        if current_equity > self.state.peak_equity:
            self.state.peak_equity = current_equity
        self.state.drawdown = (self.state.peak_equity - current_equity) / self.state.peak_equity
    
    def _check_done(self) -> bool:
        """Check if episode should terminate."""
        # End of data
        if self.current_idx >= len(self.bars) - 1:
            return True
        
        # Blown account (equity below 50% of initial)
        if self.state.equity < self.initial_capital * 0.5:
            return True
        
        # Maximum drawdown exceeded
        if self.state.drawdown > 0.25:  # 25% drawdown
            return True
        
        return False
    
    def get_episode_stats(self) -> Dict[str, Any]:
        """Get statistics for the current episode."""
        total_reward = sum(self.episode_rewards)
        n_trades = len(self.episode_trades)
        
        if n_trades > 0:
            winning_trades = [t for t in self.episode_trades if t["pnl"] > 0]
            win_rate = len(winning_trades) / n_trades
            avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0.0
            losing_trades = [t for t in self.episode_trades if t["pnl"] <= 0]
            avg_loss = np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0.0
        else:
            win_rate = 0.0
            avg_win = 0.0
            avg_loss = 0.0
        
        return {
            "total_reward": total_reward,
            "n_trades": n_trades,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "final_equity": self.state.equity,
            "max_drawdown": self.state.drawdown,
            "realized_pnl": self.state.realized_pnl,
        }


class ReplayBuffer:
    """Experience replay buffer for RL training."""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer: List[Tuple[np.ndarray, int, float, np.ndarray, bool]] = []
        self.position = 0
    
    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        """Add experience to buffer."""
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)  # type: ignore
        self.buffer[self.position] = (state, action, reward, next_state, done)
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int) -> List[Tuple[np.ndarray, int, float, np.ndarray, bool]]:
        """Sample a batch of experiences."""
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))
    
    def __len__(self) -> int:
        return len(self.buffer)


class RLAgent:
    """
    Reinforcement Learning Agent for trading decisions.
    
    Uses a simple neural network policy with epsilon-greedy exploration.
    Can be upgraded to use more sophisticated algorithms (PPO, SAC, etc.)
    when stable-baselines3 is available.
    """
    
    def __init__(self, state_dim: int, action_dim: int, config: RLConfig):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config
        
        # Epsilon for exploration
        self.epsilon = config.epsilon_start
        
        # Experience replay
        self.memory = ReplayBuffer(config.memory_size)
        
        # Simple Q-table approximation (can be replaced with neural network)
        # For now, use a simple linear model
        self.weights = np.random.randn(state_dim, action_dim) * 0.01
        self.bias = np.zeros(action_dim)
        
        # Training stats
        self.training_steps = 0
        self.episode_count = 0
        
        logger.info(f"RLAgent initialized: state_dim={state_dim}, action_dim={action_dim}")
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Select an action using epsilon-greedy policy.
        
        Args:
            state: Current state observation
            training: Whether in training mode (enables exploration)
            
        Returns:
            Selected action index
        """
        if training and random.random() < self.epsilon:
            # Exploration: random action
            return random.randint(0, self.action_dim - 1)
        else:
            # Exploitation: best action according to Q-values
            q_values = self._compute_q_values(state)
            return int(np.argmax(q_values))
    
    def _compute_q_values(self, state: np.ndarray) -> np.ndarray:
        """Compute Q-values for all actions."""
        return np.dot(state, self.weights) + self.bias
    
    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        """Store experience in replay buffer."""
        self.memory.push(state, action, reward, next_state, done)
    
    def train_step(self) -> Optional[float]:
        """
        Perform one training step using experience replay.
        
        Returns:
            Loss value if training occurred, None otherwise
        """
        if len(self.memory) < self.config.batch_size:
            return None
        
        # Sample batch
        batch = self.memory.sample(self.config.batch_size)
        
        total_loss = 0.0
        for state, action, reward, next_state, done in batch:
            # Current Q-value
            current_q = self._compute_q_values(state)[action]
            
            # Target Q-value (Bellman equation)
            if done:
                target_q = reward
            else:
                next_q_values = self._compute_q_values(next_state)
                target_q = reward + self.config.gamma * np.max(next_q_values)
            
            # TD error
            td_error = target_q - current_q
            total_loss += td_error ** 2
            
            # Update weights (simple gradient descent)
            self.weights[:, action] += self.config.learning_rate * td_error * state
            self.bias[action] += self.config.learning_rate * td_error
        
        self.training_steps += 1
        
        # Decay epsilon
        self.epsilon = max(
            self.config.epsilon_end,
            self.epsilon * self.config.epsilon_decay
        )
        
        return total_loss / len(batch)
    
    def train_episode(self, env: TradingEnvironment) -> Dict[str, Any]:
        """
        Train for one episode.
        
        Args:
            env: Trading environment
            
        Returns:
            Episode statistics
        """
        state = env.reset()
        total_reward = 0.0
        losses = []
        
        while True:
            # Select action
            action = self.select_action(state, training=True)
            
            # Take step
            next_state, reward, done, info = env.step(action)
            
            # Store experience
            self.store_experience(state, action, reward, next_state, done)
            
            # Train
            loss = self.train_step()
            if loss is not None:
                losses.append(loss)
            
            total_reward += reward
            state = next_state
            
            if done:
                break
        
        self.episode_count += 1
        
        stats = env.get_episode_stats()
        stats["avg_loss"] = np.mean(losses) if losses else 0.0
        stats["epsilon"] = self.epsilon
        stats["episode"] = self.episode_count
        
        return stats
    
    def evaluate(self, env: TradingEnvironment, n_episodes: int = 5) -> Dict[str, Any]:
        """
        Evaluate the agent without training.
        
        Args:
            env: Trading environment
            n_episodes: Number of evaluation episodes
            
        Returns:
            Aggregated evaluation statistics
        """
        all_stats = []
        
        for _ in range(n_episodes):
            state = env.reset()
            
            while True:
                action = self.select_action(state, training=False)
                next_state, reward, done, info = env.step(action)
                state = next_state
                
                if done:
                    break
            
            all_stats.append(env.get_episode_stats())
        
        # Aggregate stats
        return {
            "avg_reward": np.mean([s["total_reward"] for s in all_stats]),
            "avg_trades": np.mean([s["n_trades"] for s in all_stats]),
            "avg_win_rate": np.mean([s["win_rate"] for s in all_stats]),
            "avg_final_equity": np.mean([s["final_equity"] for s in all_stats]),
            "avg_max_drawdown": np.mean([s["max_drawdown"] for s in all_stats]),
        }
    
    def save(self, path: Path) -> None:
        """Save agent to file."""
        data = {
            "weights": self.weights.tolist(),
            "bias": self.bias.tolist(),
            "epsilon": self.epsilon,
            "training_steps": self.training_steps,
            "episode_count": self.episode_count,
            "config": self.config.to_dict(),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"RLAgent saved to {path}")
    
    def load(self, path: Path) -> None:
        """Load agent from file."""
        with open(path, "r") as f:
            data = json.load(f)
        
        self.weights = np.array(data["weights"])
        self.bias = np.array(data["bias"])
        self.epsilon = data["epsilon"]
        self.training_steps = data["training_steps"]
        self.episode_count = data["episode_count"]
        logger.info(f"RLAgent loaded from {path}")
    
    def get_action_recommendation(
        self,
        state: np.ndarray,
        confidence_threshold: float = 0.6,
    ) -> Tuple[RLAction, float, List[str]]:
        """
        Get action recommendation with confidence and reason codes.
        
        This method is designed to integrate with the existing veto cascade.
        
        Args:
            state: Current state observation
            confidence_threshold: Minimum confidence to recommend action
            
        Returns:
            Tuple of (action, confidence, reason_codes)
        """
        q_values = self._compute_q_values(state)
        
        # Softmax to get probabilities
        exp_q = np.exp(q_values - np.max(q_values))
        probs = exp_q / np.sum(exp_q)
        
        best_action_idx = int(np.argmax(q_values))
        confidence = float(probs[best_action_idx])
        
        reason_codes = []
        
        if confidence < confidence_threshold:
            # Low confidence - recommend abstention
            reason_codes.append(ReasonCode.RL_LOW_CONFIDENCE.value if hasattr(ReasonCode, 'RL_LOW_CONFIDENCE') else "RL_LOW_CONFIDENCE")
            return RLAction.HOLD, confidence, reason_codes
        
        action = RLAction(best_action_idx)
        reason_codes.append(f"RL_RECOMMEND_{action.name}")
        
        return action, confidence, reason_codes
