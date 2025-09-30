"""
Theme Applier

Utilità per applicare il design system a componenti esistenti.

Autore: Gestionale Team
Versione: 1.0.0
Data: 2024
"""

import customtkinter as ctk
from typing import Dict, Any, Optional
from src.design.design_system import DesignSystem, IconSystem


class ThemeApplier:
    """Applicatore di temi per componenti esistenti"""
    
    @staticmethod
    def apply_button_theme(button: ctk.CTkButton, variant: str = "primary", size: str = "md"):
        """Applica il tema a un pulsante esistente"""
        style = DesignSystem.get_button_style(variant, size)
        
        # Applica le proprietà di stile
        for prop, value in style.items():
            if hasattr(button, 'configure'):
                try:
                    button.configure(**{prop: value})
                except Exception:
                    pass  # Ignora proprietà non supportate
    
    @staticmethod
    def apply_frame_theme(frame: ctk.CTkFrame, variant: str = "default"):
        """Applica il tema a un frame esistente"""
        style = DesignSystem.get_card_style(variant)
        
        for prop, value in style.items():
            if hasattr(frame, 'configure'):
                try:
                    frame.configure(**{prop: value})
                except Exception:
                    pass
    
    @staticmethod
    def apply_label_theme(
        label: ctk.CTkLabel, 
        size: str = "base", 
        weight: str = "normal",
        color: Optional[str] = None
    ):
        """Applica il tema a un'etichetta esistente"""
        font = DesignSystem.get_font(size, weight)
        
        if hasattr(label, 'configure'):
            label.configure(font=font)
            
            if color:
                text_color = DesignSystem.get_color(color.split('_')[0], color.split('_')[1] if '_' in color else '600')
                label.configure(text_color=text_color)
    
    @staticmethod
    def apply_entry_theme(entry: ctk.CTkEntry):
        """Applica il tema a un campo di input esistente"""
        style = DesignSystem.get_input_style()
        
        for prop, value in style.items():
            if hasattr(entry, 'configure'):
                try:
                    entry.configure(**{prop: value})
                except Exception:
                    pass
    
    @staticmethod
    def apply_modal_theme(modal: ctk.CTkToplevel):
        """Applica il tema a una modale esistente"""
        style = DesignSystem.get_modal_style()
        
        for prop, value in style.items():
            if hasattr(modal, 'configure'):
                try:
                    modal.configure(**{prop: value})
                except Exception:
                    pass
    
    @staticmethod
    def create_icon_label(parent, icon: str, text: str = "", **kwargs) -> ctk.CTkLabel:
        """Crea un'etichetta con icona"""
        icon_text = IconSystem.get_icon(icon)
        display_text = f"{icon_text} {text}" if text else icon_text
        
        return ctk.CTkLabel(
            parent,
            text=display_text,
            **kwargs
        )
    
    @staticmethod
    def create_section_header(parent, title: str, icon: Optional[str] = None) -> ctk.CTkFrame:
        """Crea un header di sezione"""
        header = ctk.CTkFrame(parent, fg_color=DesignSystem.get_color('primary', '50'))
        
        title_text = title
        if icon:
            title_text = f"{IconSystem.get_icon(icon)} {title}"
        
        title_label = ctk.CTkLabel(
            header,
            text=title_text,
            font=DesignSystem.get_font('lg', 'bold'),
            text_color=DesignSystem.get_color('primary', '800')
        )
        title_label.pack(padx=DesignSystem.get_spacing('md'), pady=DesignSystem.get_spacing('sm'))
        
        return header
    
    @staticmethod
    def create_info_panel(parent, title: str, content: str, icon: Optional[str] = None) -> ctk.CTkFrame:
        """Crea un pannello informativo"""
        panel = ctk.CTkFrame(parent, **DesignSystem.get_card_style('default'))
        
        # Header
        if title or icon:
            header = ctk.CTkFrame(panel, fg_color="transparent")
            header.pack(fill="x", padx=DesignSystem.get_spacing('md'), pady=DesignSystem.get_spacing('sm'))
            
            if icon:
                icon_label = ctk.CTkLabel(
                    header,
                    text=IconSystem.get_icon(icon),
                    font=DesignSystem.get_font('lg')
                )
                icon_label.pack(side="left", padx=(0, DesignSystem.get_spacing('sm')))
            
            if title:
                title_label = ctk.CTkLabel(
                    header,
                    text=title,
                    font=DesignSystem.get_font('md', 'bold'),
                    text_color=DesignSystem.get_color('primary', '700')
                )
                title_label.pack(side="left")
        
        # Contenuto
        if content:
            content_label = ctk.CTkLabel(
                panel,
                text=content,
                font=DesignSystem.get_font('sm'),
                text_color=DesignSystem.get_color('neutral', '600'),
                wraplength=300
            )
            content_label.pack(padx=DesignSystem.get_spacing('md'), pady=(0, DesignSystem.get_spacing('sm')))
        
        return panel
    
    @staticmethod
    def create_status_indicator(parent, status: str, text: str) -> ctk.CTkFrame:
        """Crea un indicatore di stato"""
        status_colors = {
            'success': DesignSystem.get_color('success', '600'),
            'warning': DesignSystem.get_color('warning', '600'),
            'error': DesignSystem.get_color('danger', '600'),
            'info': DesignSystem.get_color('info', '600')
        }
        
        status_icons = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'info': 'ℹ️'
        }
        
        indicator = ctk.CTkFrame(parent, fg_color="transparent")
        
        icon_label = ctk.CTkLabel(
            indicator,
            text=status_icons.get(status, ''),
            font=DesignSystem.get_font('md')
        )
        icon_label.pack(side="left", padx=(0, DesignSystem.get_spacing('sm')))
        
        text_label = ctk.CTkLabel(
            indicator,
            text=text,
            font=DesignSystem.get_font('sm', 'medium'),
            text_color=status_colors.get(status, DesignSystem.get_color('neutral', '600'))
        )
        text_label.pack(side="left")
        
        return indicator
    
    @staticmethod
    def create_progress_bar(parent, value: int = 0, max_value: int = 100) -> ctk.CTkProgressBar:
        """Crea una barra di progresso"""
        progress = ctk.CTkProgressBar(parent)
        progress.set(value / max_value)
        return progress
    
    @staticmethod
    def create_loading_spinner(parent, text: str = "Caricamento...") -> ctk.CTkFrame:
        """Crea un indicatore di caricamento"""
        spinner_frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        spinner_label = ctk.CTkLabel(
            spinner_frame,
            text="⏳",
            font=DesignSystem.get_font('lg')
        )
        spinner_label.pack(side="left", padx=(0, DesignSystem.get_spacing('sm')))
        
        text_label = ctk.CTkLabel(
            spinner_frame,
            text=text,
            font=DesignSystem.get_font('sm'),
            text_color=DesignSystem.get_color('neutral', '600')
        )
        text_label.pack(side="left")
        
        return spinner_frame
