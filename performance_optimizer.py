"""
Performance Optimizer

Sistema di ottimizzazione per migliorare le prestazioni del gestionale.

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import gc
import psutil
import threading
import time
import sys
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import json


@dataclass
class PerformanceMetrics:
    """Metriche di performance"""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_usage_percent: float
    active_threads: int
    gc_objects: int
    timestamp: float


class PerformanceOptimizer:
    """Ottimizzatore di performance per il gestionale"""
    
    def __init__(self, enable_monitoring: bool = True):
        """
        Inizializza l'ottimizzatore
        
        Args:
            enable_monitoring: Se abilitare il monitoraggio automatico
        """
        self.enable_monitoring = enable_monitoring
        self.metrics_history: List[PerformanceMetrics] = []
        self.optimization_rules: Dict[str, Callable] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Soglie di performance
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0
        }
        
        # Inizializza regole di ottimizzazione
        self._init_optimization_rules()
        
        if self.enable_monitoring:
            self.start_monitoring()
    
    def _init_optimization_rules(self):
        """Inizializza le regole di ottimizzazione"""
        self.optimization_rules = {
            'memory_cleanup': self._cleanup_memory,
            'gc_collect': self._force_garbage_collection,
            'database_optimize': self._optimize_databases,
            'cache_cleanup': self._cleanup_caches,
            'thread_cleanup': self._cleanup_threads,
            'file_cleanup': self._cleanup_temp_files
        }
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Ottiene le metriche di performance correnti"""
        process = psutil.Process()
        
        # CPU
        cpu_percent = process.cpu_percent()
        
        # Memoria
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()
        
        # Disco
        disk_usage = psutil.disk_usage('/')
        disk_usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        # Thread
        active_threads = threading.active_count()
        
        # Garbage Collection
        gc_objects = len(gc.get_objects())
        
        return PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            disk_usage_percent=disk_usage_percent,
            active_threads=active_threads,
            gc_objects=gc_objects,
            timestamp=time.time()
        )
    
    def start_monitoring(self):
        """Avvia il monitoraggio automatico"""
        if self.running:
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        print("🔍 Monitoraggio performance avviato")
    
    def stop_monitoring(self):
        """Ferma il monitoraggio automatico"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        print("⏹️ Monitoraggio performance fermato")
    
    def _monitoring_loop(self):
        """Loop di monitoraggio continuo"""
        while self.running:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)
                
                # Mantieni solo gli ultimi 100 record
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-100:]
                
                # Controlla soglie e applica ottimizzazioni
                self._check_thresholds_and_optimize(metrics)
                
                # Pausa tra i controlli
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Errore monitoraggio: {e}")
                time.sleep(10)
    
    def _check_thresholds_and_optimize(self, metrics: PerformanceMetrics):
        """Controlla le soglie e applica ottimizzazioni automatiche"""
        optimizations_applied = []
        
        # Controllo CPU
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            self._cleanup_memory()
            self._force_garbage_collection()
            optimizations_applied.append('cpu_critical')
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            self._force_garbage_collection()
            optimizations_applied.append('cpu_warning')
        
        # Controllo Memoria
        if metrics.memory_percent > self.thresholds['memory_critical']:
            self._cleanup_memory()
            self._force_garbage_collection()
            self._cleanup_caches()
            optimizations_applied.append('memory_critical')
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            self._cleanup_memory()
            optimizations_applied.append('memory_warning')
        
        # Controllo Disco
        if metrics.disk_usage_percent > self.thresholds['disk_critical']:
            self._cleanup_temp_files()
            self._optimize_databases()
            optimizations_applied.append('disk_critical')
        elif metrics.disk_usage_percent > self.thresholds['disk_warning']:
            self._cleanup_temp_files()
            optimizations_applied.append('disk_warning')
        
        # Log ottimizzazioni applicate
        if optimizations_applied:
            print(f"⚡ Ottimizzazioni applicate: {', '.join(optimizations_applied)}")
    
    def _cleanup_memory(self):
        """Pulizia memoria"""
        try:
            # Forza garbage collection
            collected = gc.collect()
            
            # Pulisci cache Python
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
            
            print(f"🧹 Memoria pulita: {collected} oggetti raccolti")
            return True
        except Exception as e:
            print(f"❌ Errore pulizia memoria: {e}")
            return False
    
    def _force_garbage_collection(self):
        """Forza garbage collection"""
        try:
            collected = gc.collect()
            print(f"🗑️ Garbage collection: {collected} oggetti raccolti")
            return True
        except Exception as e:
            print(f"❌ Errore garbage collection: {e}")
            return False
    
    def _optimize_databases(self):
        """Ottimizza i database SQLite"""
        try:
            db_files = [
                "data/gestionale.db",
                "data/biciclette_usate.db",
                "data/biciclette_restaurate.db",
                "data/biciclette_artigianali.db",
                "data/pricing.db"
            ]
            
            optimized_count = 0
            for db_file in db_files:
                if Path(db_file).exists():
                    conn = sqlite3.connect(db_file)
                    conn.execute("VACUUM")
                    conn.execute("ANALYZE")
                    conn.close()
                    optimized_count += 1
            
            print(f"🗄️ Database ottimizzati: {optimized_count}")
            return True
        except Exception as e:
            print(f"❌ Errore ottimizzazione database: {e}")
            return False
    
    def _cleanup_caches(self):
        """Pulisce le cache dell'applicazione"""
        try:
            # Pulisci cache di import
            if hasattr(sys, 'modules'):
                modules_to_remove = []
                for module_name, module in sys.modules.items():
                    if module_name.startswith('_') and hasattr(module, '__file__'):
                        modules_to_remove.append(module_name)
                
                for module_name in modules_to_remove:
                    del sys.modules[module_name]
            
            print("🧹 Cache pulite")
            return True
        except Exception as e:
            print(f"❌ Errore pulizia cache: {e}")
            return False
    
    def _cleanup_threads(self):
        """Pulisce thread non necessari"""
        try:
            # Conta thread attivi
            active_threads = threading.active_count()
            
            # Se ci sono troppi thread, forza garbage collection
            if active_threads > 20:
                self._force_garbage_collection()
            
            print(f"🧵 Thread attivi: {active_threads}")
            return True
        except Exception as e:
            print(f"❌ Errore pulizia thread: {e}")
            return False
    
    def _cleanup_temp_files(self):
        """Pulisce file temporanei"""
        try:
            temp_dirs = [
                "temp",
                "cache",
                "logs"
            ]
            
            cleaned_files = 0
            for temp_dir in temp_dirs:
                if Path(temp_dir).exists():
                    for file_path in Path(temp_dir).glob("*"):
                        if file_path.is_file():
                            # Elimina file più vecchi di 7 giorni
                            if file_path.stat().st_mtime < time.time() - (7 * 24 * 3600):
                                file_path.unlink()
                                cleaned_files += 1
            
            print(f"🗂️ File temporanei puliti: {cleaned_files}")
            return True
        except Exception as e:
            print(f"❌ Errore pulizia file temporanei: {e}")
            return False
    
    def optimize_all(self) -> Dict[str, bool]:
        """Applica tutte le ottimizzazioni"""
        results = {}
        
        print("⚡ Avvio ottimizzazione completa...")
        
        for rule_name, rule_func in self.optimization_rules.items():
            try:
                result = rule_func()
                results[rule_name] = result
                print(f"✅ {rule_name}: {'OK' if result else 'FALLITO'}")
            except Exception as e:
                results[rule_name] = False
                print(f"❌ {rule_name}: ERRORE - {e}")
        
        print("🎯 Ottimizzazione completata!")
        return results
    
    def get_performance_report(self) -> Dict:
        """Ottiene un report completo delle performance"""
        if not self.metrics_history:
            return {"error": "Nessuna metrica disponibile"}
        
        latest_metrics = self.metrics_history[-1]
        
        # Calcola medie
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        memory_values = [m.memory_percent for m in self.metrics_history]
        
        avg_cpu = sum(cpu_values) / len(cpu_values)
        avg_memory = sum(memory_values) / len(memory_values)
        
        # Identifica picchi
        max_cpu = max(cpu_values)
        max_memory = max(memory_values)
        
        # Valuta stato generale
        status = "OK"
        if (latest_metrics.cpu_percent > self.thresholds['cpu_critical'] or 
            latest_metrics.memory_percent > self.thresholds['memory_critical']):
            status = "CRITICO"
        elif (latest_metrics.cpu_percent > self.thresholds['cpu_warning'] or 
              latest_metrics.memory_percent > self.thresholds['memory_warning']):
            status = "ATTENZIONE"
        
        return {
            "status": status,
            "current": {
                "cpu_percent": latest_metrics.cpu_percent,
                "memory_mb": latest_metrics.memory_mb,
                "memory_percent": latest_metrics.memory_percent,
                "disk_usage_percent": latest_metrics.disk_usage_percent,
                "active_threads": latest_metrics.active_threads,
                "gc_objects": latest_metrics.gc_objects
            },
            "averages": {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory
            },
            "peaks": {
                "cpu_percent": max_cpu,
                "memory_percent": max_memory
            },
            "thresholds": self.thresholds,
            "samples_count": len(self.metrics_history)
        }
    
    def set_threshold(self, metric: str, value: float):
        """Imposta una soglia personalizzata"""
        if metric in self.thresholds:
            self.thresholds[metric] = value
            print(f"📊 Soglia {metric} impostata a {value}")
        else:
            print(f"❌ Soglia {metric} non valida")
    
    def add_custom_optimization(self, name: str, func: Callable):
        """Aggiunge una regola di ottimizzazione personalizzata"""
        self.optimization_rules[name] = func
        print(f"➕ Regola personalizzata aggiunta: {name}")
    
    def remove_optimization(self, name: str):
        """Rimuove una regola di ottimizzazione"""
        if name in self.optimization_rules:
            del self.optimization_rules[name]
            print(f"➖ Regola rimossa: {name}")
        else:
            print(f"❌ Regola {name} non trovata")
    
    def export_metrics(self, filename: str = "performance_metrics.json"):
        """Esporta le metriche in un file JSON"""
        try:
            metrics_data = []
            for metric in self.metrics_history:
                metrics_data.append({
                    "cpu_percent": metric.cpu_percent,
                    "memory_mb": metric.memory_mb,
                    "memory_percent": metric.memory_percent,
                    "disk_usage_percent": metric.disk_usage_percent,
                    "active_threads": metric.active_threads,
                    "gc_objects": metric.gc_objects,
                    "timestamp": metric.timestamp
                })
            
            with open(filename, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            print(f"📊 Metriche esportate in {filename}")
            return True
        except Exception as e:
            print(f"❌ Errore esportazione metriche: {e}")
            return False
    
    def __del__(self):
        """Distruttore - ferma il monitoraggio"""
        self.stop_monitoring()


if __name__ == "__main__":
    # Test del performance optimizer
    optimizer = PerformanceOptimizer()
    
    print("🔍 Test Performance Optimizer")
    print("=" * 40)
    
    # Mostra metriche correnti
    metrics = optimizer.get_current_metrics()
    print(f"CPU: {metrics.cpu_percent:.1f}%")
    print(f"Memoria: {metrics.memory_mb:.1f} MB ({metrics.memory_percent:.1f}%)")
    print(f"Disco: {metrics.disk_usage_percent:.1f}%")
    print(f"Thread: {metrics.active_threads}")
    print(f"Oggetti GC: {metrics.gc_objects}")
    
    # Applica ottimizzazioni
    print("\n⚡ Applicazione ottimizzazioni...")
    results = optimizer.optimize_all()
    
    # Mostra report
    print("\n📊 Report Performance:")
    report = optimizer.get_performance_report()
    print(json.dumps(report, indent=2))
    
    # Ferma il monitoraggio
    optimizer.stop_monitoring()
