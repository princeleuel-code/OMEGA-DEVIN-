from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class ExperimentRow:
    experiment_id: str
    run_id: str
    created_at: str
    symbol: str
    timeframe: str
    dataset_hash: str
    genome_id: str
    passed: bool
    score: float
    fail_reasons: Sequence[str]
    artifacts_dir: str
    genome_json: Dict[str, Any]
    results_json: Dict[str, Any]


class ExperimentRegistry:
    """SQLite registry for experiment runs.

    This is the research agent's SSOT for:
    - reproducibility: dataset_hash + genome_json + config snapshot
    - searchability: leaderboard queries
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        try:
            self._conn.close()
        finally:
            self._conn = None  # type: ignore[assignment]

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
              experiment_id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              symbol TEXT NOT NULL,
              timeframe TEXT NOT NULL,
              dataset_hash TEXT NOT NULL,
              genome_id TEXT NOT NULL,
              passed INTEGER NOT NULL,
              score REAL NOT NULL,
              fail_reasons_json TEXT NOT NULL,
              artifacts_dir TEXT NOT NULL,
              genome_json TEXT NOT NULL,
              results_json TEXT NOT NULL
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_experiments_symbol_tf ON experiments(symbol, timeframe)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_experiments_passed_score ON experiments(passed, score)")
        self._conn.commit()

    def upsert(self, row: ExperimentRow) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO experiments (
              experiment_id, run_id, created_at, symbol, timeframe, dataset_hash,
              genome_id, passed, score, fail_reasons_json, artifacts_dir, genome_json, results_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(experiment_id) DO UPDATE SET
              run_id=excluded.run_id,
              created_at=excluded.created_at,
              symbol=excluded.symbol,
              timeframe=excluded.timeframe,
              dataset_hash=excluded.dataset_hash,
              genome_id=excluded.genome_id,
              passed=excluded.passed,
              score=excluded.score,
              fail_reasons_json=excluded.fail_reasons_json,
              artifacts_dir=excluded.artifacts_dir,
              genome_json=excluded.genome_json,
              results_json=excluded.results_json
            """,
            (
                row.experiment_id,
                row.run_id,
                row.created_at,
                row.symbol,
                row.timeframe,
                row.dataset_hash,
                row.genome_id,
                int(bool(row.passed)),
                float(row.score),
                json.dumps(list(row.fail_reasons), sort_keys=True),
                row.artifacts_dir,
                json.dumps(row.genome_json, sort_keys=True),
                json.dumps(row.results_json, sort_keys=True),
            ),
        )
        self._conn.commit()

    def get(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM experiments WHERE experiment_id = ?", (str(experiment_id),))
        r = cur.fetchone()
        if not r:
            return None
        return self._row_to_dict(r)

    def leaderboard(
        self,
        *,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = 10,
        passed_only: bool = True,
    ) -> List[Dict[str, Any]]:
        clauses: List[str] = []
        args: List[Any] = []
        if symbol:
            clauses.append("symbol = ?")
            args.append(str(symbol))
        if timeframe:
            clauses.append("timeframe = ?")
            args.append(str(timeframe))
        if passed_only:
            clauses.append("passed = 1")

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        lim = max(1, min(1000, int(limit)))
        sql = (
            "SELECT * FROM experiments"
            + where
            + " ORDER BY passed DESC, score DESC, created_at DESC LIMIT ?"
        )
        args.append(lim)

        cur = self._conn.cursor()
        cur.execute(sql, tuple(args))
        rows = cur.fetchall()
        return [self._row_to_dict(r) for r in rows]

    def _row_to_dict(self, r: sqlite3.Row) -> Dict[str, Any]:
        return {
            "experiment_id": r["experiment_id"],
            "run_id": r["run_id"],
            "created_at": r["created_at"],
            "symbol": r["symbol"],
            "timeframe": r["timeframe"],
            "dataset_hash": r["dataset_hash"],
            "genome_id": r["genome_id"],
            "passed": bool(r["passed"]),
            "score": float(r["score"]),
            "fail_reasons": json.loads(r["fail_reasons_json"]),
            "artifacts_dir": r["artifacts_dir"],
            "genome": json.loads(r["genome_json"]),
            "results": json.loads(r["results_json"]),
        }

