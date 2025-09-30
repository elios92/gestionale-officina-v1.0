"""
Configurazione avanzata per il debug e la validazione degli errori
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

class DebugConfig:
    """Configurazione centralizzata per il debug"""
    
    def __init__(self):
        self.debug_enabled = True
        self.log_level = logging.DEBUG
        self.log_file = "debug_errors.log"
        self.console_output = True
        self.file_output = True
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        
        # Configurazione per diversi tipi di errori
        self.error_categories = {
            'gui_creation': True,
            'database_operations': True,
            'file_operations': True,
            'threading_operations': True,
            'tab_operations': True,
            'method_calls': True,
            'attribute_access': True,
            'validation_errors': True
        }
        
        # Soglie per warning
        self.warning_thresholds = {
            'max_errors_per_object': 10,
            'max_warnings_per_object': 20,
            'max_errors_per_second': 50
        }
        
        # Filtri per errori
        self.error_filters = {
            'ignore_common_warnings': True,
            'ignore_deprecated_warnings': True,
            'ignore_import_warnings': True
        }
    
    def setup_logging(self):
        """Configura il sistema di logging"""
        if not self.debug_enabled:
            return
        
        # Crea la directory per i log se non esiste
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configura il logger principale
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        
        # Rimuovi handler esistenti
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Handler per console
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_formatter = logging.Formatter(self.log_format)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # Handler per file
        if self.file_output:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_log_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            file_formatter = logging.Formatter(self.log_format)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # Logger specifici per categoria
        self._setup_category_loggers()
    
    def _setup_category_loggers(self):
        """Configura logger specifici per categoria"""
        for category in self.error_categories.keys():
            if self.error_categories[category]:
                category_logger = logging.getLogger(f"debug.{category}")
                category_logger.setLevel(self.log_level)
    
    def log_error(self, category: str, message: str, exception: Exception = None):
        """Logga un errore con categoria"""
        if not self.debug_enabled or not self.error_categories.get(category, False):
            return
        
        logger = logging.getLogger(f"debug.{category}")
        
        if exception:
            logger.error(f"{message} - Exception: {exception}")
            logger.debug(f"Stack trace: {exception.__traceback__}")
        else:
            logger.error(message)
    
    def log_warning(self, category: str, message: str):
        """Logga un warning con categoria"""
        if not self.debug_enabled or not self.error_categories.get(category, False):
            return
        
        logger = logging.getLogger(f"debug.{category}")
        logger.warning(message)
    
    def log_info(self, category: str, message: str):
        """Logga un info con categoria"""
        if not self.debug_enabled or not self.error_categories.get(category, False):
            return
        
        logger = logging.getLogger(f"debug.{category}")
        logger.info(message)
    
    def log_debug(self, category: str, message: str):
        """Logga un debug con categoria"""
        if not self.debug_enabled or not self.error_categories.get(category, False):
            return
        
        logger = logging.getLogger(f"debug.{category}")
        logger.debug(message)
    
    def should_log_error(self, category: str) -> bool:
        """Controlla se dovrebbe loggare errori per questa categoria"""
        return self.debug_enabled and self.error_categories.get(category, False)
    
    def get_log_file_path(self) -> str:
        """Restituisce il percorso del file di log"""
        return os.path.abspath(self.log_file)
    
    def clear_log_file(self):
        """Pulisce il file di log"""
        if os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"Log file pulito il {datetime.now()}\n")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche sui log"""
        stats = {
            'log_file_exists': os.path.exists(self.log_file),
            'log_file_size': 0,
            'log_file_modified': None
        }
        
        if stats['log_file_exists']:
            stats['log_file_size'] = os.path.getsize(self.log_file)
            stats['log_file_modified'] = datetime.fromtimestamp(os.path.getmtime(self.log_file))
        
        return stats

# Istanza globale della configurazione
debug_config = DebugConfig()

# Funzioni di utilità per logging rapido
def log_gui_error(message: str, exception: Exception = None):
    """Logga un errore GUI"""
    debug_config.log_error('gui_creation', message, exception)

def log_database_error(message: str, exception: Exception = None):
    """Logga un errore database"""
    debug_config.log_error('database_operations', message, exception)

def log_file_error(message: str, exception: Exception = None):
    """Logga un errore file"""
    debug_config.log_error('file_operations', message, exception)

def log_threading_error(message: str, exception: Exception = None):
    """Logga un errore threading"""
    debug_config.log_error('threading_operations', message, exception)

