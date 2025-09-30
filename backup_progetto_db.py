"""
Database per il backup automatico del progetto Gestionale Biciclette.

Gestisce:
- Backup automatico del progetto
- Ripristino da backup
- Gestione errori robusta
- Auto-riparazione file mancanti
- Sistema di recovery automatico

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.utils.logger import logger


class BackupProgettoDB:
    """Database per il backup automatico del progetto"""

    def __init__(self, data_dir: str):
        """
        Inizializza il database di backup progetto
        
        Args:
            data_dir: Directory dove salvare i dati
        """
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, 'backup_progetto.db')
        self._init_database()
        self._migrate_existing_database()

    def _init_database(self):
        """Inizializza il database con le tabelle necessarie"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabella backup progetto
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS backup_progetto (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome_backup TEXT NOT NULL,
                        percorso_backup TEXT NOT NULL,
                        dimensione_backup INTEGER,
                        tipo_backup TEXT DEFAULT 'automatico',
                        stato TEXT DEFAULT 'completato',
                        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        descrizione TEXT,
                        file_inclusi TEXT,
                        hash_backup TEXT,
                        versione_progetto TEXT
                    )
                """)
                
                # Tabella file critici
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_critici (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        percorso_file TEXT UNIQUE NOT NULL,
                        hash_file TEXT,
                        dimensione_file INTEGER,
                        tipo_file TEXT,
                        critico BOOLEAN DEFAULT TRUE,
                        descrizione TEXT,
                        data_ultimo_backup TIMESTAMP,
                        data_modifica TIMESTAMP,
                        contenuto_backup TEXT
                    )
                """)
                
                # Tabella errori e recovery
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS errori_recovery (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo_errore TEXT NOT NULL,
                        file_coinvolto TEXT,
                        descrizione_errore TEXT,
                        stato_risoluzione TEXT DEFAULT 'da_risolvere',
                        data_errore TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_risoluzione TIMESTAMP,
                        azione_eseguita TEXT,
                        backup_utilizzato TEXT
                    )
                """)
                
                # Tabella configurazioni backup
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS config_backup (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chiave TEXT UNIQUE NOT NULL,
                        valore TEXT NOT NULL,
                        descrizione TEXT,
                        categoria TEXT DEFAULT 'backup',
                        data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_modifica TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Inserisce le configurazioni predefinite
                self._insert_default_configs(cursor)
                
                # Verifica e aggiunge colonna descrizione se mancante
                self._check_and_add_descrizione_column(cursor)
                
                # Inserisce i file critici predefiniti
                self._insert_critical_files(cursor)
                
                conn.commit()
                logger.info("Database backup progetto inizializzato", "BACKUP_PROGETTO")
                
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione database backup progetto: {str(e)}", "BACKUP_PROGETTO", e)
            raise

    def _migrate_existing_database(self):
        """Migra il database esistente per aggiungere nuove colonne"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verifica e aggiunge colonna descrizione se mancante
                self._check_and_add_descrizione_column(cursor)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Errore nella migrazione database: {str(e)}", "BACKUP_PROGETTO", e)

    def _insert_default_configs(self, cursor):
        """Inserisce le configurazioni predefinite"""
        try:
            # Verifica se ci sono già configurazioni
            cursor.execute("SELECT COUNT(*) FROM config_backup")
            if cursor.fetchone()[0] > 0:
                return
            
            # Configurazioni predefinite
            configs = [
                # Backup Automatico
                ('backup_automatico_progetto', 'true', 'Abilita backup automatico del progetto', 'backup'),
                ('frequenza_backup_progetto', 'giornaliero', 'Frequenza backup progetto (giornaliero/settimanale/mensile)', 'backup'),
                ('mantieni_backup_giorni', '30', 'Giorni di conservazione backup progetto', 'backup'),
                ('backup_compresso_progetto', 'true', 'Comprimi i backup del progetto', 'backup'),
                ('backup_incremental', 'true', 'Abilita backup incrementali', 'backup'),
                
                # File Critici
                ('monitora_file_critici', 'true', 'Monitora i file critici del progetto', 'monitoraggio'),
                ('auto_riparazione', 'true', 'Abilita auto-riparazione file mancanti', 'riparazione'),
                ('verifica_integrita_file', 'true', 'Verifica integrità dei file critici', 'verifica'),
                ('alert_file_mancanti', 'true', 'Alert per file mancanti o corrotti', 'alert'),
                
                # Recovery
                ('recovery_automatico', 'true', 'Abilita recovery automatico', 'recovery'),
                ('backup_prima_modifiche', 'true', 'Backup prima di modifiche critiche', 'sicurezza'),
                ('rollback_automatico', 'false', 'Rollback automatico in caso di errori critici', 'sicurezza'),
                ('notifica_backup', 'true', 'Notifica completamento backup', 'notifiche'),
                ('pulizia_automatica_duplicati', 'false', 'Pulizia automatica file duplicati all\'avvio', 'pulizia')
            ]
            
            for chiave, valore, descrizione, categoria in configs:
                cursor.execute("""
                    INSERT INTO config_backup (chiave, valore, descrizione, categoria)
                    VALUES (?, ?, ?, ?)
                """, (chiave, valore, descrizione, categoria))
                
        except Exception as e:
            logger.error(f"Errore nell'inserimento configurazioni predefinite: {str(e)}", "BACKUP_PROGETTO", e)
            raise

    def _check_and_add_descrizione_column(self, cursor):
        """Verifica se la colonna descrizione esiste e la aggiunge se mancante"""
        try:
            # Verifica se la colonna descrizione esiste
            cursor.execute("PRAGMA table_info(file_critici)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'descrizione' not in columns:
                # Aggiunge la colonna descrizione
                cursor.execute("ALTER TABLE file_critici ADD COLUMN descrizione TEXT")
                logger.info("Colonna descrizione aggiunta alla tabella file_critici", "BACKUP_PROGETTO")
                
        except Exception as e:
            logger.error(f"Errore nell'aggiunta colonna descrizione: {str(e)}", "BACKUP_PROGETTO", e)

    def _insert_critical_files(self, cursor):
        """Inserisce i file critici predefiniti"""
        try:
            # Verifica se ci sono già file critici
            cursor.execute("SELECT COUNT(*) FROM file_critici")
            if cursor.fetchone()[0] > 0:
                return
            
            # File critici del progetto
            file_critici = [
                ('main.py', 'python', True, 'File principale dell\'applicazione'),
                ('requirements.txt', 'config', True, 'Dipendenze del progetto'),
                ('src/modules/app_controller.py', 'python', True, 'Controller principale'),
                ('src/gui/menu_handler.py', 'python', True, 'Gestore menu'),
                ('src/gui/tab_manager.py', 'python', True, 'Gestore tab'),
                ('src/gui/screen_manager.py', 'python', True, 'Gestore schermate'),
                ('src/gui/impostazioni_gui.py', 'python', True, 'GUI impostazioni'),
                ('src/modules/impostazioni/impostazioni_db.py', 'python', True, 'Database impostazioni'),
                ('src/modules/impostazioni/impostazioni_controller.py', 'python', True, 'Controller impostazioni'),
                ('src/modules/clienti/clienti_db.py', 'python', True, 'Database clienti'),
                ('src/modules/clienti/clienti_controller.py', 'python', True, 'Controller clienti'),
                ('src/modules/officina/officina_db.py', 'python', True, 'Database officina'),
                ('src/modules/officina/officina_controller.py', 'python', True, 'Controller officina'),
                ('src/modules/inventario/inventario_db.py', 'python', True, 'Database inventario'),
                ('src/modules/inventario/inventario_controller.py', 'python', True, 'Controller inventario'),
                ('src/modules/listino/listino_db.py', 'python', True, 'Database listino'),
                ('src/modules/listino/listino_controller.py', 'python', True, 'Controller listino'),
                ('src/modules/pricing/pricing_db.py', 'python', True, 'Database pricing'),
                ('src/modules/pricing/pricing_controller.py', 'python', True, 'Controller pricing'),
                ('src/modules/configurazioni_avanzate/configurazioni_avanzate_db.py', 'python', True, 'Database configurazioni avanzate'),
                ('src/modules/configurazioni_avanzate/configurazioni_avanzate_controller.py', 'python', True, 'Controller configurazioni avanzate'),
                ('src/modules/gestione_database/gestione_database_db.py', 'python', True, 'Database gestione database'),
                ('src/modules/gestione_database/gestione_database_controller.py', 'python', True, 'Controller gestione database'),
                ('src/utils/logger.py', 'python', True, 'Sistema di logging'),
                ('src/utils/icon_manager.py', 'python', True, 'Gestore icone'),
                ('avvia.bat', 'batch', False, 'Script di avvio rapido'),
                ('installa_e_avvia.bat', 'batch', False, 'Script di installazione')
            ]
            
            for percorso, tipo, critico, descrizione in file_critici:
                cursor.execute("""
                    INSERT INTO file_critici (percorso_file, tipo_file, critico, descrizione)
                    VALUES (?, ?, ?, ?)
                """, (percorso, tipo, critico, descrizione))
                
        except Exception as e:
            logger.error(f"Errore nell'inserimento file critici: {str(e)}", "BACKUP_PROGETTO", e)
            raise

    # ===== GESTIONE CONFIGURAZIONI =====

    def get_configurazione(self, chiave: str, default: str = "") -> str:
        """Recupera una configurazione"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT valore FROM config_backup WHERE chiave = ?",
                    (chiave,)
                )
                result = cursor.fetchone()
                return result[0] if result else default
        except Exception as e:
            logger.error(f"Errore nel recupero configurazione {chiave}: {str(e)}", "BACKUP_PROGETTO", e)
            return default

    def set_configurazione(self, chiave: str, valore: str, descrizione: str = "", categoria: str = "backup") -> bool:
        """Imposta una configurazione"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO config_backup 
                    (chiave, valore, descrizione, categoria, data_modifica)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (chiave, valore, descrizione, categoria))
                conn.commit()
                logger.info(f"Configurazione {chiave} aggiornata", "BACKUP_PROGETTO")
                return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio configurazione {chiave}: {str(e)}", "BACKUP_PROGETTO", e)
            return False

    # ===== GESTIONE BACKUP PROGETTO =====

    def salva_backup_progetto(self, nome_backup: str, percorso_backup: str, 
                            dimensione_backup: int, tipo_backup: str = "automatico",
                            descrizione: str = "", file_inclusi: List[str] = None,
                            hash_backup: str = "", versione_progetto: str = "1.0.0") -> bool:
        """Salva un backup del progetto"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO backup_progetto 
                    (nome_backup, percorso_backup, dimensione_backup, tipo_backup, 
                     descrizione, file_inclusi, hash_backup, versione_progetto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    nome_backup, percorso_backup, dimensione_backup, tipo_backup,
                    descrizione, json.dumps(file_inclusi or []), hash_backup, versione_progetto
                ))
                conn.commit()
                logger.info(f"Backup progetto salvato: {nome_backup}", "BACKUP_PROGETTO")
                return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio backup progetto: {str(e)}", "BACKUP_PROGETTO", e)
            return False

    def get_ultimi_backup_progetto(self, limite: int = 10) -> List[Dict[str, Any]]:
        """Recupera gli ultimi backup del progetto"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, nome_backup, percorso_backup, dimensione_backup, tipo_backup,
                           stato, data_creazione, descrizione, file_inclusi, hash_backup, versione_progetto
                    FROM backup_progetto 
                    ORDER BY data_creazione DESC 
                    LIMIT ?
                """, (limite,))
                
                backup = []
                for row in cursor.fetchall():
                    backup.append({
                        'id': row[0],
                        'nome_backup': row[1],
                        'percorso_backup': row[2],
                        'dimensione_backup': row[3],
                        'tipo_backup': row[4],
                        'stato': row[5],
                        'data_creazione': row[6],
                        'descrizione': row[7],
                        'file_inclusi': json.loads(row[8]) if row[8] else [],
                        'hash_backup': row[9],
                        'versione_progetto': row[10]
                    })
                
                return backup
        except Exception as e:
            logger.error(f"Errore nel recupero backup progetto: {str(e)}", "BACKUP_PROGETTO", e)
            return []

    def get_backup_by_id(self, backup_id: int) -> Optional[Dict[str, Any]]:
        """Recupera un backup specifico per ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, nome_backup, percorso_backup, dimensione_backup, tipo_backup,
                           stato, data_creazione, descrizione, file_inclusi, hash_backup, versione_progetto
                    FROM backup_progetto 
                    WHERE id = ?
                """, (backup_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'nome_backup': row[1],
                        'percorso_backup': row[2],
                        'dimensione_backup': row[3],
                        'tipo_backup': row[4],
                        'stato': row[5],
                        'data_creazione': row[6],
                        'descrizione': row[7],
                        'file_inclusi': json.loads(row[8]) if row[8] else [],
                        'hash_backup': row[9],
                        'versione_progetto': row[10]
                    }
                return None
        except Exception as e:
            logger.error(f"Errore nel recupero backup {backup_id}: {str(e)}", "BACKUP_PROGETTO", e)
            return None

    # ===== GESTIONE FILE CRITICI =====

    def aggiorna_file_critico(self, percorso_file: str, hash_file: str = "", 
                            dimensione_file: int = 0, contenuto_backup: str = "") -> bool:
        """Aggiorna le informazioni di un file critico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO file_critici 
                    (percorso_file, hash_file, dimensione_file, data_ultimo_backup, 
                     data_modifica, contenuto_backup)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
                """, (percorso_file, hash_file, dimensione_file, contenuto_backup))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento file critico {percorso_file}: {str(e)}", "BACKUP_PROGETTO", e)
            return False

    def get_file_critici(self) -> List[Dict[str, Any]]:
        """Recupera tutti i file critici"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT percorso_file, hash_file, dimensione_file, tipo_file, critico,
                           data_ultimo_backup, data_modifica, contenuto_backup
                    FROM file_critici 
                    ORDER BY critico DESC, percorso_file
                """)
                
                file_critici = []
                for row in cursor.fetchall():
                    file_critici.append({
                        'percorso_file': row[0],
                        'hash_file': row[1],
                        'dimensione_file': row[2],
                        'tipo_file': row[3],
                        'critico': row[4],
                        'data_ultimo_backup': row[5],
                        'data_modifica': row[6],
                        'contenuto_backup': row[7]
                    })
                
                return file_critici
        except Exception as e:
            logger.error(f"Errore nel recupero file critici: {str(e)}", "BACKUP_PROGETTO", e)
            return []

    def get_file_critico(self, percorso_file: str) -> Optional[Dict[str, Any]]:
        """Recupera un file critico specifico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT percorso_file, hash_file, dimensione_file, tipo_file, critico,
                           data_ultimo_backup, data_modifica, contenuto_backup
                    FROM file_critici 
                    WHERE percorso_file = ?
                """, (percorso_file,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'percorso_file': row[0],
                        'hash_file': row[1],
                        'dimensione_file': row[2],
                        'tipo_file': row[3],
                        'critico': row[4],
                        'data_ultimo_backup': row[5],
                        'data_modifica': row[6],
                        'contenuto_backup': row[7]
                    }
                return None
        except Exception as e:
            logger.error(f"Errore nel recupero file critico {percorso_file}: {str(e)}", "BACKUP_PROGETTO", e)
            return None

    # ===== GESTIONE ERRORI E RECOVERY =====

    def registra_errore(self, tipo_errore: str, file_coinvolto: str = "", 
                       descrizione_errore: str = "", azione_eseguita: str = "",
                       backup_utilizzato: str = "") -> int:
        """Registra un errore nel sistema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO errori_recovery 
                    (tipo_errore, file_coinvolto, descrizione_errore, azione_eseguita, backup_utilizzato)
                    VALUES (?, ?, ?, ?, ?)
                """, (tipo_errore, file_coinvolto, descrizione_errore, azione_eseguita, backup_utilizzato))
                
                errore_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Errore registrato: {tipo_errore} - {file_coinvolto}", "BACKUP_PROGETTO")
                return errore_id
        except Exception as e:
            logger.error(f"Errore nella registrazione errore: {str(e)}", "BACKUP_PROGETTO", e)
            return 0

    def risolvi_errore(self, errore_id: int, azione_eseguita: str) -> bool:
        """Marca un errore come risolto"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE errori_recovery 
                    SET stato_risoluzione = 'risolto', data_risoluzione = CURRENT_TIMESTAMP,
                        azione_eseguita = ?
                    WHERE id = ?
                """, (azione_eseguita, errore_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Errore nella risoluzione errore {errore_id}: {str(e)}", "BACKUP_PROGETTO", e)
            return False

    def aggiorna_percorso_file_critico(self, vecchio_percorso: str, nuovo_percorso: str) -> bool:
        """Aggiorna il percorso di un file critico nel database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE file_critici 
                    SET percorso_file = ?
                    WHERE percorso_file = ?
                """, (nuovo_percorso, vecchio_percorso))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Errore aggiornamento percorso file critico: {str(e)}", "BACKUP_PROGETTO", e)
            return False

    def get_errori_non_risolti(self) -> List[Dict[str, Any]]:
        """Recupera gli errori non risolti"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, tipo_errore, file_coinvolto, descrizione_errore, 
                           data_errore, azione_eseguita, backup_utilizzato
                    FROM errori_recovery 
                    WHERE stato_risoluzione = 'da_risolvere'
                    ORDER BY data_errore DESC
                """)
                
                errori = []
                for row in cursor.fetchall():
                    errori.append({
                        'id': row[0],
                        'tipo_errore': row[1],
                        'file_coinvolto': row[2],
                        'descrizione_errore': row[3],
                        'data_errore': row[4],
                        'azione_eseguita': row[5],
                        'backup_utilizzato': row[6]
                    })
                
                return errori
        except Exception as e:
            logger.error(f"Errore nel recupero errori non risolti: {str(e)}", "BACKUP_PROGETTO", e)
            return []

    def pulisci_backup_vecchi(self, giorni: int = 30) -> bool:
        """Pulisce i backup più vecchi di N giorni"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM backup_progetto 
                    WHERE data_creazione < datetime('now', '-{} days')
                    AND tipo_backup = 'automatico'
                """.format(giorni))
                conn.commit()
                logger.info(f"Backup progetto più vecchi di {giorni} giorni rimossi", "BACKUP_PROGETTO")
                return True
        except Exception as e:
            logger.error(f"Errore nella pulizia backup vecchi: {str(e)}", "BACKUP_PROGETTO", e)
            return False
