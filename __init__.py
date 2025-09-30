"""
Optimization Package

Sistema di ottimizzazione completo per il Gestionale Biciclette.

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

from .performance_optimizer import PerformanceOptimizer, PerformanceMetrics
from .cache_manager import (
    CacheManager, DatabaseCache, UICache,
    get_cache_manager, get_database_cache, get_ui_cache
)
from .lazy_loader import LazyLoader, LoadState, get_lazy_loader

__all__ = [
    'PerformanceOptimizer', 'PerformanceMetrics',
    'CacheManager', 'DatabaseCache', 'UICache',
    'get_cache_manager', 'get_database_cache', 'get_ui_cache',
    'LazyLoader', 'LoadState', 'get_lazy_loader'
]
