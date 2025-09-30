"""
Sistema di gestione errori robusto per il Gestionale Biciclette.

Gestisce:
- Cattura e gestione errori globali
- Auto-riparazione file mancanti
- Recovery automatico
- Logging dettagliato degli errori
- Sistema di fallback

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import sys
import traceback
import os
import importlib
import sqlite3
from typing import Dict, Any, Optional, Callable
from src.utils.logger import logger


class ErrorHandler:
    """Gestore globale degli errori per l'applicazione"""

    def __init__(self, backup_controller=None):
        """
        Inizializza il gestore errori
        
        Args:
            backup_controller: Controller per il backup e recovery
        """
        self.backup_controller = backup_controller
        self.error_handlers = {}
        self.fallback_functions = {}
        self._setup_global_error_handling()

    def _setup_global_error_handling(self):
        """Configura la gestione globale degli errori"""
        # Intercetta tutti gli errori non gestiti
        sys.excepthook = self._handle_uncaught_exception
        
        # Intercetta KeyboardInterrupt
        original_excepthook = sys.excepthook
        
        def custom_excepthook(exc_type, exc_value, exc_traceback):
            if exc_type == KeyboardInterrupt:
                self._handle_keyboard_interrupt(exc_type, exc_value, exc_traceback)
            else:
                original_excepthook(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = custom_excepthook

    def _handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """Gestisce le eccezioni non catturate"""
        try:
            # Log dell'errore
            error_msg = f"Errore non gestito: {exc_type.__name__}: {exc_value}"
            logger.critical(error_msg, "ERROR_HANDLER", exc_value)
            
            # Stampa il traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            
            # Tenta il recovery automatico
            self._attempt_auto_recovery(exc_type, exc_value, exc_traceback)
            
        except Exception as recovery_error:
            logger.critical(f"Errore nel recovery automatico: {str(recovery_error)}", "ERROR_HANDLER", recovery_error)
            print(f"ERRORE CRITICO: Impossibile recuperare dall'errore. {str(recovery_error)}")

    def _handle_keyboard_interrupt(self, exc_type, exc_value, exc_traceback):
        """Gestisce l'interruzione da tastiera"""
        try:
            logger.info("Applicazione interrotta dall'utente", "ERROR_HANDLER")
            print("\n🛑 Applicazione interrotta dall'utente. Salvataggio in corso...")
            
            # Tenta di salvare lo stato prima dell'uscita
            self._save_state_before_exit()
            
        except Exception as e:
            logger.error(f"Errore durante l'uscita: {str(e)}", "ERROR_HANDLER", e)
        finally:
            sys.exit(0)

    def _attempt_auto_recovery(self, exc_type, exc_value, exc_traceback):
        """Tenta il recovery automatico da un errore"""
        try:
            if not self.backup_controller:
                return
            
            # Verifica se è un errore di importazione
            if exc_type == ImportError or exc_type == ModuleNotFoundError:
                self._recover_missing_module(exc_value)
            
            # Verifica se è un errore di file mancante
            elif exc_type == FileNotFoundError:
                self._recover_missing_file(exc_value)
            
            # Verifica se è un errore di sintassi
            elif exc_type == SyntaxError:
                self._recover_syntax_error(exc_value)
            
            # Verifica se è un errore di database
            elif 'sqlite3' in str(exc_type) or 'database' in str(exc_value).lower():
                self._recover_database_error(exc_value)
            
            # Recovery generico
            else:
                self._recover_generic_error(exc_type, exc_value)
                
        except Exception as recovery_error:
            logger.error(f"Errore nel recovery automatico: {str(recovery_error)}", "ERROR_HANDLER", recovery_error)

    def _recover_missing_module(self, error_value):
        """Recupera da errori di moduli mancanti"""
        try:
            error_str = str(error_value)
            if "No module named" in error_str:
                module_name = error_str.split("'")[1] if "'" in error_str else "unknown"
                logger.warning(f"Modulo mancante rilevato: {module_name}", "ERROR_HANDLER")
                
                # Tenta di reinstallare il modulo
                self._reinstall_missing_module(module_name)
                
        except Exception as e:
            logger.error(f"Errore nel recovery modulo mancante: {str(e)}", "ERROR_HANDLER", e)

    def _recover_missing_file(self, error_value):
        """Recupera da errori di file mancanti"""
        try:
            error_str = str(error_value)
            if "No such file or directory" in error_str:
                # Estrai il nome del file dall'errore
                file_path = error_str.split(":")[0] if ":" in error_str else "unknown"
                logger.warning(f"File mancante rilevato: {file_path}", "ERROR_HANDLER")
                
                # Tenta di riparare il file
                if self.backup_controller:
                    self.backup_controller.auto_ripara_file_mancanti()
                    
        except Exception as e:
            logger.error(f"Errore nel recovery file mancante: {str(e)}", "ERROR_HANDLER", e)

    def _recover_syntax_error(self, error_value):
        """Recupera da errori di sintassi"""
        try:
            logger.warning(f"Errore di sintassi rilevato: {str(error_value)}", "ERROR_HANDLER")
            
            # Tenta di riparare il file con errore di sintassi
            if self.backup_controller:
                self.backup_controller.auto_ripara_file_mancanti()
                
        except Exception as e:
            logger.error(f"Errore nel recovery sintassi: {str(e)}", "ERROR_HANDLER", e)

    def _recover_database_error(self, error_value):
        """Recupera da errori di database"""
        try:
            logger.warning(f"Errore database rilevato: {str(error_value)}", "ERROR_HANDLER")
            
            # Tenta di riparare il database
            if self.backup_controller:
                # Verifica integrità e ripara
                verifica = self.backup_controller.verifica_integrita_progetto()
                if not verifica['successo'] or verifica['file_mancanti'] > 0:
                    self.backup_controller.auto_ripara_file_mancanti()
                    
        except Exception as e:
            logger.error(f"Errore nel recovery database: {str(e)}", "ERROR_HANDLER", e)

    def _recover_generic_error(self, exc_type, exc_value):
        """Recovery generico per errori non specifici"""
        try:
            logger.warning(f"Errore generico rilevato: {exc_type.__name__}: {exc_value}", "ERROR_HANDLER")
            
            # Tenta un backup di emergenza
            if self.backup_controller:
                self.backup_controller.crea_backup_progetto("manuale", "Backup di emergenza dopo errore")
                
        except Exception as e:
            logger.error(f"Errore nel recovery generico: {str(e)}", "ERROR_HANDLER", e)

    def _reinstall_missing_module(self, module_name):
        """Tenta di reinstallare un modulo mancante"""
        try:
            import subprocess
            import sys
            
            logger.info(f"Tentativo di reinstallazione modulo: {module_name}", "ERROR_HANDLER")
            
            # Lista dei moduli comuni e i loro nomi pip
            module_mapping = {
                'customtkinter': 'customtkinter',
                'tkinter': 'tkinter',  # Built-in, non reinstallabile
                'sqlite3': 'sqlite3',  # Built-in
                'pandas': 'pandas',
                'openpyxl': 'openpyxl',
                'PIL': 'Pillow',
                'Pillow': 'Pillow'
            }
            
            pip_name = module_mapping.get(module_name, module_name)
            
            if pip_name not in ['tkinter', 'sqlite3']:  # Non reinstallare moduli built-in
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                logger.info(f"Modulo {module_name} reinstallato con successo", "ERROR_HANDLER")
            
        except Exception as e:
            logger.error(f"Errore nella reinstallazione modulo {module_name}: {str(e)}", "ERROR_HANDLER", e)

    def _save_state_before_exit(self):
        """Salva lo stato dell'applicazione prima dell'uscita"""
        try:
            if self.backup_controller:
                # Crea un backup di emergenza
                self.backup_controller.crea_backup_progetto("manuale", "Backup di emergenza prima dell'uscita")
                
        except Exception as e:
            logger.error(f"Errore nel salvataggio stato: {str(e)}", "ERROR_HANDLER", e)

    # ===== GESTIONE ERRORI PERSONALIZZATA =====

    def register_error_handler(self, error_type: type, handler: Callable):
        """
        Registra un gestore personalizzato per un tipo di errore
        
        Args:
            error_type: Tipo di errore da gestire
            handler: Funzione per gestire l'errore
        """
        self.error_handlers[error_type] = handler

    def register_fallback_function(self, function_name: str, fallback: Callable):
        """
        Registra una funzione di fallback
        
        Args:
            function_name: Nome della funzione
            fallback: Funzione di fallback
        """
        self.fallback_functions[function_name] = fallback

    def safe_execute(self, function: Callable, *args, **kwargs) -> Any:
        """
        Esegue una funzione in modo sicuro con gestione errori
        
        Args:
            function: Funzione da eseguire
            *args: Argomenti posizionali
            **kwargs: Argomenti keyword
            
        Returns:
            Risultato della funzione o None in caso di errore
        """
        try:
            return function(*args, **kwargs)
        except Exception as e:
            logger.error(f"Errore nell'esecuzione sicura: {str(e)}", "ERROR_HANDLER", e)
            
            # Tenta il recovery
            self._attempt_auto_recovery(type(e), e, None)
            
            return None

    def safe_import(self, module_name: str, fallback_module: str = None) -> Optional[Any]:
        """
        Importa un modulo in modo sicuro
        
        Args:
            module_name: Nome del modulo da importare
            fallback_module: Modulo di fallback se il primo fallisce
            
        Returns:
            Modulo importato o None
        """
        try:
            return importlib.import_module(module_name)
        except ImportError as e:
            logger.warning(f"Impossibile importare {module_name}: {str(e)}", "ERROR_HANDLER")
            
            if fallback_module:
                try:
                    logger.info(f"Tentativo import modulo di fallback: {fallback_module}", "ERROR_HANDLER")
                    return importlib.import_module(fallback_module)
                except ImportError as fallback_error:
                    logger.error(f"Anche il modulo di fallback {fallback_module} non disponibile: {str(fallback_error)}", "ERROR_HANDLER", fallback_error)
            
            return None

    def safe_file_operation(self, operation: Callable, file_path: str, *args, **kwargs) -> Any:
        """
        Esegue un'operazione su file in modo sicuro
        
        Args:
            operation: Operazione da eseguire
            file_path: Percorso del file
            *args: Argomenti posizionali
            **kwargs: Argomenti keyword
            
        Returns:
            Risultato dell'operazione o None in caso di errore
        """
        try:
            return operation(file_path, *args, **kwargs)
        except FileNotFoundError:
            logger.warning(f"File non trovato: {file_path}", "ERROR_HANDLER")
            
            # Tenta di riparare il file
            if self.backup_controller:
                self.backup_controller.auto_ripara_file_mancanti()
            
            return None
        except Exception as e:
            logger.error(f"Errore nell'operazione file {file_path}: {str(e)}", "ERROR_HANDLER", e)
            return None

    # ===== UTILITY =====

    def get_error_statistics(self) -> Dict[str, Any]:
        """Recupera statistiche sugli errori"""
        try:
            if self.backup_controller:
                errori = self.backup_controller.get_errori_non_risolti()
                return {
                    'errori_totali': len(errori),
                    'errori_per_tipo': self._count_errors_by_type(errori),
                    'ultimo_errore': errori[0] if errori else None
                }
            return {}
        except Exception as e:
            logger.error(f"Errore nel recupero statistiche errori: {str(e)}", "ERROR_HANDLER", e)
            return {}

    def _count_errors_by_type(self, errori: list) -> Dict[str, int]:
        """Conta gli errori per tipo"""
        count = {}
        for errore in errori:
            tipo = errore.get('tipo_errore', 'unknown')
            count[tipo] = count.get(tipo, 0) + 1
        return count

    def is_system_healthy(self) -> bool:
        """Verifica se il sistema è in salute"""
        try:
            if self.backup_controller:
                errori = self.backup_controller.get_errori_non_risolti()
                return len(errori) == 0
            return True
        except Exception as e:
            logger.error(f"Errore verifica salute sistema: {str(e)}", "ERROR_HANDLER", e)
            return False
    
    # ===== METODI DI UTILITÀ PER REFACTORING =====
    
    @staticmethod
    def safe_execute(operation: Callable, context: str = "", show_message: bool = True, default_return = None):
        """
        Esegue un'operazione in modo sicuro con gestione errori standardizzata
        
        Args:
            operation: Funzione da eseguire
            context: Contesto dell'operazione per logging
            show_message: Se mostrare messagebox in caso di errore
            default_return: Valore di ritorno in caso di errore
            
        Returns:
            Risultato dell'operazione o default_return
        """
        try:
            return operation()
        except Exception as e:
            logger.error(f"Errore in {context}: {e}")
            if show_message:
                try:
                    import tkinter.messagebox as messagebox
                    messagebox.showerror("Errore", f"Errore in {context}: {e}")
                except:
                    pass  # Se messagebox non disponibile, ignora
            return default_return
    
    @staticmethod
    def safe_database_operation(operation: Callable, context: str = "Database Operation"):
        """
        Esegue un'operazione database in modo sicuro
        
        Args:
            operation: Operazione database da eseguire
            context: Contesto per logging
            
        Returns:
            Tupla (successo, risultato)
        """
        try:
            result = operation()
            return True, result
        except sqlite3.Error as e:
            logger.error(f"Errore database in {context}: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Errore generico in {context}: {e}")
            return False, None
    
    @staticmethod
    def safe_gui_operation(operation: Callable, context: str = "GUI Operation"):
        """
        Esegue un'operazione GUI in modo sicuro
        
        Args:
            operation: Operazione GUI da eseguire
            context: Contesto per logging
            
        Returns:
            Tupla (successo, risultato)
        """
        try:
            result = operation()
            return True, result
        except Exception as e:
            logger.error(f"Errore GUI in {context}: {e}")
            try:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Errore GUI", f"Errore in {context}: {e}")
            except:
                pass
            return False, None
        try:
            if not self.backup_controller:
                return True
            
            # Verifica integrità del progetto
            verifica = self.backup_controller.verifica_integrita_progetto()
            if not verifica['successo']:
                return False
            
            # Sistema sano se non ci sono file mancanti o corrotti
            return verifica['file_mancanti'] == 0 and verifica['file_corotti'] == 0
            
        except Exception as e:
            logger.error(f"Errore nella verifica salute sistema: {str(e)}", "ERROR_HANDLER", e)
            return False


# Istanza globale del gestore errori
error_handler = None


def initialize_error_handler(backup_controller=None):
    """Inizializza il gestore errori globale"""
    global error_handler
    error_handler = ErrorHandler(backup_controller)
    return error_handler


def get_error_handler() -> Optional[ErrorHandler]:
    """Recupera il gestore errori globale"""
    return error_handler
