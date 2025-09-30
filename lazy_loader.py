"""
Lazy Loader

Sistema di caricamento lazy per ottimizzare le performance del gestionale.

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import threading
import time
from typing import Any, Callable, Dict, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import weakref


class LoadState(Enum):
    """Stati di caricamento"""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


@dataclass
class LazyItem:
    """Item lazy caricato"""
    key: str
    loader: Callable[[], Any]
    state: LoadState = LoadState.NOT_LOADED
    value: Any = None
    error: Optional[Exception] = None
    load_time: float = 0.0
    access_count: int = 0
    last_access: float = 0.0
    dependencies: List[str] = None
    priority: int = 0  # Priorità di caricamento (più alto = più prioritario)


class LazyLoader:
    """Gestore di caricamento lazy"""
    
    def __init__(self, max_concurrent_loads: int = 5):
        """
        Inizializza il lazy loader
        
        Args:
            max_concurrent_loads: Numero massimo di caricamenti concorrenti
        """
        self.max_concurrent_loads = max_concurrent_loads
        self.items: Dict[str, LazyItem] = {}
        self.loading_items: Dict[str, threading.Thread] = {}
        self.lock = threading.RLock()
        self.loading_semaphore = threading.Semaphore(max_concurrent_loads)
        
        # Callback per eventi
        self.on_load_start: Optional[Callable[[str], None]] = None
        self.on_load_complete: Optional[Callable[[str, Any], None]] = None
        self.on_load_error: Optional[Callable[[str, Exception], None]] = None
    
    def register(self, key: str, loader: Callable[[], Any], 
                dependencies: List[str] = None, priority: int = 0) -> bool:
        """
        Registra un item per il caricamento lazy
        
        Args:
            key: Chiave univoca dell'item
            loader: Funzione per caricare l'item
            dependencies: Dipendenze da caricare prima
            priority: Priorità di caricamento
            
        Returns:
            True se registrato con successo
        """
        with self.lock:
            if key in self.items:
                return False
            
            self.items[key] = LazyItem(
                key=key,
                loader=loader,
                dependencies=dependencies or [],
                priority=priority
            )
            return True
    
    def get(self, key: str, force_reload: bool = False) -> Any:
        """
        Ottiene un item, caricandolo se necessario
        
        Args:
            key: Chiave dell'item
            force_reload: Se forzare il ricaricamento
            
        Returns:
            Valore dell'item o None se errore
        """
        with self.lock:
            if key not in self.items:
                return None
            
            item = self.items[key]
            
            # Aggiorna statistiche di accesso
            item.access_count += 1
            item.last_access = time.time()
            
            # Se già caricato e non forzare reload
            if item.state == LoadState.LOADED and not force_reload:
                return item.value
            
            # Se in caricamento, aspetta
            if item.state == LoadState.LOADING:
                self._wait_for_load(key)
                return item.value if item.state == LoadState.LOADED else None
            
            # Se errore e non forzare reload
            if item.state == LoadState.ERROR and not force_reload:
                return None
            
            # Carica l'item
            self._load_item(key)
            return item.value if item.state == LoadState.LOADED else None
    
    def preload(self, key: str) -> bool:
        """
        Avvia il caricamento di un item in background
        
        Args:
            key: Chiave dell'item
            
        Returns:
            True se avviato con successo
        """
        with self.lock:
            if key not in self.items:
                return False
            
            item = self.items[key]
            
            # Se già caricato o in caricamento
            if item.state in [LoadState.LOADED, LoadState.LOADING]:
                return True
            
            # Avvia caricamento in background
            self._load_item_async(key)
            return True
    
    def preload_multiple(self, keys: List[str]) -> int:
        """
        Avvia il caricamento di più item in background
        
        Args:
            keys: Lista di chiavi da precaricare
            
        Returns:
            Numero di item avviati per il caricamento
        """
        started = 0
        for key in keys:
            if self.preload(key):
                started += 1
        return started
    
    def preload_by_priority(self, max_items: int = 10) -> int:
        """
        Precarca gli item con priorità più alta
        
        Args:
            max_items: Numero massimo di item da precaricare
            
        Returns:
            Numero di item avviati per il caricamento
        """
        with self.lock:
            # Ordina per priorità (decrescente) e access_count (decrescente)
            sorted_items = sorted(
                self.items.items(),
                key=lambda x: (x[1].priority, x[1].access_count),
                reverse=True
            )
            
            started = 0
            for key, item in sorted_items:
                if started >= max_items:
                    break
                
                if item.state == LoadState.NOT_LOADED:
                    if self.preload(key):
                        started += 1
            
            return started
    
    def _load_item(self, key: str):
        """Carica un item sincronamente"""
        item = self.items[key]
        
        # Controlla dipendenze
        if not self._check_dependencies(item):
            return
        
        # Imposta stato di caricamento
        item.state = LoadState.LOADING
        
        # Callback di inizio caricamento
        if self.on_load_start:
            self.on_load_start(key)
        
        try:
            # Carica l'item
            start_time = time.time()
            item.value = item.loader()
            item.load_time = time.time() - start_time
            item.state = LoadState.LOADED
            
            # Callback di completamento
            if self.on_load_complete:
                self.on_load_complete(key, item.value)
                
        except Exception as e:
            item.error = e
            item.state = LoadState.ERROR
            
            # Callback di errore
            if self.on_load_error:
                self.on_load_error(key, e)
    
    def _load_item_async(self, key: str):
        """Carica un item in modo asincrono"""
        def load_worker():
            with self.loading_semaphore:
                self._load_item(key)
                # Rimuovi il thread dalla lista quando finisce
                with self.lock:
                    if key in self.loading_items:
                        del self.loading_items[key]
        
        thread = threading.Thread(target=load_worker, daemon=True)
        self.loading_items[key] = thread
        thread.start()
    
    def _check_dependencies(self, item: LazyItem) -> bool:
        """Controlla se le dipendenze sono soddisfatte"""
        if not item.dependencies:
            return True
        
        for dep_key in item.dependencies:
            if dep_key not in self.items:
                return False
            
            dep_item = self.items[dep_key]
            if dep_item.state != LoadState.LOADED:
                # Carica la dipendenza
                self._load_item(dep_key)
                if dep_item.state != LoadState.LOADED:
                    return False
        
        return True
    
    def _wait_for_load(self, key: str, timeout: float = 30.0):
        """Aspetta che un item finisca di caricarsi"""
        if key not in self.loading_items:
            return
        
        thread = self.loading_items[key]
        thread.join(timeout=timeout)
    
    def unload(self, key: str) -> bool:
        """
        Scarica un item dalla memoria
        
        Args:
            key: Chiave dell'item
            
        Returns:
            True se scaricato con successo
        """
        with self.lock:
            if key not in self.items:
                return False
            
            item = self.items[key]
            item.value = None
            item.state = LoadState.NOT_LOADED
            item.error = None
            return True
    
    def unload_multiple(self, keys: List[str]) -> int:
        """
        Scarica più item dalla memoria
        
        Args:
            keys: Lista di chiavi da scaricare
            
        Returns:
            Numero di item scaricati
        """
        unloaded = 0
        for key in keys:
            if self.unload(key):
                unloaded += 1
        return unloaded
    
    def unload_unused(self, max_age: float = 3600.0) -> int:
        """
        Scarica gli item non utilizzati da troppo tempo
        
        Args:
            max_age: Età massima in secondi
            
        Returns:
            Numero di item scaricati
        """
        with self.lock:
            current_time = time.time()
            keys_to_unload = []
            
            for key, item in self.items.items():
                if (item.state == LoadState.LOADED and 
                    current_time - item.last_access > max_age):
                    keys_to_unload.append(key)
            
            return self.unload_multiple(keys_to_unload)
    
    def get_stats(self) -> Dict[str, Any]:
        """Ottiene le statistiche del lazy loader"""
        with self.lock:
            stats = {
                'total_items': len(self.items),
                'loaded_items': sum(1 for item in self.items.values() 
                                  if item.state == LoadState.LOADED),
                'loading_items': sum(1 for item in self.items.values() 
                                   if item.state == LoadState.LOADING),
                'error_items': sum(1 for item in self.items.values() 
                                 if item.state == LoadState.ERROR),
                'not_loaded_items': sum(1 for item in self.items.values() 
                                       if item.state == LoadState.NOT_LOADED),
                'active_threads': len(self.loading_items),
                'max_concurrent_loads': self.max_concurrent_loads
            }
            
            # Calcola statistiche di accesso
            if self.items:
                access_counts = [item.access_count for item in self.items.values()]
                stats['avg_access_count'] = sum(access_counts) / len(access_counts)
                stats['max_access_count'] = max(access_counts)
                
                load_times = [item.load_time for item in self.items.values() 
                            if item.load_time > 0]
                if load_times:
                    stats['avg_load_time'] = sum(load_times) / len(load_times)
                    stats['max_load_time'] = max(load_times)
            
            return stats
    
    def get_item_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Ottiene informazioni dettagliate su un item"""
        with self.lock:
            if key not in self.items:
                return None
            
            item = self.items[key]
            return {
                'key': item.key,
                'state': item.state.value,
                'access_count': item.access_count,
                'last_access': item.last_access,
                'load_time': item.load_time,
                'dependencies': item.dependencies,
                'priority': item.priority,
                'has_error': item.error is not None,
                'error_message': str(item.error) if item.error else None
            }
    
    def set_priority(self, key: str, priority: int) -> bool:
        """
        Imposta la priorità di un item
        
        Args:
            key: Chiave dell'item
            priority: Nuova priorità
            
        Returns:
            True se impostata con successo
        """
        with self.lock:
            if key not in self.items:
                return False
            
            self.items[key].priority = priority
            return True
    
    def clear(self):
        """Svuota completamente il lazy loader"""
        with self.lock:
            # Aspetta che tutti i thread finiscano
            for thread in self.loading_items.values():
                thread.join(timeout=1)
            
            self.items.clear()
            self.loading_items.clear()
    
    def __del__(self):
        """Distruttore - pulisce le risorse"""
        self.clear()


