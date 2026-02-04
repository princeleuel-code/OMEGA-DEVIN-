"""
MAP-Elites Archive - Maintain diverse population of strategies

MAP-Elites keeps the best strategy for each "niche" in behavior space.
This prevents collapse to a single strategy and maintains diversity.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple, Any
from pathlib import Path
import json
import logging

from .genome import StrategyGenome
from .behaviors import BehaviorDescriptor, get_grid_dimensions, get_total_cells


logger = logging.getLogger(__name__)


@dataclass
class ArchiveEntry:
    """An entry in the MAP-Elites archive"""
    genome: StrategyGenome
    behavior: BehaviorDescriptor
    fitness: float
    generation_added: int
    evaluations: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "genome": self.genome.to_dict(),
            "behavior": self.behavior.to_dict(),
            "fitness": self.fitness,
            "generation_added": self.generation_added,
            "evaluations": self.evaluations
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ArchiveEntry":
        return cls(
            genome=StrategyGenome.from_dict(d["genome"]),
            behavior=BehaviorDescriptor(**d["behavior"]),
            fitness=d["fitness"],
            generation_added=d["generation_added"],
            evaluations=d.get("evaluations", 1)
        )


class MAPElitesArchive:
    """
    MAP-Elites archive for maintaining diverse strategies.
    
    The archive is a grid where each cell corresponds to a unique
    combination of behavior descriptors. Only the best (highest fitness)
    strategy for each cell is kept.
    """
    
    def __init__(self):
        self._archive: Dict[Tuple[int, ...], ArchiveEntry] = {}
        self._generation = 0
        self._total_evaluations = 0
        self._improvements = 0
        self._discoveries = 0
    
    def add(
        self,
        genome: StrategyGenome,
        behavior: BehaviorDescriptor,
        fitness: float
    ) -> bool:
        """
        Try to add a genome to the archive.
        
        Returns True if the genome was added (new cell or better fitness).
        """
        self._total_evaluations += 1
        key = behavior.to_tuple()
        
        if key not in self._archive:
            # New cell discovered
            self._archive[key] = ArchiveEntry(
                genome=genome,
                behavior=behavior,
                fitness=fitness,
                generation_added=self._generation
            )
            self._discoveries += 1
            logger.info(f"New niche discovered: {key} with fitness {fitness:.4f}")
            return True
        
        existing = self._archive[key]
        if fitness > existing.fitness:
            # Better strategy for this cell
            self._archive[key] = ArchiveEntry(
                genome=genome,
                behavior=behavior,
                fitness=fitness,
                generation_added=self._generation,
                evaluations=existing.evaluations + 1
            )
            self._improvements += 1
            logger.info(
                f"Improved niche {key}: {existing.fitness:.4f} -> {fitness:.4f}"
            )
            return True
        
        # Not better than existing
        existing.evaluations += 1
        return False
    
    def get(self, behavior: BehaviorDescriptor) -> Optional[ArchiveEntry]:
        """Get the entry for a specific behavior"""
        return self._archive.get(behavior.to_tuple())
    
    def get_all(self) -> List[ArchiveEntry]:
        """Get all entries in the archive"""
        return list(self._archive.values())
    
    def get_best(self, n: int = 10) -> List[ArchiveEntry]:
        """Get the n best entries by fitness"""
        entries = self.get_all()
        entries.sort(key=lambda e: e.fitness, reverse=True)
        return entries[:n]
    
    def get_random(self) -> Optional[ArchiveEntry]:
        """Get a random entry from the archive"""
        import random
        if not self._archive:
            return None
        key = random.choice(list(self._archive.keys()))
        return self._archive[key]
    
    def get_random_weighted(self) -> Optional[ArchiveEntry]:
        """Get a random entry, weighted by fitness"""
        import random
        if not self._archive:
            return None
        
        entries = list(self._archive.values())
        # Shift fitness to be positive
        min_fit = min(e.fitness for e in entries)
        weights = [e.fitness - min_fit + 0.1 for e in entries]
        total = sum(weights)
        weights = [w / total for w in weights]
        
        return random.choices(entries, weights=weights, k=1)[0]
    
    def increment_generation(self):
        """Move to next generation"""
        self._generation += 1
    
    @property
    def size(self) -> int:
        """Number of filled cells"""
        return len(self._archive)
    
    @property
    def coverage(self) -> float:
        """Fraction of cells filled"""
        return self.size / get_total_cells()
    
    @property
    def generation(self) -> int:
        return self._generation
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get archive statistics"""
        if not self._archive:
            return {
                "size": 0,
                "coverage": 0.0,
                "generation": self._generation,
                "total_evaluations": self._total_evaluations,
                "discoveries": self._discoveries,
                "improvements": self._improvements
            }
        
        fitnesses = [e.fitness for e in self._archive.values()]
        
        return {
            "size": self.size,
            "coverage": self.coverage,
            "coverage_pct": f"{self.coverage * 100:.1f}%",
            "generation": self._generation,
            "total_evaluations": self._total_evaluations,
            "discoveries": self._discoveries,
            "improvements": self._improvements,
            "fitness_min": min(fitnesses),
            "fitness_max": max(fitnesses),
            "fitness_mean": sum(fitnesses) / len(fitnesses),
            "total_cells": get_total_cells()
        }
    
    def save(self, path: Path):
        """Save archive to file"""
        data = {
            "generation": self._generation,
            "total_evaluations": self._total_evaluations,
            "discoveries": self._discoveries,
            "improvements": self._improvements,
            "entries": {
                str(k): v.to_dict() 
                for k, v in self._archive.items()
            }
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved archive with {self.size} entries to {path}")
    
    def load(self, path: Path):
        """Load archive from file"""
        with open(path, "r") as f:
            data = json.load(f)
        
        self._generation = data["generation"]
        self._total_evaluations = data["total_evaluations"]
        self._discoveries = data["discoveries"]
        self._improvements = data["improvements"]
        
        self._archive = {}
        for k_str, v in data["entries"].items():
            # Parse key tuple from string
            k = tuple(int(x) for x in k_str.strip("()").split(","))
            self._archive[k] = ArchiveEntry.from_dict(v)
        
        logger.info(f"Loaded archive with {self.size} entries from {path}")
    
    def get_heatmap_data(self, dim1: int = 0, dim2: int = 1) -> Dict[Tuple[int, int], float]:
        """
        Get 2D heatmap data for visualization.
        
        Projects the archive onto two dimensions, taking max fitness for each cell.
        """
        heatmap: Dict[Tuple[int, int], float] = {}
        
        for key, entry in self._archive.items():
            cell = (key[dim1], key[dim2])
            if cell not in heatmap or entry.fitness > heatmap[cell]:
                heatmap[cell] = entry.fitness
        
        return heatmap
