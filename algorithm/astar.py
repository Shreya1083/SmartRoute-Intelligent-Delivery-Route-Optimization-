"""
Algorithm module wrapper for A* Search.
Re-exports the core functions from backend.astar.
"""

from backend.astar import (
    calculate_heuristic,
    verify_heuristic_consistency,
    astar_search,
)

__all__ = [
    "calculate_heuristic",
    "verify_heuristic_consistency",
    "astar_search",
]
