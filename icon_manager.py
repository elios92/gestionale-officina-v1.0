"""
Gestore Icone per Gestionale Biciclette

Gestisce le icone della finestra, desktop e system tray.
"""

import os
import sys
from PIL import Image

# Import condizionale per Windows
try:
    import win32com.client
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

try:
    import pystray
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


class IconManager:
    """Gestore per le icone dell'applicazione"""

    def __init__(self, app_instance):
        """
        Inizializza il gestore icone
        
        Args:
            app_instance: Istanza dell'applicazione principale
        """
        self.app = app_instance
        self.icon_path = self._create_default_icon()
        self.tray_icon = None

    def _create_default_icon(self) -> str:
        """
        Crea un'icona di default se non esiste
        
        Returns:
            Percorso dell'icona
        """
        icon_path = "assets/icon.ico"
        
        # Crea la directory assets se non esiste
        os.makedirs("assets", exist_ok=True)
        
        # Se l'icona non esiste, crea una di default
        if not os.path.exists(icon_path):
            self._create_bicycle_icon(icon_path)
        
        return icon_path

    def _create_bicycle_icon(self, icon_path: str):
        """
        Crea un'icona di bicicletta di default
        
        Args:
            icon_path: Percorso dove salvare l'icona
        """
        try:
            # Crea un'icona di alta qualità con PIL
            base_size = 256
            image = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
            
            # Disegna una bicicletta semplice
            from PIL import ImageDraw
            
            draw = ImageDraw.Draw(image)
            
            # Colore principale
            color = (0, 100, 200)  # Blu
            
            # Scala per la dimensione base
            scale = base_size / 64
            
            # Disegna cerchi (ruote) - più grandi e definiti
            wheel1 = [int(10 * scale), int(35 * scale), int(25 * scale), int(50 * scale)]
            wheel2 = [int(35 * scale), int(35 * scale), int(50 * scale), int(50 * scale)]
            draw.ellipse(wheel1, fill=color, outline=color, width=int(2 * scale))
            draw.ellipse(wheel2, fill=color, outline=color, width=int(2 * scale))
            
            # Disegna telaio - più spesso
            draw.line([(int(17 * scale), int(42 * scale)), (int(42 * scale), int(42 * scale))], 
                     fill=color, width=int(4 * scale))
            draw.line([(int(17 * scale), int(42 * scale)), (int(25 * scale), int(25 * scale))], 
                     fill=color, width=int(4 * scale))
            draw.line([(int(25 * scale), int(25 * scale)), (int(42 * scale), int(42 * scale))], 
                     fill=color, width=int(4 * scale))
            
            # Crea multiple dimensioni per l'icona ICO
            sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            ico_images = []
            
            for size in sizes:
                # Ridimensiona con algoritmo di alta qualità
                resized = image.resize(size, Image.Resampling.LANCZOS)
                ico_images.append(resized)
            
            # Salva come ICO con tutte le dimensioni
            ico_images[0].save(
                icon_path, 
                format='ICO', 
                sizes=[(img.width, img.height) for img in ico_images],
                quality=95
            )
            
        except (OSError, ValueError, TypeError) as e:
            print(f"Errore nella creazione dell'icona: {e}")
            # Crea un'icona vuota come fallback
            image = Image.new('RGBA', (32, 32), (255, 255, 255))
            image.save(icon_path, format='ICO')

    def set_window_icon(self, window):
        """
        Imposta l'icona della finestra
        
        Args:
            window: Finestra CustomTkinter
        """
        try:
            # Prova a ottenere l'icona dalle impostazioni
            if hasattr(self.app, 'app_controller'):
                icona_impostazioni = self.app.app_controller.impostazioni.get_icona_attuale()
                if os.path.exists(icona_impostazioni):
                    # Forza il refresh dell'icona
                    window.iconbitmap(icona_impostazioni)
                    # Aggiorna anche l'icona della finestra
                    window.update_idletasks()
                    return
            
            # Fallback: usa l'icona di default
            if os.path.exists(self.icon_path):
                window.iconbitmap(self.icon_path)
                window.update_idletasks()
            else:
                # Fallback: usa un'icona di sistema
                window.iconbitmap(default="")
        except (OSError, ValueError, TypeError) as e:
            print(f"Errore nell'impostazione dell'icona finestra: {e}")

    def refresh_window_icon(self, window):
        """
        Aggiorna l'icona della finestra forzando il refresh
        
        Args:
            window: Finestra CustomTkinter
        """
        try:
            # Ottieni l'icona attuale dalle impostazioni
            if hasattr(self.app, 'app_controller'):
                icona_impostazioni = self.app.app_controller.impostazioni.get_icona_attuale()
                if os.path.exists(icona_impostazioni):
                    # Forza il refresh completo
                    window.iconbitmap(icona_impostazioni)
                    window.update()
                    window.update_idletasks()
                    return True
            return False
        except (OSError, ValueError, TypeError) as e:
            print(f"Errore nel refresh dell'icona finestra: {e}")
            return False

    def set_desktop_icon(self, shortcut_path: str = "Gestionale Biciclette.lnk"):
        """
        Crea un'icona sul desktop (Windows)
        
        Args:
            shortcut_path: Nome del collegamento
        """
        if not WINDOWS_AVAILABLE:
            print("Funzionalità desktop icon disponibile solo su Windows")
            return

        try:
            # Percorso del desktop
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, shortcut_path)
            
            # Crea il collegamento
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{os.path.abspath("main.py")}"'
            shortcut.WorkingDirectory = os.path.dirname(os.path.abspath("main.py"))
            shortcut.IconLocation = os.path.abspath(self.icon_path)
            shortcut.Description = "Gestionale Biciclette v1.0"
            shortcut.save()
            
            print(f"Collegamento desktop creato: {shortcut_path}")
            
        except (OSError, ValueError, TypeError) as e:
            print(f"Errore nella creazione del collegamento desktop: {e}")

    def create_system_tray_icon(self):
        """
        Crea un'icona nella system tray
        """
        if not TRAY_AVAILABLE:
            print("Libreria pystray non disponibile")
            return

        try:
            # Crea il menu della system tray
            menu = pystray.Menu(
                pystray.MenuItem("Apri Gestionale", self._show_window),
                pystray.MenuItem("Minimizza", self._minimize_window),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Esci", self._quit_app)
            )
            
            # Crea l'icona
            image = Image.open(self.icon_path) if os.path.exists(self.icon_path) else None
            self.tray_icon = pystray.Icon("Gestionale Biciclette", image, menu=menu)
            
            # Avvia l'icona in un thread separato
            import threading
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            
        except (OSError, ValueError, TypeError) as e:
            print(f"Errore nella creazione della system tray: {e}")

    def _show_window(self, _icon=None, _item=None):
        """Mostra la finestra principale"""
        if hasattr(self.app, 'root'):
            self.app.root.deiconify()
            self.app.root.lift()

    def _minimize_window(self, _icon=None, _item=None):
        """Minimizza la finestra"""
        if hasattr(self.app, 'root'):
            self.app.root.withdraw()

    def _quit_app(self, _icon=None, _item=None):
        """Chiude l'applicazione"""
        if hasattr(self.app, 'root'):
            self.app.root.quit()

    def cleanup(self):
        """Pulisce le risorse"""
        if self.tray_icon:
            self.tray_icon.stop()


# Esempio di utilizzo
if __name__ == "__main__":
    print("Icon Manager - Test")
    
    # Test creazione icona
    manager = IconManager(None)
    print(f"Icona creata: {manager.icon_path}")
    
    # Test collegamento desktop (solo su Windows)
    if WINDOWS_AVAILABLE:
        manager.set_desktop_icon()
    
    print("Test completato!")
