"""
Gestionale Biciclette v1.0 - Applicazione Principale (Nuova Architettura)

Sistema di gestione completo per negozi di biciclette con architettura modulare.
Ogni funzionalità ha il suo database, controller e GUI specifici.

Autore: elios 1992
Versione: 1.0.0 final bro
Data: 2025
"""

# Pyright / Pylance: disabilita controlli rumorosi su questo file monolitico
# (temporaneo: permette di lavorare sui bug runtime senza centinaia di false-positive)
# pyright: reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownLambdaType=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
# type: ignore

import os
import sys
import time
import logging
from tkinter import messagebox
import customtkinter as ctk  # type: ignore[reportMissingTypeStubs]

# Aggiungi il percorso src al sys.path per importare i moduli locali
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
# Directory dei database usata in più punti: definita in anticipo per evitare variabili non associate
db_dir = os.path.join(current_dir, "data")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Imposta un logger di fallback prima degli import per poter loggare anche se gli import falliscono
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gestionale_main")

# Import dei moduli locali (tentativo)
try:
    from src.modules.app_controller import AppController
    from src.modules.officina.officina_controller import OfficinaController
    from src.gui.menu_handler import MenuHandler
    from src.gui.tab_manager import TabManager
    from src.gui.screen_manager import ScreenManager
    from src.gui.bici_restaurate_gui import BiciRestaurateGUI
    from src.gui.impostazioni_gui import ImpostazioniGUI
    from src.gui.riparazioni_gui import RiparazioniGUI
    from src.utils.icon_manager import IconManager
    # Sovrascrive il fallback logger se disponibile
    from src.utils.logger import logger
    from src.utils.error_handler import initialize_error_handler
    from src.utils.translations import translation_manager
except Exception as e:
    # Se falliscono gli import, logga e fallisci in modo controllato usando il fallback logger
    logger.critical(f"Errore import moduli principali: {e}")
    raise


