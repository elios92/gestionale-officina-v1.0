"""
Base Database Class

Classe base per tutti i database del gestionale che unifica i pattern comuni.
Riduce la duplicazione di codice e standardizza l'inizializzazione.

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import os
import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from abc import ABC, abstractmethod
from src.utils.logger import logger


class BaseDatabase(ABC):
    """
    Classe base per tutti i database del gestionale.
    
    Fornisce funzionalità comuni:
    - Inizializzazione directory
    - Connessione database
    - Gestione errori standardizzata
    - Metodi utility comuni
    """
    
    def __init__(self, db_dir: str, db_name: str):
        """
        Inizializza il database base
        
        Args:
            db_dir: Directory dove salvare il database
            db_name: Nome del file database (con estensione .db)
        """
        self.db_dir = db_dir
        self.db_name = db_name
        self.db_path = os.path.join(db_dir, db_name)
        
        # Crea la directory se non esiste
        self._ensure_directory()
        
        # Inizializza il database specifico
        self._init_database()
    
    def _ensure_directory(self):
        """Crea la directory del database se non esiste"""
        try:
            if not os.path.exists(self.db_dir):
                os.makedirs(self.db_dir)
                logger.info(f"Directory database creata: {self.db_dir}")
        except Exception as e:
            logger.error(f"Errore creazione directory {self.db_dir}: {e}")
            raise
    
    @abstractmethod
    def _init_database(self):
        """
        Inizializza il database specifico.
        Deve essere implementato da ogni classe derivata.
        """
        pass
    
    def _execute_query(self, query: str, params: Tuple = (), fetch: bool = False) -> Optional[List[Dict]]:
        """
        Esegue una query SQL in modo sicuro
        
        Args:
            query: Query SQL da eseguire
            params: Parametri per la query
            fetch: Se restituire i risultati
            
        Returns:
            Lista di dizionari con i risultati o None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Permette accesso per nome colonna
                cursor = conn.cursor()
                
                cursor.execute(query, params)
                
                if fetch:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return []
                    
        except Exception as e:
            logger.error(f"Errore esecuzione query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parametri: {params}")
            return None
    
    def _execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """
        Esegue una query con più parametri
        
        Args:
            query: Query SQL da eseguire
            params_list: Lista di tuple con i parametri
            
        Returns:
            True se successo, False altrimenti
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Errore esecuzione query multipla: {e}")
            return False
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """
        Ottiene una connessione al database
        
        Returns:
            Connessione SQLite o None in caso di errore
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Errore connessione database: {e}")
            return None
    
    def table_exists(self, table_name: str) -> bool:
        """
        Verifica se una tabella esiste
        
        Args:
            table_name: Nome della tabella
            
        Returns:
            True se la tabella esiste
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self._execute_query(query, (table_name,), fetch=True)
        return len(result) > 0 if result else False
    
    def get_table_info(self, table_name: str) -> Optional[List[Dict]]:
        """
        Ottiene informazioni su una tabella
        
        Args:
            table_name: Nome della tabella
            
        Returns:
            Lista con informazioni sulle colonne
        """
        query = f"PRAGMA table_info({table_name})"
        return self._execute_query(query, fetch=True)
    
    def get_table_count(self, table_name: str) -> int:
        """
        Conta i record in una tabella
        
        Args:
            table_name: Nome della tabella
            
        Returns:
            Numero di record
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self._execute_query(query, fetch=True)
        return result[0]['count'] if result else 0
    
    def backup_table(self, table_name: str, backup_path: str) -> bool:
        """
        Crea un backup di una tabella
        
        Args:
            table_name: Nome della tabella
            backup_path: Percorso del file di backup
            
        Returns:
            True se successo
        """
        try:
            # Crea la directory di backup se non esiste
            backup_dir = os.path.dirname(backup_path)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Copia la tabella
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            
            logger.info(f"Backup tabella {table_name} creato: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Errore backup tabella {table_name}: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni generali sul database
        
        Returns:
            Dizionario con informazioni del database
        """
        try:
            info = {
                'db_path': self.db_path,
                'db_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
                'tables': []
            }
            
            # Ottieni lista tabelle
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables = self._execute_query(query, fetch=True)
            
            if tables:
                for table in tables:
                    table_name = table['name']
                    count = self.get_table_count(table_name)
                    info['tables'].append({
                        'name': table_name,
                        'count': count
                    })
            
            return info
            
        except Exception as e:
            logger.error(f"Errore recupero info database: {e}")
            return {'error': str(e)}
    
    def optimize_database(self) -> bool:
        """
        Ottimizza il database (VACUUM)
        
        Returns:
            True se successo
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                logger.info(f"Database ottimizzato: {self.db_path}")
                return True
        except Exception as e:
            logger.error(f"Errore ottimizzazione database: {e}")
            return False
