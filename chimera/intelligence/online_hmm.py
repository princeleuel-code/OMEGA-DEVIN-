"""
Online Hidden Markov Model (HMM) filtering (Gaussian emissions).

Design goals:
- No external dependencies
- Deterministic and testable
- Suitable for streaming updates (online filtering)

This is a building block for regime detection, not a complete regime classifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import math


def _normalize(probs: List[float]) -> List[float]:
    s = sum(probs)
    if s <= 0:
        n = len(probs)
        return [1.0 / n for _ in probs] if n else []
    return [p / s for p in probs]


def _gaussian_pdf(x: float, mean: float, var: float) -> float:
    var = max(var, 1e-12)
    z = (x - mean) ** 2 / var
    return math.exp(-0.5 * z) / math.sqrt(2.0 * math.pi * var)


@dataclass
class OnlineGaussianHMM:
    """
    Online HMM filter with optional exponential-averaging parameter updates.

    Args:
        transition: row-stochastic transition matrix A (n_states x n_states)
        means: per-state emission mean
        variances: per-state emission variance
        init_probs: initial state distribution (defaults to uniform)
        learning_rate: if > 0, update mean/variance online using posterior weights
    """

    transition: List[List[float]]
    means: List[float]
    variances: List[float]
    init_probs: Optional[List[float]] = None
    learning_rate: float = 0.0

    def __post_init__(self) -> None:
        n = len(self.means)
        if n <= 0:
            raise ValueError("means must be non-empty")
        if len(self.variances) != n:
            raise ValueError("variances must match means length")
        if len(self.transition) != n or any(len(row) != n for row in self.transition):
            raise ValueError("transition must be n_states x n_states")

        # Normalize transition rows.
        self.transition = [_normalize(list(row)) for row in self.transition]

        if self.init_probs is None:
            self.init_probs = [1.0 / n for _ in range(n)]
        else:
            if len(self.init_probs) != n:
                raise ValueError("init_probs must match means length")
            self.init_probs = _normalize(list(self.init_probs))

        # Filter state.
        self.state_probs: List[float] = list(self.init_probs)

    def update(self, x: float) -> List[float]:
        """
        Update filtered state probabilities given observation x.
        Returns the updated state probabilities.
        """
        n = len(self.means)

        # Predict: alpha_pred[j] = sum_i alpha[i] * A[i][j]
        pred = [0.0 for _ in range(n)]
        for i in range(n):
            ai = self.state_probs[i]
            if ai <= 0:
                continue
            row = self.transition[i]
            for j in range(n):
                pred[j] += ai * row[j]

        # Update with emission likelihood.
        post = [0.0 for _ in range(n)]
        for j in range(n):
            like = _gaussian_pdf(x, self.means[j], self.variances[j])
            post[j] = pred[j] * like
        post = _normalize(post)

        # Optional online parameter update (EMA-like) using posterior weights.
        lr = float(self.learning_rate)
        if lr > 0:
            for j in range(n):
                w = post[j]
                if w <= 0:
                    continue
                mu = self.means[j]
                mu_new = mu + lr * w * (x - mu)
                # Update variance with the new mean (stable incremental form).
                var = self.variances[j]
                var_new = var + lr * w * (((x - mu_new) ** 2) - var)
                self.means[j] = mu_new
                self.variances[j] = max(var_new, 1e-12)

        self.state_probs = post
        return post

    def most_likely_state(self) -> int:
        if not self.state_probs:
            return 0
        return max(range(len(self.state_probs)), key=lambda i: self.state_probs[i])