def log_tab_error(message: str, exception: Exception = None):
    """Logga un errore tab"""
    debug_config.log_error('tab_operations', message, exception)

def log_method_error(message: str, exception: Exception = None):
    """Logga un errore metodo"""
    debug_config.log_error('method_calls', message, exception)

def log_attribute_error(message: str, exception: Exception = None):
    """Logga un errore attributo"""
    debug_config.log_error('attribute_access', message, exception)

def log_validation_error(message: str, exception: Exception = None):
    """Logga un errore validazione"""
    debug_config.log_error('validation_errors', message, exception)

# Funzioni per warning
def log_gui_warning(message: str):
    """Logga un warning GUI"""
    debug_config.log_warning('gui_creation', message)

def log_database_warning(message: str):
    """Logga un warning database"""
    debug_config.log_warning('database_operations', message)

def log_file_warning(message: str):
    """Logga un warning file"""
    debug_config.log_warning('file_operations', message)

def log_threading_warning(message: str):
    """Logga un warning threading"""
    debug_config.log_warning('threading_operations', message)

def log_tab_warning(message: str):
    """Logga un warning tab"""
    debug_config.log_warning('tab_operations', message)

def log_method_warning(message: str):
    """Logga un warning metodo"""
    debug_config.log_warning('method_calls', message)

def log_attribute_warning(message: str):
    """Logga un warning attributo"""
    debug_config.log_warning('attribute_access', message)

def log_validation_warning(message: str):
    """Logga un warning validazione"""
    debug_config.log_warning('validation_errors', message)

# Funzioni per info
def log_gui_info(message: str):
    """Logga un info GUI"""
    debug_config.log_info('gui_creation', message)

def log_database_info(message: str):
    """Logga un info database"""
    debug_config.log_info('database_operations', message)

def log_file_info(message: str):
    """Logga un info file"""
    debug_config.log_info('file_operations', message)

def log_threading_info(message: str):
    """Logga un info threading"""
    debug_config.log_info('threading_operations', message)

def log_tab_info(message: str):
    """Logga un info tab"""
    debug_config.log_info('tab_operations', message)

def log_method_info(message: str):
    """Logga un info metodo"""
    debug_config.log_info('method_calls', message)

def log_attribute_info(message: str):
    """Logga un info attributo"""
    debug_config.log_info('attribute_access', message)

def log_validation_info(message: str):
    """Logga un info validazione"""
    debug_config.log_info('validation_errors', message)

# Funzioni per debug
def log_gui_debug(message: str):
    """Logga un debug GUI"""
    debug_config.log_debug('gui_creation', message)

def log_database_debug(message: str):
    """Logga un debug database"""
    debug_config.log_debug('database_operations', message)

def log_file_debug(message: str):
    """Logga un debug file"""
    debug_config.log_debug('file_operations', message)

def log_threading_debug(message: str):
    """Logga un debug threading"""
    debug_config.log_debug('threading_operations', message)

def log_tab_debug(message: str):
    """Logga un debug tab"""
    debug_config.log_debug('tab_operations', message)

def log_method_debug(message: str):
    """Logga un debug metodo"""
    debug_config.log_debug('method_calls', message)

def log_attribute_debug(message: str):
    """Logga un debug attributo"""
    debug_config.log_debug('attribute_access', message)

def log_validation_debug(message: str):
    """Logga un debug validazione"""
    debug_config.log_debug('validation_errors', message)

# Funzione per inizializzare il sistema di debug
def initialize_debug_system():
    """Inizializza il sistema di debug"""
    debug_config.setup_logging()
    log_validation_info("🚀 Sistema di debug inizializzato")
    log_validation_info(f"📁 File di log: {debug_config.get_log_file_path()}")
    return debug_config

# Funzione per stampare statistiche debug
def print_debug_stats():
    """Stampa le statistiche del debug"""
    stats = debug_config.get_log_stats()
    print("\n" + "="*60)
    print("📊 STATISTICHE DEBUG")
    print("="*60)
    print(f"📁 File di log: {debug_config.get_log_file_path()}")
    print(f"📄 File esiste: {stats['log_file_exists']}")
    if stats['log_file_exists']:
        print(f"📏 Dimensione file: {stats['log_file_size']} bytes")
        print(f"🕒 Ultima modifica: {stats['log_file_modified']}")
    print("="*60)

if __name__ == "__main__":
    # Test del sistema
    config = initialize_debug_system()
    print("✅ Sistema di debug testato con successo")
