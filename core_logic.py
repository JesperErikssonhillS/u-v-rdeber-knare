import os
import json
import tkinter as tk
from tkinter import messagebox

# =====================================================================
# DATABASLADDNING FRÅN EXTERNA FILER
# =====================================================================
def load_json_db(filename):
    if '__file__' in globals():
        base_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        base_dir = os.getcwd()
        
    filepath = os.path.join(base_dir, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        messagebox.showerror("Kritiskt fel", f"Kunde inte hitta databasen:\n{filepath}\n\nProgrammet avslutas.")
        import sys; sys.exit(1)
    except json.JSONDecodeError as e:
        messagebox.showerror("JSON-fel", f"Något är felformaterat i {filename}.\nDetaljer: {e}\n\nProgrammet avslutas.")
        import sys; sys.exit(1)

# Ladda filerna
RAW_MATERIALS_DB = load_json_db("materials.json")
LIBRARY_PARTS = load_json_db("library_parts.json")

# Bygg materiallistan för menyerna
MATERIALS = {}
current_category = ""

for db_name, properties in RAW_MATERIALS_DB.items():
    cat = properties.get("category", "▬▬▬ ÖVRIGT ▬▬▬")
    if cat != current_category:
        MATERIALS[cat] = None
        current_category = cat
        
    db_lam = properties.get("lambda", 0.0)
    db_mu = properties.get("mu")
    
    if db_mu is not None:
        MATERIALS[f"{db_name} [λ={db_lam:.3f}, µ={db_mu:g}]"] = db_lam
    else:
        MATERIALS[f"{db_name} [λ={db_lam:.3f}]"] = db_lam

# =====================================================================
# FÄRG OCH KONSTANTER
# =====================================================================
def get_material_color(mat_name):
    m = mat_name.lower()
    if any(x in m for x in ["mineralull", "glasull", "stenull", "lösull", "träfiberisolering", "cellulosaisolering"]): return "#F4D03F" 
    if any(x in m for x in ["cellplast", "pir", "pur", "skum", "leca"]): return "#AED6F1" 
    if "gips" in m: return "#E5E7E9" 
    if any(x in m for x in ["betong", "cement", "puts", "bruk", "sten", "makadam"]): return "#7F8C8D" 
    if any(x in m for x in ["tegel", "klinker"]): return "#CB4335" 
    if any(x in m for x in ["trä", "plywood", "osb", "spån", "mdf", "virke", "panel", "parkett", "ek"]): return "#D35400" 
    if any(x in m for x in ["plast", "papp", "duk", "folie", "gummi", "matta", "asfalt"]): return "#273746" 
    if any(x in m for x in ["stål", "aluminium", "plåt", "metall", "koppar", "mässing"]): return "#BDC3C7" 
    if "glas" in m: return "#E0FFFF" 
    if any(x in m for x in ["sand", "grus", "lera", "jord"]): return "#8D6E63" 
    if "luft" in m: return "#E8F8F5" 
    return "#D5D8DC"

HEAT_FLOWS = {
    "Horisontellt (t.ex. Yttervägg)": {"R_si": 0.13, "R_se": 0.04},
    "Källarvägg / Motfylld vägg (ISO 13370)": {"R_si": 0.13, "R_se": 0.04},
    "Uppåtriktat (t.ex. Yttertak)": {"R_si": 0.10, "R_se": 0.04},
    "Nedåtriktat (t.ex. Golv)": {"R_si": 0.17, "R_se": 0.04},
    "Platta på mark (ISO 13370)": {"R_si": 0.17, "R_se": 0.00},
    "Fönster / Dörr (Ange färdigt U-värde)": {"R_si": 0.0, "R_se": 0.0} 
}

DIRECTIONS = ["Ospecifierat", "N (Norr)", "NO (Nordost)", "O (Ost)", "SO (Sydost)", "S (Söder)", "SV (Sydväst)", "V (Väst)", "NV (Nordväst)"]

B_FACTORS = [
    "1.00 (Utomhusluft / Öppen grund)",
    "0.80 (Ouppvärmd kallvind)",
    "0.70 (Sluten krypgrund)",
    "0.60 (Ouppvärmd källare)"
]

DELTA_U_OPTIONS = [
    "0.00 (Korslagda reglar)",
    "0.01 (Ett isolerskikt mellan genomgående reglar)",
    "0.03 (Normalt spalt-tillägg)",
    "0.04 (Isolerad dubbel tegelvägg utan lufttätning)",
    "0.05 (Tydliga köldbryggor)"
]

KB_TEMPLATES = {
    "--- Skriv eget namn ---": "",
    "Fönster- och dörrsmygar": 0.04,
    "Yttervägghörn (Utåtgående)": 0.04,
    "Mellanbjälklagskant (Trä)": 0.05,
    "Mellanbjälklagskant (Betong)": 0.15,
    "Vindsbjälklagskant": 0.06,
    "Kantförlust Platta (Standard kantelement)": 0.15,
    "Kantförlust Platta (Lågenergi/Passiv)": 0.08,
    "Takfot / Takanslutning": 0.05,
    "Suterräng/Källarvägg anslutning": 0.10,
    "Balkonginfästning (Trä)": 0.05,
    "Balkonginfästning (Stål/Betong, per st/m)": 0.40
}

# =====================================================================
# GUI-HJÄLPARE
# =====================================================================
def enable_combo_cycling(cb):
    """Filtreringsfunktion för öppen rullgardin utan aggressiv autofill."""
    cb.config(state="normal")
    if not hasattr(cb, '_full_list'):
        cb._full_list = list(cb['values'])
        
    def _on_keyrelease(event):
        if event.keysym in ("Up", "Down", "Left", "Right", "Return", "Tab", "Escape", "Shift_L", "Shift_R", "Control_L", "Control_R", "Caps_Lock"):
            return
        
        typed = cb.get()
        cursor_pos = cb.index(tk.INSERT)
        
        if typed == "":
            cb['values'] = cb._full_list
        else:
            matches = []
            for item in cb._full_list:
                if str(item).startswith("▬"): continue
                if typed.lower() in str(item).lower():
                    matches.append(item)
            cb['values'] = matches if matches else cb._full_list
        
        try:
            cb.tk.call('ttk::combobox::Post', cb)
        except tk.TclError:
            pass
            
        cb.after(20, lambda: (cb.focus_force(), cb.icursor(cursor_pos)))
            
    cb.bind("<KeyRelease>", _on_keyrelease)