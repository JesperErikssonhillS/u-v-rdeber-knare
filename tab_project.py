import tkinter as tk
from tkinter import ttk, messagebox

class TabProject:
    def __init__(self, parent, app_data):
        self.parent = parent
        self.app_data = app_data
        
        frame_proj = ttk.LabelFrame(parent, text="Projektdetaljer", padding=10)
        frame_proj.pack(fill="x", padx=15, pady=15)
        
        frame_proj.columnconfigure(4, weight=1)
        ttk.Button(frame_proj, text="❓ Guide", command=self.show_guide).grid(row=0, column=4, rowspan=3, sticky="ne", padx=(10,0))
        
        ttk.Label(frame_proj, text="Företag:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_proj, textvariable=self.app_data["company_var"], width=20).grid(row=0, column=1, padx=(0,15), pady=2)

        ttk.Label(frame_proj, text="Projektnamn:").grid(row=0, column=2, sticky="w")
        ttk.Entry(frame_proj, textvariable=self.app_data["proj_name_var"], width=20).grid(row=0, column=3, pady=2)
        
        ttk.Label(frame_proj, text="Projektnr:").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame_proj, textvariable=self.app_data["proj_num_var"], width=20).grid(row=1, column=1, padx=(0,15), pady=2)
        
        ttk.Label(frame_proj, text="Signatur:").grid(row=1, column=2, sticky="w")
        ttk.Entry(frame_proj, textvariable=self.app_data["sig_var"], width=20).grid(row=1, column=3, pady=2)
        
        ttk.Label(frame_proj, text="Kund:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame_proj, textvariable=self.app_data["kund_var"], width=20).grid(row=2, column=1, padx=(0,15), pady=2)

    def show_guide(self):
        messagebox.showinfo(
            "Guide: Projektdetaljer",
            "Välkommen till Hillstatik Byggfysik!\n\n"
            "Här på första sidan fyller du i grundläggande information om ditt projekt.\n\n"
            "Dessa fält sparas i din projektfil (.json) och används för att automatiskt skapa ett prydligt sidhuvud på de PDF-rapporter som programmet genererar. Det skapar tydlighet när dina beräkningar ska redovisas för kund eller kommun."
        )