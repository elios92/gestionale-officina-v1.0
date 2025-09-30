"""
Script per creare l'eseguibile del Gestionale Biciclette

Questo script crea un file .exe standalone del gestionale.
Eseguire solo quando il progetto è completamente finito.

Autore: Gestionale Team
Versione: 1.0.0
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_exe():
    """Crea l'eseguibile del gestionale"""
    print("🚀 Creazione eseguibile Gestionale Biciclette v1.0")
    print("=" * 50)
    
    # Verifica che PyInstaller sia installato
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} trovato")
    except ImportError:
        print("❌ PyInstaller non trovato. Installare con: pip install pyinstaller")
        return False
    
    # Comando PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",                    # Un singolo file exe
        "--windowed",                   # Senza console
        "--name=GestionaleBiciclette",  # Nome eseguibile
        "--icon=assets/icon.ico",       # Icona
        "--add-data=sounds;sounds",     # Includi cartella suoni
        "--add-data=data;data",         # Includi cartella dati
        "--hidden-import=pygame",       # Import nascosti
        "--hidden-import=psutil",
        "--hidden-import=scipy",
        "--hidden-import=numpy",
        "--hidden-import=customtkinter",
        "main.py"                       # File principale
    ]
    
    print("🔧 Comando PyInstaller:")
    print(" ".join(cmd))
    print()
    
    try:
        # Esegui PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Eseguibile creato con successo!")
        print(f"📁 Posizione: dist/GestionaleBiciclette.exe")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante la creazione: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def cleanup_build():
    """Pulisce i file temporanei di build"""
    print("\n🧹 Pulizia file temporanei...")
    
    dirs_to_remove = ["build", "__pycache__"]
    files_to_remove = ["GestionaleBiciclette.spec"]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Rimosso: {dir_name}")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"✅ Rimosso: {file_name}")

def main():
    """Funzione principale"""
    print("⚠️  ATTENZIONE: Questo script crea l'eseguibile finale!")
    print("Assicurati che il progetto sia completamente finito.")
    print()
    
    response = input("Vuoi continuare? (s/n): ").lower().strip()
    if response != 's':
        print("❌ Operazione annullata.")
        return
    
    # Crea l'eseguibile
    if create_exe():
        print("\n🎉 SUCCESSO!")
        print("📁 L'eseguibile è disponibile in: dist/GestionaleBiciclette.exe")
        print("💾 Dimensione stimata: ~50-100 MB")
        print("\nPer distribuire:")
        print("1. Copia dist/GestionaleBiciclette.exe")
        print("2. L'eseguibile è completamente standalone")
        
        # Pulisci i file temporanei
        cleanup_build()
    else:
        print("\n❌ ERRORE durante la creazione dell'eseguibile")

if __name__ == "__main__":
    main()
