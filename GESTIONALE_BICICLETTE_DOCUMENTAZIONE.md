# 🚴‍♂️ GESTIONALE BICICLETTE v1.0 - DOCUMENTAZIONE COMPLETA

## 📋 INDICE
1. [Panoramica](#panoramica)
2. [Installazione](#installazione)
3. [Avvio](#avvio)
4. [Funzionalità](#funzionalità)
5. [Struttura Progetto](#struttura-progetto)
6. [Sistemi Avanzati](#sistemi-avanzati)
7. [Troubleshooting](#troubleshooting)
8. [Changelog](#changelog)

---

## 🎯 PANORAMICA

**Gestionale Biciclette v1.0** è un sistema completo per la gestione di un'officina di biciclette con funzionalità avanzate di:

- **Gestione Biciclette Usate e Ricondizionate**
- **Sistema Restauro Completo**
- **Bici Artigianali Personalizzate**
- **Calcolo Prezzi Dinamico**
- **Sistema Audio Immersivo**
- **Design System Professionale**
- **Ottimizzazione Performance**

### ✨ Caratteristiche Principali
- 🎵 **Sistema Audio**: Suoni realistici per ogni azione
- 🎨 **Design Moderno**: Interfaccia professionale e intuitiva
- ⚡ **Performance Ottimizzate**: Gestione avanzata delle risorse
- 🔧 **Modulare**: Architettura scalabile e manutenibile
- 📊 **Database SQLite**: Gestione dati offline
- 🎯 **Workflow Completi**: Processi guidati per ogni tipo di lavoro

---

## 🚀 INSTALLAZIONE

### Requisiti di Sistema
- **OS**: Windows 10/11
- **Python**: 3.11+
- **RAM**: Minimo 4GB (Consigliato 8GB+)
- **Spazio**: 1GB libero

### Dipendenze
```bash
pip install -r requirements.txt
```

**Librerie Principali:**
- `customtkinter` - GUI moderna
- `pygame` - Sistema audio
- `psutil` - Monitoraggio performance
- `scipy` - Elaborazione audio
- `numpy` - Calcoli numerici

---

## ▶️ AVVIO

### Metodo 1: Batch File (Consigliato)
```bash
# Doppio click su:
avvia.bat
```

### Metodo 2: Installazione e Avvio
```bash
# Doppio click su:
installa_e_avvia.bat
```

### Metodo 3: Manuale
```bash
python main.py
```

---

## 🔧 FUNZIONALITÀ

### 1. **BICICLETTE USATE**
- **Creazione Schede Lavoro**: Inserimento dati bicicletta
- **Gestione Operazioni**: Lista operazioni da eseguire
- **Ricambi Necessari**: Catalogo componenti
- **Checkbox Restauro**: Attivazione workflow restauro

### 2. **BICICLETTE RICONDIZIONATE**
- **Modifica Dinamica**: Aggiornamento operazioni e ricambi
- **Calcolo Prezzi**: Formula automatica con IVA
- **Ricalcolo Costi**: Aggiornamento in tempo reale
- **Gestione IVA**: Toggle per inclusione/esclusione

### 3. **BICICLETTE RESTAURATE**
- **Avvio Restauro**: Selezione bici da restaurare
- **Restauri in Corso**: Monitoraggio lavori attivi
- **Messa in Vendita**: Gestione vendite
- **Calcolo Costi**: Verniciatura + ricambi × 2

### 4. **BICICLETTE ARTIGIANALI**
- **Assemblaggio**: Montaggio da zero con componenti nuovi
- **Selezione Telaio**: Materiale e dimensioni
- **Componenti**: Catalogo completo accessori
- **Calcolo Prezzi**: (Verniciatura + Componenti) × 2

### 5. **SISTEMA PREZZI**
- **Formule Personalizzate**: Per ogni tipo di bicicletta
- **IVA Configurabile**: Inclusione/esclusione
- **Arrotondamento**: A cifra tonda
- **Storico Calcoli**: Tracciamento prezzi

---

## 📁 STRUTTURA PROGETTO

```
gestionale-v1.0/
├── main.py                          # Entry point principale
├── icon_manager.py                  # Gestione icone
├── avvia.bat                       # Script avvio rapido
├── installa_e_avvia.bat            # Script installazione
├── requirements.txt                # Dipendenze Python
├── sounds/                         # File audio
│   ├── bell.wav, chain.wav, etc.
│   └── README.md
├── data/                          # Database SQLite
│   ├── *.db files
│   └── backup_progetto/
├── src/                           # Codice sorgente
│   ├── audio/                     # Sistema audio
│   ├── components/                # Componenti UI
│   ├── config/                    # Configurazioni
│   ├── design/                    # Design system
│   ├── gui/                       # Interfacce grafiche
│   ├── modules/                   # Logica business
│   ├── optimization/              # Ottimizzazioni
│   └── utils/                     # Utility
└── logs/                          # File di log
```

---

## 🎵 SISTEMI AVANZATI

### **Sistema Audio**
- **11 Suoni Base**: Campanello, catena, freni, cambio, etc.
- **Feedback UI**: Suoni per click, success, error
- **Volume Configurabile**: Controllo individuale
- **Riproduzione Asincrona**: Non blocca l'interfaccia

### **Design System**
- **Colori Professionali**: Palette coerente
- **Tipografia**: Font ottimizzati per leggibilità
- **Componenti Riutilizzabili**: Button, Card, Form, Table
- **Temi**: Supporto per temi personalizzati

### **Sistema Ottimizzazione**
- **Monitoraggio Performance**: CPU, RAM, Disco
- **Cache Intelligente**: TTL e gestione automatica
- **Lazy Loading**: Caricamento on-demand
- **Cleanup Automatico**: Pulizia risorse

### **Configurazione Avanzata**
- **Multi-Livello**: UI, Audio, Performance, Database
- **Backup Automatico**: Salvataggio configurazioni
- **Import/Export**: Condivisione impostazioni
- **Validazione**: Controllo parametri

---

## 🔧 TROUBLESHOOTING

### **Errori Comuni**

#### 1. **"No module named 'pygame'"**
```bash
pip install pygame
```

#### 2. **"No module named 'psutil'"**
```bash
pip install psutil
```

#### 3. **"No module named 'scipy'"**
```bash
pip install scipy
```

#### 4. **"ImportError: attempted relative import"**
- Verificare che si stia eseguendo dalla directory principale
- Controllare che tutti i file `__init__.py` siano presenti

#### 5. **"pygame.error: mixer not initialized"**
- Errore normale durante la chiusura
- Non influisce sul funzionamento

### **File Audio Mancanti**
- I file audio mancanti sono normali
- Il sistema funziona con i file base presenti
- Suoni aggiuntivi possono essere aggiunti in `sounds/`

### **Performance**
- Per PC con poca RAM: Ridurre cache in configurazioni
- Per PC lenti: Disabilitare suoni in configurazioni
- Monitoraggio attivo in tempo reale

---

## 📊 CHANGELOG

### **v1.0.0 - 2024**
- ✅ **Sistema Base**: Biciclette usate e ricondizionate
- ✅ **Workflow Restauro**: Processo completo
- ✅ **Bici Artigianali**: Assemblaggio personalizzato
- ✅ **Sistema Audio**: 11 suoni immersivi
- ✅ **Design System**: Componenti professionali
- ✅ **Ottimizzazione**: Performance avanzate
- ✅ **Configurazione**: Sistema multi-livello
- ✅ **Database**: SQLite con backup automatico
- ✅ **UI/UX**: Interfaccia moderna e intuitiva

---

## 🚀 CREAZIONE ESEGUIBILE

### **Prerequisiti**
- ✅ Progetto completamente finito
- ✅ Tutte le librerie installate
- ✅ Test completati e funzionanti

### **Creazione Exe**
```bash
# Metodo 1: Script automatico
crea_exe.bat

# Metodo 2: Script Python
python build_exe.py

# Metodo 3: Comando manuale
pyinstaller --onefile --windowed --name=GestionaleBiciclette --icon=assets/icon.ico --add-data=sounds;sounds --add-data=data;data main.py
```

### **Risultato**
- **File**: `dist/GestionaleBiciclette.exe`
- **Dimensione**: ~50-100 MB
- **Tipo**: Standalone (non richiede Python)
- **Compatibilità**: Windows 10/11

### **Distribuzione**
1. Copia `GestionaleBiciclette.exe`
2. Esegui l'eseguibile
3. L'applicazione si avvia automaticamente

---

## 🎯 PROSSIMI SVILUPPI

### **Funzionalità Future**
- 📱 **App Mobile**: Sincronizzazione cloud
- 🌐 **Web Interface**: Accesso browser
- 📊 **Reportistica**: Grafici e statistiche
- 🔄 **Sincronizzazione**: Multi-dispositivo
- 🎨 **Temi Personalizzati**: Editor temi
- 🔊 **Suoni Personalizzati**: Upload audio

### **Miglioramenti Tecnici**
- 🚀 **Performance**: Ottimizzazioni avanzate
- 🔒 **Sicurezza**: Crittografia dati
- 📈 **Scalabilità**: Supporto multi-utente
- 🌍 **Internazionalizzazione**: Multi-lingua

---

## 📞 SUPPORTO

### **Documentazione**
- Questo file contiene tutte le informazioni necessarie
- I log sono disponibili in `logs/`
- Le configurazioni sono in `src/config/`

### **Manutenzione**
- **Backup**: Automatico in `data/backup_progetto/`
- **Log**: Rotazione automatica
- **Database**: Ottimizzazione periodica

---

## 🏆 CREDITI

**Gestionale Biciclette v1.0** è stato sviluppato con:
- **Python 3.11+**
- **CustomTkinter** per l'interfaccia
- **Pygame** per l'audio
- **SQLite** per i dati
- **Design System** personalizzato

---

*Ultimo aggiornamento: 2024*
*Versione: 1.0.0*
*Stato: Produzione*
