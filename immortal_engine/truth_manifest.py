# TRUTH MANIFEST - Reproducibility & Audit Trail
#
# Every run writes a "truth manifest" containing:
# - Git SHA (exact code version)
# - Manifest hash (configuration snapshot)
# - Dataset hash (exact data used)
# - Decision log with veto reason codes
#
# This ensures EVERY trade decision can be reproduced and audited.

import hashlib
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class TruthManifest:
    """
    THE TRUTH MANIFEST
    
    A cryptographic record of exactly what code, config, and data
    was used for each trading run. This enables:
    
    1. Reproducibility: Re-run any historical decision
    2. Audit: Prove exactly why a trade was/wasn't taken
    3. Debugging: Find exactly what changed between runs
    4. Compliance: Regulatory audit trail
    """
    
    # Identifiers
    run_id: str = field(default_factory=lambda: f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Code version
    git_sha: str = ""
    git_branch: str = ""
    git_dirty: bool = False
    
    # Configuration
    config_hash: str = ""
    config_snapshot: Dict = field(default_factory=dict)
    
    # Data
    dataset_hash: str = ""
    dataset_info: Dict = field(default_factory=dict)
    
    # Strategy
    strategy_id: str = ""
    strategy_params: Dict = field(default_factory=dict)
    
    # Results
    decisions: List[Dict] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Capture git info on creation"""
        self._capture_git_info()
        
    def _capture_git_info(self):
        """Capture current git state"""
        try:
            # Get current SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd="/home/ubuntu/omega_devin"
            )
            self.git_sha = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, cwd="/home/ubuntu/omega_devin"
            )
            self.git_branch = result.stdout.strip() if result.returncode == 0 else "unknown"
            
            # Check if dirty
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd="/home/ubuntu/omega_devin"
            )
            self.git_dirty = len(result.stdout.strip()) > 0
            
        except Exception:
            self.git_sha = "unavailable"
            self.git_branch = "unavailable"
            self.git_dirty = True
            
    def set_config(self, config: Dict) -> 'TruthManifest':
        """Set and hash the configuration"""
        self.config_snapshot = config
        config_str = json.dumps(config, sort_keys=True)
        self.config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]
        return self
        
    def set_dataset(self, data: Any, info: Dict = None) -> 'TruthManifest':
        """Set and hash the dataset"""
        self.dataset_info = info or {}
        
        # Hash the data
        if isinstance(data, list):
            data_str = json.dumps(data, sort_keys=True, default=str)
        elif isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)
            
        self.dataset_hash = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        return self
        
    def set_strategy(self, strategy_id: str, params: Dict = None) -> 'TruthManifest':
        """Set the strategy being used"""
        self.strategy_id = strategy_id
        self.strategy_params = params or {}
        return self
        
    def log_decision(self, decision: Dict) -> 'TruthManifest':
        """Log a trading decision"""
        self.decisions.append({
            "timestamp": datetime.now().isoformat(),
            **decision
        })
        return self
        
    def set_metrics(self, metrics: Dict) -> 'TruthManifest':
        """Set the final metrics"""
        self.metrics = metrics
        return self
        
    def get_manifest_hash(self) -> str:
        """Get a hash of the entire manifest"""
        manifest_str = json.dumps({
            "git_sha": self.git_sha,
            "config_hash": self.config_hash,
            "dataset_hash": self.dataset_hash,
            "strategy_id": self.strategy_id
        }, sort_keys=True)
        return hashlib.sha256(manifest_str.encode()).hexdigest()[:16]
        
    def save(self, path: str = None) -> str:
        """Save the manifest to disk"""
        if path is None:
            os.makedirs("logs/manifests", exist_ok=True)
            path = f"logs/manifests/{self.run_id}.json"
            
        manifest_dict = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "manifest_hash": self.get_manifest_hash(),
            "code": {
                "git_sha": self.git_sha,
                "git_branch": self.git_branch,
                "git_dirty": self.git_dirty
            },
            "config": {
                "hash": self.config_hash,
                "snapshot": self.config_snapshot
            },
            "dataset": {
                "hash": self.dataset_hash,
                "info": self.dataset_info
            },
            "strategy": {
                "id": self.strategy_id,
                "params": self.strategy_params
            },
            "decisions": self.decisions,
            "metrics": self.metrics
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(manifest_dict, f, indent=2, default=str)
            
        return path
        
    @classmethod
    def load(cls, path: str) -> 'TruthManifest':
        """Load a manifest from disk"""
        with open(path, "r") as f:
            data = json.load(f)
            
        manifest = cls(
            run_id=data["run_id"],
            timestamp=data["timestamp"]
        )
        manifest.git_sha = data["code"]["git_sha"]
        manifest.git_branch = data["code"]["git_branch"]
        manifest.git_dirty = data["code"]["git_dirty"]
        manifest.config_hash = data["config"]["hash"]
        manifest.config_snapshot = data["config"]["snapshot"]
        manifest.dataset_hash = data["dataset"]["hash"]
        manifest.dataset_info = data["dataset"]["info"]
        manifest.strategy_id = data["strategy"]["id"]
        manifest.strategy_params = data["strategy"]["params"]
        manifest.decisions = data["decisions"]
        manifest.metrics = data["metrics"]
        
        return manifest
        
    def verify(self) -> Dict[str, bool]:
        """Verify the manifest integrity"""
        return {
            "git_sha_valid": len(self.git_sha) == 40 or self.git_sha in ["unknown", "unavailable"],
            "config_hash_valid": len(self.config_hash) == 16,
            "dataset_hash_valid": len(self.dataset_hash) == 16,
            "has_strategy": len(self.strategy_id) > 0,
            "has_decisions": len(self.decisions) > 0,
            "has_metrics": len(self.metrics) > 0
        }
        
    def summary(self) -> str:
        """Get a human-readable summary"""
        return f"""
=== TRUTH MANIFEST ===
Run ID: {self.run_id}
Timestamp: {self.timestamp}
Manifest Hash: {self.get_manifest_hash()}

CODE:
  Git SHA: {self.git_sha[:8]}...
  Branch: {self.git_branch}
  Dirty: {self.git_dirty}

CONFIG:
  Hash: {self.config_hash}

DATASET:
  Hash: {self.dataset_hash}
  Info: {self.dataset_info}

STRATEGY:
  ID: {self.strategy_id}
  Params: {self.strategy_params}

RESULTS:
  Decisions: {len(self.decisions)}
  Metrics: {self.metrics}
========================
"""


class ManifestRegistry:
    """
    Registry of all truth manifests.
    
    Enables:
    - Finding manifests by hash
    - Comparing runs
    - Tracking strategy evolution
    """
    
    def __init__(self, manifests_dir: str = "logs/manifests"):
        self.manifests_dir = manifests_dir
        os.makedirs(manifests_dir, exist_ok=True)
        
    def list_manifests(self) -> List[str]:
        """List all manifest files"""
        if not os.path.exists(self.manifests_dir):
            return []
        return [f for f in os.listdir(self.manifests_dir) if f.endswith(".json")]
        
    def get_manifest(self, run_id: str) -> Optional[TruthManifest]:
        """Get a manifest by run ID"""
        path = os.path.join(self.manifests_dir, f"{run_id}.json")
        if os.path.exists(path):
            return TruthManifest.load(path)
        return None
        
    def find_by_git_sha(self, sha: str) -> List[TruthManifest]:
        """Find all manifests for a specific git SHA"""
        results = []
        for filename in self.list_manifests():
            manifest = TruthManifest.load(os.path.join(self.manifests_dir, filename))
            if manifest.git_sha.startswith(sha):
                results.append(manifest)
        return results
        
    def find_by_strategy(self, strategy_id: str) -> List[TruthManifest]:
        """Find all manifests for a specific strategy"""
        results = []
        for filename in self.list_manifests():
            manifest = TruthManifest.load(os.path.join(self.manifests_dir, filename))
            if manifest.strategy_id == strategy_id:
                results.append(manifest)
        return results
        
    def compare(self, run_id_1: str, run_id_2: str) -> Dict[str, Any]:
        """Compare two runs"""
        m1 = self.get_manifest(run_id_1)
        m2 = self.get_manifest(run_id_2)
        
        if not m1 or not m2:
            return {"error": "One or both manifests not found"}
            
        return {
            "code_changed": m1.git_sha != m2.git_sha,
            "config_changed": m1.config_hash != m2.config_hash,
            "dataset_changed": m1.dataset_hash != m2.dataset_hash,
            "strategy_changed": m1.strategy_id != m2.strategy_id,
            "metrics_diff": {
                k: (m1.metrics.get(k), m2.metrics.get(k))
                for k in set(m1.metrics.keys()) | set(m2.metrics.keys())
            }
        }


# Example usage
if __name__ == "__main__":
    # Create a manifest for a trading run
    manifest = TruthManifest()
    
    # Set configuration
    manifest.set_config({
        "min_confluence": 10,
        "min_confidence": 0.80,
        "max_drawdown": 0.10
    })
    
    # Set dataset
    manifest.set_dataset(
        data=[{"price": 100}, {"price": 101}],
        info={"symbol": "BTC", "timeframe": "1h", "bars": 1000}
    )
    
    # Set strategy
    manifest.set_strategy("confluence_v2", {"version": "2.0"})
    
    # Log some decisions
    manifest.log_decision({
        "action": "BUY",
        "price": 50000,
        "confidence": 0.85,
        "vetoed": False
    })
    
    manifest.log_decision({
        "action": "SELL",
        "price": 51000,
        "confidence": 0.55,
        "vetoed": True,
        "veto_reasons": ["LOW_CONFIDENCE"]
    })
    
    # Set final metrics
    manifest.set_metrics({
        "win_rate": 0.72,
        "profit_factor": 1.8,
        "total_trades": 150,
        "sharpe_ratio": 1.5
    })
    
    # Save and print summary
    path = manifest.save()
    print(f"Saved to: {path}")
    print(manifest.summary())
    
    # Verify integrity
    print(f"Verification: {manifest.verify()}")
