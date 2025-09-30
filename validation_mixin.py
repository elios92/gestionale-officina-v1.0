"""
Validation Mixin

Mixin per validazioni comuni che riduce la duplicazione di codice di validazione
in tutto il gestionale.

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from src.utils.logger import logger


class ValidationMixin:
    """Mixin per validazioni comuni"""
    
    # ===== VALIDAZIONI CAMPI OBBLIGATORI =====
    
    def validate_required_fields(self, fields_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida che tutti i campi obbligatori siano compilati
        
        Args:
            fields_dict: Dizionario {nome_campo: valore}
            
        Returns:
            Tupla (tutti_validi, lista_errori)
        """
        errors = []
        
        for field_name, value in fields_dict.items():
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"Il campo '{field_name}' è obbligatorio")
        
        return len(errors) == 0, errors
    
    def validate_required_widgets(self, widgets_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida widget con metodo get() (Entry, Textbox, etc.)
        
        Args:
            widgets_dict: Dizionario {nome_campo: widget}
            
        Returns:
            Tupla (tutti_validi, lista_errori)
        """
        errors = []
        
        for field_name, widget in widgets_dict.items():
            if widget and hasattr(widget, 'get'):
                value = widget.get()
                if not value or (isinstance(value, str) and not value.strip()):
                    errors.append(f"Il campo '{field_name}' è obbligatorio")
        
        return len(errors) == 0, errors
    
    # ===== VALIDAZIONI FORMATO =====
    
    def validate_email(self, email: str) -> bool:
        """
        Valida formato email
        
        Args:
            email: Email da validare
            
        Returns:
            True se valida
        """
        if not email:
            return True  # Email opzionale
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_phone(self, phone: str) -> bool:
        """
        Valida formato telefono italiano
        
        Args:
            phone: Telefono da validare
            
        Returns:
            True se valido
        """
        if not phone:
            return True  # Telefono opzionale
        
        # Rimuovi spazi e caratteri speciali
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Pattern per telefoni italiani
        patterns = [
            r'^\+39\d{10}$',  # +39xxxxxxxxxx
            r'^39\d{10}$',    # 39xxxxxxxxxx
            r'^0\d{9,10}$',   # 0xxxxxxxxx o 0xxxxxxxxxx
            r'^\d{10}$'       # xxxxxxxxxx
        ]
        
        return any(re.match(pattern, clean_phone) for pattern in patterns)
    
    def validate_cap(self, cap: str) -> bool:
        """
        Valida CAP italiano
        
        Args:
            cap: CAP da validare
            
        Returns:
            True se valido
        """
        if not cap:
            return True  # CAP opzionale
        
        # CAP italiano: 5 cifre
        return bool(re.match(r'^\d{5}$', cap.strip()))
    
    def validate_cf(self, cf: str) -> bool:
        """
        Valida Codice Fiscale italiano
        
        Args:
            cf: Codice Fiscale da validare
            
        Returns:
            True se valido
        """
        if not cf:
            return True  # CF opzionale
        
        cf = cf.strip().upper()
        
        # Lunghezza corretta
        if len(cf) != 16:
            return False
        
        # Pattern: 6 lettere + 2 cifre + 1 lettera + 2 cifre + 1 lettera + 3 cifre + 1 lettera
        pattern = r'^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$'
        return bool(re.match(pattern, cf))
    
    def validate_partita_iva(self, piva: str) -> bool:
        """
        Valida Partita IVA italiana
        
        Args:
            piva: Partita IVA da validare
            
        Returns:
            True se valida
        """
        if not piva:
            return True  # P.IVA opzionale
        
        piva = piva.strip()
        
        # Lunghezza corretta
        if len(piva) != 11:
            return False
        
        # Solo cifre
        if not piva.isdigit():
            return False
        
        # Algoritmo di controllo P.IVA italiana
        try:
            # Calcola cifra di controllo
            somma = 0
            for i in range(10):
                cifra = int(piva[i])
                if i % 2 == 1:  # Posizioni dispari (1, 3, 5, 7, 9)
                    cifra *= 2
                    if cifra > 9:
                        cifra = cifra // 10 + cifra % 10
                somma += cifra
            
            resto = somma % 10
            cifra_controllo = (10 - resto) % 10
            
            return cifra_controllo == int(piva[10])
        except:
            return False
    
    # ===== VALIDAZIONI NUMERICHE =====
    
    def validate_positive_number(self, value: Any, field_name: str = "Valore") -> Tuple[bool, str]:
        """
        Valida che un valore sia un numero positivo
        
        Args:
            value: Valore da validare
            field_name: Nome del campo per messaggi errore
            
        Returns:
            Tupla (valido, messaggio_errore)
        """
        try:
            num = float(value)
            if num < 0:
                return False, f"{field_name} deve essere positivo"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} deve essere un numero valido"
    
    def validate_positive_integer(self, value: Any, field_name: str = "Valore") -> Tuple[bool, str]:
        """
        Valida che un valore sia un intero positivo
        
        Args:
            value: Valore da validare
            field_name: Nome del campo per messaggi errore
            
        Returns:
            Tupla (valido, messaggio_errore)
        """
        try:
            num = int(value)
            if num < 0:
                return False, f"{field_name} deve essere positivo"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} deve essere un numero intero valido"
    
    def validate_percentage(self, value: Any, field_name: str = "Percentuale") -> Tuple[bool, str]:
        """
        Valida che un valore sia una percentuale (0-100)
        
        Args:
            value: Valore da validare
            field_name: Nome del campo per messaggi errore
            
        Returns:
            Tupla (valido, messaggio_errore)
        """
        try:
            num = float(value)
            if num < 0 or num > 100:
                return False, f"{field_name} deve essere tra 0 e 100"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} deve essere un numero valido"
    
    def validate_price(self, value: Any, field_name: str = "Prezzo") -> Tuple[bool, str]:
        """
        Valida che un valore sia un prezzo valido
        
        Args:
            value: Valore da validare
            field_name: Nome del campo per messaggi errore
            
        Returns:
            Tupla (valido, messaggio_errore)
        """
        try:
            price = float(value)
            if price < 0:
                return False, f"{field_name} non può essere negativo"
            if price > 999999.99:
                return False, f"{field_name} troppo elevato"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} deve essere un numero valido"
    
    # ===== VALIDAZIONI STRINGHE =====
    
    def validate_string_length(self, value: str, min_length: int = 0, max_length: int = 255, field_name: str = "Campo") -> Tuple[bool, str]:
        """
        Valida lunghezza di una stringa
        
        Args:
            value: Stringa da validare
            min_length: Lunghezza minima
            max_length: Lunghezza massima
            field_name: Nome del campo per messaggi errore
            
        Returns:
            Tupla (valido, messaggio_errore)
        """
        if not isinstance(value, str):
            return False, f"{field_name} deve essere una stringa"
        
        length = len(value.strip())
        
        if length < min_length:
            return False, f"{field_name} deve essere di almeno {min_length} caratteri"
        
        if length > max_length:
            return False, f"{field_name} non può superare {max_length} caratteri"
        
        return True, ""
    
    def validate_alphanumeric(self, value: str, field_name: str = "Campo") -> Tuple[bool, str]:
        """
        Valida che una stringa contenga solo caratteri alfanumerici
        
        Args:
            value: Stringa da validare
            field_name: Nome del campo per messaggi errore
            
        Returns:
            Tupla (valido, messaggio_errore)
        """
        if not value:
            return True, ""
        
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', value):
            return False, f"{field_name} può contenere solo lettere, numeri, spazi, trattini e underscore"
        
        return True, ""
    
    # ===== VALIDAZIONI COMPOSTE =====
    
    def validate_form_data(self, form_data: Dict[str, Any], validation_rules: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Valida dati di un form con regole personalizzate
        
        Args:
            form_data: Dati del form {campo: valore}
            validation_rules: Regole di validazione {
                'campo': {
                    'required': bool,
                    'type': str,  # 'email', 'phone', 'number', 'string', etc.
                    'min_length': int,
                    'max_length': int,
                    'min_value': float,
                    'max_value': float
                }
            }
            
        Returns:
            Tupla (tutti_validi, lista_errori)
        """
        errors = []
        
        for field_name, rules in validation_rules.items():
            value = form_data.get(field_name, "")
            
            # Controllo obbligatorietà
            if rules.get('required', False) and (not value or (isinstance(value, str) and not value.strip())):
                errors.append(f"Il campo '{field_name}' è obbligatorio")
                continue
            
            # Se il campo è vuoto e non obbligatorio, salta le altre validazioni
            if not value or (isinstance(value, str) and not value.strip()):
                continue
            
            # Validazioni specifiche per tipo
            field_type = rules.get('type', 'string')
            
            if field_type == 'email':
                if not self.validate_email(value):
                    errors.append(f"Email non valida per il campo '{field_name}'")
            
            elif field_type == 'phone':
                if not self.validate_phone(value):
                    errors.append(f"Telefono non valido per il campo '{field_name}'")
            
            elif field_type == 'number':
                valid, msg = self.validate_positive_number(value, field_name)
                if not valid:
                    errors.append(msg)
            
            elif field_type == 'string':
                min_len = rules.get('min_length', 0)
                max_len = rules.get('max_length', 255)
                valid, msg = self.validate_string_length(value, min_len, max_len, field_name)
                if not valid:
                    errors.append(msg)
        
        return len(errors) == 0, errors
    
    # ===== UTILITY =====
    
    def show_validation_errors(self, errors: List[str], title: str = "Errori di Validazione"):
        """
        Mostra errori di validazione in un messagebox
        
        Args:
            errors: Lista errori
            title: Titolo del messagebox
        """
        if errors:
            try:
                import tkinter.messagebox as messagebox
                error_text = "\n".join(f"• {error}" for error in errors)
                messagebox.showerror(title, error_text)
            except ImportError:
                logger.error(f"Errori validazione: {errors}")
    
    def log_validation_error(self, field_name: str, error: str, context: str = ""):
        """
        Logga un errore di validazione
        
        Args:
            field_name: Nome del campo
            error: Messaggio di errore
            context: Contesto aggiuntivo
        """
        logger.warning(f"Validazione fallita - {field_name}: {error} {context}")
