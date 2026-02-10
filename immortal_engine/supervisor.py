# SUPERVISOR - The "Let It Crash" Pattern
# Inspired by Elixir/OTP Supervision Trees
#
# If a worker crashes, the supervisor:
# 1. Logs the crash
# 2. Kills the worker cleanly
# 3. Spawns a fresh worker instantly
# 4. The rest of the system doesn't even notice
#
# This is how you build a bot that runs for 5 years without a restart.

import multiprocessing as mp
from multiprocessing import Process, Queue, Event
import threading
import time
import traceback
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class WorkerConfig:
    """Configuration for a supervised worker"""
    name: str
    target: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    restart_strategy: str = "permanent"  # permanent, temporary, transient
    max_restarts: int = 10
    restart_window: int = 60  # seconds
    

class Worker:
    """
    A supervised worker process.
    
    If this worker crashes, the Supervisor will restart it automatically.
    The worker should be stateless - all state lives in external stores.
    """
    
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.process: Optional[Process] = None
        self.restart_count = 0
        self.restart_times: List[float] = []
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        self.status = "stopped"
        
    def start(self, input_queue: Queue, output_queue: Queue, stop_event: Event):
        """Start the worker process"""
        self.process = Process(
            target=self._run_worker,
            args=(self.config.target, input_queue, output_queue, stop_event, 
                  self.config.args, self.config.kwargs),
            name=self.config.name
        )
        self.process.start()
        self.started_at = datetime.now()
        self.status = "running"
        
    @staticmethod
    def _run_worker(target: Callable, input_queue: Queue, output_queue: Queue, 
                    stop_event: Event, args: tuple, kwargs: dict):
        """
        The actual worker loop.
        
        Pattern: Read from input queue -> Process -> Write to output queue
        If ANY error occurs, let it crash. The supervisor will restart us.
        """
        while not stop_event.is_set():
            try:
                # Non-blocking get with timeout
                try:
                    data = input_queue.get(timeout=1.0)
                except:
                    continue
                    
                # Process the data - LET IT CRASH if something goes wrong
                result = target(data, *args, **kwargs)
                
                # Send result to output queue
                if result is not None:
                    output_queue.put(result)
                    
            except Exception as e:
                # Log and re-raise - supervisor will handle restart
                print(f"[WORKER CRASH] {mp.current_process().name}: {e}")
                raise
                
    def stop(self):
        """Stop the worker gracefully"""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill()
        self.stopped_at = datetime.now()
        self.status = "stopped"
        
    def is_alive(self) -> bool:
        """Check if worker is still running"""
        return self.process is not None and self.process.is_alive()
        
    def record_restart(self):
        """Record a restart event"""
        now = time.time()
        self.restart_times.append(now)
        # Clean old restart times outside window
        cutoff = now - self.config.restart_window
        self.restart_times = [t for t in self.restart_times if t > cutoff]
        self.restart_count = len(self.restart_times)
        
    def can_restart(self) -> bool:
        """Check if we can restart (haven't exceeded max restarts in window)"""
        if self.config.restart_strategy == "temporary":
            return False
        return self.restart_count < self.config.max_restarts


