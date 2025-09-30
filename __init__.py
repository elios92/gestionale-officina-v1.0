"""
Modulo per il backup automatico del progetto Gestionale Biciclette.

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

from .backup_progetto_db import BackupProgettoDB
from .backup_progetto_controller import BackupProgettoController

__all__ = ['BackupProgettoDB', 'BackupProgettoController']
