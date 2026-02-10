# PIPELINE - The "Code as a Sentence" Pattern
# Inspired by Elixir's Pipe Operator (|>)
#
# Instead of: execute(risk_check(analyze(normalize(data))))
# We write:   data |> normalize() |> analyze() |> risk_check() |> execute()
#
# This makes the logic flow like a river, readable by AI and humans.
# Each step is a pure function - no hidden state, no surprises.

from typing import Any, Callable, List, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
import traceback
import json
import os

T = TypeVar('T')


@dataclass
class PipelineStep:
    """A single step in the pipeline"""
    name: str
    func: Callable
    required: bool = True  # If True, pipeline fails if this step fails
    timeout: float = 30.0  # Max seconds for this step
    

@dataclass
class PipelineResult:
    """Result of running a pipeline"""
    success: bool
    data: Any
    steps_completed: List[str]
    failed_step: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Pipeline:
    """
    THE SENTENCE PIPELINE
    
    Build data processing as a readable sentence:
    
    result = (Pipeline("MarketAnalysis")
        .pipe("normalize", normalize_data)
        .pipe("enrich", add_indicators)
        .pipe("analyze", find_signals)
        .pipe("validate", check_risk)
        .pipe("execute", place_order)
        .run(market_data))
    
    The pipeline reads like English:
    "Take market data, normalize it, enrich it with indicators,
     analyze for signals, validate risk, then execute."
    """
    
    def __init__(self, name: str):
        self.name = name
        self.steps: List[PipelineStep] = []
        self.log_file = f"logs/pipeline_{name}.json"
        
    def pipe(self, name: str, func: Callable, required: bool = True, 
             timeout: float = 30.0) -> 'Pipeline':
        """
        Add a step to the pipeline (fluent interface).
        
        Each step receives the output of the previous step.
        If a step fails and is required, the pipeline stops.
        """
        self.steps.append(PipelineStep(name, func, required, timeout))
        return self
        
    def run(self, initial_data: Any) -> PipelineResult:
        """
        Run the pipeline with initial data.
        
        Data flows through each step in order:
        initial_data -> step1 -> step2 -> ... -> final_result
        """
        start_time = datetime.now()
        data = initial_data
        steps_completed = []
        
        for step in self.steps:
            try:
                # Run the step
                data = step.func(data)
                steps_completed.append(step.name)
                
            except Exception as e:
                # Step failed
                error_msg = f"{step.name}: {str(e)}\n{traceback.format_exc()}"
                
                if step.required:
                    # Required step failed - stop pipeline
                    result = PipelineResult(
                        success=False,
                        data=data,
                        steps_completed=steps_completed,
                        failed_step=step.name,
                        error=error_msg,
                        execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                    )
                    self._log_result(result)
                    return result
                else:
                    # Optional step failed - continue with previous data
                    steps_completed.append(f"{step.name}(skipped)")
                    
        # All steps completed
        result = PipelineResult(
            success=True,
            data=data,
            steps_completed=steps_completed,
            execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        self._log_result(result)
        return result
        
    def _log_result(self, result: PipelineResult):
        """Log pipeline execution"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        log_entry = {
            "pipeline": self.name,
            "success": result.success,
            "steps_completed": result.steps_completed,
            "failed_step": result.failed_step,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": result.timestamp
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except:
            pass
            
    def describe(self) -> str:
        """Describe the pipeline as a sentence"""
        step_names = [s.name for s in self.steps]
        return f"{self.name}: {' -> '.join(step_names)}"


class TradingPipeline(Pipeline):
    """
    THE TRADING SENTENCE
    
    A specialized pipeline for trading that enforces the core interfaces:
    
    tick |> get_features() |> propose_action() |> veto() |> send_order() |> score()
    
    This is the "Omni-Pipeline" from the architecture spec.
    """
    
    def __init__(self, name: str = "TradingPipeline"):
        super().__init__(name)
        self._feature_extractor = None
        self._action_proposer = None
        self._veto_gate = None
        self._order_sender = None
        self._scorer = None
        
    def with_features(self, extractor: Callable) -> 'TradingPipeline':
        """Set the feature extractor: get_features(t) -> x_t"""
        self._feature_extractor = extractor
        return self.pipe("get_features", extractor)
        
    def with_proposer(self, proposer: Callable) -> 'TradingPipeline':
        """Set the action proposer: propose_action(x_t) -> proposal"""
        self._action_proposer = proposer
        return self.pipe("propose_action", proposer)
        
    def with_veto(self, veto_gate: Callable) -> 'TradingPipeline':
        """Set the veto gate: veto(proposal, context) -> allow/deny + reason_codes[]"""
        self._veto_gate = veto_gate
        return self.pipe("veto", veto_gate)
        
    def with_executor(self, executor: Callable) -> 'TradingPipeline':
        """Set the order sender: send_order(order) (paper only)"""
        self._order_sender = executor
        return self.pipe("send_order", executor, required=False)  # Optional - may be vetoed
        
    def with_scorer(self, scorer: Callable) -> 'TradingPipeline':
        """Set the scorer: score(run) -> metrics"""
        self._scorer = scorer
        return self.pipe("score", scorer, required=False)
        
    def process_tick(self, tick: Dict) -> PipelineResult:
        """Process a single market tick through the pipeline"""
        return self.run(tick)


# Functional helpers for building pipelines
def compose(*funcs: Callable) -> Callable:
    """Compose multiple functions: compose(f, g, h)(x) = h(g(f(x)))"""
    def composed(data):
        result = data
        for func in funcs:
            result = func(result)
        return result
    return composed


def tap(func: Callable) -> Callable:
    """
    Tap into the pipeline for side effects without changing data.
    Useful for logging, metrics, etc.
    """
    def tapped(data):
        func(data)  # Side effect
        return data  # Pass through unchanged
    return tapped


def filter_by(predicate: Callable) -> Callable:
    """Filter data based on a predicate"""
    def filtered(data):
        if isinstance(data, list):
            return [x for x in data if predicate(x)]
        return data if predicate(data) else None
    return filtered


def transform(key: str, func: Callable) -> Callable:
    """Transform a specific key in a dict"""
    def transformed(data):
        if isinstance(data, dict) and key in data:
            return {**data, key: func(data[key])}
        return data
    return transformed


# Example usage
if __name__ == "__main__":
    # Define pure functions for each step
    def normalize(tick):
        """Normalize market data"""
        return {
            "symbol": tick.get("symbol", "UNKNOWN"),
            "price": float(tick.get("price", 0)),
            "volume": float(tick.get("volume", 0)),
            "timestamp": tick.get("timestamp", datetime.now().isoformat())
        }
        
    def add_indicators(data):
        """Add technical indicators"""
        return {
            **data,
            "rsi": 55.0,  # Placeholder
            "ema_20": data["price"] * 0.98,
            "ema_50": data["price"] * 0.95
        }
        
    def find_signal(data):
        """Find trading signal"""
        signal = "HOLD"
        if data["price"] > data["ema_20"] > data["ema_50"]:
            signal = "BUY"
        elif data["price"] < data["ema_20"] < data["ema_50"]:
            signal = "SELL"
        return {**data, "signal": signal, "confidence": 0.75}
        
    def check_risk(data):
        """Check risk constraints"""
        return {
            **data,
            "risk_ok": data["confidence"] > 0.6,
            "position_size": 0.01 if data["risk_ok"] else 0
        }
        
    def execute_paper(data):
        """Execute paper trade"""
        if data.get("risk_ok") and data.get("signal") != "HOLD":
            return {
                **data,
                "executed": True,
                "order_id": f"PAPER-{datetime.now().timestamp()}"
            }
        return {**data, "executed": False}
    
    # Build the pipeline - reads like a sentence!
    pipeline = (Pipeline("MarketAnalysis")
        .pipe("normalize", normalize)
        .pipe("add_indicators", add_indicators)
        .pipe("find_signal", find_signal)
        .pipe("check_risk", check_risk)
        .pipe("execute", execute_paper))
    
    print(f"Pipeline: {pipeline.describe()}")
    
    # Run it
    tick = {"symbol": "BTC", "price": 50000, "volume": 100}
    result = pipeline.run(tick)
    
    print(f"\nResult: {result.success}")
    print(f"Steps: {result.steps_completed}")
    print(f"Data: {result.data}")
    print(f"Time: {result.execution_time_ms:.2f}ms")