class Supervisor:
    """
    THE IMMORTAL SUPERVISOR
    
    Watches all workers with a sniper rifle.
    If any worker crashes, it shoots it in the head and spawns a fresh one instantly.
    The rest of the system doesn't even notice.
    
    Strategies:
    - one_for_one: If one dies, restart just that one
    - one_for_all: If one dies, restart all workers
    - rest_for_one: If one dies, restart it and all workers started after it
    """
    
    def __init__(self, name: str = "MainSupervisor", strategy: str = "one_for_one"):
        self.name = name
        self.strategy = strategy
        self.workers: Dict[str, Worker] = {}
        self.queues: Dict[str, Dict[str, Queue]] = {}  # worker_name -> {input, output}
        self.stop_events: Dict[str, Event] = {}
        self.monitor_thread: Optional[threading.Thread] = None
        self.running = False
        self.log_file = f"logs/supervisor_{name}.json"
        
    def add_worker(self, config: WorkerConfig) -> 'Supervisor':
        """Add a worker to supervise (fluent interface)"""
        self.workers[config.name] = Worker(config)
        self.queues[config.name] = {
            "input": Queue(),
            "output": Queue()
        }
        self.stop_events[config.name] = Event()
        return self
        
    def start(self):
        """Start all workers and the monitoring thread"""
        self.running = True
        
        # Start all workers
        for name, worker in self.workers.items():
            self._start_worker(name)
            
        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self._log_event("supervisor_started", {"workers": list(self.workers.keys())})
        
    def _start_worker(self, name: str):
        """Start a specific worker"""
        worker = self.workers[name]
        self.stop_events[name].clear()
        worker.start(
            self.queues[name]["input"],
            self.queues[name]["output"],
            self.stop_events[name]
        )
        self._log_event("worker_started", {"worker": name})
        
    def _monitor_loop(self):
        """
        The heartbeat loop - checks all workers every second.
        If any worker is dead, handle according to strategy.
        """
        while self.running:
            for name, worker in self.workers.items():
                if not worker.is_alive() and worker.status == "running":
                    self._handle_worker_death(name)
            time.sleep(1.0)
            
    def _handle_worker_death(self, name: str):
        """Handle a worker that has died"""
        worker = self.workers[name]
        
        self._log_event("worker_crashed", {
            "worker": name,
            "restart_count": worker.restart_count
        })
        
        if self.strategy == "one_for_one":
            self._restart_worker(name)
        elif self.strategy == "one_for_all":
            self._restart_all_workers()
        elif self.strategy == "rest_for_one":
            self._restart_from_worker(name)
            
    def _restart_worker(self, name: str):
        """Restart a single worker"""
        worker = self.workers[name]
        
        if not worker.can_restart():
            self._log_event("worker_max_restarts", {"worker": name})
            worker.status = "failed"
            return
            
        worker.record_restart()
        worker.stop()
        
        # Clear the stop event and restart
        self.stop_events[name] = Event()
        worker.start(
            self.queues[name]["input"],
            self.queues[name]["output"],
            self.stop_events[name]
        )
        
        self._log_event("worker_restarted", {
            "worker": name,
            "restart_count": worker.restart_count
        })
        
    def _restart_all_workers(self):
        """Restart all workers (one_for_all strategy)"""
        for name in self.workers:
            self._restart_worker(name)
            
    def _restart_from_worker(self, name: str):
        """Restart this worker and all workers added after it"""
        names = list(self.workers.keys())
        idx = names.index(name)
        for n in names[idx:]:
            self._restart_worker(n)
            
    def stop(self):
        """Stop all workers and the supervisor"""
        self.running = False
        
        for name in self.workers:
            self.stop_events[name].set()
            self.workers[name].stop()
            
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        self._log_event("supervisor_stopped", {})
        
    def send(self, worker_name: str, data: Any):
        """Send data to a worker's input queue"""
        if worker_name in self.queues:
            self.queues[worker_name]["input"].put(data)
            
    def receive(self, worker_name: str, timeout: float = 1.0) -> Optional[Any]:
        """Receive data from a worker's output queue"""
        if worker_name in self.queues:
            try:
                return self.queues[worker_name]["output"].get(timeout=timeout)
            except:
                return None
        return None
        
    def pipe(self, from_worker: str, to_worker: str):
        """Connect output of one worker to input of another"""
        # This creates a pipeline: worker1 -> worker2
        def pipe_thread():
            while self.running:
                result = self.receive(from_worker, timeout=1.0)
                if result is not None:
                    self.send(to_worker, result)
                    
        thread = threading.Thread(target=pipe_thread, daemon=True)
        thread.start()
        return self
        
    def _log_event(self, event_type: str, data: Dict):
        """Log supervisor events"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "supervisor": self.name,
            "event": event_type,
            "data": data
        }
        
        # Append to log file
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except:
            pass
            
    def status(self) -> Dict[str, Any]:
        """Get status of all workers"""
        return {
            "supervisor": self.name,
            "strategy": self.strategy,
            "running": self.running,
            "workers": {
                name: {
                    "status": worker.status,
                    "alive": worker.is_alive(),
                    "restart_count": worker.restart_count,
                    "started_at": worker.started_at.isoformat() if worker.started_at else None
                }
                for name, worker in self.workers.items()
            }
        }


# Example usage showing the "Sentence" pattern
if __name__ == "__main__":
    # Define worker functions (pure functions)
    def normalize(data):
        """Clean and normalize market data"""
        return {"normalized": True, **data}
        
    def analyze(data):
        """Analyze for trading signals"""
        return {"signal": "BUY" if data.get("price", 0) > 100 else "HOLD", **data}
        
    def risk_check(data):
        """Check risk constraints"""
        return {"risk_ok": True, **data}
        
    def execute(data):
        """Execute the trade (paper)"""
        if data.get("signal") == "BUY" and data.get("risk_ok"):
            return {"executed": True, "action": "BUY", **data}
        return {"executed": False, **data}
    
    # Build the supervision tree
    supervisor = Supervisor("TradingEngine", strategy="one_for_one")
    
    # Add workers - each is isolated, can crash independently
    supervisor.add_worker(WorkerConfig("normalizer", normalize))
    supervisor.add_worker(WorkerConfig("analyzer", analyze))
    supervisor.add_worker(WorkerConfig("risk_checker", risk_check))
    supervisor.add_worker(WorkerConfig("executor", execute))
    
    # Create the pipeline: normalize -> analyze -> risk_check -> execute
    supervisor.pipe("normalizer", "analyzer")
    supervisor.pipe("analyzer", "risk_checker")
    supervisor.pipe("risk_checker", "executor")
    
    # Start the immortal engine
    supervisor.start()
    
    # Send data through the pipeline
    supervisor.send("normalizer", {"price": 150, "symbol": "BTC"})
    
    # Get result
    time.sleep(2)
    result = supervisor.receive("executor")
    print(f"Result: {result}")
    
    # Check status
    print(f"Status: {supervisor.status()}")
    
    supervisor.stop()
