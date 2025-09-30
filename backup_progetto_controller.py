"""
Controller per il backup automatico del progetto Gestionale Biciclette.

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
import shutil
import zipfile
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from src.utils.logger import logger


class BackupProgettoController:
    """Controller per il backup automatico del progetto"""

    def __init__(self, data_dir: str, project_root: str = None):
        """
        Inizializza il controller di backup progetto
        
        Args:
            data_dir: Directory dove salvare i dati
            project_root: Directory root del progetto (default: parent di data_dir)
        """
        self.data_dir = data_dir
        self.project_root = project_root or os.path.dirname(data_dir)
        from .backup_progetto_db import BackupProgettoDB
        self.db = BackupProgettoDB(data_dir)

    # ===== GESTIONE CONFIGURAZIONI =====

    def get_configurazione(self, chiave: str, default: str = "") -> str:
        """Recupera una configurazione"""
        return self.db.get_configurazione(chiave, default)

    def set_configurazione(self, chiave: str, valore: str, descrizione: str = "", categoria: str = "backup") -> bool:
        """Imposta una configurazione"""
        return self.db.set_configurazione(chiave, valore, descrizione, categoria)

    # ===== BACKUP AUTOMATICO PROGETTO =====

    def crea_backup_progetto(self, tipo_backup: str = "automatico", descrizione: str = "") -> Dict[str, Any]:
        """
        Crea un backup completo del progetto
        
        Args:
            tipo_backup: Tipo di backup (automatico/manuale)
            descrizione: Descrizione del backup
            
        Returns:
            Dizionario con il risultato del backup
        """
        try:
            # Verifica se il backup automatico è abilitato
            if tipo_backup == "automatico" and not self.is_backup_automatico_abilitato():
                return {
                    'successo': False,
                    'messaggio': 'Backup automatico disabilitato',
                    'percorso_file': None
                }

            # Prepara il percorso di backup
            backup_dir = os.path.join(self.data_dir, 'backup_progetto')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nome file con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_file = f"backup_progetto_{tipo_backup}_{timestamp}.zip"
            percorso_completo = os.path.join(backup_dir, nome_file)
            
            # Lista file da includere nel backup
            file_inclusi = self._get_file_da_backup()
            
            # Crea il backup
            with zipfile.ZipFile(percorso_completo, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_inclusi:
                    try:
                        if os.path.exists(file_path):
                            # Percorso relativo nel backup
                            arcname = os.path.relpath(file_path, self.project_root)
                            zipf.write(file_path, arcname)
                            
                            # Aggiorna il file critico nel database
                            self._aggiorna_file_critico_backup(file_path)
                    except Exception as e:
                        logger.error(f"Errore nel backup del file {file_path}: {str(e)}", "BACKUP_PROGETTO", e)
            
            # Calcola la dimensione del file
            dimensione_file = os.path.getsize(percorso_completo)
            
            # Calcola hash del backup
            hash_backup = self._calcola_hash_file(percorso_completo)
            
            # Salva il backup nel database
            self.db.salva_backup_progetto(
                nome_file, percorso_completo, dimensione_file, tipo_backup,
                descrizione, file_inclusi, hash_backup, "1.0.0"
            )
            
            # Pulisci i backup vecchi
            self._pulisci_backup_vecchi()
            
            logger.info(f"Backup progetto creato: {percorso_completo}", "BACKUP_PROGETTO")
            
            return {
                'successo': True,
                'messaggio': f'Backup progetto creato con successo: {nome_file}',
                'percorso_file': percorso_completo,
                'dimensione_mb': round(dimensione_file / (1024 * 1024), 2),
                'file_inclusi': len(file_inclusi),
                'hash_backup': hash_backup
            }
            
        except Exception as e:
            error_msg = f"Errore nella creazione backup progetto: {str(e)}"
            logger.error(error_msg, "BACKUP_PROGETTO", e)
            
            return {
                'successo': False,
                'messaggio': error_msg,
                'percorso_file': None
            }

    def _get_file_da_backup(self) -> List[str]:
        """Recupera la lista dei file da includere nel backup"""
        try:
            file_da_backup = []
            
            # Estensioni da includere
            estensioni_incluse = ['.py', '.txt', '.md', '.bat', '.json', '.sql', '.db']
            
            # Percorre il progetto
            for root, dirs, files in os.walk(self.project_root):
                # Esclude directory specifiche
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', 'env']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Includi file con estensioni specifiche
                    if any(file.endswith(ext) for ext in estensioni_incluse):
                        file_da_backup.append(file_path)
                    
                    # Includi file critici specifici
                    elif file in ['main.py', 'requirements.txt', 'avvia.bat', 'installa_e_avvia.bat']:
                        file_da_backup.append(file_path)
            
            return file_da_backup
            
        except Exception as e:
            logger.error(f"Errore nel recupero file da backup: {str(e)}", "BACKUP_PROGETTO", e)
            return []

    def _aggiorna_file_critico_backup(self, file_path: str):
        """Aggiorna le informazioni di backup di un file critico"""
        try:
            if os.path.exists(file_path):
                # Calcola hash del file
                hash_file = self._calcola_hash_file(file_path)
                
                # Dimensione del file
                dimensione_file = os.path.getsize(file_path)
                
                # Leggi contenuto per backup
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        contenuto_backup = f.read()
                except Exception:
                    # Se non è un file di testo, salva come binario
                    with open(file_path, 'rb') as f:
                        contenuto_backup = f.read().hex()
                
                # Percorso relativo
                percorso_relativo = os.path.relpath(file_path, self.project_root)
                
                # Aggiorna nel database
                self.db.aggiorna_file_critico(
                    percorso_relativo, hash_file, dimensione_file, contenuto_backup
                )
                
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento file critico {file_path}: {str(e)}", "BACKUP_PROGETTO", e)

    def _calcola_hash_file(self, file_path: str) -> str:
        """Calcola l'hash SHA256 di un file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Errore nel calcolo hash {file_path}: {str(e)}", "BACKUP_PROGETTO", e)
            return ""

    def _pulisci_backup_vecchi(self):
        """Pulisce i backup più vecchi del limite configurato"""
        try:
            giorni_conservazione = int(self.get_configurazione('mantieni_backup_giorni', '30'))
            self.db.pulisci_backup_vecchi(giorni_conservazione)
        except Exception as e:
            logger.error(f"Errore nella pulizia backup vecchi: {str(e)}", "BACKUP_PROGETTO", e)

    # ===== RIPRISTINO PROGETTO =====

    def ripristina_progetto(self, backup_id: int) -> Dict[str, Any]:
        """
        Ripristina il progetto da un backup
        
        Args:
            backup_id: ID del backup da utilizzare
            
        Returns:
            Dizionario con il risultato del ripristino
        """
        try:
            # Recupera i dati del backup
            backup_data = self.db.get_backup_by_id(backup_id)
            if not backup_data:
                return {
                    'successo': False,
                    'messaggio': 'Backup non trovato'
                }
            
            backup_path = backup_data['percorso_backup']
            if not os.path.exists(backup_path):
                return {
                    'successo': False,
                    'messaggio': 'File di backup non trovato'
                }
            
            # Crea un backup di sicurezza prima del ripristino
            backup_sicurezza = self.crea_backup_progetto("manuale", f"Backup sicurezza prima ripristino {backup_id}")
            if not backup_sicurezza['successo']:
                return {
                    'successo': False,
                    'messaggio': 'Impossibile creare backup di sicurezza per il ripristino'
                }
            
            # Estrai il backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                for file_info in zipf.infolist():
                    try:
                        # Percorso completo del file
                        file_path = os.path.join(self.project_root, file_info.filename)
                        
                        # Crea la directory se non esiste
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        # Estrai il file
                        zipf.extract(file_info, self.project_root)
                        
                    except Exception as e:
                        logger.error(f"Errore nell'estrazione {file_info.filename}: {str(e)}", "BACKUP_PROGETTO", e)
            
            # Registra il ripristino
            self.db.registra_errore(
                'ripristino_progetto', '', f'Ripristino da backup {backup_id}',
                f'Ripristinato da {backup_data["nome_backup"]}', backup_data['nome_backup']
            )
            
            logger.info(f"Progetto ripristinato da backup: {backup_path}", "BACKUP_PROGETTO")
            
            return {
                'successo': True,
                'messaggio': f'Progetto ripristinato con successo da {backup_data["nome_backup"]}'
            }
            
        except Exception as e:
            error_msg = f"Errore nel ripristino progetto: {str(e)}"
            logger.error(error_msg, "BACKUP_PROGETTO", e)
            
            return {
                'successo': False,
                'messaggio': error_msg
            }

    # ===== MONITORAGGIO E VERIFICA FILE =====

    def migra_percorsi_file_critici(self) -> bool:
        """Migra i percorsi dei file critici nel database"""
        try:
            # Aggiorna icon_manager.py
            successo = self.db.aggiorna_percorso_file_critico(
                'icon_manager.py', 
                'src/utils/icon_manager.py'
            )
            
            if successo:
                logger.info("Percorsi file critici migrati con successo")
            else:
                logger.warning("Nessun file critico da migrare")
            
            return True
        except Exception as e:
            logger.error(f"Errore migrazione percorsi file critici: {str(e)}", "BACKUP_PROGETTO", e)
            return False

    def verifica_integrita_progetto(self) -> Dict[str, Any]:
        """
        Verifica l'integrità del progetto controllando i file critici
        
        Returns:
            Dizionario con i risultati della verifica
        """
        try:
            file_critici = self.db.get_file_critici()
            file_mancanti = []
            file_corotti = []
            file_ok = []
            
            for file_info in file_critici:
                file_path = os.path.join(self.project_root, file_info['percorso_file'])
                
                if not os.path.exists(file_path):
                    file_mancanti.append(file_info)
                else:
                    # Verifica hash se disponibile
                    if file_info['hash_file']:
                        hash_attuale = self._calcola_hash_file(file_path)
                        if hash_attuale != file_info['hash_file']:
                            file_corotti.append(file_info)
                        else:
                            file_ok.append(file_info)
                    else:
                        file_ok.append(file_info)
            
            # Registra errori se trovati
            if file_mancanti or file_corotti:
                for file_info in file_mancanti:
                    self.db.registra_errore(
                        'file_mancante', file_info['percorso_file'],
                        f'File critico mancante: {file_info["percorso_file"]}',
                        'File non trovato nel progetto'
                    )
                
                for file_info in file_corotti:
                    self.db.registra_errore(
                        'file_corrotto', file_info['percorso_file'],
                        f'File critico corrotto: {file_info["percorso_file"]}',
                        'Hash del file non corrisponde al backup'
                    )
            
            return {
                'successo': True,
                'file_totali': len(file_critici),
                'file_ok': len(file_ok),
                'file_mancanti': len(file_mancanti),
                'file_corotti': len(file_corotti),
                'dettagli_mancanti': [f['percorso_file'] for f in file_mancanti],
                'dettagli_corotti': [f['percorso_file'] for f in file_corotti]
            }
            
        except Exception as e:
            error_msg = f"Errore nella verifica integrità: {str(e)}"
            logger.error(error_msg, "BACKUP_PROGETTO", e)
            
            return {
                'successo': False,
                'messaggio': error_msg
            }

    def auto_ripara_file_mancanti(self) -> Dict[str, Any]:
        """
        Ripara automaticamente i file mancanti dal backup più recente
        
        Returns:
            Dizionario con i risultati della riparazione
        """
        try:
            if not self.get_configurazione('auto_riparazione', 'true').lower() == 'true':
                return {
                    'successo': False,
                    'messaggio': 'Auto-riparazione disabilitata'
                }
            
            # Verifica integrità
            verifica = self.verifica_integrita_progetto()
            if not verifica['successo']:
                return verifica
            
            file_riparati = []
            errori_riparazione = []
            
            # Ripara file mancanti
            for file_path in verifica['dettagli_mancanti']:
                try:
                    successo = self._ripara_file_mancante(file_path)
                    if successo:
                        file_riparati.append(file_path)
                    else:
                        errori_riparazione.append(file_path)
                except Exception as e:
                    errori_riparazione.append(f"{file_path}: {str(e)}")
                    logger.error(f"Errore nella riparazione {file_path}: {str(e)}", "BACKUP_PROGETTO", e)
            
            # Ripara file corrotti
            for file_path in verifica['dettagli_corotti']:
                try:
                    successo = self._ripara_file_corrotto(file_path)
                    if successo:
                        file_riparati.append(file_path)
                    else:
                        errori_riparazione.append(file_path)
                except Exception as e:
                    errori_riparazione.append(f"{file_path}: {str(e)}")
                    logger.error(f"Errore nella riparazione {file_path}: {str(e)}", "BACKUP_PROGETTO", e)
            
            return {
                'successo': True,
                'file_riparati': len(file_riparati),
                'errori_riparazione': len(errori_riparazione),
                'dettagli_riparati': file_riparati,
                'dettagli_errori': errori_riparazione
            }
            
        except Exception as e:
            error_msg = f"Errore nell'auto-riparazione: {str(e)}"
            logger.error(error_msg, "BACKUP_PROGETTO", e)
            
            return {
                'successo': False,
                'messaggio': error_msg
            }

    def _ripara_file_mancante(self, file_path: str) -> bool:
        """Ripara un file mancante dal backup"""
        try:
            # Recupera il file critico dal database
            file_info = self.db.get_file_critico(file_path)
            if not file_info or not file_info['contenuto_backup']:
                return False
            
            # Percorso completo
            full_path = os.path.join(self.project_root, file_path)
            
            # Crea la directory se non esiste
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Ripristina il contenuto
            try:
                # Prova come file di testo
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_info['contenuto_backup'])
            except Exception:
                # Se fallisce, prova come file binario
                with open(full_path, 'wb') as f:
                    f.write(bytes.fromhex(file_info['contenuto_backup']))
            
            # Aggiorna le informazioni del file
            self._aggiorna_file_critico_backup(full_path)
            
            logger.info(f"File riparato: {file_path}", "BACKUP_PROGETTO")
            return True
            
        except Exception as e:
            logger.error(f"Errore nella riparazione file {file_path}: {str(e)}", "BACKUP_PROGETTO", e)
            return False

    def _ripara_file_corrotto(self, file_path: str) -> bool:
        """Ripara un file corrotto dal backup"""
        # Per ora, tratta i file corrotti come file mancanti
        return self._ripara_file_mancante(file_path)

    # ===== GESTIONE ERRORI =====

    def get_errori_non_risolti(self) -> List[Dict[str, Any]]:
        """Recupera gli errori non risolti"""
        return self.db.get_errori_non_risolti()

    def risolvi_errore(self, errore_id: int, azione_eseguita: str) -> bool:
        """Marca un errore come risolto"""
        return self.db.risolvi_errore(errore_id, azione_eseguita)

    # ===== UTILITY =====

    def is_backup_automatico_abilitato(self) -> bool:
        """Verifica se il backup automatico è abilitato"""
        return self.get_configurazione('backup_automatico_progetto', 'true').lower() == 'true'

    def get_ultimi_backup_progetto(self, limite: int = 10) -> List[Dict[str, Any]]:
        """Recupera gli ultimi backup del progetto"""
        return self.db.get_ultimi_backup_progetto(limite)

    def get_statistiche_backup(self) -> Dict[str, Any]:
        """Recupera statistiche sui backup"""
        try:
            backup_list = self.get_ultimi_backup_progetto(50)
            file_critici = self.db.get_file_critici()
            errori = self.get_errori_non_risolti()
            
            totale_dimensioni = sum(backup.get('dimensione_backup', 0) for backup in backup_list)
            backup_automatici = len([b for b in backup_list if b['tipo_backup'] == 'automatico'])
            backup_manuali = len([b for b in backup_list if b['tipo_backup'] == 'manuale'])
            
            return {
                'backup_totali': len(backup_list),
                'backup_automatici': backup_automatici,
                'backup_manuali': backup_manuali,
                'dimensioni_totali_mb': round(totale_dimensioni / (1024 * 1024), 2),
                'file_critici_totali': len(file_critici),
                'errori_non_risolti': len(errori),
                'backup_automatico_abilitato': self.is_backup_automatico_abilitato(),
                'auto_riparazione_abilitata': self.get_configurazione('auto_riparazione', 'true').lower() == 'true'
            }
        except Exception as e:
            logger.error(f"Errore nel recupero statistiche backup: {str(e)}", "BACKUP_PROGETTO", e)
            return {}

    def esegui_backup_automatico(self) -> Dict[str, Any]:
        """Esegue un backup automatico se necessario"""
        try:
            if not self.is_backup_automatico_abilitato():
                return {
                    'successo': False,
                    'messaggio': 'Backup automatico disabilitato'
                }
            
            # Verifica se è necessario un backup
            ultimi_backup = self.get_ultimi_backup_progetto(1)
            if ultimi_backup:
                ultimo_backup = ultimi_backup[0]
                data_ultimo = datetime.fromisoformat(ultimo_backup['data_creazione'])
                
                # Controlla la frequenza
                frequenza = self.get_configurazione('frequenza_backup_progetto', 'giornaliero')
                if frequenza == 'giornaliero' and (datetime.now() - data_ultimo).days < 1:
                    return {
                        'successo': False,
                        'messaggio': 'Backup automatico non necessario (ultimo backup recente)'
                    }
                elif frequenza == 'settimanale' and (datetime.now() - data_ultimo).days < 7:
                    return {
                        'successo': False,
                        'messaggio': 'Backup automatico non necessario (ultimo backup recente)'
                    }
                elif frequenza == 'mensile' and (datetime.now() - data_ultimo).days < 30:
                    return {
                        'successo': False,
                        'messaggio': 'Backup automatico non necessario (ultimo backup recente)'
                    }
            
            # Esegue il backup automatico
            return self.crea_backup_progetto("automatico", "Backup automatico del progetto")
            
        except Exception as e:
            error_msg = f"Errore nel backup automatico: {str(e)}"
            logger.error(error_msg, "BACKUP_PROGETTO", e)
            
            return {
                'successo': False,
                'messaggio': error_msg
            }

    # ===== PULIZIA FILE DUPLICATI E IN ECCESSO =====

    def pulisci_file_duplicati_e_eccesso(self) -> Dict[str, Any]:
        """
        Pulisce file duplicati e in eccesso nel progetto
        
        Returns:
            Dizionario con il risultato della pulizia
        """
        try:
            # Backup di sicurezza prima della pulizia
            backup_sicurezza = self.crea_backup_progetto("manuale", "Backup sicurezza prima pulizia duplicati")
            if not backup_sicurezza['successo']:
                return {
                    'successo': False,
                    'messaggio': 'Impossibile creare backup di sicurezza per la pulizia'
                }
            
            start_time = time.time()
            file_rimossi = []
            errori = []
            
            # 1. Pulisce file duplicati nel filesystem
            duplicati_rimossi = self._pulisci_file_duplicati_filesystem()
            file_rimossi.extend(duplicati_rimossi)
            
            # 2. Pulisce file temporanei e cache
            temp_rimossi = self._pulisci_file_temporanei()
            file_rimossi.extend(temp_rimossi)
            
            # 3. Pulisce file di log vecchi
            log_rimossi = self._pulisci_file_log_vecchi()
            file_rimossi.extend(log_rimossi)
            
            # 4. Pulisce file di backup vecchi
            backup_rimossi = self._pulisci_file_backup_vecchi()
            file_rimossi.extend(backup_rimossi)
            
            # 5. Pulisce file di test e sviluppo
            test_rimossi = self._pulisci_file_test_sviluppo()
            file_rimossi.extend(test_rimossi)
            
            # 6. Pulisce database duplicati
            db_duplicati = self._pulisci_database_duplicati()
            
            tempo_esecuzione = time.time() - start_time
            
            return {
                'successo': True,
                'messaggio': f'Pulizia completata: {len(file_rimossi)} file rimossi',
                'file_rimossi': len(file_rimossi),
                'dettagli_file_rimossi': file_rimossi,
                'database_duplicati_rimossi': db_duplicati,
                'tempo_esecuzione': round(tempo_esecuzione, 2),
                'errori': errori
            }
            
        except Exception as e:
            error_msg = f"Errore nella pulizia file duplicati: {str(e)}"
            logger.error(error_msg, "BACKUP_PROGETTO", e)
            
            return {
                'successo': False,
                'messaggio': error_msg
            }

    def _pulisci_file_duplicati_filesystem(self) -> List[str]:
        """Pulisce file duplicati nel filesystem"""
        try:
            file_rimossi = []
            
            # Percorre il progetto per trovare file duplicati
            file_hash_map = {}
            duplicati_trovati = []
            
            for root, dirs, files in os.walk(self.project_root):
                # Esclude directory specifiche
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', 'env', 'backup_progetto', 'logs']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Salta file critici
                    if self._is_file_critico(file_path):
                        continue
                    
                    try:
                        # Calcola hash del file
                        file_hash = self._calcola_hash_file(file_path)
                        if file_hash:
                            if file_hash in file_hash_map:
                                # File duplicato trovato
                                duplicati_trovati.append((file_path, file_hash_map[file_hash]))
                            else:
                                file_hash_map[file_hash] = file_path
                    except Exception:
                        # Salta file che non possono essere letti
                        continue
            
            # Rimuove i duplicati (mantiene il primo trovato)
            for duplicato_path, originale_path in duplicati_trovati:
                try:
                    # Verifica che non sia un file critico
                    if not self._is_file_critico(duplicato_path):
                        os.remove(duplicato_path)
                        file_rimossi.append(f"Duplicato: {os.path.relpath(duplicato_path, self.project_root)}")
                        logger.info(f"File duplicato rimosso: {duplicato_path}", "PULIZIA")
                except Exception as e:
                    logger.error(f"Errore nella rimozione duplicato {duplicato_path}: {str(e)}", "PULIZIA", e)
            
            return file_rimossi
            
        except Exception as e:
            logger.error(f"Errore nella pulizia file duplicati filesystem: {str(e)}", "PULIZIA", e)
            return []

    def _pulisci_file_temporanei(self) -> List[str]:
        """Pulisce file temporanei e cache"""
        try:
            file_rimossi = []
            
            # Estensioni e pattern di file temporanei
            temp_patterns = [
                '*.tmp', '*.temp', '*.cache', '*.log',
                '*~', '*.swp', '*.swo', '*.pyc', '*.pyo',
                '*.bak', '*.backup', '*.old', '*.orig'
            ]
            
            for root, dirs, files in os.walk(self.project_root):
                # Esclude directory critiche
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', 'env', 'backup_progetto']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Verifica se è un file temporaneo
                    if self._is_file_temporaneo(file):
                        try:
                            if not self._is_file_critico(file_path):
                                os.remove(file_path)
                                file_rimossi.append(f"Temporaneo: {os.path.relpath(file_path, self.project_root)}")
                                logger.info(f"File temporaneo rimosso: {file_path}", "PULIZIA")
                        except Exception as e:
                            logger.error(f"Errore nella rimozione file temporaneo {file_path}: {str(e)}", "PULIZIA", e)
            
            return file_rimossi
            
        except Exception as e:
            logger.error(f"Errore nella pulizia file temporanei: {str(e)}", "PULIZIA", e)
            return []

    def _pulisci_file_log_vecchi(self) -> List[str]:
        """Pulisce file di log vecchi"""
        try:
            file_rimossi = []
            giorni_conservazione = int(self.get_configurazione('giorni_pulizia_log', '90'))
            
            for root, dirs, files in os.walk(self.project_root):
                for file in files:
                    if file.endswith('.log'):
                        file_path = os.path.join(root, file)
                        
                        try:
                            # Verifica l'età del file
                            file_time = os.path.getmtime(file_path)
                            file_age_days = (time.time() - file_time) / (24 * 3600)
                            
                            if file_age_days > giorni_conservazione:
                                if not self._is_file_critico(file_path):
                                    os.remove(file_path)
                                    file_rimossi.append(f"Log vecchio: {os.path.relpath(file_path, self.project_root)}")
                                    logger.info(f"File log vecchio rimosso: {file_path}", "PULIZIA")
                        except Exception as e:
                            logger.error(f"Errore nella rimozione log {file_path}: {str(e)}", "PULIZIA", e)
            
            return file_rimossi
            
        except Exception as e:
            logger.error(f"Errore nella pulizia file log vecchi: {str(e)}", "PULIZIA", e)
            return []

    def _pulisci_file_backup_vecchi(self) -> List[str]:
        """Pulisce file di backup vecchi"""
        try:
            file_rimossi = []
            giorni_conservazione = int(self.get_configurazione('mantieni_backup_giorni', '30'))
            
            for root, dirs, files in os.walk(self.project_root):
                for file in files:
                    if any(file.endswith(ext) for ext in ['.bak', '.backup', '.old', '.orig']):
                        file_path = os.path.join(root, file)
                        
                        try:
                            # Verifica l'età del file
                            file_time = os.path.getmtime(file_path)
                            file_age_days = (time.time() - file_time) / (24 * 3600)
                            
                            if file_age_days > giorni_conservazione:
                                if not self._is_file_critico(file_path):
                                    os.remove(file_path)
                                    file_rimossi.append(f"Backup vecchio: {os.path.relpath(file_path, self.project_root)}")
                                    logger.info(f"File backup vecchio rimosso: {file_path}", "PULIZIA")
                        except Exception as e:
                            logger.error(f"Errore nella rimozione backup {file_path}: {str(e)}", "PULIZIA", e)
            
            return file_rimossi
            
        except Exception as e:
            logger.error(f"Errore nella pulizia file backup vecchi: {str(e)}", "PULIZIA", e)
            return []

    def _pulisci_file_test_sviluppo(self) -> List[str]:
        """Pulisce file di test e sviluppo"""
        try:
            file_rimossi = []
            
            # Pattern di file di test e sviluppo
            test_patterns = [
                'test_*.py', '*_test.py', 'debug_*.py', 'temp_*.py',
                '*.test', '*.debug', '*.dev'
            ]
            
            for root, dirs, files in os.walk(self.project_root):
                # Esclude directory critiche
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', 'env', 'backup_progetto']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Verifica se è un file di test/sviluppo
                    if self._is_file_test_sviluppo(file):
                        try:
                            if not self._is_file_critico(file_path):
                                os.remove(file_path)
                                file_rimossi.append(f"Test/Sviluppo: {os.path.relpath(file_path, self.project_root)}")
                                logger.info(f"File test/sviluppo rimosso: {file_path}", "PULIZIA")
                        except Exception as e:
                            logger.error(f"Errore nella rimozione file test {file_path}: {str(e)}", "PULIZIA", e)
            
            return file_rimossi
            
        except Exception as e:
            logger.error(f"Errore nella pulizia file test/sviluppo: {str(e)}", "PULIZIA", e)
            return []

    def _pulisci_database_duplicati(self) -> int:
        """Pulisce record duplicati nei database"""
        try:
            record_rimossi = 0
            
            # Lista dei database da pulire
            database_list = self.db.get_lista_database()
            
            for db_name in database_list:
                if db_name == 'backup_progetto':  # Salta il database di backup
                    continue
                
                db_path = os.path.join(self.data_dir, f"{db_name}.db")
                if os.path.exists(db_path):
                    try:
                        with sqlite3.connect(db_path) as conn:
                            cursor = conn.cursor()
                            
                            # Pulisce duplicati per tabella (esempi generici)
                            tabelle_da_pulire = [
                                ('clienti', 'email'),
                                ('prodotti', 'codice'),
                                ('fornitori', 'nome'),
                                ('categorie', 'nome')
                            ]
                            
                            for tabella, campo in tabelle_da_pulire:
                                try:
                                    # Verifica se la tabella esiste
                                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabella}'")
                                    if cursor.fetchone():
                                        # Rimuove duplicati
                                        cursor.execute(f"""
                                            DELETE FROM {tabella} 
                                            WHERE id NOT IN (
                                                SELECT MIN(id) FROM {tabella} 
                                                GROUP BY {campo}
                                            )
                                        """)
                                        record_rimossi += cursor.rowcount
                                except Exception as e:
                                    logger.error(f"Errore pulizia duplicati {tabella}: {str(e)}", "PULIZIA", e)
                            
                            conn.commit()
                            
                    except Exception as e:
                        logger.error(f"Errore pulizia database {db_name}: {str(e)}", "PULIZIA", e)
            
            return record_rimossi
            
        except Exception as e:
            logger.error(f"Errore nella pulizia database duplicati: {str(e)}", "PULIZIA", e)
            return 0

    def _is_file_critico(self, file_path: str) -> bool:
        """Verifica se un file è critico per il funzionamento"""
        try:
            # Percorso relativo
            rel_path = os.path.relpath(file_path, self.project_root)
            
            # Lista file critici
            file_critici = [
                'main.py', 'requirements.txt', 'avvia.bat', 'installa_e_avvia.bat',
                'src/modules/app_controller.py', 'src/gui/menu_handler.py',
                'src/gui/tab_manager.py', 'src/gui/screen_manager.py',
                'src/gui/impostazioni_gui.py', 'src/utils/logger.py',
                'src/utils/icon_manager.py'
            ]
            
            # Verifica se è un file critico
            for file_critico in file_critici:
                if rel_path == file_critico or rel_path.endswith(file_critico):
                    return True
            
            # Verifica se è un file di database
            if rel_path.endswith('.db'):
                return True
            
            # Verifica se è un file di configurazione
            if rel_path.endswith(('.json', '.ini', '.cfg', '.conf')):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Errore nella verifica file critico {file_path}: {str(e)}", "PULIZIA", e)
            return True  # In caso di errore, considera critico per sicurezza

    def _is_file_temporaneo(self, filename: str) -> bool:
        """Verifica se un file è temporaneo"""
        temp_extensions = ['.tmp', '.temp', '.cache', '.log', '.pyc', '.pyo', '.bak', '.backup', '.old', '.orig']
        temp_prefixes = ['temp_', 'tmp_', 'debug_', 'test_']
        temp_suffixes = ['~', '.swp', '.swo']
        
        # Verifica estensioni
        if any(filename.endswith(ext) for ext in temp_extensions):
            return True
        
        # Verifica prefissi
        if any(filename.startswith(prefix) for prefix in temp_prefixes):
            return True
        
        # Verifica suffissi
        if any(filename.endswith(suffix) for suffix in temp_suffixes):
            return True
        
        return False

    def _is_file_test_sviluppo(self, filename: str) -> bool:
        """Verifica se un file è di test o sviluppo"""
        test_patterns = ['test_', '_test', 'debug_', 'temp_', 'dev_']
        
        # Verifica pattern
        if any(pattern in filename.lower() for pattern in test_patterns):
            return True
        
        # Verifica estensioni specifiche
        if filename.endswith(('.test', '.debug', '.dev')):
            return True
        
        return False
