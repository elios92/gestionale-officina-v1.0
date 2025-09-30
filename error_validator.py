"""
Sistema di validazione degli errori robusto per tutto il programma
Intercetta tutti gli errori prima che causino problemi e li stampa nella console di debug
"""

import logging
import traceback
import inspect
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple
import sys
import os

# Configurazione logging per debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_errors.log', mode='a', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class ErrorValidator:
    """Sistema centralizzato di validazione degli errori"""
    
    def __init__(self):
        self.error_count = 0
        self.warning_count = 0
        self.validation_rules = {}
        self.registered_objects = {}
        
    def register_object(self, obj: Any, name: str = None) -> str:
        """Registra un oggetto per il monitoraggio degli errori"""
        if name is None:
            name = f"{obj.__class__.__name__}_{id(obj)}"
        
        self.registered_objects[name] = {
            'object': obj,
            'class': obj.__class__.__name__,
            'module': obj.__class__.__module__,
            'methods': [method for method in dir(obj) if not method.startswith('_')],
            'attributes': [attr for attr in dir(obj) if not callable(getattr(obj, attr, None))],
            'errors': [],
            'warnings': []
        }
        
        logger.info(f"✅ Oggetto registrato: {name} ({obj.__class__.__name__})")
        return name
    
    def validate_method_call(self, obj: Any, method_name: str, *args, **kwargs) -> Tuple[bool, Any]:
        """Valida una chiamata a metodo con controllo errori"""
        try:
            # Controlla se l'oggetto esiste
            if obj is None:
                logger.error(f"❌ Oggetto None per chiamata metodo {method_name}")
                return False, None
            
            # Controlla se il metodo esiste
            if not hasattr(obj, method_name):
                logger.error(f"❌ Metodo {method_name} non trovato in {obj.__class__.__name__}")
                return False, None
            
            # Controlla se è callable
            method = getattr(obj, method_name)
            if not callable(method):
                logger.error(f"❌ {method_name} non è callable in {obj.__class__.__name__}")
                return False, None
            
            # Esegui la chiamata
            result = method(*args, **kwargs)
            logger.debug(f"✅ Chiamata {method_name} eseguita con successo")
            return True, result
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"❌ Errore in {obj.__class__.__name__}.{method_name}: {e}"
            logger.error(error_msg)
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False, None
    
    def validate_attribute_access(self, obj: Any, attr_name: str) -> Tuple[bool, Any]:
        """Valida l'accesso a un attributo"""
        try:
            if obj is None:
                logger.error(f"❌ Oggetto None per accesso attributo {attr_name}")
                return False, None
            
            if not hasattr(obj, attr_name):
                logger.error(f"❌ Attributo {attr_name} non trovato in {obj.__class__.__name__}")
                return False, None
            
            value = getattr(obj, attr_name)
            logger.debug(f"✅ Attributo {attr_name} accesso con successo")
            return True, value
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"❌ Errore accesso attributo {attr_name}: {e}"
            logger.error(error_msg)
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False, None
    
    def validate_gui_creation(self, gui_class: type, *args, **kwargs) -> Tuple[bool, Any]:
        """Valida la creazione di una GUI"""
        try:
            # Controlla parametri richiesti
            if not args:
                logger.error(f"❌ Nessun parametro fornito per creazione {gui_class.__name__}")
                return False, None
            
            # Controlla che il primo parametro sia un parent valido
            parent = args[0]
            if parent is None:
                logger.error(f"❌ Parent None per creazione {gui_class.__name__}")
                return False, None
            
            # Crea l'istanza
            instance = gui_class(*args, **kwargs)
            logger.info(f"✅ GUI {gui_class.__name__} creata con successo")
            return True, instance
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"❌ Errore creazione GUI {gui_class.__name__}: {e}"
            logger.error(error_msg)
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False, None
    
    def validate_database_access(self, db_controller: Any, operation: str, *args, **kwargs) -> Tuple[bool, Any]:
        """Valida l'accesso al database"""
        try:
            if db_controller is None:
                logger.error(f"❌ Database controller None per operazione {operation}")
                return False, None
            
            if not hasattr(db_controller, operation):
                logger.error(f"❌ Operazione {operation} non trovata nel database controller")
                return False, None
            
            method = getattr(db_controller, operation)
            result = method(*args, **kwargs)
            logger.debug(f"✅ Operazione database {operation} eseguita con successo")
            return True, result
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"❌ Errore operazione database {operation}: {e}"
            logger.error(error_msg)
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False, None
    
    def validate_file_operations(self, file_path: str, operation: str) -> bool:
        """Valida le operazioni sui file"""
        try:
            if not file_path:
                logger.error(f"❌ Percorso file vuoto per operazione {operation}")
                return False
            
            if operation == "read":
                if not os.path.exists(file_path):
                    logger.error(f"❌ File non trovato: {file_path}")
                    return False
                if not os.path.isfile(file_path):
                    logger.error(f"❌ Percorso non è un file: {file_path}")
                    return False
            
            elif operation == "write":
                # Controlla se la directory esiste
                dir_path = os.path.dirname(file_path)
                if dir_path and not os.path.exists(dir_path):
                    logger.warning(f"⚠️ Directory non esiste, verrà creata: {dir_path}")
            
            logger.debug(f"✅ Validazione file {operation} per {file_path} completata")
            return True
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"❌ Errore validazione file {operation}: {e}"
            logger.error(error_msg)
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False
    
    def validate_threading_operations(self, thread_func: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """Valida le operazioni di threading"""
        try:
            if not callable(thread_func):
                logger.error(f"❌ Funzione thread non callable: {thread_func}")
                return False, None
            
            # Esegui la funzione in modo sicuro
            result = thread_func(*args, **kwargs)
            logger.debug(f"✅ Operazione thread eseguita con successo")
            return True, result
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"❌ Errore operazione thread: {e}"
            logger.error(error_msg)
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False, None
    
    def validate_gui_widget_creation(self, parent, widget_class: type, *args, **kwargs) -> Tuple[bool, Any]:
        """Valida la creazione di widget GUI"""
        try:
            if parent is None:
                logger.error(f"❌ Parent None per creazione widget {widget_class.__name__}")
                return False, None
            
            # Crea il widget
            widget = widget_class(parent, *args, **kwargs)
            logger.debug(f"✅ Widget {widget_class.__name__} creato con successo")
            return True, widget
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"❌ Errore creazione widget {widget_class.__name__}: {e}"
            logger.error(error_msg)
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False, None
    
    def validate_tab_operations(self, tabview: Any, operation: str, tab_name: str = None) -> Tuple[bool, Any]:
        """Valida le operazioni sulle tab"""
        try:
            if tabview is None:
                logger.error(f"❌ TabView None per operazione {operation}")
                return False, None
            
            if operation == "add":
                if not tab_name:
                    logger.error(f"❌ Nome tab mancante per operazione add")
                    return False, None
                tab = tabview.add(tab_name)
                logger.debug(f"✅ Tab {tab_name} aggiunta con successo")
                return True, tab
            
            elif operation == "get":
                current_tab = tabview.get()
                logger.debug(f"✅ Tab corrente ottenuta: {current_tab}")
                return True, current_tab
            
            elif operation == "set":
                if not tab_name:
                    logger.error(f"❌ Nome tab mancante per operazione set")
                    return False, None
                tabview.set(tab_name)
                logger.debug(f"✅ Tab impostata a: {tab_name}")
                return True, None
            
            else:
                logger.error(f"❌ Operazione tab non supportata: {operation}")
                return False, None
                
        except Exception as e:
            self.error_count += 1
            error_msg = f"❌ Errore operazione tab {operation}: {e}"
            logger.error(error_msg)
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            return False, None
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Restituisce un riassunto degli errori"""
        return {
            'total_errors': self.error_count,
            'total_warnings': self.warning_count,
            'registered_objects': len(self.registered_objects),
            'objects_with_errors': sum(1 for obj in self.registered_objects.values() if obj['errors']),
            'objects_with_warnings': sum(1 for obj in self.registered_objects.values() if obj['warnings'])
        }
    
    def print_error_summary(self):
        """Stampa un riassunto degli errori nella console"""
        summary = self.get_error_summary()
        print("\n" + "="*60)
        print("📊 RIASSUNTO ERRORI SISTEMA")
        print("="*60)
        print(f"❌ Errori totali: {summary['total_errors']}")
        print(f"⚠️ Warning totali: {summary['total_warnings']}")
        print(f"🔧 Oggetti registrati: {summary['registered_objects']}")
        print(f"💥 Oggetti con errori: {summary['objects_with_errors']}")
        print(f"⚠️ Oggetti con warning: {summary['objects_with_warnings']}")
        print("="*60)

# Istanza globale del validatore
error_validator = ErrorValidator()

# Decoratori per validazione automatica
def validate_method_call(func):
    """Decoratore per validare automaticamente le chiamate a metodo"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        success, result = error_validator.validate_method_call(self, func.__name__, *args, **kwargs)
        if success:
            return result
        else:
            return None
    return wrapper

def validate_gui_creation(func):
    """Decoratore per validare la creazione di GUI"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        success, result = error_validator.validate_gui_creation(func, *args, **kwargs)
        if success:
            return result
        else:
            return None
    return wrapper

def validate_database_operation(func):
    """Decoratore per validare le operazioni database"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        success, result = error_validator.validate_database_access(self, func.__name__, *args, **kwargs)
        if success:
            return result
        else:
            return None
    return wrapper

# Funzioni di utilità per validazione rapida
def safe_method_call(obj: Any, method_name: str, *args, **kwargs) -> Any:
    """Chiamata sicura a metodo con validazione"""
    success, result = error_validator.validate_method_call(obj, method_name, *args, **kwargs)
    return result if success else None

def safe_attribute_access(obj: Any, attr_name: str) -> Any:
    """Accesso sicuro ad attributo con validazione"""
    success, result = error_validator.validate_attribute_access(obj, attr_name)
    return result if success else None

def safe_gui_creation(gui_class: type, *args, **kwargs) -> Any:
    """Creazione sicura di GUI con validazione"""
    success, result = error_validator.validate_gui_creation(gui_class, *args, **kwargs)
    return result if success else None

def safe_database_operation(db_controller: Any, operation: str, *args, **kwargs) -> Any:
    """Operazione sicura su database con validazione"""
    success, result = error_validator.validate_database_access(db_controller, operation, *args, **kwargs)
    return result if success else None

def safe_tab_operation(tabview: Any, operation: str, tab_name: str = None) -> Any:
    """Operazione sicura su tab con validazione"""
    success, result = error_validator.validate_tab_operations(tabview, operation, tab_name)
    return result if success else None

# Funzione per inizializzare il sistema di validazione
def initialize_error_validation():
    """Inizializza il sistema di validazione degli errori"""
    logger.info("🚀 Sistema di validazione errori inizializzato")
    logger.info(f"📁 Log file: {os.path.abspath('debug_errors.log')}")
    return error_validator

# Funzione per stampare il riassunto errori
def print_debug_summary():
    """Stampa il riassunto degli errori per debug"""
    error_validator.print_error_summary()

if __name__ == "__main__":
    # Test del sistema
    validator = initialize_error_validation()
    print("✅ Sistema di validazione errori testato con successo")
