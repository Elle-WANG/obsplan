"""Observation planning utilities for radio astronomy."""

__all__ = [
    "ObservationPlan",
    "build_observation_plan",
    "load_sources",
    "load_telescope",
    "plot_elevation",
]

__version__ = "0.1.0"


def __getattr__(name):
    """Lazily expose the public API without importing plotting dependencies."""

    if name in __all__:
        from obsplan import planner

        return getattr(planner, name)
    raise AttributeError(f"module 'obsplan' has no attribute {name!r}")
