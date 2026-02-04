"""
Truth Manifest - Proof/audit layer for every run

Every run must be provable: what inputs, what outputs, what decisions.
"""

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class TruthManifest:
    """
    Immutable record of a trading run.
    
    Contains everything needed to reproduce and verify the run:
    - Command and configuration
    - Input data signatures
    - Git state
    - All decisions made
    - Final verdict
    """
    
    # Run identification
    run_id: str = ""
    timestamp: str = ""
    
    # Command info
    command: str = ""
    modes: Dict[str, Any] = field(default_factory=dict)
    
    # Input signatures
    input_files: Dict[str, str] = field(default_factory=dict)  # path -> hash
    config_hash: str = ""
    
    # Git state
    git_sha: str = ""
    git_branch: str = ""
    git_dirty: bool = False
    
    # Decisions
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Verdict
    verdict: str = "PENDING"  # PENDING, VERIFIED, FAILED, ERROR
    checks_passed: int = 0
    checks_total: int = 0
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.run_id:
            self.run_id = self._generate_run_id()
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def _generate_run_id(self) -> str:
        """Generate unique run ID"""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rand = hashlib.sha256(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:8]
        return f"run_{ts}_{rand}"
    
    @staticmethod
    def hash_file(path: Path) -> str:
        """Compute SHA256 hash of a file"""
        if not path.exists():
            return "FILE_NOT_FOUND"
        
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    @staticmethod
    def hash_dict(d: Dict) -> str:
        """Compute deterministic hash of a dictionary"""
        canonical = json.dumps(d, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def capture_git_state(self):
        """Capture current git state"""
        try:
            self.git_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            self.git_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            # Check for uncommitted changes
            status = subprocess.check_output(
                ["git", "status", "--porcelain"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            self.git_dirty = len(status) > 0
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.git_sha = "NOT_A_GIT_REPO"
            self.git_branch = "N/A"
            self.git_dirty = False
    
    def add_input_file(self, path: Path):
        """Register an input file with its hash"""
        self.input_files[str(path)] = self.hash_file(path)
    
    def add_decision(self, decision: Dict[str, Any]):
        """Record a decision"""
        decision["_seq"] = len(self.decisions)
        decision["_ts"] = datetime.utcnow().isoformat()
        self.decisions.append(decision)
    
    def set_config(self, config: Dict[str, Any]):
        """Set configuration and compute hash"""
        self.modes = config
        self.config_hash = self.hash_dict(config)
    
    def finalize(self, passed: int, total: int, errors: Optional[List[str]] = None):
        """Finalize the manifest with verdict"""
        self.checks_passed = passed
        self.checks_total = total
        self.errors = errors or []
        
        if errors:
            self.verdict = "ERROR"
        elif passed == total:
            self.verdict = "VERIFIED"
        else:
            self.verdict = "FAILED"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "command": self.command,
            "modes": self.modes,
            "input_files": self.input_files,
            "config_hash": self.config_hash,
            "git": {
                "sha": self.git_sha,
                "branch": self.git_branch,
                "dirty": self.git_dirty
            },
            "decisions_count": len(self.decisions),
            "verdict": {
                "status": self.verdict,
                "checks_passed": self.checks_passed,
                "checks_total": self.checks_total,
                "errors": self.errors
            }
        }
    
    def save(self, output_dir: Path):
        """Save manifest and decisions to files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save manifest
        manifest_path = output_dir / f"{self.run_id}_MANIFEST.json"
        with open(manifest_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        
        # Save decisions
        decisions_path = output_dir / f"{self.run_id}_DECISIONS.jsonl"
        with open(decisions_path, "w") as f:
            for decision in self.decisions:
                f.write(json.dumps(decision) + "\n")
        
        # Save verdict summary
        verdict_path = output_dir / f"{self.run_id}_VERDICT.json"
        with open(verdict_path, "w") as f:
            json.dump({
                "run_id": self.run_id,
                "verdict": self.verdict,
                "checks_passed": self.checks_passed,
                "checks_total": self.checks_total,
                "timestamp": self.timestamp
            }, f, indent=2)
        
        return manifest_path, decisions_path, verdict_path


def create_manifest(command: str, config: Dict[str, Any]) -> TruthManifest:
    """Factory function to create a new manifest"""
    manifest = TruthManifest(command=command)
    manifest.set_config(config)
    manifest.capture_git_state()
    return manifest
