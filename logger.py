"""
Sistema di logging per il Gestionale Biciclette.

Gestisce la registrazione di errori, warning e informazioni dell'applicazione.

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional


class GestionaleLogger:
    """Gestore del sistema di logging per il gestionale"""

    def __init__(self, log_dir: str = "logs"):
        """
        Inizializza il sistema di logging
        
        Args:
            log_dir: Directory dove salvare i log
        """
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "gestionale.log")
        self.error_file = os.path.join(log_dir, "errori.log")
        
        # Crea la directory se non esiste
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configura il logger
        self._setup_logger()

    def _setup_logger(self):
        """Configura il sistema di logging"""
        # Logger principale
        self.logger = logging.getLogger("gestionale")
        self.logger.setLevel(logging.DEBUG)
        
        # Evita duplicazione di handler
        if self.logger.handlers:
            return
        
        # Formatter per i log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler per file generale (rotazione settimanale)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_file,
            when='W0',  # Ogni lunedì
            interval=1,
            backupCount=4,  # Mantieni 4 settimane di log
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Handler per errori (rotazione giornaliera)
        error_handler = logging.handlers.TimedRotatingFileHandler(
            self.error_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Mantieni 30 giorni di errori
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Handler per console (solo errori critici)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(formatter)
        
        # Aggiungi gli handler
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str, module: str = "GENERAL"):
        """
        Registra un messaggio informativo
        
        Args:
            message: Messaggio da registrare
            module: Modulo che ha generato il messaggio
        """
        self.logger.info("[%s] %s", module, message)

    def warning(self, message: str, module: str = "GENERAL"):
        """
        Registra un warning
        
        Args:
            message: Messaggio di warning
            module: Modulo che ha generato il warning
        """
        self.logger.warning("[%s] %s", module, message)

    def error(self, message: str, module: str = "GENERAL", exception: Optional[Exception] = None):
        """
        Registra un errore
        
        Args:
            message: Messaggio di errore
            module: Modulo che ha generato l'errore
            exception: Eccezione opzionale da registrare
        """
        if exception:
            self.logger.error("[%s] %s - Exception: %s", module, message, str(exception), exc_info=True)
        else:
            self.logger.error("[%s] %s", module, message)

    def critical(self, message: str, module: str = "GENERAL", exception: Optional[Exception] = None):
        """
        Registra un errore critico
        
        Args:
            message: Messaggio di errore critico
            module: Modulo che ha generato l'errore
            exception: Eccezione opzionale da registrare
        """
        if exception:
            self.logger.critical("[%s] %s - Exception: %s", module, message, str(exception), exc_info=True)
        else:
            self.logger.critical("[%s] %s", module, message)

    def debug(self, message: str, module: str = "GENERAL"):
        """
        Registra un messaggio di debug
        
        Args:
            message: Messaggio di debug
            module: Modulo che ha generato il messaggio
        """
        self.logger.debug("[%s] %s", module, message)

    def log_database_operation(self, operation: str, table: str, success: bool, 
                              details: str = "", module: str = "DATABASE"):
        """
        Registra un'operazione sul database
        
        Args:
            operation: Tipo di operazione (INSERT, UPDATE, DELETE, SELECT)
            table: Nome della tabella
            success: Se l'operazione è riuscita
            details: Dettagli aggiuntivi
            module: Modulo che ha eseguito l'operazione
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"DB {operation} on {table} - {status}"
        if details:
            message += f" - {details}"
        
        if success:
            self.info(message, module)
        else:
            self.error(message, module)

    def log_user_action(self, action: str, user: str = "SYSTEM", details: str = ""):
        """
        Registra un'azione dell'utente
        
        Args:
            action: Azione eseguita
            user: Utente che ha eseguito l'azione
            details: Dettagli aggiuntivi
        """
        message = f"User action: {action} by {user}"
        if details:
            message += f" - {details}"
        self.info(message, "USER_ACTION")

    def log_application_start(self, version: str = "1.0.0"):
        """
        Registra l'avvio dell'applicazione
        
        Args:
            version: Versione dell'applicazione
        """
        self.info(f"Gestionale Biciclette v{version} started", "APPLICATION")

    def log_application_stop(self):
        """Registra la chiusura dell'applicazione"""
        self.info("Gestionale Biciclette stopped", "APPLICATION")

    def get_log_stats(self) -> dict:
        """
        Ottiene statistiche sui log
        
        Returns:
            Dizionario con statistiche sui log
        """
        stats = {
            "log_dir": self.log_dir,
            "log_file": self.log_file,
            "error_file": self.error_file,
            "log_file_exists": os.path.exists(self.log_file),
            "error_file_exists": os.path.exists(self.error_file)
        }
        
        if stats["log_file_exists"]:
            stats["log_file_size"] = os.path.getsize(self.log_file)
        
        if stats["error_file_exists"]:
            stats["error_file_size"] = os.path.getsize(self.error_file)
        
        return stats

    def cleanup_old_logs(self, days: int = 30):
        """
        Pulisce i log più vecchi di N giorni
        
        Args:
            days: Numero di giorni da mantenere
        """
        try:
            import glob
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Pulisce i file di log rotati
            for pattern in [f"{self.log_file}.*", f"{self.error_file}.*"]:
                for log_file in glob.glob(pattern):
                    if os.path.getmtime(log_file) < cutoff_date.timestamp():
                        os.remove(log_file)
                        self.info(f"Removed old log file: {log_file}", "LOGGER")
        
        except (OSError, ValueError, TypeError) as e:
            self.error(f"Error cleaning up old logs: {str(e)}", "LOGGER", e)


# Istanza globale del logger
logger = GestionaleLogger()
