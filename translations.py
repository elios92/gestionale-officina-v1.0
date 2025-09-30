"""
Sistema di traduzione multilingua per il Gestionale Biciclette.

Gestisce le traduzioni per:
- Italiano (default)
- English
- Español
- Français

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import os
import json
from typing import Dict, Any


class TranslationManager:
    """Gestore delle traduzioni multilingua"""

    def __init__(self):
        """Inizializza il gestore traduzioni"""
        self.current_language = "it"
        self.translations = {}
        self._load_translations()

    def _load_translations(self):
        """Carica tutte le traduzioni"""
        try:
            # Traduzioni hardcoded per semplicità
            self.translations = {
                "it": self._get_italian_translations(),
                "en": self._get_english_translations(),
                "es": self._get_spanish_translations(),
                "fr": self._get_french_translations()
            }
        except Exception as e:
            print(f"Errore nel caricamento traduzioni: {e}")
            # Fallback all'italiano
            self.translations = {"it": self._get_italian_translations()}

    def set_language(self, language: str):
        """Imposta la lingua corrente"""
        if language in self.translations:
            self.current_language = language
        else:
            print(f"Lingua {language} non supportata, uso italiano")
            self.current_language = "it"

    def get_text(self, key: str, **kwargs) -> str:
        """Ottiene il testo tradotto per la chiave data"""
        try:
            # Naviga nella struttura delle traduzioni
            keys = key.split('.')
            text = self.translations[self.current_language]
            
            for k in keys:
                text = text[k]
            
            # Sostituisce i placeholder se presenti
            if kwargs:
                text = text.format(**kwargs)
            
            return text
        except (KeyError, TypeError):
            # Fallback alla chiave stessa se non trovata
            return key

    def _get_italian_translations(self) -> Dict[str, Any]:
        """Traduzioni italiane (default)"""
        return {
            "app": {
                "title": "Gestionale Biciclette",
                "welcome": "Benvenuto nel Gestionale Biciclette!",
                "thanks": "Grazie per aver scaricato la nostra applicazione!",
                "dashboard": "Dashboard Gestionale"
            },
            "menu": {
                "file": "File",
                "edit": "Modifica",
                "view": "Visualizza",
                "finances": "Finanze",
                "orders": "Ordini",
                "help": "Aiuto",
                "new_work": "Nuovo Lavoro",
                "open": "Apri",
                "save": "Salva",
                "export": "Esporta",
                "settings": "Impostazioni",
                "exit": "Esci"
            },
            "dashboard": {
                "warehouse": "MAGAZZINO",
                "bikes_sale": "BICI IN VENDITA",
                "new_work": "NUOVO LAVORO",
                "quick_stats": "STATISTICHE RAPIDE",
                "quick_guide": "GUIDA RAPIDA",
                "open_warehouse": "Apri Magazzino",
                "open_catalog": "Apri Catalogo",
                "new_work_btn": "Nuovo Lavoro",
                "how_to_start": "Come Iniziare",
                "settings_btn": "Impostazioni",
                "active_customers": "Clienti Attivi",
                "monthly_revenue": "Fatturato Mensile",
                "products_stock": "Prodotti in Stock",
                "work_in_progress": "Lavori in Corso"
            },
            "settings": {
                "title": "Impostazioni",
                "general": "Generale",
                "appearance": "Aspetto",
                "system": "Sistema",
                "advanced": "Avanzate",
                "backup": "Backup",
                "company_name": "Nome Azienda",
                "company_placeholder": "Inserisci il nome della tua azienda",
                "theme": "Tema",
                "language": "Lingua",
                "icon": "Icona Applicazione",
                "choose_icon": "Scegli Icona",
                "reset_icon": "Reset",
                "font": "Font",
                "font_family": "Famiglia Font",
                "font_size": "Dimensione",
                "window_size": "Dimensioni Finestra",
                "auto_backup": "Backup Automatico",
                "enable_auto_backup": "Abilita backup automatico",
                "notifications": "Notifiche",
                "enable_notifications": "Abilita notifiche sistema",
                "maintenance": "Manutenzione",
                "clean_database": "Pulisci Database",
                "technical_config": "Configurazioni Tecniche",
                "debug_mode": "Modalità debug",
                "log_level": "Livello Log",
                "reset": "Reset",
                "reset_all_settings": "Reset Tutte le Impostazioni",
                "backup_info": "Informazioni Backup",
                "backup_description": "Il sistema di backup automatico protegge i tuoi dati:\n• Backup automatico ogni avvio\n• Ripristino automatico file mancanti\n• Pulizia file duplicati e temporanei\n• Verifica integrità database",
                "create_manual_backup": "Crea Backup Manuale",
                "cleanup_duplicates": "Pulizia Duplicati",
                "save_settings": "Salva Impostazioni",
                "cancel": "Annulla"
            },
            "guide": {
                "title": "Guida Rapida",
                "main_menu": "Menu Principale",
                "main_menu_desc": "• File: Nuovo lavoro, Apri, Salva, Esporta\n• Modifica: Annulla, Ripeti, Taglia, Copia, Incolla\n• Visualizza: Gestione Biciclette, Ordini, Finanze\n• Finanze: Dashboard, Fatture, Entrate, Uscite\n• Ordini: Nuovo Ordine, Inventario, Statistiche\n• Aiuto: Informazioni sull'applicazione",
                "customer_management": "Gestione Clienti",
                "customer_management_desc": "Accedi dal menu Visualizza per gestire:\n• Anagrafica clienti\n• Dati di contatto\n• Storico riparazioni\n• Fatture emesse",
                "new_work": "Nuovo Lavoro",
                "new_work_desc": "Dal menu File > Nuovo lavoro puoi creare:\n• Riparazioni e manutenzioni\n• Gestione biciclette\n• Preventivi e fatture",
                "settings_desc": "Personalizza l'applicazione:\n• Nome azienda\n• Tema e aspetto\n• Backup automatico\n• Configurazioni sistema",
                "start_working": "Inizia a Lavorare",
                "disable_guide": "Disabilita Guida"
            },
            "first_launch": {
                "title": "Benvenuto nel Gestionale Biciclette!",
                "thanks": "Grazie per aver scaricato la nostra applicazione!",
                "app_info": "Informazioni sull'Applicazione",
                "app_description": "Il Gestionale Biciclette è un sistema completo per la gestione\ndel tuo negozio di biciclette. Include:\n\n• Gestione clienti e anagrafica\n• Gestione riparazioni e manutenzioni\n• Catalogo e vendita biciclette\n• Sistema di fatturazione\n• Report e statistiche\n• Backup automatico dei dati",
                "start_using": "Inizia a Usare l'Applicazione",
                "settings": "Impostazioni"
            },
            "messages": {
                "success": "Successo",
                "error": "Errore",
                "info": "Info",
                "confirm": "Conferma",
                "settings_saved": "Impostazioni salvate con successo!",
                "icon_changed": "Icona cambiata con successo!",
                "icon_reset": "Icona resettata al default!",
                "backup_created": "Backup manuale creato con successo!",
                "cleanup_completed": "Pulizia completata con successo!",
                "changes_cancelled": "Modifiche annullate",
                "clean_database_confirm": "Vuoi pulire il database? Questa operazione non può essere annullata.",
                "reset_settings_confirm": "Vuoi resettare tutte le impostazioni? Questa operazione non può essere annullata.",
                "cleanup_duplicates_confirm": "Vuoi pulire i file duplicati e in eccesso?",
                "feature_development": "Funzionalità in fase di sviluppo"
            }
        }

    def _get_english_translations(self) -> Dict[str, Any]:
        """Traduzioni inglesi"""
        return {
            "app": {
                "title": "Bicycle Management System",
                "welcome": "Welcome to the Bicycle Management System!",
                "thanks": "Thank you for downloading our application!",
                "dashboard": "Management Dashboard"
            },
            "menu": {
                "file": "File",
                "edit": "Edit",
                "view": "View",
                "finances": "Finances",
                "orders": "Orders",
                "help": "Help",
                "new_work": "New Work",
                "open": "Open",
                "save": "Save",
                "export": "Export",
                "settings": "Settings",
                "exit": "Exit"
            },
            "dashboard": {
                "warehouse": "WAREHOUSE",
                "bikes_sale": "BIKES FOR SALE",
                "new_work": "NEW WORK",
                "quick_stats": "QUICK STATISTICS",
                "quick_guide": "QUICK GUIDE",
                "open_warehouse": "Open Warehouse",
                "open_catalog": "Open Catalog",
                "new_work_btn": "New Work",
                "how_to_start": "How to Start",
                "settings_btn": "Settings",
                "active_customers": "Active Customers",
                "monthly_revenue": "Monthly Revenue",
                "products_stock": "Products in Stock",
                "work_in_progress": "Work in Progress"
            },
            "settings": {
                "title": "Settings",
                "general": "General",
                "appearance": "Appearance",
                "system": "System",
                "advanced": "Advanced",
                "backup": "Backup",
                "company_name": "Company Name",
                "company_placeholder": "Enter your company name",
                "theme": "Theme",
                "language": "Language",
                "icon": "Application Icon",
                "choose_icon": "Choose Icon",
                "reset_icon": "Reset",
                "font": "Font",
                "font_family": "Font Family",
                "font_size": "Size",
                "window_size": "Window Size",
                "auto_backup": "Automatic Backup",
                "enable_auto_backup": "Enable automatic backup",
                "notifications": "Notifications",
                "enable_notifications": "Enable system notifications",
                "maintenance": "Maintenance",
                "clean_database": "Clean Database",
                "technical_config": "Technical Configurations",
                "debug_mode": "Debug mode",
                "log_level": "Log Level",
                "reset": "Reset",
                "reset_all_settings": "Reset All Settings",
                "backup_info": "Backup Information",
                "backup_description": "The automatic backup system protects your data:\n• Automatic backup on startup\n• Automatic restoration of missing files\n• Cleanup of duplicate and temporary files\n• Database integrity verification",
                "create_manual_backup": "Create Manual Backup",
                "cleanup_duplicates": "Cleanup Duplicates",
                "save_settings": "Save Settings",
                "cancel": "Cancel"
            },
            "guide": {
                "title": "Quick Guide",
                "main_menu": "Main Menu",
                "main_menu_desc": "• File: New work, Open, Save, Export\n• Edit: Undo, Redo, Cut, Copy, Paste\n• View: Bicycle Management, Orders, Finances\n• Finances: Dashboard, Invoices, Income, Expenses\n• Orders: New Order, Inventory, Statistics\n• Help: Application information",
                "customer_management": "Customer Management",
                "customer_management_desc": "Access from View menu to manage:\n• Customer records\n• Contact information\n• Repair history\n• Issued invoices",
                "new_work": "New Work",
                "new_work_desc": "From File > New work you can create:\n• Repairs and maintenance\n• Bicycle management\n• Quotes and invoices",
                "settings_desc": "Customize the application:\n• Company name\n• Theme and appearance\n• Automatic backup\n• System configurations",
                "start_working": "Start Working",
                "disable_guide": "Disable Guide"
            },
            "first_launch": {
                "title": "Welcome to the Bicycle Management System!",
                "thanks": "Thank you for downloading our application!",
                "app_info": "Application Information",
                "app_description": "The Bicycle Management System is a complete solution for managing\nyour bicycle shop. It includes:\n\n• Customer and contact management\n• Repair and maintenance management\n• Bicycle catalog and sales\n• Invoicing system\n• Reports and statistics\n• Automatic data backup",
                "start_using": "Start Using the Application",
                "settings": "Settings"
            },
            "messages": {
                "success": "Success",
                "error": "Error",
                "info": "Info",
                "confirm": "Confirm",
                "settings_saved": "Settings saved successfully!",
                "icon_changed": "Icon changed successfully!",
                "icon_reset": "Icon reset to default!",
                "backup_created": "Manual backup created successfully!",
                "cleanup_completed": "Cleanup completed successfully!",
                "changes_cancelled": "Changes cancelled",
                "clean_database_confirm": "Do you want to clean the database? This operation cannot be undone.",
                "reset_settings_confirm": "Do you want to reset all settings? This operation cannot be undone.",
                "cleanup_duplicates_confirm": "Do you want to clean duplicate and excess files?",
                "feature_development": "Feature under development"
            }
        }

    def _get_spanish_translations(self) -> Dict[str, Any]:
        """Traduzioni spagnole"""
        return {
            "app": {
                "title": "Sistema de Gestión de Bicicletas",
                "welcome": "¡Bienvenido al Sistema de Gestión de Bicicletas!",
                "thanks": "¡Gracias por descargar nuestra aplicación!",
                "dashboard": "Panel de Gestión"
            },
            "menu": {
                "file": "Archivo",
                "edit": "Editar",
                "view": "Ver",
                "finances": "Finanzas",
                "orders": "Pedidos",
                "help": "Ayuda",
                "new_work": "Nuevo Trabajo",
                "open": "Abrir",
                "save": "Guardar",
                "export": "Exportar",
                "settings": "Configuración",
                "exit": "Salir"
            },
            "dashboard": {
                "warehouse": "ALMACÉN",
                "bikes_sale": "BICICLETAS EN VENTA",
                "new_work": "NUEVO TRABAJO",
                "quick_stats": "ESTADÍSTICAS RÁPIDAS",
                "quick_guide": "GUÍA RÁPIDA",
                "open_warehouse": "Abrir Almacén",
                "open_catalog": "Abrir Catálogo",
                "new_work_btn": "Nuevo Trabajo",
                "how_to_start": "Cómo Empezar",
                "settings_btn": "Configuración",
                "active_customers": "Clientes Activos",
                "monthly_revenue": "Ingresos Mensuales",
                "products_stock": "Productos en Stock",
                "work_in_progress": "Trabajos en Curso"
            },
            "settings": {
                "title": "Configuración",
                "general": "General",
                "appearance": "Apariencia",
                "system": "Sistema",
                "advanced": "Avanzado",
                "backup": "Respaldo",
                "company_name": "Nombre de la Empresa",
                "company_placeholder": "Ingrese el nombre de su empresa",
                "theme": "Tema",
                "language": "Idioma",
                "icon": "Icono de la Aplicación",
                "choose_icon": "Elegir Icono",
                "reset_icon": "Restablecer",
                "font": "Fuente",
                "font_family": "Familia de Fuente",
                "font_size": "Tamaño",
                "window_size": "Tamaño de Ventana",
                "auto_backup": "Respaldo Automático",
                "enable_auto_backup": "Habilitar respaldo automático",
                "notifications": "Notificaciones",
                "enable_notifications": "Habilitar notificaciones del sistema",
                "maintenance": "Mantenimiento",
                "clean_database": "Limpiar Base de Datos",
                "technical_config": "Configuraciones Técnicas",
                "debug_mode": "Modo de depuración",
                "log_level": "Nivel de Registro",
                "reset": "Restablecer",
                "reset_all_settings": "Restablecer Todas las Configuraciones",
                "backup_info": "Información de Respaldo",
                "backup_description": "El sistema de respaldo automático protege sus datos:\n• Respaldo automático en cada inicio\n• Restauración automática de archivos faltantes\n• Limpieza de archivos duplicados y temporales\n• Verificación de integridad de la base de datos",
                "create_manual_backup": "Crear Respaldo Manual",
                "cleanup_duplicates": "Limpiar Duplicados",
                "save_settings": "Guardar Configuración",
                "cancel": "Cancelar"
            },
            "guide": {
                "title": "Guía Rápida",
                "main_menu": "Menú Principal",
                "main_menu_desc": "• Archivo: Nuevo trabajo, Abrir, Guardar, Exportar\n• Editar: Deshacer, Rehacer, Cortar, Copiar, Pegar\n• Ver: Gestión de Bicicletas, Pedidos, Finanzas\n• Finanzas: Panel, Facturas, Ingresos, Gastos\n• Pedidos: Nuevo Pedido, Inventario, Estadísticas\n• Ayuda: Información de la aplicación",
                "customer_management": "Gestión de Clientes",
                "customer_management_desc": "Acceda desde el menú Ver para gestionar:\n• Registros de clientes\n• Información de contacto\n• Historial de reparaciones\n• Facturas emitidas",
                "new_work": "Nuevo Trabajo",
                "new_work_desc": "Desde Archivo > Nuevo trabajo puede crear:\n• Reparaciones y mantenimiento\n• Gestión de bicicletas\n• Cotizaciones y facturas",
                "settings_desc": "Personalice la aplicación:\n• Nombre de la empresa\n• Tema y apariencia\n• Respaldo automático\n• Configuraciones del sistema",
                "start_working": "Comenzar a Trabajar",
                "disable_guide": "Deshabilitar Guía"
            },
            "first_launch": {
                "title": "¡Bienvenido al Sistema de Gestión de Bicicletas!",
                "thanks": "¡Gracias por descargar nuestra aplicación!",
                "app_info": "Información de la Aplicación",
                "app_description": "El Sistema de Gestión de Bicicletas es una solución completa para gestionar\ntu tienda de bicicletas. Incluye:\n\n• Gestión de clientes y contactos\n• Gestión de reparaciones y mantenimiento\n• Catálogo y venta de bicicletas\n• Sistema de facturación\n• Reportes y estadísticas\n• Respaldo automático de datos",
                "start_using": "Comenzar a Usar la Aplicación",
                "settings": "Configuración"
            },
            "messages": {
                "success": "Éxito",
                "error": "Error",
                "info": "Info",
                "confirm": "Confirmar",
                "settings_saved": "¡Configuración guardada exitosamente!",
                "icon_changed": "¡Icono cambiado exitosamente!",
                "icon_reset": "¡Icono restablecido al predeterminado!",
                "backup_created": "¡Respaldo manual creado exitosamente!",
                "cleanup_completed": "¡Limpieza completada exitosamente!",
                "changes_cancelled": "Cambios cancelados",
                "clean_database_confirm": "¿Desea limpiar la base de datos? Esta operación no se puede deshacer.",
                "reset_settings_confirm": "¿Desea restablecer todas las configuraciones? Esta operación no se puede deshacer.",
                "cleanup_duplicates_confirm": "¿Desea limpiar archivos duplicados y en exceso?",
                "feature_development": "Funcionalidad en desarrollo"
            }
        }

    def _get_french_translations(self) -> Dict[str, Any]:
        """Traduzioni francesi"""
        return {
            "app": {
                "title": "Système de Gestion de Vélos",
                "welcome": "Bienvenue dans le Système de Gestion de Vélos !",
                "thanks": "Merci d'avoir téléchargé notre application !",
                "dashboard": "Tableau de Bord de Gestion"
            },
            "menu": {
                "file": "Fichier",
                "edit": "Modifier",
                "view": "Voir",
                "finances": "Finances",
                "orders": "Commandes",
                "help": "Aide",
                "new_work": "Nouveau Travail",
                "open": "Ouvrir",
                "save": "Enregistrer",
                "export": "Exporter",
                "settings": "Paramètres",
                "exit": "Quitter"
            },
            "dashboard": {
                "warehouse": "ENTREPÔT",
                "bikes_sale": "VÉLOS EN VENTE",
                "new_work": "NOUVEAU TRAVAIL",
                "quick_stats": "STATISTIQUES RAPIDES",
                "quick_guide": "GUIDE RAPIDE",
                "open_warehouse": "Ouvrir Entrepôt",
                "open_catalog": "Ouvrir Catalogue",
                "new_work_btn": "Nouveau Travail",
                "how_to_start": "Comment Commencer",
                "settings_btn": "Paramètres",
                "active_customers": "Clients Actifs",
                "monthly_revenue": "Revenus Mensuels",
                "products_stock": "Produits en Stock",
                "work_in_progress": "Travaux en Cours"
            },
            "settings": {
                "title": "Paramètres",
                "general": "Général",
                "appearance": "Apparence",
                "system": "Système",
                "advanced": "Avancé",
                "backup": "Sauvegarde",
                "company_name": "Nom de l'Entreprise",
                "company_placeholder": "Entrez le nom de votre entreprise",
                "theme": "Thème",
                "language": "Langue",
                "icon": "Icône de l'Application",
                "choose_icon": "Choisir Icône",
                "reset_icon": "Réinitialiser",
                "font": "Police",
                "font_family": "Famille de Police",
                "font_size": "Taille",
                "window_size": "Taille de Fenêtre",
                "auto_backup": "Sauvegarde Automatique",
                "enable_auto_backup": "Activer la sauvegarde automatique",
                "notifications": "Notifications",
                "enable_notifications": "Activer les notifications système",
                "maintenance": "Maintenance",
                "clean_database": "Nettoyer Base de Données",
                "technical_config": "Configurations Techniques",
                "debug_mode": "Mode débogage",
                "log_level": "Niveau de Journal",
                "reset": "Réinitialiser",
                "reset_all_settings": "Réinitialiser Tous les Paramètres",
                "backup_info": "Informations de Sauvegarde",
                "backup_description": "Le système de sauvegarde automatique protège vos données :\n• Sauvegarde automatique à chaque démarrage\n• Restauration automatique des fichiers manquants\n• Nettoyage des fichiers dupliqués et temporaires\n• Vérification de l'intégrité de la base de données",
                "create_manual_backup": "Créer Sauvegarde Manuelle",
                "cleanup_duplicates": "Nettoyer Doublons",
                "save_settings": "Enregistrer Paramètres",
                "cancel": "Annuler"
            },
            "guide": {
                "title": "Guide Rapide",
                "main_menu": "Menu Principal",
                "main_menu_desc": "• Fichier : Nouveau travail, Ouvrir, Enregistrer, Exporter\n• Modifier : Annuler, Rétablir, Couper, Copier, Coller\n• Voir : Gestion Vélos, Commandes, Finances\n• Finances : Tableau de bord, Factures, Revenus, Dépenses\n• Commandes : Nouvelle Commande, Inventaire, Statistiques\n• Aide : Informations sur l'application",
                "customer_management": "Gestion Clients",
                "customer_management_desc": "Accédez depuis le menu Voir pour gérer :\n• Dossiers clients\n• Informations de contact\n• Historique des réparations\n• Factures émises",
                "new_work": "Nouveau Travail",
                "new_work_desc": "Depuis Fichier > Nouveau travail vous pouvez créer :\n• Réparations et maintenance\n• Gestion des vélos\n• Devis et factures",
                "settings_desc": "Personnalisez l'application :\n• Nom de l'entreprise\n• Thème et apparence\n• Sauvegarde automatique\n• Configurations système",
                "start_working": "Commencer à Travailler",
                "disable_guide": "Désactiver Guide"
            },
            "first_launch": {
                "title": "Bienvenue dans le Système de Gestion de Vélos !",
                "thanks": "Merci d'avoir téléchargé notre application !",
                "app_info": "Informations sur l'Application",
                "app_description": "Le Système de Gestion de Vélos est une solution complète pour gérer\nvotre magasin de vélos. Il inclut :\n\n• Gestion des clients et contacts\n• Gestion des réparations et maintenance\n• Catalogue et vente de vélos\n• Système de facturation\n• Rapports et statistiques\n• Sauvegarde automatique des données",
                "start_using": "Commencer à Utiliser l'Application",
                "settings": "Paramètres"
            },
            "messages": {
                "success": "Succès",
                "error": "Erreur",
                "info": "Info",
                "confirm": "Confirmer",
                "settings_saved": "Paramètres enregistrés avec succès !",
                "icon_changed": "Icône changée avec succès !",
                "icon_reset": "Icône réinitialisée par défaut !",
                "backup_created": "Sauvegarde manuelle créée avec succès !",
                "cleanup_completed": "Nettoyage terminé avec succès !",
                "changes_cancelled": "Modifications annulées",
                "clean_database_confirm": "Voulez-vous nettoyer la base de données ? Cette opération ne peut pas être annulée.",
                "reset_settings_confirm": "Voulez-vous réinitialiser tous les paramètres ? Cette opération ne peut pas être annulée.",
                "cleanup_duplicates_confirm": "Voulez-vous nettoyer les fichiers dupliqués et en excès ?",
                "feature_development": "Fonctionnalité en développement"
            }
        }


# Istanza globale del gestore traduzioni
translation_manager = TranslationManager()
