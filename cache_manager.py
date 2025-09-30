"""
Cache Manager

Sistema di cache intelligente per ottimizzare le performance del gestionale.

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import time
import threading
import json
import pickle
from typing import Any, Dict, Optional, Callable, Union
from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass
class CacheEntry:
    """Entry della cache"""
    key: str
    value: Any
    timestamp: float
    ttl: float  # Time To Live in seconds
    access_count: int = 0
    last_access: float = 0.0


class CacheManager:
    """Gestore cache intelligente"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        """
        Inizializza il cache manager
        
        Args:
            max_size: Dimensione massima della cache
            default_ttl: TTL di default in secondi
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.RLock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        
        # Avvia thread di pulizia
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self.cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Ottiene un valore dalla cache
        
        Args:
            key: Chiave del valore
            
        Returns:
            Valore dalla cache o None se non trovato/scaduto
        """
        with self.lock:
            self.stats['total_requests'] += 1
            
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            entry = self.cache[key]
            
            # Controlla se è scaduto
            if time.time() - entry.timestamp > entry.ttl:
                del self.cache[key]
                self.stats['misses'] += 1
                return None
            
            # Aggiorna statistiche di accesso
            entry.access_count += 1
            entry.last_access = time.time()
            self.stats['hits'] += 1
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Imposta un valore nella cache
        
        Args:
            key: Chiave del valore
            value: Valore da memorizzare
            ttl: TTL personalizzato (opzionale)
            
        Returns:
            True se impostato con successo
        """
        with self.lock:
            # Se la cache è piena, rimuovi l'entry meno usata
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_least_used()
            
            # Crea entry
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl or self.default_ttl,
                access_count=0,
                last_access=time.time()
            )
            
            self.cache[key] = entry
            return True
    
    def delete(self, key: str) -> bool:
        """
        Elimina un valore dalla cache
        
        Args:
            key: Chiave del valore
            
        Returns:
            True se eliminato con successo
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Svuota completamente la cache"""
        with self.lock:
            self.cache.clear()
            self.stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'total_requests': 0
            }
    
    def exists(self, key: str) -> bool:
        """
        Controlla se una chiave esiste nella cache
        
        Args:
            key: Chiave da controllare
            
        Returns:
            True se la chiave esiste e non è scaduta
        """
        with self.lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            return time.time() - entry.timestamp <= entry.ttl
    
    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[float] = None) -> Any:
        """
        Ottiene un valore dalla cache o lo crea se non esiste
        
        Args:
            key: Chiave del valore
            factory: Funzione per creare il valore se non esiste
            ttl: TTL personalizzato (opzionale)
            
        Returns:
            Valore dalla cache o creato
        """
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalida tutte le chiavi che corrispondono a un pattern
        
        Args:
            pattern: Pattern da cercare nelle chiavi
        """
        with self.lock:
            keys_to_remove = []
            for key in self.cache.keys():
                if pattern in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Ottiene le statistiche della cache"""
        with self.lock:
            hit_rate = 0.0
            if self.stats['total_requests'] > 0:
                hit_rate = (self.stats['hits'] / self.stats['total_requests']) * 100
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'total_requests': self.stats['total_requests']
            }
    
    def _evict_least_used(self):
        """Rimuove l'entry meno usata dalla cache"""
        if not self.cache:
            return
        
        # Trova l'entry con il minor access_count e last_access più vecchio
        least_used_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k].access_count, self.cache[k].last_access)
        )
        
        del self.cache[least_used_key]
        self.stats['evictions'] += 1
    
    def _cleanup_loop(self):
        """Loop di pulizia per rimuovere entry scadute"""
        while True:
            try:
                time.sleep(60)  # Pulisci ogni minuto
                self._cleanup_expired()
            except Exception as e:
                print(f"❌ Errore pulizia cache: {e}")
    
    def _cleanup_expired(self):
        """Rimuove le entry scadute"""
        with self.lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self.cache.items():
                if current_time - entry.timestamp > entry.ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
    
    def export_cache(self, filename: str):
        """Esporta la cache in un file"""
        with self.lock:
            try:
                cache_data = {
                    'entries': {},
                    'stats': self.stats
                }
                
                for key, entry in self.cache.items():
                    cache_data['entries'][key] = {
                        'value': entry.value,
                        'timestamp': entry.timestamp,
                        'ttl': entry.ttl,
                        'access_count': entry.access_count,
                        'last_access': entry.last_access
                    }
                
                with open(filename, 'w') as f:
                    json.dump(cache_data, f, indent=2, default=str)
                
                print(f"💾 Cache esportata in {filename}")
                return True
            except Exception as e:
                print(f"❌ Errore esportazione cache: {e}")
                return False
    
    def import_cache(self, filename: str):
        """Importa la cache da un file"""
        with self.lock:
            try:
                with open(filename, 'r') as f:
                    cache_data = json.load(f)
                
                self.cache.clear()
                for key, entry_data in cache_data['entries'].items():
                    entry = CacheEntry(
                        key=key,
                        value=entry_data['value'],
                        timestamp=entry_data['timestamp'],
                        ttl=entry_data['ttl'],
                        access_count=entry_data['access_count'],
                        last_access=entry_data['last_access']
                    )
                    self.cache[key] = entry
                
                self.stats = cache_data['stats']
                print(f"📥 Cache importata da {filename}")
                return True
            except Exception as e:
                print(f"❌ Errore importazione cache: {e}")
                return False