# Lazy loader globale
_global_lazy_loader = None


def get_lazy_loader() -> LazyLoader:
    """Ottiene l'istanza globale del lazy loader"""
    global _global_lazy_loader
    if _global_lazy_loader is None:
        _global_lazy_loader = LazyLoader()
    return _global_lazy_loader


if __name__ == "__main__":
    # Test del lazy loader
    print("🔄 Test Lazy Loader")
    print("=" * 30)
    
    # Crea lazy loader
    loader = LazyLoader(max_concurrent_loads=3)
    
    # Definisce callback
    def on_load_start(key):
        print(f"🔄 Inizio caricamento: {key}")
    
    def on_load_complete(key, value):
        print(f"✅ Caricamento completato: {key} = {value}")
    
    def on_load_error(key, error):
        print(f"❌ Errore caricamento: {key} - {error}")
    
    loader.on_load_start = on_load_start
    loader.on_load_complete = on_load_complete
    loader.on_load_error = on_load_error
    
    # Registra alcuni item
    def load_fast():
        time.sleep(0.1)
        return "valore_veloce"
    
    def load_slow():
        time.sleep(1.0)
        return "valore_lento"
    
    def load_error():
        raise Exception("Errore di caricamento")
    
    loader.register("fast", load_fast, priority=10)
    loader.register("slow", load_slow, priority=5)
    loader.register("error", load_error, priority=1)
    loader.register("dependent", lambda: "dipendente", dependencies=["fast"], priority=8)
    
    # Test caricamento
    print("\n📝 Test caricamento...")
    print(f"fast: {loader.get('fast')}")
    print(f"slow: {loader.get('slow')}")
    print(f"error: {loader.get('error')}")
    print(f"dependent: {loader.get('dependent')}")
    
    # Test preload
    print("\n🚀 Test preload...")
    loader.preload_multiple(["fast", "slow"])
    time.sleep(2)
    
    # Test statistiche
    print("\n📊 Statistiche:")
    stats = loader.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Test info item
    print("\nℹ️ Info item 'fast':")
    info = loader.get_item_info("fast")
    if info:
        for key, value in info.items():
            print(f"{key}: {value}")
    
    print("\n✅ Test completato!")