class GestionaleApp:
    """Classe principale dell'applicazione Gestionale"""

    def __init__(self):
        # Inizializza il controller dell'applicazione
        self.app_controller = AppController()

        # Settings proxy: for compatibility with older code expecting dict-like .get
        class _SettingsProxy:
            def __init__(self, imp_controller):
                self._imp = imp_controller
            def get(self, key, default=""):
                try:
                    return self._imp.get_impostazione(key, default)
                except Exception:
                    return default

        # Imposta un proxy delle impostazioni sempre valido: evita None e rende
        # sicuro chiamare `self.settings.get(...)` in tutto il codice.
        try:
            self.settings = _SettingsProxy(self.app_controller.impostazioni)
        except Exception:
            # Fallback: proxy che usa valori predefiniti vuoti e logga l'errore
            class _FallbackSettings:
                def get(self, key, default=""):
                    try:
                        logger.debug(f"Fallback settings used for key: {key}")
                        return default
                    except Exception:
                        return default

            self.settings = _FallbackSettings()

        # Controller e attributi che potrebbero essere richiesti in background
        self.officina_controller = None
        self.riparazioni_controller = None
        self.bici_restaurate_controller = None
        self.bici_artigianali_controller = None
        self.inventario_controller = None
        self.menu_handler = None
        self.tab_manager = None
        self.screen_manager = None
        self.icon_manager = None
        self.audio_system = None
        

        # Configurazione iniziale di customtkinter
        # translation_manager espone get_text; non usare .get()
        try:
            theme = translation_manager.get_text('app.theme')
            if not theme:
                theme = 'light'
        except Exception:
            theme = 'light'
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

        # Crea la finestra principale
        self.root = ctk.CTk()
        try:
            self.root.title(f"{translation_manager.get_text('app.title')} v1.0")
        except Exception:
            self.root.title("Gestionale Biciclette v1.0")

        # Applica le impostazioni della finestra
        try:
            self._apply_window_settings()
        except Exception:
            # _apply_window_settings può fare riferimento a impostazioni non ancora inizializzate
            pass
        self.root.minsize(600, 800)

        # Inizializza i gestori GUI
        self.menu_handler = MenuHandler(self.root, self)
        self.icon_manager = IconManager(self)

        # Inizializza le GUI come None (caricate in background)
        self.bici_restaurate_gui = None
        self.bici_artigianali_gui = None
        self.inventario_gui = None

        # Defensive initialization: ensure attribute exists before async GUI loading
        self.guida_manager = None

        # Inizializza il sistema di gestione errori (se disponibile)
        try:
            initialize_error_handler(self.app_controller.backup_progetto)
        except Exception:
            logger.warning("initialize_error_handler non disponibile al momento dell'inizializzazione")

        # Esegue backup automatico se necessario
        try:
            self._check_auto_backup()
        except Exception:
            pass

        # Attributi per l'inventario (inizializzati quando necessario)
        self.search_entry = None
        self.prodotti_frame = None

        # Crea la barra menu e imposta icona
        try:
            self.menu_handler.create_menu_bar()
        except Exception:
            pass
        try:
            self.icon_manager.set_window_icon(self.root)
        except Exception:
            pass

        # Crea l'interfaccia principale
        try:
            self._create_interface()
        except Exception:
            pass

        # Centra la finestra
        try:
            self._center_window()
        except Exception:
            pass

        # Caricamento progressivo delle GUI (più veloce)
        try:
            self._load_guis_progressively()
        except Exception:
            pass

        # Mostra indicatore di caricamento
        try:
            self._show_loading_indicator()
        except Exception:
            pass

        # Cache avanzata per le GUI
        self.gui_cache = {}
        self.cache_loaded = False

        # Inizializza il gestore delle guide (se possibile)
        try:
            from src.gui.guida_manager import GuidaManager
            self.guida_manager = GuidaManager(self)
        except Exception as e:
            logger.error(f"Errore inizializzazione guida_manager: {e}")
            self.guida_manager = None

        # Inizializza il controller pricing in modo difensivo
        try:
            from src.modules.pricing.pricing_controller import PricingController
            self.pricing_controller = PricingController("data")
        except Exception:
            self.pricing_controller = None

        # Inizializza i controller per i nuovi lavori (in blocchi separati per
        # evitare che l'eccezione di un controller impedisca l'inizializzazione
        # degli altri)
        try:
            from src.controllers.nuovo_lavoro_controller import NuovoLavoroController
            try:
                self.nuovo_lavoro_controller = NuovoLavoroController(self)
            except Exception as e:
                logger.error(f"Errore inizializzazione NuovoLavoroController: {e}")
                self.nuovo_lavoro_controller = None
        except Exception as e:
            logger.error(f"Errore import NuovoLavoroController: {e}")
            self.nuovo_lavoro_controller = None

        try:
            from src.controllers.biciclette_controller import BicicletteController
            try:
                self.biciclette_controller = BicicletteController(self)
            except Exception as e:
                logger.error(f"Errore inizializzazione BicicletteController: {e}")
                self.biciclette_controller = None
        except Exception as e:
            logger.error(f"Errore import BicicletteController: {e}")
            self.biciclette_controller = None

        try:
            from src.controllers.clienti_controller import ClientiController
            try:
                self.clienti_controller = ClientiController(self)
            except Exception as e:
                logger.error(f"Errore inizializzazione ClientiController: {e}")
                self.clienti_controller = None
        except Exception as e:
            logger.error(f"Errore import ClientiController: {e}")
            self.clienti_controller = None

        try:
            from src.controllers.vendite_controller import VenditeController
            try:
                self.vendite_controller = VenditeController(self)
            except Exception as e:
                logger.error(f"Errore inizializzazione VenditeController: {e}")
                self.vendite_controller = None
        except Exception as e:
            logger.error(f"Errore import VenditeController: {e}")
            self.vendite_controller = None

        # Inizializza i controller delle biciclette specifici (difensivamente)
        try:
            from src.modules.biciclette.bici_restaurate_controller import BiciRestaurateController
            from src.modules.biciclette.bici_artigianali_controller import BiciArtigianaliController
            # Usa la directory dei database (data) definita a livello di modulo
            self.bici_restaurate_controller = BiciRestaurateController(db_dir)
            self.bici_artigianali_controller = BiciArtigianaliController(db_dir)
        except Exception as e:
            logger.error(f"Errore inizializzazione controller bici specifici: {e}")
            self.bici_restaurate_controller = None
            self.bici_artigianali_controller = None

        # Eager initialization del controller delle biciclette usate
        try:
            from src.modules.biciclette.bici_usate_controller import BiciUsateController
            # Supponiamo che app_controller sia già inizializzato in app
            self.bici_usate_controller = BiciUsateController("data", self.app_controller)
            logger.info("Inizializzato eager BiciUsateController")
        except Exception as e:
            logger.error(f"Errore inizializzazione BiciUsateController: {e}")
            self.bici_usate_controller = None

        # Inizializza il controller officina se possibile (richiede db_dir)
        try:
            self.officina_controller = OfficinaController(db_dir)
        except Exception as e:
            logger.error(f"Errore inizializzazione OfficinaController: {e}")
            self.officina_controller = None

        # Inizializza il controller riparazioni in modo difensivo
        try:
            from src.controllers.riparazioni_controller import RiparazioniController
            # Passiamo la directory dei db; il controller può accettare un manager o path
            self.riparazioni_controller = RiparazioniController(db_dir)
        except Exception as e:
            logger.error(f"Errore inizializzazione RiparazioniController: {e}")
            self.riparazioni_controller = None


    def _load_guis_progressively(self):
        """Carica le GUI in background con approccio moderno e lazy loading"""
        try:
            from concurrent.futures import ThreadPoolExecutor
            
            # Pool di thread per caricamento parallelo
            self.executor = ThreadPoolExecutor(max_workers=3)
            
            # Lista delle GUI da caricare con priorità
            self.gui_loading_tasks = [
                ("inventario", self._load_inventario_gui, 1),
                ("bici_restaurate", self._load_bici_restaurate_gui, 2),
                ("bici_artigianali", self._load_bici_artigianali_gui, 3)
            ]
            
            # Avvia il caricamento asincrono
            self._start_async_loading()
            
        except Exception as e:
            logger.error(f"Errore avvio caricamento progressivo: {e}")
    
    def _start_async_loading(self):
        """Avvia il caricamento asincrono delle GUI"""
        try:
            # Carica le GUI in parallelo con priorità
            futures = []
            
            for gui_name, load_func, priority in self.gui_loading_tasks:
                future = self.executor.submit(self._load_gui_with_priority, gui_name, load_func, priority)
                futures.append((gui_name, future))
            
            # Monitora il completamento
            self._monitor_loading_futures(futures)
            
        except Exception as e:
            logger.error(f"Errore avvio caricamento asincrono: {e}")
    
    def _load_gui_with_priority(self, gui_name, load_func, priority):
        """Carica una GUI con priorità specifica"""
        try:
            # Simula il tempo di caricamento basato sulla priorità
            time.sleep(0.1 * priority)
            
            # Carica la GUI
            load_func()
            
            logger.info(f"✅ {gui_name} caricata con priorità {priority}")
            return gui_name, "success"
            
        except Exception as e:
            logger.error(f"❌ Errore caricamento {gui_name}: {e}")
            return gui_name, f"error:{e}"
    
    def _monitor_loading_futures(self, futures):
        """Monitora il completamento delle GUI in caricamento"""
        try:
            completed = 0
            total = len(futures)
            
            for _, future in futures:
                # '_' perché il nome della GUI è nel result[0]
                if future.done():
                    result = future.result()
                    if result[1] == "success":
                        completed += 1
                        logger.info(f"🎯 {result[0]} completata ({completed}/{total})")
                    else:
                        logger.error(f"❌ {result[0]} fallita: {result[1]}")
            
            # Se tutte le GUI sono caricate, nascondi l'indicatore
            if completed == total:
                self.root.after(500, self._hide_loading_indicator)
                logger.info("🚀 Tutte le GUI caricate con successo!")
            else:
                # Riprogramma il controllo
                self.root.after(200, lambda: self._monitor_loading_futures(futures))
                
        except Exception as e:
            logger.error(f"Errore monitoraggio futures: {e}")
            # Riprogramma comunque il controllo
            self.root.after(1000, lambda: self._monitor_loading_futures(futures))
    
    def _load_inventario_gui(self):
        """Carica la GUI inventario con caching intelligente"""
        try:
            # Verifica che l'oggetto sia completamente inizializzato
            if not hasattr(self, 'gui_cache'):
                self.gui_cache = {}
            
            if not hasattr(self, 'inventario_gui') or self.inventario_gui is None:
                # Controlla la cache
                if 'inventario' in self.gui_cache:
                    self.inventario_gui = self.gui_cache['inventario']
                    logger.info("✅ GUI Inventario caricata dalla cache")
                else:
                    from src.gui.inventario_gui import InventarioGUI
                    self.inventario_gui = InventarioGUI(self, self.guida_manager if self.guida_manager else None)
                    # Salva nella cache
                    self.gui_cache['inventario'] = self.inventario_gui
                    logger.info("✅ GUI Inventario caricata in background")
        except Exception as e:
            logger.error(f"❌ inventario fallita: {e}")
    
    def _load_bici_restaurate_gui(self):
        """Carica la GUI bici restaurate con caching intelligente"""
        try:
            # Verifica che l'oggetto sia completamente inizializzato
            if not hasattr(self, 'gui_cache'):
                self.gui_cache = {}
            
            if not hasattr(self, 'bici_restaurate_gui') or self.bici_restaurate_gui is None:
                # Controlla la cache
                if 'bici_restaurate' in self.gui_cache:
                    self.bici_restaurate_gui = self.gui_cache['bici_restaurate']
                    logger.info("✅ GUI Bici Restaurate caricata dalla cache")
                else:
                    self.bici_restaurate_gui = BiciRestaurateGUI(self.root, self.bici_restaurate_controller, self)
                    # Salva nella cache
                    self.gui_cache['bici_restaurate'] = self.bici_restaurate_gui
                    logger.info("✅ GUI Bici Restaurate caricata in background")
        except Exception as e:
            logger.error(f"❌ bici_restaurate fallita: {e}")
    
    def _load_bici_artigianali_gui(self):
        """Carica la GUI bici artigianali con caching intelligente"""
        try:
            # Verifica che l'oggetto sia completamente inizializzato
            if not hasattr(self, 'gui_cache'):
                self.gui_cache = {}
            
            if not hasattr(self, 'bici_artigianali_gui') or self.bici_artigianali_gui is None:
                # Controlla la cache
                if 'bici_artigianali' in self.gui_cache:
                    self.bici_artigianali_gui = self.gui_cache['bici_artigianali']
                    logger.info("✅ GUI Bici Artigianali caricata dalla cache")
                else:
                    # Import dal package src.gui (coerente con gli altri import)
                    from src.gui.bici_artigianali_gui import BiciArtigianaliGUI
                    self.bici_artigianali_gui = BiciArtigianaliGUI(self.root, self.bici_artigianali_controller, self)
                    # Salva nella cache
                    self.gui_cache['bici_artigianali'] = self.bici_artigianali_gui
                    logger.info("✅ GUI Bici Artigianali caricata in background")
        except Exception as e:
            logger.error(f"❌ bici_artigianali fallita: {e}")
    
    
    def _show_loading_indicator(self):
        """Mostra un indicatore di caricamento visivo"""
        try:
            # Frame per l'indicatore di caricamento
            self.loading_frame = ctk.CTkFrame(self.root, fg_color="transparent")
            self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
            
            # Titolo
            loading_title = ctk.CTkLabel(
                self.loading_frame,
                text="🚀 Caricamento in corso...",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            loading_title.pack(pady=20)
            
            # Barra di progresso
            self.loading_progress = ctk.CTkProgressBar(
                self.loading_frame,
                width=300,
                height=20
            )
            self.loading_progress.pack(pady=10)
            self.loading_progress.set(0)
            
            # Testo di stato
            self.loading_status = ctk.CTkLabel(
                self.loading_frame,
                text="Inizializzazione componenti...",
                font=ctk.CTkFont(size=12)
            )
            self.loading_status.pack(pady=10)
            
            # Avvia l'animazione
            self._animate_loading()
            
        except Exception as e:
            logger.error(f"Errore creazione indicatore caricamento: {e}")
    
    def _animate_loading(self):
        """Anima l'indicatore di caricamento"""
        try:
            if hasattr(self, 'loading_progress'):
                # Incrementa la barra di progresso
                current_value = self.loading_progress.get()
                if current_value < 0.9:
                    new_value = current_value + 0.1
                    self.loading_progress.set(new_value)
                    
                    # Aggiorna il testo di stato
                    if new_value < 0.3:
                        self.loading_status.configure(text="Caricamento inventario...")
                    elif new_value < 0.6:
                        self.loading_status.configure(text="Caricamento bici restaurate...")
                    elif new_value < 0.9:
                        self.loading_status.configure(text="Caricamento bici artigianali...")
                    else:
                        self.loading_status.configure(text="Completamento...")
                    
                    # Riprogramma l'animazione
                    self.root.after(200, self._animate_loading)
                else:
                    # Nasconde l'indicatore quando completo
                    self.root.after(500, self._hide_loading_indicator)
                    
        except Exception as e:
            logger.error(f"Errore animazione caricamento: {e}")
    
    def _hide_loading_indicator(self):
        """Nasconde l'indicatore di caricamento"""
        try:
            if hasattr(self, 'loading_frame'):
                self.loading_frame.destroy()
                del self.loading_frame
                
            if hasattr(self, 'loading_progress'):
                del self.loading_progress
                
            if hasattr(self, 'loading_status'):
                del self.loading_status
                
            logger.info("✅ Indicatore di caricamento rimosso")
            
        except Exception as e:
            logger.error(f"Errore rimozione indicatore: {e}")

    def _apply_window_settings(self):
        """Applica le impostazioni della finestra all'avvio - COMPLETAMENTE RESPONSIVE"""
        try:
            # Ottieni le dimensioni dello schermo
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Dimensioni fisse più piccole come richiesto
            window_width = 600
            window_height = 800
            
            # Centra la finestra
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            # Applica le dimensioni responsive
            self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Configura il ridimensionamento COMPLETAMENTE RESPONSIVE
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)
            
            # Abilita il ridimensionamento della finestra
            self.root.resizable(True, True)
            
            # Imposta dimensioni minime per evitare finestre troppo piccole
            self.root.minsize(600, 800)
            
            # Gestore per il ridimensionamento della finestra
            self.root.bind('<Configure>', self._on_window_resize)
            
            # Applica il nome azienda al titolo
            nome_azienda = self.settings.get('nome_azienda', '').strip()
            if nome_azienda:
                self.root.title(f"Gestionale Biciclette - {nome_azienda} v1.0")
                
        except Exception as e:
            print(f"❌ Errore nell'applicazione delle impostazioni finestra: {e}")

    def _on_window_resize(self, event):
        """Gestisce il ridimensionamento della finestra per mantenere il layout responsive"""
        try:
            # Aggiorna il layout quando la finestra viene ridimensionata
            if event.widget == self.root:
                # Forza l'aggiornamento del layout
                self.root.update_idletasks()
                
                # Se siamo nella tab inventario, aggiorna la tabella
                if hasattr(self, 'current_tab') and self.current_tab == "inventario":
                    if hasattr(self, '_refresh_inventario_table'):
                        self._refresh_inventario_table()
                        
        except Exception as e:
            print(f"❌ Errore nel ridimensionamento finestra: {e}")

    def _chiudi_tab_inventario(self):
        """Chiude la tab inventario e torna al menu principale"""
        try:
            # Chiude la tab inventario
            if hasattr(self, 'tab_manager'):
                self.tab_manager.close_tab("inventario")
            
            # Torna alla dashboard principale
            if hasattr(self, 'screen_manager'):
                self.screen_manager.show_dashboard()
                
        except Exception as e:
            print(f"❌ Errore nella chiusura della tab inventario: {e}")

    def _mostra_guida_inventario(self):
        """Mostra la guida per l'inventario"""
        if self.guida_manager:
            self.guida_manager.mostra_guida_inventario()

    def _check_auto_backup(self):
        """Verifica e esegue backup automatico se necessario"""
        try:
            # Verifica se il backup automatico è abilitato
            if self.app_controller.backup_progetto.is_backup_automatico_abilitato():
                # Esegue backup automatico
                result = self.app_controller.backup_progetto.esegui_backup_automatico()
                
                if result['successo']:
                    logger.info(f"Backup automatico eseguito: {result['percorso_file']}", "BACKUP_AUTO")
                else:
                    logger.info(f"Backup automatico non necessario: {result['messaggio']}", "BACKUP_AUTO")
            
            # Verifica integrità del progetto
            verifica = self.app_controller.backup_progetto.verifica_integrita_progetto()
            if verifica['successo'] and (verifica['file_mancanti'] > 0 or verifica['file_corotti'] > 0):
                logger.warning(f"Problemi di integrità rilevati: {verifica['file_mancanti']} mancanti, {verifica['file_corotti']} corrotti", "INTEGRITY")
                
                # Auto-riparazione se abilitata
                if self.app_controller.backup_progetto.get_configurazione('auto_riparazione', 'true').lower() == 'true':
                    repair_result = self.app_controller.backup_progetto.auto_ripara_file_mancanti()
                    if repair_result['successo'] and repair_result['file_riparati'] > 0:
                        logger.info(f"Auto-riparazione completata: {repair_result['file_riparati']} file riparati", "AUTO_REPAIR")
            
            # Pulizia automatica duplicati se abilitata
            if self.app_controller.backup_progetto.get_configurazione('pulizia_automatica_duplicati', 'false').lower() == 'true':
                cleanup_result = self.app_controller.backup_progetto.pulisci_file_duplicati_e_eccesso()
                if cleanup_result['successo'] and cleanup_result['file_rimossi'] > 0:
                    logger.info(f"Pulizia automatica completata: {cleanup_result['file_rimossi']} file rimossi", "AUTO_CLEANUP")
            
        except Exception as e:
            logger.error(f"Errore nel controllo backup automatico: {str(e)}", "BACKUP_AUTO", e)

    def _center_window(self):
        """Centra la finestra sullo schermo"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _create_interface(self):
        """Crea l'interfaccia principale con sistema di tab - COMPLETAMENTE RESPONSIVE"""
        # Frame principale - COMPLETAMENTE RESPONSIVE
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Configura il ridimensionamento del frame principale
        self.main_frame.grid_rowconfigure(0, weight=0)  # Tab bar fissa
        self.main_frame.grid_rowconfigure(1, weight=1)  # Contenuto espandibile
        self.main_frame.grid_columnconfigure(0, weight=1)  # Larghezza completa

        # Frame per la barra delle tab
        self.tab_bar_frame = ctk.CTkFrame(
            self.main_frame, fg_color="transparent")
        self.tab_bar_frame.pack(fill="x", pady=(0, 10))

        # Frame per il contenuto delle tab - COMPLETAMENTE RESPONSIVE
        self.tab_content_frame = ctk.CTkFrame(
            self.main_frame, fg_color="transparent")
        self.tab_content_frame.pack(fill="both", expand=True)
        
        # Configura il ridimensionamento del contenuto delle tab
        self.tab_content_frame.grid_rowconfigure(0, weight=1)
        self.tab_content_frame.grid_columnconfigure(0, weight=1)

        # Inizializza i gestori
        self.tab_manager = TabManager(
            self.tab_bar_frame,
            self.tab_content_frame,
            self
        )
        # Crea il gestore delle schermate (dashboard, guida, welcome)
        try:
            self.screen_manager = ScreenManager(self.tab_content_frame, self)
            # Mostra la schermata iniziale (dashboard o primo avvio)
            try:
                self.screen_manager.show_initial_screen()
            except Exception:
                # Fallback a mostrare la dashboard direttamente
                try:
                    self.screen_manager.show_dashboard()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Errore inizializzazione ScreenManager: {e}")
    def apri_gestione_clienti(self):
        """Apre la tab di gestione dei clienti."""
        try:
            # Pulisce il contenuto precedente se esiste
            self._clear_tab_content()
            
            if self.tab_manager.has_tab("clienti"):
                self.tab_manager.switch_tab("clienti")
            else:
                self.tab_manager.create_tab(
                    "clienti", "👥 Gestione Clienti", self._clienti_tab_content)
        except Exception as e:
            print(f"Errore nell'aprire clienti: {e}")
            import traceback
            traceback.print_exc()

    def _clienti_tab_content(self):
        """Contenuto della tab gestione clienti"""
        # Pulisce il frame del contenuto
        for widget in self.tab_content_frame.winfo_children():
            widget.destroy()

        # Titolo
        title_label = ctk.CTkLabel(
            self.tab_content_frame,
            text="👥 Gestione Clienti",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Messaggio temporaneo
        info_label = ctk.CTkLabel(
            self.tab_content_frame,
            text="Funzionalità in sviluppo...\n\nQui sarà integrata la gestione clienti con la nuova architettura",
            font=ctk.CTkFont(size=16),
            text_color="#666666"
        )
        info_label.pack(pady=50)

        # Pulsante per aprire la finestra completa (temporaneo)
        open_full_btn = ctk.CTkButton(
            self.tab_content_frame,
            text="🔧 Apri Gestione Clienti Completa",
            command=self._open_clienti_full,
            width=250,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        open_full_btn.pack(pady=20)

    def _open_clienti_full(self):
        """Apre la finestra completa di gestione clienti (temporaneo)"""
        try:
            # GUI clienti sarà implementata con la nuova architettura modulare
            messagebox.showinfo(
                "Info", "GUI Clienti in sviluppo con nuova architettura modulare")
        except Exception as e:  # pylint: disable=broad-except
            error_msg = f"Errore imprevisto nell'aprire la gestione clienti:\n{str(e)}"
            messagebox.showerror("Errore", error_msg)

    def apri_impostazioni(self):
        """Apre la tab delle impostazioni."""
        try:
            # Pulisce il contenuto precedente se esiste
            self._clear_tab_content()
            
            if self.tab_manager.has_tab("impostazioni"):
                self.tab_manager.switch_tab("impostazioni")
            else:
                self.tab_manager.create_tab(
                    "impostazioni", "⚙️ Impostazioni", self._impostazioni_tab_content)
        except Exception as e:
            print(f"Errore nell'aprire impostazioni: {e}")
            import traceback
            traceback.print_exc()

    def _clear_tab_content(self):
        """Pulisce il contenuto delle tab per evitare conflitti"""
        try:
            # Pulisce il frame principale del contenuto
            if hasattr(self, 'tab_content_frame'):
                # Distruggi tutti i widget figli in modo sicuro
                widgets_to_destroy = list(self.tab_content_frame.winfo_children())
                for widget in widgets_to_destroy:
                    try:
                        widget.destroy()
                    except Exception:
                        pass
                
                # Forza l'aggiornamento della GUI
                self.tab_content_frame.update_idletasks()
                
            # Pulisce anche eventuali riferimenti a GUI specifiche
            if hasattr(self, 'inventario_gui'):
                try:
                    del self.inventario_gui
                except Exception:
                    pass
                    
            # Pulisce il frame prodotti se esiste
            if hasattr(self, 'prodotti_frame'):
                try:
                    for widget in self.prodotti_frame.winfo_children():
                        widget.destroy()
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Errore nella pulizia del contenuto: {e}")
            import traceback
            traceback.print_exc()

    def apri_inventario(self):
        """Apre la tab dell'inventario."""
        try:
            # Pulisce il contenuto precedente se esiste
            self._clear_tab_content()
            
            if self.tab_manager.has_tab("inventario"):
                self.tab_manager.switch_tab("inventario")
            else:
                self.tab_manager.create_tab(
                    "inventario", "📦 Inventario", self._inventario_tab_content)
        except Exception as e:
            print(f"Errore nell'aprire inventario: {e}")
            import traceback
            traceback.print_exc()

    def _impostazioni_tab_content(self):
        """Contenuto della tab impostazioni"""
        # Crea l'istanza della GUI delle impostazioni
        self.impostazioni_gui = ImpostazioniGUI(
            self.tab_content_frame,
            self.app_controller,
            self.icon_manager,
            self.root,
            self.officina_controller,
            self  # Passa l'oggetto app
        )
        
        # Crea il contenuto delle impostazioni
        self.impostazioni_gui.create_impostazioni_content()

    def _open_impostazioni_full(self):
        """Apre la finestra completa delle impostazioni (temporaneo)"""
        try:
            # GUI impostazioni sarà implementata con la nuova architettura modulare
            messagebox.showinfo(
                "Info", "GUI Impostazioni in sviluppo con nuova architettura modulare")
        except Exception as e:  # pylint: disable=broad-except
            error_msg = f"Errore imprevisto nell'aprire le impostazioni:\n{str(e)}"
            messagebox.showerror("Errore", error_msg)

    def _nuovo(self):
        """Crea un nuovo lavoro (riparazioni o biciclette)"""
        if self.tab_manager.has_tab("nuovo_lavoro"):
            self.tab_manager.switch_tab("nuovo_lavoro")
        else:
            self.tab_manager.create_tab(
                "nuovo_lavoro", "🆕 Nuovo Lavoro", self._nuovo_lavoro_tab_content)
    
    def _nuovo_lavoro_tab_content(self):
        """Contenuto della tab nuovo lavoro"""
        self.nuovo_lavoro_controller.mostra_nuovo_lavoro_content()
    
    def _clienti(self):
        """Apre il database clienti"""
        if self.tab_manager.has_tab("clienti"):
            self.tab_manager.switch_tab("clienti")
        else:
            self.tab_manager.create_tab(
                "clienti", "👥 Database Clienti", self._clienti_tab_content)
    
    def _vendite(self):
        """Apre la gestione vendite"""
        if self.tab_manager.has_tab("vendite"):
            self.tab_manager.switch_tab("vendite")
        else:
            self.tab_manager.create_tab(
                "vendite", "💰 Gestione Vendite", self._vendite_tab_content)
    
    def _vendite_tab_content(self):
        """Contenuto della tab vendite"""
        self.vendite_controller.mostra_vendite_content()
 
    # ===== GESTIONE INTERVENTI E RICAMBI =====

    def _on_stato_valutazione_change(self, choice, fields_frame, dialog):
        """Gestisce il cambio di stato valutazione"""
        try:
            if choice == "Da riparare":
                self._mostra_selezione_interventi(fields_frame, dialog)
            else:
                self._nascondi_selezione_interventi(fields_frame)
        except Exception as e:
            logger.error(f"Errore cambio stato valutazione: {e}")

    def _on_necessita_riparazioni_change(self, checked, fields_frame, dialog):
        """Gestisce il cambio di necessita riparazioni"""
        try:
            if checked:
                # Mostra selezione operazioni e ricambi nella stessa finestra
                self._mostra_selezione_interventi(fields_frame, dialog)
            else:
                self._nascondi_selezione_interventi(fields_frame)
        except Exception as e:
            logger.error(f"Errore cambio necessita riparazioni: {e}")


    def _mostra_lista_bici_ricondizionate_con_costi(self, biciclette, titolo, sottotitolo):
        """Mostra una lista di biciclette ricondizionate con gestione costi"""
        try:
            # Pulisce il frame del contenuto
            for widget in self.tab_content_frame.winfo_children():
                widget.destroy()

            # Titolo
            title_label = ctk.CTkLabel(
                self.tab_content_frame,
                text=titolo,
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=20)

            # Sottotitolo
            subtitle_label = ctk.CTkLabel(
                self.tab_content_frame,
                text=sottotitolo,
                font=ctk.CTkFont(size=16)
            )
            subtitle_label.pack(pady=(0, 30))

            if not biciclette:
                # Nessuna bicicletta
                no_bici_label = ctk.CTkLabel(
                    self.tab_content_frame,
                    text="Nessuna bicicletta trovata",
                    font=ctk.CTkFont(size=16),
                    text_color="#6B7280"
                )
                no_bici_label.pack(pady=50)
            else:
                # Frame scrollabile per la lista
                scroll_frame = ctk.CTkScrollableFrame(self.tab_content_frame, height=400)
                scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

                # Mostra ogni bicicletta con gestione costi
                for bici in biciclette:
                    self._create_bici_ricondizionata_widget_con_costi(scroll_frame, bici)

            # Pulsanti di controllo
            button_frame = ctk.CTkFrame(self.tab_content_frame, fg_color="transparent")
            button_frame.pack(pady=20)

            # Pulsante Torna indietro
            back_btn = ctk.CTkButton(
                button_frame,
                text="⬅️ Torna Indietro",
                command=self._seleziona_bici_ricondizionate,
                width=200,
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#6B7280",
                hover_color="#4B5563"
            )
            back_btn.pack(side="left", padx=10)

            # Pulsante Chiudi tab
            close_btn = ctk.CTkButton(
                button_frame,
                text="❌ Chiudi Tab",
                command=lambda: self.tab_manager.close_tab("nuovo_lavoro"),
                width=200,
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#DC2626",
                hover_color="#B91C1C"
            )
            close_btn.pack(side="left", padx=10)

        except Exception as e:
            logger.error(f"Errore mostrazione lista bici ricondizionate con costi: {e}")
            messagebox.showerror("Errore", f"Errore nella visualizzazione: {e}")

    def _create_bici_ricondizionata_widget_con_costi(self, parent, bici):
        """Crea un widget per una bicicletta ricondizionata con gestione costi"""
        try:
            # Frame per la bicicletta
            bici_frame = ctk.CTkFrame(parent)
            bici_frame.pack(fill="x", padx=10, pady=10)

            # Informazioni principali
            info_frame = ctk.CTkFrame(bici_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=15, pady=10)

            # Marca e modello
            marca_modello = ctk.CTkLabel(
                info_frame,
                text=f"{bici['marca']} {bici['modello']}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            marca_modello.pack(anchor="w")

            # Codice e stato
            codice_stato = ctk.CTkLabel(
                info_frame,
                text=f"Codice: {bici['codice']} | Stato: {bici.get('stato_ricondizionamento', 'N/A')}",
                font=ctk.CTkFont(size=12)
            )
            codice_stato.pack(anchor="w")

            # Dettagli
            dettagli = []
            if bici.get('anno'):
                dettagli.append(f"Anno: {bici['anno']}")
            if bici.get('colore'):
                dettagli.append(f"Colore: {bici['colore']}")
            if bici.get('taglia'):
                dettagli.append(f"Taglia: {bici['taglia']}")
            
            if dettagli:
                dettagli_label = ctk.CTkLabel(
                    info_frame,
                    text=" | ".join(dettagli),
                    font=ctk.CTkFont(size=11),
                    text_color="#6B7280"
                )
                dettagli_label.pack(anchor="w")

            # Costi attuali
            costi_frame = ctk.CTkFrame(bici_frame, fg_color="transparent")
            costi_frame.pack(fill="x", padx=15, pady=(0, 10))

            costo_acquisto = bici.get('prezzo_acquisto', 0)
            costo_totale = bici.get('costo_totale', 0)

            ctk.CTkLabel(
                costi_frame,
                text=f"Acquisto: €{costo_acquisto:.2f} | Costo Totale: €{costo_totale:.2f}",
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(anchor="w")

            # Pulsanti azione
            actions_frame = ctk.CTkFrame(bici_frame, fg_color="transparent")
            actions_frame.pack(fill="x", padx=15, pady=(0, 10))

            # Pulsante Modifica Scheda Lavoro
            modifica_scheda_btn = ctk.CTkButton(
                actions_frame,
                text="🔧 Modifica Scheda",
                command=lambda: self._modifica_scheda_lavoro_ricondizionata(bici),
                width=120,
                height=30,
                font=ctk.CTkFont(size=11),
                fg_color="#7C3AED",
                hover_color="#6D28D9"
            )
            modifica_scheda_btn.pack(side="left", padx=5)

            # Pulsante Calcola Costi
            calcola_btn = ctk.CTkButton(
                actions_frame,
                text="💰 Calcola Costi",
                command=lambda: self._calcola_costi_ricondizionamento(bici),
                width=120,
                height=30,
                font=ctk.CTkFont(size=11),
                fg_color="#10B981",
                hover_color="#059669"
            )
            calcola_btn.pack(side="left", padx=5)

            # Pulsante Modifica Costo
            modifica_costo_btn = ctk.CTkButton(
                actions_frame,
                text="✏️ Modifica Costo",
                command=lambda: self._modifica_costo_bicicletta(bici),
                width=120,
                height=30,
                font=ctk.CTkFont(size=11),
                fg_color="#3B82F6",
                hover_color="#2563EB"
            )
            modifica_costo_btn.pack(side="left", padx=5)

            # Pulsante Dettagli
            dettagli_btn = ctk.CTkButton(
                actions_frame,
                text="📋 Dettagli",
                command=lambda: self._mostra_dettagli_bici_ricondizionata(bici),
                width=100,
                height=30,
                font=ctk.CTkFont(size=11)
            )
            dettagli_btn.pack(side="left", padx=5)

            # Pulsante Elimina
            elimina_btn = ctk.CTkButton(
                actions_frame,
                text="🗑️ Elimina",
                command=lambda: self._elimina_bici_ricondizionata(bici),
                width=100,
                height=30,
                font=ctk.CTkFont(size=11),
                fg_color="#DC2626",
                hover_color="#B91C1C"
            )
            elimina_btn.pack(side="left", padx=5)

        except Exception as e:
            logger.error(f"Errore creazione widget bici ricondizionata con costi: {e}")

    def _modifica_scheda_lavoro_ricondizionata(self, bici):
        """Modifica la scheda di lavoro per una bicicletta ricondizionata"""
        try:
            # Crea finestra modifica scheda lavoro
            dialog = ctk.CTkToplevel(self.root)
            dialog.title(f"Modifica Scheda Lavoro - {bici['marca']} {bici['modello']}")
            dialog.geometry("1000x700")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Centra la finestra
            x = (dialog.winfo_screenwidth() // 2) - (1000 // 2)
            y = (dialog.winfo_screenheight() // 2) - (700 // 2)
            dialog.geometry(f"1000x700+{x}+{y}")
            
            # Titolo
            title_label = ctk.CTkLabel(
                dialog,
                text=f"🔧 Modifica Scheda Lavoro - {bici['marca']} {bici['modello']}",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=15)
            
            # Sottotitolo
            subtitle_label = ctk.CTkLabel(
                dialog,
                text="Modifica operazioni e ricambi, poi ricalcola i costi automaticamente",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            subtitle_label.pack(pady=(0, 20))
            
            # Tabview per le sezioni
            tabview = ctk.CTkTabview(dialog, width=950, height=500)
            tabview.pack(padx=20, pady=10)
            
            # Tab 1: Operazioni
            tab_operazioni = tabview.add("🔧 Operazioni")
            self._create_modifica_operazioni_tab(tab_operazioni, bici, dialog)
            
            # Tab 2: Ricambi
            tab_ricambi = tabview.add("⚙️ Ricambi")
            self._create_modifica_ricambi_tab(tab_ricambi, bici, dialog)
            
            # Tab 3: Calcolo Prezzo
            tab_prezzo = tabview.add("💰 Calcolo Prezzo")
            self._create_calcolo_prezzo_ricondizionata_tab(tab_prezzo, bici, dialog)
            
            # Pulsanti di controllo
            control_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            control_frame.pack(pady=20)
            
            # Pulsante Salva Modifiche
            salva_btn = ctk.CTkButton(
                control_frame,
                text="💾 Salva Modifiche e Ricalcola",
                command=lambda: self._salva_modifiche_scheda_lavoro(bici, dialog),
                width=200,
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#059669",
                hover_color="#047857"
            )
            salva_btn.pack(side="left", padx=10)
            
            # Pulsante Annulla
            annulla_btn = ctk.CTkButton(
                control_frame,
                text="❌ Annulla",
                command=dialog.destroy,
                width=150,
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#6B7280",
                hover_color="#4B5563"
            )
            annulla_btn.pack(side="left", padx=10)
            
        except Exception as e:
            logger.error(f"Errore modifica scheda lavoro ricondizionata: {e}")
            messagebox.showerror("Errore", f"Errore nella modifica scheda: {e}")

    def _create_modifica_operazioni_tab(self, tab, bici, dialog):
        """Crea la tab per modificare le operazioni"""
        try:
            # Titolo
            ctk.CTkLabel(
                tab,
                text="🔧 Modifica Operazioni Eseguite:",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=10)
            
            # Sottotitolo
            ctk.CTkLabel(
                tab,
                text="Seleziona le operazioni che sono state effettivamente eseguite",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(pady=(0, 15))
            
            # Frame scrollabile per le operazioni
            scroll_frame = ctk.CTkScrollableFrame(tab, height=300)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Inizializza controller se non esiste
            if not hasattr(self, 'bici_usate_controller'):
                from src.modules.biciclette.bici_usate_controller import BiciUsateController
                self.bici_usate_controller = BiciUsateController("data", self.app_controller)
            
            # Ottieni operazioni disponibili
            operazioni_disponibili = self.bici_usate_controller.get_interventi_disponibili()
            
            # Variabili per i checkbox
            self.operazioni_modifica_vars = {}
            
            # Crea checkbox per ogni operazione
            for operazione in operazioni_disponibili:
                var = ctk.BooleanVar()
                self.operazioni_modifica_vars[operazione['id']] = var
                
                check = ctk.CTkCheckBox(
                    scroll_frame,
                    text=operazione['nome'],
                    variable=var
                )
                check.pack(anchor="w", pady=2)
            
            # Pulsante Continua a Ricambi
            continua_ricambi_btn = ctk.CTkButton(
                tab,
                text="⚙️ Continua a Ricambi",
                command=lambda: self.tab_manager.set_tab("⚙️ Ricambi"),
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#7C3AED",
                hover_color="#6D28D9"
            )
            continua_ricambi_btn.pack(pady=15)
            
        except Exception as e:
            logger.error(f"Errore creazione tab modifica operazioni: {e}")

    def _create_modifica_ricambi_tab(self, tab, bici, dialog):
        """Crea la tab per modificare i ricambi"""
        try:
            # Titolo
            ctk.CTkLabel(
                tab,
                text="⚙️ Modifica Ricambi Utilizzati:",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=10)
            
            # Sottotitolo
            ctk.CTkLabel(
                tab,
                text="Seleziona i ricambi che sono stati effettivamente utilizzati",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(pady=(0, 15))
            
            # Frame scrollabile per i ricambi
            scroll_frame = ctk.CTkScrollableFrame(tab, height=300)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Ottieni ricambi disponibili
            ricambi_disponibili = self.bici_usate_controller.get_ricambi_disponibili()
            
            # Variabili per i checkbox
            self.ricambi_modifica_vars = {}
            
            # Crea checkbox per ogni ricambio
            for ricambio in ricambi_disponibili:
                var = ctk.BooleanVar()
                self.ricambi_modifica_vars[ricambio['id']] = var
                
                check = ctk.CTkCheckBox(
                    scroll_frame,
                    text=ricambio['nome'],
                    variable=var
                )
                check.pack(anchor="w", pady=2)
            
            # Pulsante Continua a Calcolo Prezzo
            continua_prezzo_btn = ctk.CTkButton(
                tab,
                text="💰 Continua a Calcolo Prezzo",
                command=lambda: self._continua_a_calcolo_prezzo_ricondizionata(dialog),
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#7C3AED",
                hover_color="#6D28D9"
            )
            continua_prezzo_btn.pack(pady=15)
            
        except Exception as e:
            logger.error(f"Errore creazione tab modifica ricambi: {e}")

    def _continua_a_calcolo_prezzo_ricondizionata(self, dialog):
        """Passa al calcolo prezzo per bici ricondizionata"""
        try:
            # Trova il tabview nella finestra
            for widget in dialog.winfo_children():
                if isinstance(widget, ctk.CTkTabview):
                    widget.set("💰 Calcolo Prezzo")
                    break
        except Exception as e:
            logger.error(f"Errore continua a calcolo prezzo ricondizionata: {e}")

    def _create_calcolo_prezzo_ricondizionata_tab(self, tab, bici, dialog):
        """Crea la tab per il calcolo prezzo delle bici ricondizionate"""
        try:
            # Titolo
            ctk.CTkLabel(
                tab,
                text="💰 Calcolo Prezzo di Vendita:",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack(pady=10)
            
            # Sottotitolo
            ctk.CTkLabel(
                tab,
                text="Calcolo automatico basato su costi + moltiplicatore 2x",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(pady=(0, 20))
            
            # Frame per i controlli
            controls_frame = ctk.CTkFrame(tab)
            controls_frame.pack(fill="x", padx=20, pady=10)
            
            # Checkbox IVA
            self.iva_modifica_var = ctk.BooleanVar(value=False)
            iva_check = ctk.CTkCheckBox(
                controls_frame,
                text="Includi IVA (22%)",
                variable=self.iva_modifica_var,
                command=lambda: self._on_iva_change_modifica(self.iva_modifica_var.get(), tab, bici)
            )
            iva_check.pack(pady=10)
            
            # Pulsante Ricalcola
            ricalcola_btn = ctk.CTkButton(
                controls_frame,
                text="🔄 Ricalcola Prezzo",
                command=lambda: self._ricalcola_prezzo_ricondizionata(tab, bici),
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#10B981",
                hover_color="#059669"
            )
            ricalcola_btn.pack(pady=15)
            
            # Frame per i risultati
            self.risultati_prezzo_frame = ctk.CTkFrame(tab)
            self.risultati_prezzo_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Calcola automaticamente all'apertura
            self._ricalcola_prezzo_ricondizionata(tab, bici)
            
        except Exception as e:
            logger.error(f"Errore creazione tab calcolo prezzo ricondizionata: {e}")

    def _on_iva_change_modifica(self, con_iva, tab, bici):
        """Gestisce il cambio IVA nella modifica"""
        try:
            self._ricalcola_prezzo_ricondizionata(tab, bici)
        except Exception as e:
            logger.error(f"Errore cambio IVA modifica: {e}")

    def _ricalcola_prezzo_ricondizionata(self, tab, bici):
        """Ricalcola il prezzo per bici ricondizionata"""
        try:
            # Pulisci i risultati precedenti
            for widget in self.risultati_prezzo_frame.winfo_children():
                widget.destroy()
            
            # Ottieni costo acquisto
            costo_acquisto = bici.get('prezzo_acquisto', 0.0)
            
            # Calcola costo ricambi selezionati
            costo_ricambi = 0.0
            if hasattr(self, 'ricambi_modifica_vars'):
                ricambi_disponibili = self.bici_usate_controller.get_ricambi_disponibili()
                for ricambio_id, var in self.ricambi_modifica_vars.items():
                    if var.get():
                        for ricambio in ricambi_disponibili:
                            if ricambio['id'] == ricambio_id:
                                costo_ricambi += ricambio['prezzo_vendita']
                                break
            
            # Calcola il prezzo
            calcolo = self.pricing_controller.calcola_prezzo_bicicletta(
                costo_acquisto=costo_acquisto,
                costo_ricambi=costo_ricambi,
                con_iva=self.iva_modifica_var.get()
            )
            
            # Mostra i dettagli del calcolo
            self._mostra_dettagli_calcolo_modifica(self.risultati_prezzo_frame, calcolo)
            
        except Exception as e:
            logger.error(f"Errore ricalcolo prezzo ricondizionata: {e}")

    def _mostra_dettagli_calcolo_modifica(self, parent, calcolo):
        """Mostra i dettagli del calcolo nella modifica"""
        try:
            # Frame per i dettagli
            dettagli_frame = ctk.CTkScrollableFrame(parent, height=200)
            dettagli_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Costi base
            ctk.CTkLabel(
                dettagli_frame,
                text="📊 Costi Base:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(10, 5), anchor="w")
            
            ctk.CTkLabel(
                dettagli_frame,
                text=f"  • Costo acquisto: €{calcolo['costo_acquisto']:.2f}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                dettagli_frame,
                text=f"  • Costo ricambi: €{calcolo['costo_ricambi']:.2f}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                dettagli_frame,
                text=f"  • Costo totale: €{calcolo['costo_totale']:.2f}",
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(anchor="w", pady=(5, 10))
            
            # Calcolo prezzo
            ctk.CTkLabel(
                dettagli_frame,
                text="🧮 Calcolo Prezzo:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(10, 5), anchor="w")
            
            ctk.CTkLabel(
                dettagli_frame,
                text=f"  • Formula: (Costo totale) × {calcolo['moltiplicatore']:.1f}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                dettagli_frame,
                text=f"  • Calcolo: €{calcolo['costo_totale']:.2f} × {calcolo['moltiplicatore']:.1f} = €{calcolo['prezzo_base']:.2f}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=2)
            
            if calcolo['con_iva']:
                ctk.CTkLabel(
                    dettagli_frame,
                    text=f"  • IVA ({calcolo['iva_percentuale']:.1f}%): €{calcolo['iva_applicata']:.2f}",
                    font=ctk.CTkFont(size=12)
                ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                dettagli_frame,
                text=f"  • Arrotondamento: €{calcolo['prezzo_base']:.2f} → €{calcolo['prezzo_finale']:.2f}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=2)
            
            # Risultato finale
            ctk.CTkLabel(
                dettagli_frame,
                text="💰 Prezzo di Vendita Suggerito:",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#059669"
            ).pack(pady=(20, 5), anchor="w")
            
            ctk.CTkLabel(
                dettagli_frame,
                text=f"€{calcolo['prezzo_finale']:.2f}",
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#059669"
            ).pack(anchor="w", pady=5)
            
        except Exception as e:
            logger.error(f"Errore mostrazione dettagli calcolo modifica: {e}")

    def _salva_modifiche_scheda_lavoro(self, bici, dialog):
        """Salva le modifiche alla scheda lavoro e ricalcola i costi"""
        try:
            # Raccogli operazioni selezionate
            operazioni_selezionate = []
            if hasattr(self, 'operazioni_modifica_vars'):
                for operazione_id, var in self.operazioni_modifica_vars.items():
                    if var.get():
                        operazioni_selezionate.append(operazione_id)
            
            # Raccogli ricambi selezionati
            ricambi_selezionati = []
            if hasattr(self, 'ricambi_modifica_vars'):
                for ricambio_id, var in self.ricambi_modifica_vars.items():
                    if var.get():
                        ricambi_selezionati.append(ricambio_id)
            
            # Calcola il nuovo prezzo
            costo_acquisto = bici.get('prezzo_acquisto', 0.0)
            costo_ricambi = 0.0
            
            if hasattr(self, 'ricambi_modifica_vars'):
                ricambi_disponibili = self.bici_usate_controller.get_ricambi_disponibili()
                for ricambio_id, var in self.ricambi_modifica_vars.items():
                    if var.get():
                        for ricambio in ricambi_disponibili:
                            if ricambio['id'] == ricambio_id:
                                costo_ricambi += ricambio['prezzo_vendita']
                                break
            
            # Calcola prezzo finale
            calcolo = self.pricing_controller.calcola_prezzo_bicicletta(
                costo_acquisto=costo_acquisto,
                costo_ricambi=costo_ricambi,
                con_iva=self.iva_modifica_var.get()
            )
            
            # Salva il calcolo nel database
            self.pricing_controller.salva_calcolo_bicicletta(
                bicicletta_id=bici['id'],
                tipo_bicicletta="ricondizionata",
                calcolo=calcolo
            )
            
            # Mostra conferma
            messagebox.showinfo(
                "Modifiche Salvate",
                f"Scheda lavoro aggiornata per {bici['marca']} {bici['modello']}!\n\n"
                f"Operazioni eseguite: {len(operazioni_selezionate)}\n"
                f"Ricambi utilizzati: {len(ricambi_selezionati)}\n"
                f"Prezzo di vendita: €{calcolo['prezzo_finale']:.2f}\n\n"
                "I costi sono stati ricalcolati automaticamente."
            )
            
            # Chiudi la finestra
            dialog.destroy()
            
            # Aggiorna la lista
            self._mostra_bici_in_lavorazione()
            
        except Exception as e:
            logger.error(f"Errore salvataggio modifiche scheda lavoro: {e}")
            messagebox.showerror("Errore", f"Errore nel salvataggio: {e}")

    def _calcola_costi_ricondizionamento(self, bici):
        """Calcola i costi di ricondizionamento per una bicicletta"""
        try:
            # Crea finestra calcolo costi
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Calcolo Costi Ricondizionamento")
            dialog.geometry("800x600")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Centra la finestra
            x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
            y = (dialog.winfo_screenheight() // 2) - (600 // 2)
            dialog.geometry(f"800x600+{x}+{y}")
            
            # Titolo
            title_label = ctk.CTkLabel(
                dialog,
                text=f"💰 Calcolo Costi - {bici['marca']} {bici['modello']}",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=15)
            
            # Frame per i controlli
            controls_frame = ctk.CTkFrame(dialog)
            controls_frame.pack(fill="x", padx=20, pady=10)
            
            # Checkbox IVA
            iva_var = ctk.BooleanVar(value=True)
            iva_check = ctk.CTkCheckBox(
                controls_frame,
                text="Includi IVA (22%)",
                variable=iva_var,
                command=lambda: self._on_iva_change(iva_var.get(), dialog, bici)
            )
            iva_check.pack(side="left", padx=10, pady=10)
            
            # Pulsante Ricalcola
            ricalcola_btn = ctk.CTkButton(
                controls_frame,
                text="🔄 Ricalcola",
                command=lambda: self._ricalcola_costi(dialog, bici, iva_var.get()),
                width=120,
                height=30
            )
            ricalcola_btn.pack(side="right", padx=10, pady=10)
            
            # Frame per i risultati
            results_frame = ctk.CTkScrollableFrame(dialog, height=400)
            results_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Calcola costi iniziali
            self._ricalcola_costi(dialog, bici, iva_var.get())
            
        except Exception as e:
            logger.error(f"Errore calcolo costi ricondizionamento: {e}")
            messagebox.showerror("Errore", f"Errore nel calcolo: {e}")

    def _on_iva_change(self, con_iva, dialog, bici):
        """Gestisce il cambio di IVA"""
        self._ricalcola_costi(dialog, bici, con_iva)

    def _ricalcola_costi(self, dialog, bici, con_iva):
        """Ricalcola i costi di ricondizionamento"""
        try:
            # Trova il frame dei risultati
            results_frame = None
            for widget in dialog.winfo_children():
                if isinstance(widget, ctk.CTkScrollableFrame):
                    results_frame = widget
                    break
            
            if not results_frame:
                return
            
            # Pulisci il frame
            for widget in results_frame.winfo_children():
                widget.destroy()
            
            # Ottieni ricambi disponibili
            ricambi_disponibili = self.bici_ricondizionate_controller.get_ricambi_disponibili()
            
            if not ricambi_disponibili:
                ctk.CTkLabel(
                    results_frame,
                    text="Nessun ricambio disponibile",
                    font=ctk.CTkFont(size=14),
                    text_color="#6B7280"
                ).pack(pady=20)
                return
            
            # Crea sezione selezione ricambi
            ctk.CTkLabel(
                results_frame,
                text="🔧 Seleziona Ricambi Necessari:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=10, anchor="w")
            
            # Variabili per checkbox
            ricambi_vars = {}
            quantita_vars = {}
            
            # Raggruppa ricambi per categoria
            ricambi_per_categoria = {}
            for ricambio in ricambi_disponibili:
                categoria = ricambio['categoria']
                if categoria not in ricambi_per_categoria:
                    ricambi_per_categoria[categoria] = []
                ricambi_per_categoria[categoria].append(ricambio)
            
            # Crea checkbox per ogni categoria
            for categoria, ricambi_cat in ricambi_per_categoria.items():
                # Titolo categoria
                ctk.CTkLabel(
                    results_frame,
                    text=f"{categoria}:",
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(pady=(10, 5), anchor="w")
                
                # Frame per ricambi della categoria
                cat_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
                cat_frame.pack(fill="x", padx=20, pady=5)
                
                for ricambio in ricambi_cat:
                    # Frame per singolo ricambio
                    ricambio_frame = ctk.CTkFrame(cat_frame)
                    ricambio_frame.pack(fill="x", padx=5, pady=2)
                    
                    # Checkbox selezione
                    var = ctk.BooleanVar()
                    ricambi_vars[ricambio['id']] = var
                    
                    checkbox = ctk.CTkCheckBox(
                        ricambio_frame,
                        text=f"{ricambio['nome']} - €{ricambio['prezzo_acquisto']:.2f} (Disponibili: {ricambio['quantita_disponibile']})",
                        variable=var,
                        command=lambda: self._on_ricambi_change(results_frame, bici, con_iva, ricambi_vars, quantita_vars)
                    )
                    checkbox.pack(side="left", padx=10, pady=5)
                    
                    # Entry quantità
                    quantita_var = ctk.StringVar(value="1")
                    quantita_vars[ricambio['id']] = quantita_var
                    
                    quantita_entry = ctk.CTkEntry(
                        ricambio_frame,
                        textvariable=quantita_var,
                        width=50,
                        placeholder_text="Qty"
                    )
                    quantita_entry.pack(side="right", padx=10, pady=5)
                    
                    quantita_entry.bind('<KeyRelease>', lambda e: self._on_ricambi_change(results_frame, bici, con_iva, ricambi_vars, quantita_vars))
            
            # Calcola costi iniziali
            self._on_ricambi_change(results_frame, bici, con_iva, ricambi_vars, quantita_vars)
            
        except Exception as e:
            logger.error(f"Errore ricalcolo costi: {e}")

    def _on_ricambi_change(self, results_frame, bici, con_iva, ricambi_vars, quantita_vars):
        """Gestisce il cambio di selezione ricambi"""
        try:
            # Trova il frame dei risultati del calcolo
            calcolo_frame = None
            for widget in results_frame.winfo_children():
                if hasattr(widget, 'winfo_name') and 'calcolo' in str(widget.winfo_name()):
                    calcolo_frame = widget
                    break
            
            if calcolo_frame:
                calcolo_frame.destroy()
            
            # Crea nuovo frame calcolo
            calcolo_frame = ctk.CTkFrame(results_frame)
            calcolo_frame.pack(fill="x", padx=20, pady=20)
            
            # Ottieni ricambi selezionati
            ricambi_selezionati = []
            for ricambio_id, var in ricambi_vars.items():
                if var.get():
                    quantita_str = quantita_vars[ricambio_id].get()
                    try:
                        quantita = int(quantita_str) if quantita_str.isdigit() else 1
                    except:
                        quantita = 1
                    
                    # Trova il ricambio
                    ricambi_disponibili = self.bici_ricondizionate_controller.get_ricambi_disponibili()
                    ricambio = next((r for r in ricambi_disponibili if r['id'] == ricambio_id), None)
                    
                    if ricambio:
                        ricambi_selezionati.append({
                            'nome': ricambio['nome'],
                            'prezzo_acquisto': ricambio['prezzo_acquisto'],
                            'quantita': quantita
                        })
            
            if not ricambi_selezionati:
                ctk.CTkLabel(
                    calcolo_frame,
                    text="Seleziona almeno un ricambio per calcolare i costi",
                    font=ctk.CTkFont(size=12),
                    text_color="#6B7280"
                ).pack(pady=20)
                return
            
            # Calcola costi
            calcolo = self.bici_ricondizionate_controller.calcola_costo_ricondizionamento(
                bici['id'], ricambi_selezionati, con_iva
            )
            
            if 'errore' in calcolo:
                ctk.CTkLabel(
                    calcolo_frame,
                    text=f"Errore: {calcolo['errore']}",
                    font=ctk.CTkFont(size=12),
                    text_color="#EF4444"
                ).pack(pady=20)
                return
            
            # Mostra risultati
            ctk.CTkLabel(
                calcolo_frame,
                text="💰 Risultati Calcolo:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=10, anchor="w")
            
            # Dettagli calcolo
            dettagli_text = f"""
Costo Base (Acquisto): €{calcolo['costo_base']:.2f}

Ricambi:
  • Senza IVA: €{calcolo['costo_ricambi_senza_iva']:.2f}
  • Con IVA: €{calcolo['costo_ricambi_con_iva']:.2f}
  • Finale: €{calcolo['costo_ricambi_finale']:.2f}

Raddoppio (Logica Officina):
  • Bicicletta: €{calcolo['costo_bici_raddoppiato']:.2f}
  • Ricambi: €{calcolo['costo_ricambi_raddoppiato']:.2f}
  • Totale: €{calcolo['costo_totale_prima_arrotondamento']:.2f}

Arrotondamento: €{calcolo['costo_totale_arrotondato']:.2f}
Margine: €{calcolo['margine']:.2f}
            """
            
            ctk.CTkLabel(
                calcolo_frame,
                text=dettagli_text.strip(),
                font=ctk.CTkFont(size=12),
                justify="left"
            ).pack(pady=10, anchor="w")
            
            # Pulsanti azione
            actions_frame = ctk.CTkFrame(calcolo_frame, fg_color="transparent")
            actions_frame.pack(fill="x", pady=10)
            
            # Pulsante Applica Costo
            applica_btn = ctk.CTkButton(
                actions_frame,
                text="✅ Applica Costo",
                command=lambda: self._applica_costo_calcolato(bici, calcolo['costo_totale']),
                width=150,
                height=40,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#10B981",
                hover_color="#059669"
            )
            applica_btn.pack(side="left", padx=10)
            
            # Pulsante Modifica Costo
            modifica_btn = ctk.CTkButton(
                actions_frame,
                text="✏️ Modifica Costo",
                command=lambda: self._modifica_costo_manuale(bici, calcolo['costo_totale']),
                width=150,
                height=40,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#3B82F6",
                hover_color="#2563EB"
            )
            modifica_btn.pack(side="left", padx=10)
            
        except Exception as e:
            logger.error(f"Errore cambio ricambi: {e}")

    def _applica_costo_calcolato(self, bici, costo_totale):
        """Applica il costo calcolato alla bicicletta"""
        try:
            success = self.bici_ricondizionate_controller.aggiorna_costo_bicicletta(
                bici['id'], costo_totale, f"Costo calcolato automaticamente - {costo_totale:.2f}€"
            )
            
            if success:
                messagebox.showinfo("Successo", f"Costo aggiornato: €{costo_totale:.2f}")
                # Ricarica la lista
                self._mostra_bici_in_lavorazione()
            else:
                messagebox.showerror("Errore", "Errore nell'aggiornamento del costo")
                
        except Exception as e:
            logger.error(f"Errore applicazione costo: {e}")
            messagebox.showerror("Errore", f"Errore: {e}")

    def _modifica_costo_manuale(self, bici, costo_suggerito):
        """Modifica manualmente il costo della bicicletta"""
        try:
            # Crea finestra modifica costo
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Modifica Costo Bicicletta")
            dialog.geometry("400x300")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Centra la finestra
            x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (dialog.winfo_screenheight() // 2) - (300 // 2)
            dialog.geometry(f"400x300+{x}+{y}")
            
            # Titolo
            title_label = ctk.CTkLabel(
                dialog,
                text=f"✏️ Modifica Costo - {bici['marca']} {bici['modello']}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            title_label.pack(pady=15)
            
            # Costo attuale
            ctk.CTkLabel(
                dialog,
                text=f"Costo Attuale: €{bici.get('costo_totale', 0):.2f}",
                font=ctk.CTkFont(size=12)
            ).pack(pady=5)
            
            # Costo suggerito
            ctk.CTkLabel(
                dialog,
                text=f"Costo Suggerito: €{costo_suggerito:.2f}",
                font=ctk.CTkFont(size=12),
                text_color="#10B981"
            ).pack(pady=5)
            
            # Input nuovo costo
            ctk.CTkLabel(dialog, text="Nuovo Costo (€):").pack(pady=(20, 5))
            nuovo_costo_entry = ctk.CTkEntry(dialog, placeholder_text="0.00")
            nuovo_costo_entry.pack(pady=5)
            nuovo_costo_entry.insert(0, str(costo_suggerito))
            
            # Note
            ctk.CTkLabel(dialog, text="Note:").pack(pady=(20, 5))
            note_text = ctk.CTkTextbox(dialog, height=60)
            note_text.pack(pady=5, padx=20, fill="x")
            
            # Pulsanti
            button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            button_frame.pack(pady=20)
            
            # Pulsante Salva
            save_btn = ctk.CTkButton(
                button_frame,
                text="💾 Salva",
                command=lambda: self._salva_costo_modificato(
                    bici, nuovo_costo_entry.get(), note_text.get("1.0", "end-1c"), dialog
                ),
                width=100,
                height=40,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#10B981",
                hover_color="#059669"
            )
            save_btn.pack(side="left", padx=10)
            
            # Pulsante Annulla
            cancel_btn = ctk.CTkButton(
                button_frame,
                text="❌ Annulla",
                command=dialog.destroy,
                width=100,
                height=40,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#6B7280",
                hover_color="#4B5563"
            )
            cancel_btn.pack(side="left", padx=10)
            
        except Exception as e:
            logger.error(f"Errore modifica costo manuale: {e}")
            messagebox.showerror("Errore", f"Errore: {e}")

    def _salva_costo_modificato(self, bici, nuovo_costo_str, note, dialog):
        """Salva il costo modificato"""
        try:
            try:
                nuovo_costo = float(nuovo_costo_str)
                if nuovo_costo < 0:
                    raise ValueError("Costo deve essere positivo")
            except ValueError:
                messagebox.showerror("Errore", "Costo non valido")
                return
            
            success = self.bici_ricondizionate_controller.aggiorna_costo_bicicletta(
                bici['id'], nuovo_costo, note
            )
            
            if success:
                messagebox.showinfo("Successo", f"Costo aggiornato: €{nuovo_costo:.2f}")
                dialog.destroy()
                # Ricarica la lista
                self._mostra_bici_in_lavorazione()
            else:
                messagebox.showerror("Errore", "Errore nell'aggiornamento del costo")
                
        except Exception as e:
            logger.error(f"Errore salvataggio costo modificato: {e}")
            messagebox.showerror("Errore", f"Errore: {e}")

    def _modifica_costo_bicicletta(self, bici):
        """Modifica il costo di una bicicletta"""
        self._modifica_costo_manuale(bici, bici.get('costo_totale', 0))

    def _mostra_raccomandazioni_valutazione(self, parent_dialog, raccomandazioni, bici_id):
        """Mostra le raccomandazioni di valutazione e chiede conferma"""
        try:
            # Crea finestra raccomandazioni
            rec_dialog = ctk.CTkToplevel(parent_dialog)
            rec_dialog.title("Raccomandazioni Valutazione")
            rec_dialog.geometry("600x500")
            rec_dialog.transient(parent_dialog)
            rec_dialog.grab_set()
            
            # Centra la finestra
            x = (rec_dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (rec_dialog.winfo_screenheight() // 2) - (500 // 2)
            rec_dialog.geometry(f"600x500+{x}+{y}")
            
            # Titolo
            title_label = ctk.CTkLabel(
                rec_dialog,
                text="🔍 Raccomandazioni Valutazione",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=15, padx=15, anchor="w")
            
            # Info bicicletta
            info_frame = ctk.CTkFrame(rec_dialog)
            info_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(info_frame, text=f"Bicicletta: {raccomandazioni['marca']} {raccomandazioni['modello']}", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5, padx=10, anchor="w")
            ctk.CTkLabel(info_frame, text=f"Colore: {raccomandazioni.get('colore', 'N/A')}").pack(pady=2, padx=10, anchor="w")
            ctk.CTkLabel(info_frame, text=f"Stato: {raccomandazioni['stato_valutazione']}").pack(pady=2, padx=10, anchor="w")
            
            # Messaggio raccomandazione
            msg_frame = ctk.CTkFrame(rec_dialog)
            msg_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(msg_frame, text="Raccomandazione:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5, padx=10, anchor="w")
            ctk.CTkLabel(msg_frame, text=raccomandazioni['messaggio'], 
                        font=ctk.CTkFont(size=11)).pack(pady=2, padx=10, anchor="w")
            
            # Azioni disponibili
            actions_frame = ctk.CTkFrame(rec_dialog)
            actions_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(actions_frame, text="Azioni Disponibili:", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5, padx=10, anchor="w")
            
            for _, azione in enumerate(raccomandazioni['azioni_disponibili']):
                # '_' perché l'indice non è usato
                ctk.CTkLabel(actions_frame, text=f"• {azione}").pack(pady=1, padx=10, anchor="w")
            
            # Pulsanti azione
            button_frame = ctk.CTkFrame(rec_dialog)
            button_frame.pack(fill="x", padx=15, pady=15)
            
            if raccomandazioni['percorso_raccomandato'] == 'vendita_diretta':
                # Pulsante per vendita diretta
                action_btn = ctk.CTkButton(
                    button_frame,
                    text="✅ Conferma Vendita Diretta",
                    command=lambda: self._conferma_vendita_diretta(rec_dialog, parent_dialog, bici_id),
                    width=200,
                    height=40,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    fg_color="#059669",
                    hover_color="#047857"
                )
                action_btn.pack(side="left", padx=10, pady=10)
                
            elif raccomandazioni['percorso_raccomandato'] == 'ricondizionamento':
                # Pulsante per spostare a ricondizionate
                action_btn = ctk.CTkButton(
                    button_frame,
                    text="🔧 Sposta a Ricondizionate",
                    command=lambda: self._conferma_spostamento_ricondizionate(rec_dialog, parent_dialog, bici_id),
                    width=200,
                    height=40,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    fg_color="#dc2626",
                    hover_color="#b91c1c"
                )
                action_btn.pack(side="left", padx=10, pady=10)
            
            # Pulsante Mantieni in Usate
            keep_btn = ctk.CTkButton(
                button_frame,
                text="📋 Mantieni in Usate",
                command=lambda: self._mantieni_in_usate(rec_dialog, parent_dialog, bici_id),
                width=150,
                height=40,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#6B7280",
                hover_color="#4B5563"
            )
            keep_btn.pack(side="right", padx=10, pady=10)
            
        except Exception as e:
            logger.error(f"Errore mostrazione raccomandazioni: {e}")
            messagebox.showerror("Errore", f"Errore nella visualizzazione: {e}")

    def _conferma_vendita_diretta(self, rec_dialog, parent_dialog, bici_id):
        """Conferma spostamento a vendita diretta"""
        try:
            success = self.bici_usate_controller.sposta_a_vendita_diretta(bici_id)
            if success:
                messagebox.showinfo("Successo", "Bicicletta spostata a vendita diretta!")
                rec_dialog.destroy()
                parent_dialog.destroy()
            else:
                messagebox.showerror("Errore", "Errore nello spostamento a vendita diretta")
        except Exception as e:
            logger.error(f"Errore conferma vendita diretta: {e}")
            messagebox.showerror("Errore", f"Errore: {e}")

    def _conferma_spostamento_ricondizionate(self, rec_dialog, parent_dialog, bici_id):
        """Conferma spostamento a ricondizionate"""
        try:
            # Inizializza controller ricondizionate se non esiste
            if not hasattr(self, 'bici_ricondizionate_controller'):
                from src.modules.biciclette.bici_ricondizionate_controller import (
                    BiciRicondizionateController
                )
                self.bici_ricondizionate_controller = BiciRicondizionateController("data")
            
            success = self.bici_usate_controller.sposta_a_ricondizionate(bici_id, self.bici_ricondizionate_controller)
            if success:
                messagebox.showinfo("Successo", "Bicicletta spostata a ricondizionate!")
                rec_dialog.destroy()
                parent_dialog.destroy()
            else:
                messagebox.showerror("Errore", "Errore nello spostamento a ricondizionate")
        except Exception as e:
            logger.error(f"Errore conferma spostamento ricondizionate: {e}")
            messagebox.showerror("Errore", f"Errore: {e}")

    def _mantieni_in_usate(self, rec_dialog, parent_dialog, bici_id):
        """Mantiene la bicicletta in usate"""
        try:
            messagebox.showinfo("Info", "Bicicletta mantenuta in categoria usate")
            rec_dialog.destroy()
            parent_dialog.destroy()
        except Exception as e:
            logger.error(f"Errore mantenimento in usate: {e}")
            messagebox.showerror("Errore", f"Errore: {e}")

    # ===== GESTIONE BICI RICONDIZIONATE =====

    def _mostra_bici_in_sospeso(self):
        """Mostra biciclette in sospeso"""
        try:
            # Inizializza controller se non esiste
            if not hasattr(self, 'bici_ricondizionate_controller'):
                from src.modules.biciclette.bici_ricondizionate_controller import BiciRicondizionateController
                self.bici_ricondizionate_controller = BiciRicondizionateController("data")
            
            # Ottieni biciclette in sospeso (non completate)
            biciclette = self.bici_ricondizionate_controller.get_biciclette(completate=False)
            
            # Filtra per stato "Sospeso" o simili
            bici_sospeso = [bici for bici in biciclette if 
                           bici.get('stato_ricondizionamento', '').lower() in 
                           ['sospeso', 'in sospeso', 'pausa', 'fermo']]
            
            self._mostra_lista_bici_ricondizionate(
                bici_sospeso, 
                "⏸️ Biciclette in Sospeso",
                "Biciclette con lavori temporaneamente sospesi"
            )
            
        except Exception as e:
            logger.error(f"Errore mostrazione bici in sospeso: {e}")
            messagebox.showerror("Errore", f"Errore nel recupero bici in sospeso: {e}")

    def _mostra_bici_in_lavorazione(self):
        """Mostra biciclette in lavorazione"""
        try:
            # Inizializza controller se non esiste
            if not hasattr(self, 'bici_ricondizionate_controller'):
                from src.modules.biciclette.bici_ricondizionate_controller import BiciRicondizionateController
                self.bici_ricondizionate_controller = BiciRicondizionateController("data")
            
            # Ottieni biciclette in lavorazione (non completate)
            biciclette = self.bici_ricondizionate_controller.get_biciclette(completate=False)
            
            # Filtra per stato "In lavorazione" o simili
            bici_lavorazione = [bici for bici in biciclette if 
                              bici.get('stato_ricondizionamento', '').lower() in 
                              ['in lavorazione', 'iniziato', 'in corso', 'attivo']]
            
            self._mostra_lista_bici_ricondizionate_con_costi(
                bici_lavorazione, 
                "🔨 Biciclette in Lavorazione",
                "Biciclette attualmente in fase di ricondizionamento"
            )
            
        except Exception as e:
            logger.error(f"Errore mostrazione bici in lavorazione: {e}")
            messagebox.showerror("Errore", f"Errore nel recupero bici in lavorazione: {e}")

    def _mostra_bici_da_vendere(self):
        """Mostra biciclette pronte per la vendita"""
        try:
            # Inizializza controller se non esiste
            if not hasattr(self, 'bici_ricondizionate_controller'):
                from src.modules.biciclette.bici_ricondizionate_controller import BiciRicondizionateController
                self.bici_ricondizionate_controller = BiciRicondizionateController("data")
            
            # Ottieni biciclette completate
            biciclette = self.bici_ricondizionate_controller.get_biciclette(completate=True)
            
            self._mostra_lista_bici_ricondizionate(
                biciclette, 
                "💰 Biciclette da Mettere in Vendita",
                "Biciclette completate e pronte per la vendita"
            )
            
        except Exception as e:
            logger.error(f"Errore mostrazione bici da vendere: {e}")
            messagebox.showerror("Errore", f"Errore nel recupero bici da vendere: {e}")

    def _mostra_lista_bici_ricondizionate(self, biciclette, titolo, sottotitolo):
        """Mostra una lista di biciclette ricondizionate"""
        try:
            # Pulisce il frame del contenuto
            for widget in self.tab_content_frame.winfo_children():
                widget.destroy()

            # Titolo
            title_label = ctk.CTkLabel(
                self.tab_content_frame,
                text=titolo,
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=20)

            # Sottotitolo
            subtitle_label = ctk.CTkLabel(
                self.tab_content_frame,
                text=sottotitolo,
                font=ctk.CTkFont(size=16)
            )
            subtitle_label.pack(pady=(0, 30))

            if not biciclette:
                # Nessuna bicicletta
                no_bici_label = ctk.CTkLabel(
                    self.tab_content_frame,
                    text="Nessuna bicicletta trovata",
                    font=ctk.CTkFont(size=16),
                    text_color="#6B7280"
                )
                no_bici_label.pack(pady=50)
            else:
                # Frame scrollabile per la lista
                scroll_frame = ctk.CTkScrollableFrame(self.tab_content_frame, height=400)
                scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

                # Mostra ogni bicicletta
                for bici in biciclette:
                    self._create_bici_ricondizionata_widget(scroll_frame, bici)

            # Pulsanti di controllo
            button_frame = ctk.CTkFrame(self.tab_content_frame, fg_color="transparent")
            button_frame.pack(pady=20)

            # Pulsante Torna Indietro
            back_btn = ctk.CTkButton(
                button_frame,
                text="⬅️ Torna Indietro",
                command=self._seleziona_bici_ricondizionate,
                width=200,
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#6B7280",
                hover_color="#4B5563"
            )
            back_btn.pack(side="left", padx=10)

            # Pulsante Chiudi Tab
            close_btn = ctk.CTkButton(
                button_frame,
                text="❌ Chiudi Tab",
                command=lambda: self.tab_manager.close_tab("nuovo_lavoro"),
                width=200,
                height=40,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#DC2626",
                hover_color="#B91C1C"
            )
            close_btn.pack(side="left", padx=10)

        except Exception as e:
            logger.error(f"Errore mostrazione lista bici ricondizionate: {e}")
            messagebox.showerror("Errore", f"Errore nella visualizzazione: {e}")

    def _create_bici_ricondizionata_widget(self, parent, bici):
        """Crea un widget per una bicicletta ricondizionata"""
        try:
            # Frame per la bicicletta
            bici_frame = ctk.CTkFrame(parent)
            bici_frame.pack(fill="x", padx=10, pady=10)

            # Informazioni principali
            info_frame = ctk.CTkFrame(bici_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=15, pady=10)

            # Marca e modello
            marca_modello = ctk.CTkLabel(
                info_frame,
                text=f"{bici['marca']} {bici['modello']}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            marca_modello.pack(anchor="w")

            # Codice e stato
            codice_stato = ctk.CTkLabel(
                info_frame,
                text=f"Codice: {bici['codice']} | Stato: {bici.get('stato_ricondizionamento', 'N/A')}",
                font=ctk.CTkFont(size=12)
            )
            codice_stato.pack(anchor="w")

            # Dettagli
            dettagli = []
            if bici.get('anno'):
                dettagli.append(f"Anno: {bici['anno']}")
            if bici.get('colore'):
                dettagli.append(f"Colore: {bici['colore']}")
            if bici.get('taglia'):
                dettagli.append(f"Taglia: {bici['taglia']}")
            
            if dettagli:
                dettagli_label = ctk.CTkLabel(
                    info_frame,
                    text=" | ".join(dettagli),
                    font=ctk.CTkFont(size=11),
                    text_color="#6B7280"
                )
                dettagli_label.pack(anchor="w")

            # Costi
            costi_frame = ctk.CTkFrame(bici_frame, fg_color="transparent")
            costi_frame.pack(fill="x", padx=15, pady=(0, 10))

            costo_acquisto = bici.get('prezzo_acquisto', 0)
            costo_totale = bici.get('costo_totale', 0)
            prezzo_vendita = bici.get('prezzo_vendita', 0)

            ctk.CTkLabel(
                costi_frame,
                text=f"Acquisto: €{costo_acquisto:.2f} | Totale: €{costo_totale:.2f} | Vendita: €{prezzo_vendita:.2f}",
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(anchor="w")

            # Pulsanti azione
            actions_frame = ctk.CTkFrame(bici_frame, fg_color="transparent")
            actions_frame.pack(fill="x", padx=15, pady=(0, 10))

            # Pulsante Dettagli
            dettagli_btn = ctk.CTkButton(
                actions_frame,
                text="📋 Dettagli",
                command=lambda: self._mostra_dettagli_bici_ricondizionata(bici),
                width=100,
                height=30,
                font=ctk.CTkFont(size=11)
            )
            dettagli_btn.pack(side="left", padx=5)

            # Pulsante Modifica
            modifica_btn = ctk.CTkButton(
                actions_frame,
                text="✏️ Modifica",
                command=lambda: self._modifica_bici_ricondizionata(bici),
                width=100,
                height=30,
                font=ctk.CTkFont(size=11)
            )
            modifica_btn.pack(side="left", padx=5)

            # Pulsante Elimina
            elimina_btn = ctk.CTkButton(
                actions_frame,
                text="🗑️ Elimina",
                command=lambda: self._elimina_bici_ricondizionata(bici),
                width=100,
                height=30,
                font=ctk.CTkFont(size=11),
                fg_color="#DC2626",
                hover_color="#B91C1C"
            )
            elimina_btn.pack(side="left", padx=5)

        except Exception as e:
            logger.error(f"Errore creazione widget bici ricondizionata: {e}")

    def _mostra_dettagli_bici_ricondizionata(self, bici):
        """Mostra i dettagli di una bicicletta ricondizionata"""
        try:
            # Crea finestra dettagli
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Dettagli Bicicletta Ricondizionata")
            dialog.geometry("600x500")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Centra la finestra
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (500 // 2)
            dialog.geometry(f"600x500+{x}+{y}")
            
            # Titolo
            title_label = ctk.CTkLabel(
                dialog,
                text=f"📋 {bici['marca']} {bici['modello']}",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=15, padx=15, anchor="w")
            
            # Frame per i dettagli
            details_frame = ctk.CTkScrollableFrame(dialog, height=350)
            details_frame.pack(fill="both", expand=True, padx=15, pady=10)
            
            # Informazioni dettagliate
            info_text = f"""
Codice: {bici['codice']}
Marca: {bici['marca']}
Modello: {bici['modello']}
Anno: {bici.get('anno', 'N/A')}
Colore: {bici.get('colore', 'N/A')}
Taglia: {bici.get('taglia', 'N/A')}
Telaio: {bici.get('telaio', 'N/A')}

Stato Ricondizionamento: {bici.get('stato_ricondizionamento', 'N/A')}
Descrizione: {bici.get('descrizione', 'N/A')}

Prezzo Acquisto: €{bici.get('prezzo_acquisto', 0):.2f}
Costo Ricambi: €{bici.get('costo_ricambi', 0):.2f}
Costo Manodopera: €{bici.get('costo_manodopera', 0):.2f}
Costo Totale: €{bici.get('costo_totale', 0):.2f}
Prezzo Vendita: €{bici.get('prezzo_vendita', 0):.2f}
Margine: €{bici.get('margine', 0):.2f}

Data Acquisto: {bici.get('data_acquisto', 'N/A')}
Data Inizio: {bici.get('data_inizio_ricondizionamento', 'N/A')}
Data Fine: {bici.get('data_fine_ricondizionamento', 'N/A')}
Completato: {'Sì' if bici.get('completato') else 'No'}

Note: {bici.get('note', 'N/A')}
            """
            
            details_label = ctk.CTkLabel(
                details_frame,
                text=info_text.strip(),
                font=ctk.CTkFont(size=12),
                justify="left"
            )
            details_label.pack(anchor="w", padx=10, pady=10)
            
            # Pulsante Chiudi
            close_btn = ctk.CTkButton(
                dialog,
                text="❌ Chiudi",
                command=dialog.destroy,
                width=100,
                height=40,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            close_btn.pack(pady=15)
            
        except Exception as e:
            logger.error(f"Errore mostrazione dettagli bici ricondizionata: {e}")
            messagebox.showerror("Errore", f"Errore nella visualizzazione dettagli: {e}")

    def _modifica_bici_ricondizionata(self, bici):
        """Modifica una bicicletta ricondizionata"""
        messagebox.showinfo("Info", "Funzionalità di modifica in fase di sviluppo")

    def _elimina_bici_ricondizionata(self, bici):
        """Elimina una bicicletta ricondizionata"""
        try:
            result = messagebox.askyesno(
                "Conferma Eliminazione",
                f"Sei sicuro di voler eliminare la bicicletta {bici['marca']} {bici['modello']}?"
            )
            
            if result:
                # Inizializza controller se non esiste
                if not hasattr(self, 'bici_ricondizionate_controller'):
                    from src.modules.biciclette.bici_ricondizionate_controller import BiciRicondizionateController
                    self.bici_ricondizionate_controller = BiciRicondizionateController("data")
                
                success = self.bici_ricondizionate_controller.elimina_bicicletta(bici['id'])
                if success:
                    messagebox.showinfo("Successo", "Bicicletta eliminata con successo!")
                    # Ricarica la lista
                    self._mostra_bici_in_sospeso()  # O il metodo appropriato
                else:
                    messagebox.showerror("Errore", "Errore nell'eliminazione della bicicletta")
        except Exception as e:
            logger.error(f"Errore eliminazione bici ricondizionata: {e}")
            messagebox.showerror("Errore", f"Errore nell'eliminazione: {e}")

    def _torna_al_workflow_ricondizionate(self):
        """Torna al workflow delle biciclette"""
        try:
            self._show_biciclette_content()
        except Exception as e:
            logger.error(f"Errore ritorno al workflow: {e}")
            messagebox.showerror("Errore", f"Errore nel ritorno al workflow: {e}")

    def _salva_bicicletta_usata(self, dialog, codice_entry, marca_entry, modello_entry, 
                               prezzo_entry, anno_entry, colore_entry, taglia_entry, 
                               stato_combo, note_text):
        """Salva una nuova bicicletta usata (metodo legacy)"""
        try:
            # Validazione campi obbligatori
            codice = codice_entry.get().strip()
            marca = marca_entry.get().strip()
            modello = modello_entry.get().strip()
            prezzo_str = prezzo_entry.get().strip()
            
            if not codice or not marca or not modello or not prezzo_str:
                messagebox.showwarning("Attenzione", "Compila tutti i campi obbligatori")
                return
            
            try:
                prezzo_acquisto = float(prezzo_str)
            except ValueError:
                messagebox.showerror("Errore", "Prezzo acquisto non valido")
                return
            
            # Inizializza controller bici usate se non esiste
            if not hasattr(self, 'bici_usate_controller'):
                from src.modules.biciclette.bici_usate_controller import BiciUsateController
                self.bici_usate_controller = BiciUsateController("data", self.app_controller)
            
            # Ottieni altri campi
            anno = anno_entry.get().strip()
            anno_int = int(anno) if anno and anno.isdigit() else None
            
            colore = colore_entry.get().strip()
            taglia = taglia_entry.get().strip()
            stato_generale = stato_combo.get()
            note = note_text.get("1.0", "end-1c").strip()
            
            # Aggiungi bicicletta
            # Se anno non è fornito, passiamo 0 come fallback (il controller si occuperà della validazione)
            success = self.bici_usate_controller.aggiungi_bicicletta(
                codice=codice,
                marca=marca,
                modello=modello,
                anno=anno_int if anno_int is not None else 0,
                colore=colore,
                taglia=taglia,
                stato_generale=stato_generale,
                prezzo_acquisto=prezzo_acquisto,
                note=note
            )
            
            if success:
                messagebox.showinfo("Successo", f"Bicicletta '{marca} {modello}' aggiunta con successo!")
                dialog.destroy()
            else:
                messagebox.showerror("Errore", "Errore nel salvataggio della bicicletta")
                
        except Exception as e:
            logger.error(f"Errore salvataggio bicicletta usata: {e}")
            messagebox.showerror("Errore", f"Errore nel salvataggio: {e}")

    def _create_bici_widget(self, parent_frame, bici):
        """Crea il widget per una bicicletta nel catalogo"""
        try:
            # Frame per la bicicletta
            bici_frame = ctk.CTkFrame(parent_frame)
            bici_frame.pack(fill="x", pady=5, padx=5)
            
            # Informazioni principali
            info_frame = ctk.CTkFrame(bici_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=10)
            
            # Codice e stato
            header_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            header_frame.pack(fill="x")
            
            codice_label = ctk.CTkLabel(
                header_frame,
                text=f"#{bici['codice']}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#059669"
            )
            codice_label.pack(side="left")
            
            stato_label = ctk.CTkLabel(
                header_frame,
                text="🟢 Disponibile" if not bici['venduta'] else "🔴 Venduta",
                font=ctk.CTkFont(size=12),
                text_color="#059669" if not bici['venduta'] else "#DC2626"
            )
            stato_label.pack(side="right")
            
            # Marca e modello
            marca_modello = ctk.CTkLabel(
                info_frame,
                text=f"{bici['marca']} {bici['modello']}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            marca_modello.pack(anchor="w", pady=(5, 0))
            
            # Dettagli
            dettagli = []
            if bici['anno']:
                dettagli.append(f"Anno: {bici['anno']}")
            if bici['colore']:
                dettagli.append(f"Colore: {bici['colore']}")
            if bici['taglia']:
                dettagli.append(f"Taglia: {bici['taglia']}")
            if bici['stato_generale']:
                dettagli.append(f"Stato: {bici['stato_generale']}")
            
            if dettagli:
                dettagli_label = ctk.CTkLabel(
                    info_frame,
                    text=" • ".join(dettagli),
                    font=ctk.CTkFont(size=12),
                    text_color="#6B7280"
                )
                dettagli_label.pack(anchor="w", pady=(2, 0))
            
            # Costi
            costi_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            costi_frame.pack(fill="x", pady=(10, 0))
            
            costo_acquisto = ctk.CTkLabel(
                costi_frame,
                text=f"Acquisto: €{bici['prezzo_acquisto']:.2f}",
                font=ctk.CTkFont(size=12)
            )
            costo_acquisto.pack(side="left")
            
            costo_totale = ctk.CTkLabel(
                costi_frame,
                text=f"Totale: €{bici['costo_totale']:.2f}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#059669"
            )
            costo_totale.pack(side="right")
            
            # Pulsanti azioni
            actions_frame = ctk.CTkFrame(bici_frame, fg_color="transparent")
            actions_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Pulsante Lavori
            lavori_btn = ctk.CTkButton(
                actions_frame,
                text="🔧 Lavori",
                command=lambda: self._gestisci_lavori_bici(bici['id']),
                width=80,
                height=30,
                font=ctk.CTkFont(size=10)
            )
            lavori_btn.pack(side="left", padx=2)
            
            # Pulsante Preventivo
            preventivo_btn = ctk.CTkButton(
                actions_frame,
                text="📄 Preventivo",
                command=lambda: self._crea_preventivo_bici(bici['id']),
                width=80,
                height=30,
                font=ctk.CTkFont(size=10)
            )
            preventivo_btn.pack(side="left", padx=2)
            
            # Pulsante Modifica
            modifica_btn = ctk.CTkButton(
                actions_frame,
                text="✏️ Modifica",
                command=lambda: self._modifica_bici_usata(bici['id']),
                width=80,
                height=30,
                font=ctk.CTkFont(size=10)
            )
            modifica_btn.pack(side="left", padx=2)
            
            # Pulsante Elimina
            elimina_btn = ctk.CTkButton(
                actions_frame,
                text="❌ Elimina",
                command=lambda: self._elimina_bici_usata(bici['id']),
                width=80,
                height=30,
                font=ctk.CTkFont(size=10),
                fg_color="#DC2626",
                hover_color="#B91C1C"
            )
            elimina_btn.pack(side="right", padx=2)
            
        except Exception as e:
            logger.error(f"Errore creazione widget bicicletta: {e}")


    def _avvia_restauro(self):
        """Avvia un restauro - mostra le bici in sospeso"""
        try:
            # Controlla se la GUI è stata caricata
            if not hasattr(self, 'bici_restaurate_gui') or self.bici_restaurate_gui is None:
                # Carica la GUI se non è ancora stata caricata
                self.bici_restaurate_gui = BiciRestaurateGUI(self.root, self.bici_restaurate_controller, self)
            
            self.bici_restaurate_gui.mostra_avvia_restauro()
        except Exception as e:
            logger.error(f"Errore avvio restauro: {e}")
            messagebox.showerror("Errore", f"Errore nell'avvio del restauro: {e}")

    def _mostra_restauri_in_corso(self):
        """Mostra i restauri in corso d'opera"""
        try:
            # Controlla se la GUI è stata caricata
            if not hasattr(self, 'bici_restaurate_gui') or self.bici_restaurate_gui is None:
                self.bici_restaurate_gui = BiciRestaurateGUI(self.root, self.bici_restaurate_controller, self)
            
            self.bici_restaurate_gui.mostra_restauri_in_corso()
        except Exception as e:
            logger.error(f"Errore mostra restauri in corso: {e}")
            messagebox.showerror("Errore", f"Errore nella visualizzazione dei restauri: {e}")

    def _metti_in_vendita_restaurata(self):
        """Mette in vendita una bicicletta restaurata"""
        try:
            # Controlla se la GUI è stata caricata
            if not hasattr(self, 'bici_restaurate_gui') or self.bici_restaurate_gui is None:
                self.bici_restaurate_gui = BiciRestaurateGUI(self.root, self.bici_restaurate_controller, self)
            
            self.bici_restaurate_gui.metti_in_vendita()
        except Exception as e:
            logger.error(f"Errore metti in vendita: {e}")
            messagebox.showerror("Errore", f"Errore nel mettere in vendita: {e}")

    def _torna_al_workflow_restauro(self):
        """Torna al workflow nuovo lavoro"""
        try:
            # Controlla se la GUI è stata caricata
            if not hasattr(self, 'bici_restaurate_gui') or self.bici_restaurate_gui is None:
                self.bici_restaurate_gui = BiciRestaurateGUI(self.root, self.bici_restaurate_controller, self)
            
            self.bici_restaurate_gui.torna_al_workflow()
        except Exception as e:
            logger.error(f"Errore ritorno workflow: {e}")
            messagebox.showerror("Errore", f"Errore nel ritorno al workflow: {e}")

    def _apri_guida_restauri_main(self):
        """Apre la guida per i restauri dal main"""
        if self.guida_manager:
            self.guida_manager.mostra_guida_restauri()

    def _show_riparazioni_submenu(self):
        """Mostra il sottomenu per le riparazioni"""
        # Pulisce il frame del contenuto
        for widget in self.tab_content_frame.winfo_children():
            widget.destroy()

        # Titolo
        title_label = ctk.CTkLabel(
            self.tab_content_frame,
            text="🔧 Gestione Riparazioni",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Sottotitolo
        subtitle_label = ctk.CTkLabel(
            self.tab_content_frame,
            text="Scegli l'operazione da effettuare:",
            font=ctk.CTkFont(size=14)
        )
        subtitle_label.pack(pady=(0, 30))

        # Container per i pulsanti principali
        main_buttons_frame = ctk.CTkFrame(self.tab_content_frame, fg_color="transparent")
        main_buttons_frame.pack(expand=True, fill="both", padx=50)

        # Pulsante Gestione Clienti
        clienti_btn = ctk.CTkButton(
            main_buttons_frame,
            text="👥 GESTIONE CLIENTI\n\nVisualizza e gestisci\nla lista dei clienti",
            command=self.apri_gestione_clienti,
            width=300,
            height=120,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            corner_radius=15
        )
        clienti_btn.pack(pady=20)

        # Pulsante Nuova Riparazione
        nuova_riparazione_btn = ctk.CTkButton(
            main_buttons_frame,
            text="🔧 NUOVA RIPARAZIONE\n\nCrea un nuovo lavoro\ndi riparazione",
            command=self._apri_nuova_riparazione,
            width=300,
            height=120,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            corner_radius=15
        )
        nuova_riparazione_btn.pack(pady=20)

        # Container per i pulsanti di navigazione
        nav_buttons_frame = ctk.CTkFrame(self.tab_content_frame, fg_color="transparent")
        nav_buttons_frame.pack(fill="x", padx=50, pady=(30, 20))

        # Pulsante Torna al Nuovo Lavoro
        back_btn = ctk.CTkButton(
            nav_buttons_frame,
            text="← Torna al Nuovo Lavoro",
            command=lambda: self.tab_manager.close_tab("nuovo_lavoro"),
            width=200,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#6B7280",
            hover_color="#4B5563",
            corner_radius=10
        )
        back_btn.pack(side="left", padx=10)

        # Pulsante Guida
        guida_btn = ctk.CTkButton(
            nav_buttons_frame,
            text="📖 Guida",
            command=lambda: self.guida_manager.mostra_guida_riparazioni() if self.guida_manager else None,
            width=200,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            corner_radius=10
        )
        guida_btn.pack(side="right", padx=10)

    def _apri_guida_riparazioni(self):
        """Apre la guida per le riparazioni"""
        if self.guida_manager:
            self.guida_manager.mostra_guida_riparazioni()

    def _create_riparazione_content(self):
        """Crea il contenuto per la tab riparazione"""
        try:
            # Pulisce il frame del contenuto
            for widget in self.tab_content_frame.winfo_children():
                widget.destroy()
            
            # Crea la GUI riparazioni integrata
            riparazioni_gui = RiparazioniGUI(
                parent=self.tab_content_frame,
                controller=self.riparazioni_controller,
                inventario_callback=self._apri_inventario_per_ricambi
            )
            
            # Crea il contenuto della riparazione direttamente nel frame
            riparazioni_gui.create_riparazione_content()
            
            # Aggiungi pulsante per chiudere la tab
            self._add_chiudi_tab_button()
            
        except Exception as e:
            logger.error(f"Errore creazione contenuto riparazione: {e}")
            messagebox.showerror("Errore", f"Errore nella creazione del contenuto: {e}")
    
    def _add_chiudi_tab_button(self):
        """Aggiunge un pulsante per chiudere la tab riparazione"""
        try:
            # Crea un frame per i pulsanti di controllo
            control_frame = ctk.CTkFrame(self.tab_content_frame)
            control_frame.pack(fill="x", padx=20, pady=10, side="bottom")
            
            # Pulsante Chiudi Tab
            chiudi_btn = ctk.CTkButton(
                control_frame,
                text="❌ Chiudi Tab",
                command=lambda: self.tab_manager.close_tab("nuova_riparazione"),
                width=120,
                height=40,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#DC2626",
                hover_color="#B91C1C"
            )
            chiudi_btn.pack(side="right", padx=10, pady=5)
            
        except Exception as e:
            logger.error(f"Errore aggiunta pulsante chiudi tab: {e}")
    
    def _apri_inventario_per_ricambi(self, callback):
        """Metodo legacy - ora i ricambi sono caricati direttamente nella tab riparazione"""
        pass

    def _show_riparazioni_content(self):
        """Mostra il contenuto per le riparazioni"""
        # Pulisce il frame del contenuto
        for widget in self.tab_content_frame.winfo_children():
            widget.destroy()

        # Titolo
        title_label = ctk.CTkLabel(
            self.tab_content_frame,
            text="🔧 Gestione Riparazioni",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)

        # Sottotitolo
        subtitle_label = ctk.CTkLabel(
            self.tab_content_frame,
            text="Seleziona il tipo di riparazione da eseguire",
            font=ctk.CTkFont(size=16)
        )
        subtitle_label.pack(pady=(0, 30))

        # Frame per il contenuto
        content_frame = ctk.CTkFrame(
            self.tab_content_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Frame per la selezione tipo cliente
        tipo_frame = ctk.CTkFrame(content_frame)
        tipo_frame.pack(fill="x", pady=(0, 20))

        # Titolo selezione tipo
        tipo_title = ctk.CTkLabel(
            tipo_frame,
            text="👤 Tipo di Cliente",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        tipo_title.pack(pady=15, padx=15, anchor="w")

        # Pulsanti per tipo cliente
        cliente_buttons_frame = ctk.CTkFrame(tipo_frame, fg_color="transparent")
        cliente_buttons_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Pulsante Cliente Esterno
        cliente_btn = ctk.CTkButton(
            cliente_buttons_frame,
            text="👥 CLIENTE ESTERNO\n\nRiparazione per cliente esterno\n(Prezzo: Mano d'opera + Ricambi)",
            command=lambda: self._seleziona_operazioni_cliente("esterno"),
            width=250,
            height=120,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            corner_radius=15
        )
        cliente_btn.pack(side="left", padx=10, fill="both", expand=True)

        # Pulsante Officina Interna
        officina_btn = ctk.CTkButton(
            cliente_buttons_frame,
            text="🏭 OFFICINA INTERNA\n\nRiparazione per officina interna\n(Prezzo: Ricambi × 2 + Aggiustamento)",
            command=lambda: self._seleziona_operazioni_cliente("interna"),
            width=250,
            height=120,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            corner_radius=15
        )
        officina_btn.pack(side="left", padx=10, fill="both", expand=True)

        # Pulsanti di controllo
        button_frame = ctk.CTkFrame(
            self.tab_content_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        # Pulsante Torna alla selezione
        back_btn = ctk.CTkButton(
            button_frame,
            text="⬅️ Torna alla Selezione",
            command=self._nuovo_lavoro_tab_content,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#6B7280",
            hover_color="#4B5563",
            corner_radius=10
        )
        back_btn.pack(side="left", padx=10)

        # Pulsante Chiudi tab
        close_btn = ctk.CTkButton(
            button_frame,
            text="❌ Chiudi Tab",
            command=lambda: self.tab_manager.close_tab("nuovo_lavoro"),
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C"
        )
        close_btn.pack(side="left", padx=10)

    def _seleziona_operazioni_cliente(self, tipo_cliente):
        """Seleziona le operazioni in base al tipo di cliente"""
        try:
            # Pulisce il frame del contenuto
            for widget in self.tab_content_frame.winfo_children():
                widget.destroy()

            # Titolo
            tipo_text = "Cliente Esterno" if tipo_cliente == "esterno" else "Officina Interna"
            title_label = ctk.CTkLabel(
                self.tab_content_frame,
                text=f"🔧 Operazioni per {tipo_text}",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=20)

            # Sottotitolo
            subtitle_label = ctk.CTkLabel(
                self.tab_content_frame,
                text="Seleziona le operazioni da eseguire",
                font=ctk.CTkFont(size=16)
            )
            subtitle_label.pack(pady=(0, 30))

            # Frame per il contenuto
            content_frame = ctk.CTkFrame(
                self.tab_content_frame, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Carica le operazioni dal database
            self._carica_operazioni_riparazioni(content_frame, tipo_cliente)

        except Exception as e:
            logger.error(f"Errore selezione operazioni cliente: {e}")
            messagebox.showerror("Errore", f"Errore nella selezione operazioni: {e}")

    def _carica_operazioni_riparazioni(self, parent_frame, tipo_cliente):
        """Carica le operazioni di riparazione dal database"""
        try:
            if not hasattr(self, 'officina_controller') or not self.officina_controller:
                # Messaggio se controller non disponibile
                no_controller_label = ctk.CTkLabel(
                    parent_frame,
                    text="⚠️ Controller officina non disponibile\n\nConfigura le operazioni nelle Impostazioni → Listino",
                    font=ctk.CTkFont(size=14),
                    text_color="#DC2626"
                )
                no_controller_label.pack(pady=50)
                return

            # Ottieni categorie e operazioni
            categorie = self.officina_controller.get_categorie_operazioni()
            operazioni = self.officina_controller.get_operazioni()

            if not categorie and not operazioni:
                # Messaggio se non ci sono operazioni
                no_ops_label = ctk.CTkLabel(
                    parent_frame,
                    text="📝 Nessuna operazione configurata\n\nVai in Impostazioni → Listino per aggiungere operazioni",
                    font=ctk.CTkFont(size=14),
                    text_color="#6B7280"
                )
                no_ops_label.pack(pady=50)
                return

            # Frame scrollabile per le operazioni
            scroll_frame = ctk.CTkScrollableFrame(parent_frame, height=400)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Raggruppa operazioni per categoria
            operazioni_per_categoria = {}
            for operazione in operazioni:
                cat_id = operazione['categoria_id']
                if cat_id not in operazioni_per_categoria:
                    operazioni_per_categoria[cat_id] = []
                operazioni_per_categoria[cat_id].append(operazione)

            # Mostra operazioni per categoria
            for categoria in categorie:
                cat_id = categoria['id']
                if cat_id in operazioni_per_categoria:
                    # Titolo categoria
                    cat_label = ctk.CTkLabel(
                        scroll_frame,
                        text=f"📁 {categoria['nome']}",
                        font=ctk.CTkFont(size=16, weight="bold"),
                        text_color="#2B5A27"
                    )
                    cat_label.pack(pady=(10, 5), padx=10, anchor="w")

                    # Frame per le operazioni della categoria
                    ops_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                    ops_frame.pack(fill="x", padx=20, pady=(0, 10))

                    for operazione in operazioni_per_categoria[cat_id]:
                        self._create_operazione_widget(ops_frame, operazione, tipo_cliente)

        except Exception as e:
            logger.error(f"Errore caricamento operazioni riparazioni: {e}")
            messagebox.showerror("Errore", f"Errore nel caricamento operazioni: {e}")

    def _create_operazione_widget(self, parent_frame, operazione, tipo_cliente):
        """Crea il widget per una singola operazione"""
        try:
            # Frame per l'operazione
            op_frame = ctk.CTkFrame(parent_frame)
            op_frame.pack(fill="x", pady=2, padx=5)

            # Nome operazione
            nome_label = ctk.CTkLabel(
                op_frame,
                text=f"⚙️ {operazione['nome']}",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            nome_label.pack(side="left", padx=10, pady=8)

            # Prezzo (placeholder per ora)
            prezzo_text = "€ --"  # TODO: Calcola prezzo in base al tipo cliente
            prezzo_label = ctk.CTkLabel(
                op_frame,
                text=prezzo_text,
                font=ctk.CTkFont(size=12),
                text_color="#059669"
            )
            prezzo_label.pack(side="right", padx=10, pady=8)

            # Pulsante seleziona
            select_btn = ctk.CTkButton(
                op_frame,
                text="✅ Seleziona",
                command=lambda: self._seleziona_operazione(operazione, tipo_cliente),
                width=100,
                height=30,
                font=ctk.CTkFont(size=10)
            )
            select_btn.pack(side="right", padx=5, pady=8)

        except Exception as e:
            logger.error(f"Errore creazione widget operazione: {e}")

    def _seleziona_operazione(self, operazione, tipo_cliente):
        """Seleziona un'operazione specifica"""
        try:
            tipo_text = "Cliente Esterno" if tipo_cliente == "esterno" else "Officina Interna"
            messagebox.showinfo(
                "Operazione Selezionata",
                f"Operazione: {operazione['nome']}\n"
                f"Tipo: {tipo_text}\n\n"
                f"Funzionalità di creazione lavoro in sviluppo..."
            )
        except Exception as e:
            logger.error(f"Errore selezione operazione: {e}")

    def _inventario_tab_content(self):
        """Contenuto della tab inventario"""
        # Pulisce il frame del contenuto
        for widget in self.tab_content_frame.winfo_children():
            widget.destroy()

        # Titolo
        title_label = ctk.CTkLabel(
            self.tab_content_frame,
            text="📦 Gestione Inventario",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=10)

        # Frame principale - RESPONSIVE
        main_frame = ctk.CTkFrame(
            self.tab_content_frame, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configura il ridimensionamento per il tab_content_frame
        self.tab_content_frame.pack_propagate(False)

        # Inizializza la GUI inventario se non esiste
        if not hasattr(self, 'inventario_gui'):
            from src.gui.inventario_gui import InventarioGUI
            self.inventario_gui = InventarioGUI(self, self.guida_manager if self.guida_manager else None)
        
        # Mostra il contenuto dell'inventario
        self.inventario_gui.mostra_inventario_content(main_frame)

    def run(self):
        """Avvia l'applicazione"""
        self.root.mainloop()

def main():
    """Funzione principale"""
    try:
        app = GestionaleApp()
        app.run()
    except (ImportError, AttributeError, RuntimeError) as e:
        error_msg = f"Errore nell'avvio dell'applicazione:\n{str(e)}"
        logger.critical(error_msg, "MAIN", e)
        messagebox.showerror("Errore Critico", error_msg)
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-except
        error_msg = f"Errore imprevisto nell'avvio dell'applicazione:\n{str(e)}"
        logger.critical(error_msg, "MAIN", e)
        messagebox.showerror("Errore Critico", error_msg)
        sys.exit(1)
    finally:
        logger.log_application_stop()


if __name__ == "__main__":
    main()