class DatabaseCache:
    """Cache specializzata per query database"""
    
    def __init__(self, cache_manager: CacheManager, ttl: float = 1800):
        """
        Inizializza la cache per database
        
        Args:
            cache_manager: Istanza del cache manager
            ttl: TTL per le query database
        """
        self.cache_manager = cache_manager
        self.ttl = ttl
    
    def get_query_result(self, query: str, params: tuple = ()) -> Optional[Any]:
        """
        Ottiene il risultato di una query dalla cache
        
        Args:
            query: Query SQL
            params: Parametri della query
            
        Returns:
            Risultato della query o None
        """
        key = self._generate_query_key(query, params)
        return self.cache_manager.get(key)
    
    def set_query_result(self, query: str, result: Any, params: tuple = (), ttl: Optional[float] = None):
        """
        Imposta il risultato di una query nella cache
        
        Args:
            query: Query SQL
            result: Risultato della query
            params: Parametri della query
            ttl: TTL personalizzato
        """
        key = self._generate_query_key(query, params)
        self.cache_manager.set(key, result, ttl or self.ttl)
    
    def invalidate_table(self, table_name: str):
        """
        Invalida tutte le query relative a una tabella
        
        Args:
            table_name: Nome della tabella
        """
        self.cache_manager.invalidate_pattern(f"db_{table_name}_")
    
    def _generate_query_key(self, query: str, params: tuple) -> str:
        """Genera una chiave univoca per una query"""
        query_hash = hashlib.md5(f"{query}_{params}".encode()).hexdigest()
        return f"db_query_{query_hash}"


class UICache:
    """Cache specializzata per elementi UI"""
    
    def __init__(self, cache_manager: CacheManager, ttl: float = 3600):
        """
        Inizializza la cache per UI
        
        Args:
            cache_manager: Istanza del cache manager
            ttl: TTL per gli elementi UI
        """
        self.cache_manager = cache_manager
        self.ttl = ttl
    
    def get_widget_data(self, widget_id: str) -> Optional[Any]:
        """Ottiene i dati di un widget dalla cache"""
        key = f"ui_widget_{widget_id}"
        return self.cache_manager.get(key)
    
    def set_widget_data(self, widget_id: str, data: Any, ttl: Optional[float] = None):
        """Imposta i dati di un widget nella cache"""
        key = f"ui_widget_{widget_id}"
        self.cache_manager.set(key, data, ttl or self.ttl)
    
    def get_form_data(self, form_name: str) -> Optional[Dict]:
        """Ottiene i dati di un form dalla cache"""
        key = f"ui_form_{form_name}"
        return self.cache_manager.get(key)
    
    def set_form_data(self, form_name: str, data: Dict, ttl: Optional[float] = None):
        """Imposta i dati di un form nella cache"""
        key = f"ui_form_{form_name}"
        self.cache_manager.set(key, data, ttl or self.ttl)
    
    def invalidate_form(self, form_name: str):
        """Invalida i dati di un form"""
        key = f"ui_form_{form_name}"
        self.cache_manager.delete(key)
    
    def invalidate_all_ui(self):
        """Invalida tutti i dati UI"""
        self.cache_manager.invalidate_pattern("ui_")


# Cache globale
_global_cache_manager = None
_global_database_cache = None
_global_ui_cache = None


def get_cache_manager() -> CacheManager:
    """Ottiene l'istanza globale del cache manager"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def get_database_cache() -> DatabaseCache:
    """Ottiene l'istanza globale della cache database"""
    global _global_database_cache
    if _global_database_cache is None:
        _global_database_cache = DatabaseCache(get_cache_manager())
    return _global_database_cache


def get_ui_cache() -> UICache:
    """Ottiene l'istanza globale della cache UI"""
    global _global_ui_cache
    if _global_ui_cache is None:
        _global_ui_cache = UICache(get_cache_manager())
    return _global_ui_cache


if __name__ == "__main__":
    # Test del cache manager
    print("🧠 Test Cache Manager")
    print("=" * 30)
    
    # Crea cache manager
    cache = CacheManager(max_size=10, default_ttl=5)
    
    # Test operazioni base
    print("📝 Test operazioni base...")
    cache.set("test1", "valore1")
    cache.set("test2", "valore2", ttl=10)
    
    print(f"test1: {cache.get('test1')}")
    print(f"test2: {cache.get('test2')}")
    print(f"test3: {cache.get('test3')}")
    
    # Test get_or_set
    print("\n🔄 Test get_or_set...")
    value = cache.get_or_set("test4", lambda: "valore4_creato")
    print(f"test4: {value}")
    
    # Test statistiche
    print("\n📊 Statistiche:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Test database cache
    print("\n🗄️ Test Database Cache...")
    db_cache = DatabaseCache(cache)
    db_cache.set_query_result("SELECT * FROM test", [1, 2, 3], ())
    result = db_cache.get_query_result("SELECT * FROM test", ())
    print(f"Query result: {result}")
    
    # Test UI cache
    print("\n🖥️ Test UI Cache...")
    ui_cache = UICache(cache)
    ui_cache.set_widget_data("button1", {"text": "Test", "state": "normal"})
    widget_data = ui_cache.get_widget_data("button1")
    print(f"Widget data: {widget_data}")
    
    print("\n✅ Test completato!")
