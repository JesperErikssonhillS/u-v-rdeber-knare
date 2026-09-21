import tkinter as tk
from tkinter import ttk, messagebox
import math
import copy
import itertools

from core_logic import (
    RAW_MATERIALS_DB, LIBRARY_PARTS, MATERIALS, HEAT_FLOWS, 
    B_FACTORS, DELTA_U_OPTIONS, get_material_color, enable_combo_cycling
)

class TabParts:
    def __init__(self, parent, app_data):
        self.parent = parent
        self.app_data = app_data
        
        self.current_layers = []
        self.editing_layer_index = None

        # --- FLIK 2: SKAPA BYGGNADSDEL ---
        frame_bygg = ttk.LabelFrame(parent, text="Skapa/Redigera Byggnadsdel", padding=10)
        frame_bygg.pack(fill="x", padx=15, pady=5)
        
        frame_bygg.columnconfigure(5, weight=1)
        ttk.Label(frame_bygg, text="Hämta typuppbyggnad från bibliotek:", font=("Arial", 9, "bold"), foreground="#273746").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        ttk.Button(frame_bygg, text="❓ Guide", command=self.show_guide).grid(row=0, column=0, columnspan=6, sticky="e", padx=10, pady=(0, 5))
        
        frame_lib = ttk.Frame(frame_bygg)
        frame_lib.grid(row=1, column=0, columnspan=5, sticky="w", pady=(0, 10))
        self.library_var = tk.StringVar()
        self.library_cb = ttk.Combobox(frame_lib, textvariable=self.library_var, values=[p["namn"] for p in LIBRARY_PARTS], state="normal", width=38)
        self.library_cb.pack(side="left", padx=(0, 10))
        enable_combo_cycling(self.library_cb)
        ttk.Button(frame_lib, text="⬇ Ladda till ritbord", command=self.load_from_library).pack(side="left")

        ttk.Separator(frame_bygg, orient="horizontal").grid(row=2, column=0, columnspan=6, sticky="we", pady=(0, 10))

        ttk.Label(frame_bygg, text="Namn:").grid(row=3, column=0, sticky="w")
        self.bygg_name_var = tk.StringVar()
        ttk.Entry(frame_bygg, textvariable=self.bygg_name_var, width=40).grid(row=3, column=1, padx=(0,10), pady=(0, 5), sticky="w")

        ttk.Label(frame_bygg, text="Riktning:").grid(row=3, column=2, sticky="w", padx=(10, 5))
        self.flow_var = tk.StringVar()
        self.flow_cb = ttk.Combobox(frame_bygg, textvariable=self.flow_var, values=list(HEAT_FLOWS.keys()), state="readonly", width=48)
        self.flow_cb.current(0)
        self.flow_cb.grid(row=3, column=3, pady=(0, 5), sticky="w")
        self.flow_cb.bind("<<ComboboxSelected>>", self.on_flow_change)

        ttk.Label(frame_bygg, text="Ytmotstånd (Rsi / Rse):").grid(row=4, column=0, sticky="w")
        frame_r = ttk.Frame(frame_bygg)
        frame_r.grid(row=4, column=1, pady=(0, 5), sticky="w")
        self.rsi_var = tk.StringVar(value="0.13")
        self.rse_var = tk.StringVar(value="0.04")
        ttk.Entry(frame_r, textvariable=self.rsi_var, width=6).pack(side="left")
        ttk.Label(frame_r, text=" / ").pack(side="left")
        ttk.Entry(frame_r, textvariable=self.rse_var, width=6).pack(side="left")
        ttk.Button(frame_r, text="?", width=3, command=self.show_r_help).pack(side="left", padx=(5,0))

        ttk.Label(frame_bygg, text="b-faktor:").grid(row=5, column=0, sticky="w")
        
        frame_b = ttk.Frame(frame_bygg)
        frame_b.grid(row=5, column=1, padx=(0, 10), pady=(0, 5), sticky="w")
        self.b_factor_var = tk.StringVar()
        self.b_factor_cb = ttk.Combobox(frame_b, textvariable=self.b_factor_var, values=B_FACTORS, state="readonly", width=38)
        self.b_factor_cb.current(0)
        self.b_factor_cb.pack(side="left")
        ttk.Button(frame_b, text="?", width=3, command=self.show_b_help).pack(side="left", padx=(5,0))
        
        ttk.Label(frame_bygg, text="Delta U-tillägg:").grid(row=5, column=2, sticky="w", padx=(10, 5))
        
        frame_du = ttk.Frame(frame_bygg)
        frame_du.grid(row=5, column=3, pady=(0, 5), sticky="w")
        self.delta_u_var = tk.StringVar()
        self.delta_u_cb = ttk.Combobox(frame_du, textvariable=self.delta_u_var, values=DELTA_U_OPTIONS, state="readonly", width=48)
        self.delta_u_cb.current(0)
        self.delta_u_cb.pack(side="left")
        ttk.Button(frame_du, text="?", width=3, command=self.show_du_help).pack(side="left", padx=(5,0))

        self.frame_ground = ttk.Frame(frame_bygg)
        ttk.Label(self.frame_ground, text="Area (m²):").grid(row=0, column=0, sticky="w")
        self.area_var = tk.StringVar(value="100")
        ttk.Entry(self.frame_ground, textvariable=self.area_var, width=8).grid(row=0, column=1, padx=(0,10))

        ttk.Label(self.frame_ground, text="Omkrets (m):").grid(row=0, column=2, sticky="w")
        self.perim_var = tk.StringVar(value="40")
        ttk.Entry(self.frame_ground, textvariable=self.perim_var, width=8).grid(row=0, column=3, padx=(0,10))

        ttk.Label(self.frame_ground, text="Väggtj. w (m):").grid(row=0, column=4, sticky="w")
        self.wall_w_var = tk.StringVar(value="0.30")
        ttk.Entry(self.frame_ground, textvariable=self.wall_w_var, width=8).grid(row=0, column=5)

        self.frame_basement = ttk.Frame(frame_bygg)
        ttk.Label(self.frame_basement, text="Djup under mark (m):").grid(row=0, column=0, sticky="w")
        self.depth_var = tk.StringVar(value="1.5")
        ttk.Entry(self.frame_basement, textvariable=self.depth_var, width=8).grid(row=0, column=1, padx=(0,15))

        ttk.Label(self.frame_basement, text="Höjd över mark (m):").grid(row=0, column=2, sticky="w")
        self.height_above_var = tk.StringVar(value="1.0")
        ttk.Entry(self.frame_basement, textvariable=self.height_above_var, width=8).grid(row=0, column=3, padx=(0,10))

        ttk.Label(frame_bygg, text="Välj skikt att lägga till (Insida först):", font=("Arial", 9, "bold"), foreground="#D35400").grid(row=8, column=0, columnspan=5, sticky="w", pady=(10,0))
        self.layer_type_var = tk.StringVar()
        # Bredd ökad för att få plats med den nya rubriken
        self.layer_type_cb = ttk.Combobox(frame_bygg, textvariable=self.layer_type_var, state="readonly", width=45, 
                                          values=["Standardmaterial", "Regelverk / Blandat skikt", "Eget material", "Färdig produkt / Sandwichpanel (Ange U-värde)", "Oventilerad luftspalt (Ange R-värde)", "Ventilerad luftspalt (R = 0)"])
        self.layer_type_cb.current(0)
        self.layer_type_cb.grid(row=9, column=0, columnspan=2, sticky="w", pady=(0, 5))
        self.layer_type_cb.bind("<<ComboboxSelected>>", self.on_layer_type_change)

        self.frame_dynamic = ttk.Frame(frame_bygg)
        self.frame_dynamic.grid(row=10, column=0, columnspan=6, pady=5, sticky="we")

        self.setup_dynamic_frames()
        self.on_layer_type_change(None) 
        self.on_flow_change(None)

        self.frame_add_btns = ttk.Frame(frame_bygg)
        self.frame_add_btns.grid(row=11, column=0, columnspan=6, pady=5, sticky="w")
        
        self.btn_add_layer = ttk.Button(self.frame_add_btns, text="⬇ Lägg till skikt (Insida först)", command=self.add_layer)
        self.btn_add_layer.pack(side="left", padx=(0,5))
        
        self.btn_cancel_edit = ttk.Button(self.frame_add_btns, text="Avbryt redigering", command=self.cancel_edit)
        self.btn_cancel_edit.pack(side="left")
        self.btn_cancel_edit.pack_forget() 
        
        self.listbox_layers = tk.Listbox(frame_bygg, height=5, width=110, exportselection=False)
        self.listbox_layers.grid(row=12, column=0, columnspan=6, pady=2, sticky="w")

        btn_frame_layers = ttk.Frame(frame_bygg)
        btn_frame_layers.grid(row=13, column=0, columnspan=6, pady=2, sticky="w")
        
        ttk.Button(btn_frame_layers, text="⬆ Upp", command=self.move_layer_up, width=8).pack(side="left", padx=(0,2))
        ttk.Button(btn_frame_layers, text="⬇ Ned", command=self.move_layer_down, width=8).pack(side="left", padx=2)
        ttk.Button(btn_frame_layers, text="✏️ Redigera", command=self.edit_layer_mode).pack(side="left", padx=(5,2))
        ttk.Button(btn_frame_layers, text="🗑️ Ta bort skikt", command=self.remove_layer, style="LeftAligned.TButton").pack(side="left", padx=2)
        
        self.canvas = tk.Canvas(frame_bygg, height=50, width=700, bg="white", relief="sunken", bd=1)
        self.canvas.grid(row=14, column=0, columnspan=6, pady=(10,5), sticky="w")
        
        ttk.Button(frame_bygg, text="✅ Spara färdig Byggnadsdel", command=self.save_building_part).grid(row=15, column=0, columnspan=6, pady=(5,0))

        # --- FLIK 2: FÄRDIGA BYGGNADSDELAR ---
        frame_rap = ttk.LabelFrame(parent, text="Färdiga Byggnadsdelar", padding=10)
        frame_rap.pack(fill="x", padx=15, pady=5)

        self.listbox_parts = tk.Listbox(frame_rap, height=5, width=110, exportselection=False)
        self.listbox_parts.pack(pady=5, anchor="w")

        btn_frame = ttk.Frame(frame_rap)
        btn_frame.pack(pady=5, anchor="w")
        ttk.Button(btn_frame, text="✏️ Redigera vald", command=self.edit_part).grid(row=0, column=0, padx=(0,5))
        ttk.Button(btn_frame, text="📋 Kopiera vald", command=self.copy_part).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="🗑️ Ta bort vald", command=self.delete_part, style="LeftAligned.TButton").grid(row=0, column=2, padx=5)

    def setup_dynamic_frames(self):
        self.frame_std = ttk.Frame(self.frame_dynamic)
        ttk.Label(self.frame_std, text="Material:").grid(row=0, column=0, sticky="w")
        self.std_mat_var = tk.StringVar()
        self.std_mat_cb = ttk.Combobox(self.frame_std, textvariable=self.std_mat_var, values=list(MATERIALS.keys()), state="readonly", width=40)
        self.std_mat_cb.grid(row=1, column=0, padx=(0,10))
        enable_combo_cycling(self.std_mat_cb)
        
        ttk.Label(self.frame_std, text="Tjocklek (mm):").grid(row=0, column=1, sticky="w")
        self.std_thick_var = tk.StringVar(value="100")
        ttk.Entry(self.frame_std, textvariable=self.std_thick_var, width=15).grid(row=1, column=1)

        self.frame_reg = ttk.Frame(self.frame_dynamic)
        ttk.Label(self.frame_reg, text="Huvudmaterial:").grid(row=0, column=0, sticky="w", pady=(0,2))
        self.reg_m1_var = tk.StringVar()
        self.reg_m1_cb = ttk.Combobox(self.frame_reg, textvariable=self.reg_m1_var, values=list(MATERIALS.keys()), state="readonly", width=45)
        self.reg_m1_cb.grid(row=0, column=1, columnspan=2, sticky="w", pady=(0,2))
        enable_combo_cycling(self.reg_m1_cb)
        
        ttk.Label(self.frame_reg, text="Regelmaterial:").grid(row=1, column=0, sticky="w", pady=(0,5))
        self.reg_m2_var = tk.StringVar()
        self.reg_m2_cb = ttk.Combobox(self.frame_reg, textvariable=self.reg_m2_var, values=list(MATERIALS.keys()), state="readonly", width=45)
        self.reg_m2_cb.grid(row=1, column=1, columnspan=2, sticky="w", pady=(0,5))
        enable_combo_cycling(self.reg_m2_cb)
        
        ttk.Label(self.frame_reg, text="Tjocklek (mm):").grid(row=2, column=0, sticky="w")
        self.reg_thick_var = tk.StringVar(value="145")
        ttk.Entry(self.frame_reg, textvariable=self.reg_thick_var, width=10).grid(row=3, column=0, sticky="w", padx=(0,10))

        ttk.Label(self.frame_reg, text="Regelbredd (mm):").grid(row=2, column=1, sticky="w")
        self.reg_width_var = tk.StringVar(value="45")
        ttk.Entry(self.frame_reg, textvariable=self.reg_width_var, width=10).grid(row=3, column=1, sticky="w", padx=(0,10))
        
        ttk.Label(self.frame_reg, text="c/c-mått (mm):").grid(row=2, column=2, sticky="w")
        self.reg_cc_var = tk.StringVar(value="600")
        ttk.Entry(self.frame_reg, textvariable=self.reg_cc_var, width=10).grid(row=3, column=2, sticky="w")

        self.frame_cst = ttk.Frame(self.frame_dynamic)
        ttk.Label(self.frame_cst, text="Namn:").grid(row=0, column=0, sticky="w")
        self.cst_name_var = tk.StringVar(value="Eget material")
        ttk.Entry(self.frame_cst, textvariable=self.cst_name_var, width=20).grid(row=1, column=0, padx=(0,10))
        
        ttk.Label(self.frame_cst, text="Lambda (W/mK):").grid(row=0, column=1, sticky="w")
        self.cst_lam_var = tk.StringVar(value="0.10")
        ttk.Entry(self.frame_cst, textvariable=self.cst_lam_var, width=15).grid(row=1, column=1, padx=(0,10))
        
        ttk.Label(self.frame_cst, text="My-värde (µ):").grid(row=0, column=2, sticky="w")
        self.cst_mu_var = tk.StringVar(value="50.0")
        ttk.Entry(self.frame_cst, textvariable=self.cst_mu_var, width=15).grid(row=1, column=2, padx=(0,10))
        
        ttk.Label(self.frame_cst, text="Tjocklek (mm):").grid(row=0, column=3, sticky="w")
        self.cst_thick_var = tk.StringVar(value="50")
        ttk.Entry(self.frame_cst, textvariable=self.cst_thick_var, width=15).grid(row=1, column=3)

        # NYTT: Frame för Sandwichpanel/Färdig produkt
        self.frame_panel = ttk.Frame(self.frame_dynamic)
        ttk.Label(self.frame_panel, text="Namn:").grid(row=0, column=0, sticky="w")
        self.panel_name_var = tk.StringVar(value="Paroc AST 240")
        ttk.Entry(self.frame_panel, textvariable=self.panel_name_var, width=18).grid(row=1, column=0, padx=(0,10))
        
        ttk.Label(self.frame_panel, text="Tjocklek (mm):").grid(row=0, column=1, sticky="w")
        self.panel_thick_var = tk.StringVar(value="240")
        ttk.Entry(self.frame_panel, textvariable=self.panel_thick_var, width=12).grid(row=1, column=1, padx=(0,10))
        
        ttk.Label(self.frame_panel, text="U-värde:").grid(row=0, column=2, sticky="w")
        self.panel_u_var = tk.StringVar(value="0.20")
        ttk.Entry(self.frame_panel, textvariable=self.panel_u_var, width=8).grid(row=1, column=2, padx=(0,10))
        
        ttk.Label(self.frame_panel, text="Inkluderar Rsi/Rse?").grid(row=0, column=3, sticky="w")
        self.panel_inc_r_var = tk.StringVar(value="Ja")
        ttk.Combobox(self.frame_panel, textvariable=self.panel_inc_r_var, values=["Ja", "Nej"], state="readonly", width=5).grid(row=1, column=3, padx=(0,10))
        
        ttk.Label(self.frame_panel, text="My-värde (µ):").grid(row=0, column=4, sticky="w")
        self.panel_mu_var = tk.StringVar(value="100000")
        ttk.Entry(self.frame_panel, textvariable=self.panel_mu_var, width=10).grid(row=1, column=4)

        self.frame_air = ttk.Frame(self.frame_dynamic)
        ttk.Label(self.frame_air, text="Namn:").grid(row=0, column=0, sticky="w")
        self.air_name_var = tk.StringVar(value="Oventilerad luftspalt")
        ttk.Entry(self.frame_air, textvariable=self.air_name_var, width=20).grid(row=1, column=0, padx=(0,10))
        
        frame_air_r = ttk.Frame(self.frame_air)
        frame_air_r.grid(row=1, column=1, padx=(0,10))
        ttk.Label(self.frame_air, text="R-värde (m²K/W):").grid(row=0, column=1, sticky="w")
        self.air_r_var = tk.StringVar(value="0.15")
        ttk.Entry(frame_air_r, textvariable=self.air_r_var, width=10).pack(side="left")
        ttk.Button(frame_air_r, text="?", width=3, command=self.show_air_r_help).pack(side="left", padx=(5,0))
        
        ttk.Label(self.frame_air, text="Fysisk tjocklek (mm):").grid(row=0, column=2, sticky="w")
        self.air_thick_var = tk.StringVar(value="25")
        ttk.Entry(self.frame_air, textvariable=self.air_thick_var, width=15).grid(row=1, column=2)

        self.frame_air_vent = ttk.Frame(self.frame_dynamic)
        ttk.Label(self.frame_air_vent, text="Namn:").grid(row=0, column=0, sticky="w")
        self.air_vent_name_var = tk.StringVar(value="Ventilerad luftspalt")
        ttk.Entry(self.frame_air_vent, textvariable=self.air_vent_name_var, width=20).grid(row=1, column=0, padx=(0,10))
        
        ttk.Label(self.frame_air_vent, text="Fysisk tjocklek (mm):").grid(row=0, column=1, sticky="w")
        self.air_vent_thick_var = tk.StringVar(value="25")
        ttk.Entry(self.frame_air_vent, textvariable=self.air_vent_thick_var, width=15).grid(row=1, column=1, padx=(0,10))
        
        ttk.Label(self.frame_air_vent, text="Obs: Ytmotstånd och skikt exkluderas enl. ISO 6946.").grid(row=2, column=0, columnspan=2, sticky="w", pady=(5,0))

        self.std_mat_var.set("skriv eller scrolla för material")
        self.reg_m1_var.set("skriv eller scrolla för material")
        self.reg_m2_var.set("skriv eller scrolla för material")

    def on_flow_change(self, event=None):
        self.frame_ground.grid_remove()
        self.frame_basement.grid_remove()
        
        flode = self.flow_var.get()
        if "Platta på mark" in flode:
            self.frame_ground.grid(row=6, column=0, columnspan=6, pady=(5, 5), sticky="w")
        elif "Källarvägg" in flode:
            self.frame_basement.grid(row=6, column=0, columnspan=6, pady=(5, 5), sticky="w")
            
        if event is not None:
            if flode in HEAT_FLOWS:
                self.rsi_var.set(str(HEAT_FLOWS[flode]["R_si"]))
                self.rse_var.set(str(HEAT_FLOWS[flode]["R_se"]))
            
        if hasattr(self.app_data.get("main_app_instance"), "scrollable_frame"):
            self.app_data["main_app_instance"].scrollable_frame.update_idletasks()
            self.app_data["main_app_instance"].main_canvas.configure(scrollregion=self.app_data["main_app_instance"].main_canvas.bbox("all"))

    def on_layer_type_change(self, _event=None):
        self.frame_std.grid_remove()
        self.frame_reg.grid_remove()
        self.frame_cst.grid_remove()
        self.frame_panel.grid_remove() # NYTT
        self.frame_air.grid_remove()
        self.frame_air_vent.grid_remove()

        val = self.layer_type_var.get()
        if val == "Standardmaterial": self.frame_std.grid(row=0, column=0, sticky="w")
        elif val == "Regelverk / Blandat skikt": self.frame_reg.grid(row=0, column=0, sticky="w")
        elif val == "Eget material": self.frame_cst.grid(row=0, column=0, sticky="w")
        elif "Färdig produkt" in val: self.frame_panel.grid(row=0, column=0, sticky="w") # NYTT
        elif "Oventilerad" in val: self.frame_air.grid(row=0, column=0, sticky="w")
        elif "Ventilerad" in val: self.frame_air_vent.grid(row=0, column=0, sticky="w")
        
        if hasattr(self.app_data.get("main_app_instance"), "scrollable_frame"):
            self.app_data["main_app_instance"].scrollable_frame.update_idletasks()
            self.app_data["main_app_instance"].main_canvas.configure(scrollregion=self.app_data["main_app_instance"].main_canvas.bbox("all"))

    def load_from_library(self):
        idx = self.library_cb.current()
        if idx == -1: 
            messagebox.showwarning("Välj mall", "Du måste välja en typuppbyggnad i listan först.")
            return
            
        if self.current_layers:
            if not messagebox.askyesno("Varning", "Detta kommer att skriva över det du har på ritbordet just nu. Vill du fortsätta?"):
                return
                
        part = LIBRARY_PARTS[idx]
        
        self.bygg_name_var.set(part["namn"])
        self.flow_var.set(part["flode"])
        self.set_bfactor_string(part.get("b_factor", 1.00))
        self.set_deltau_string(part.get("delta_u", 0.00))
        
        self.on_flow_change("force_update")
        if "r_si" in part: self.rsi_var.set(str(part["r_si"]))
        if "r_se" in part: self.rse_var.set(str(part["r_se"]))
        
        if "Platta på mark" in part["flode"]:
            self.area_var.set("100")
            self.perim_var.set("40")
            self.wall_w_var.set("0.30")
            
        if "Källarvägg" in part["flode"]:
            self.depth_var.set("1.5")
            self.height_above_var.set("1.0")
            
        self.current_layers = copy.deepcopy(part["layers"])
        
        self.listbox_layers.delete(0, tk.END)
        for layer in self.current_layers:
            if layer["Type"] == "Air":
                temp_r = layer["R"]
            else:
                temp_r = (layer["Tjocklek (mm)"] / 1000) / layer["Lambda_eff"]
            self.listbox_layers.insert(tk.END, f"{layer.get('Tjocklek (mm)', 0):g} mm   |   {layer['Material']}   |   R: {temp_r:.2f}")

        self.update_canvas()

    def add_layer(self):
        val = self.layer_type_var.get()
        new_layer = {}
        
        try:
            raw = {"type": val}
            
            if val == "Standardmaterial":
                mat_full = self.std_mat_var.get()
                lam_val = MATERIALS.get(mat_full)
                if lam_val is None: raise ValueError("Du har valt en kategori-rubrik istället för ett material.")
                
                thick = float(self.std_thick_var.get().replace(',', '.'))
                mat_clean = mat_full.split(" [λ=")[0] if " [λ=" in mat_full else mat_full
                
                raw["mat"] = mat_full
                raw["thick"] = thick
                
                new_layer = {
                    "Type": "Solid",
                    "Material": mat_clean, 
                    "Tjocklek (mm)": thick, 
                    "Parts": [{"fraction": 1.0, "lambda": lam_val}],
                    "Lambda_eff": lam_val,
                    "Color": get_material_color(mat_clean),
                    "RawData": raw
                }
                
            elif val == "Regelverk / Blandat skikt":
                m1_full = self.reg_m1_var.get()
                m2_full = self.reg_m2_var.get()
                lam1 = MATERIALS.get(m1_full)
                lam2 = MATERIALS.get(m2_full)
                if lam1 is None or lam2 is None: raise ValueError("Välj giltiga material för regelverket.")
                
                thick = float(self.reg_thick_var.get().replace(',', '.'))
                r_width = float(self.reg_width_var.get().replace(',', '.'))
                cc = float(self.reg_cc_var.get().replace(',', '.'))
                
                if cc <= 0: raise ValueError("c/c-mått måste vara större än 0")
                if r_width < 0 or r_width > cc: raise ValueError("Regelbredd orimlig jämfört med c/c")
                
                perc = r_width / cc
                lam_eff = (lam1 * (1 - perc)) + (lam2 * perc)
                
                m1_clean = m1_full.split(" [λ=")[0] if " [λ=" in m1_full else m1_full
                m2_clean = m2_full.split(" [λ=")[0] if " [λ=" in m2_full else m2_full
                name = f"{m1_clean} + {m2_clean} (c/c {int(cc)})"
                
                raw["m1"] = m1_full
                raw["m2"] = m2_full
                raw["thick"] = thick
                raw["width"] = r_width
                raw["cc"] = cc
                
                new_layer = {
                    "Type": "Solid",
                    "Material": name, 
                    "Tjocklek (mm)": thick, 
                    "Parts": [{"fraction": 1 - perc, "lambda": lam1}, {"fraction": perc, "lambda": lam2}],
                    "Lambda_eff": lam_eff, 
                    "Color": get_material_color(m1_clean),
                    "RawData": raw
                }
                
            elif val == "Eget material":
                name = self.cst_name_var.get()
                lam_val = float(self.cst_lam_var.get().replace(',', '.'))
                mu_val = float(self.cst_mu_var.get().replace(',', '.'))
                thick = float(self.cst_thick_var.get().replace(',', '.'))
                
                raw["name"] = name
                raw["lam"] = lam_val
                raw["mu"] = mu_val
                raw["thick"] = thick
                
                new_layer = {
                    "Type": "Solid",
                    "Material": name, 
                    "Tjocklek (mm)": thick, 
                    "Parts": [{"fraction": 1.0, "lambda": lam_val}],
                    "Lambda_eff": lam_val,
                    "Color": get_material_color(name),
                    "RawData": raw
                }

            elif "Färdig produkt" in val:
                name = self.panel_name_var.get()
                thick = float(self.panel_thick_var.get().replace(',', '.'))
                u_val = float(self.panel_u_var.get().replace(',', '.'))
                inc_r = self.panel_inc_r_var.get()
                mu_val = float(self.panel_mu_var.get().replace(',', '.'))
                
                if u_val <= 0: raise ValueError("U-värdet måste vara över 0")
                if thick <= 0: raise ValueError("Tjocklek måste vara över 0")
                
                r_tot_given = 1.0 / u_val
                
                if inc_r == "Ja":
                    try:
                        r_si_current = float(self.rsi_var.get().replace(',', '.'))
                        r_se_current = float(self.rse_var.get().replace(',', '.'))
                    except ValueError:
                        raise ValueError("Ange giltiga ytmotstånd (Rsi/Rse) innan du lägger till en panel som inkluderar dem.")
                    r_panel = r_tot_given - r_si_current - r_se_current
                else:
                    r_panel = r_tot_given
                    
                if r_panel <= 0:
                    raise ValueError(f"U-värdet ({u_val}) ger ett för lågt materialmotstånd när ytmotstånden subtraheras. Panelens R-värde blir <= 0.")
                    
                lam_eff = (thick / 1000.0) / r_panel
                
                # Tricket! Vi fakar det som ett "Eget material" för fuktkalkylens skull
                raw["type"] = "Eget material"
                raw["is_panel"] = True
                raw["name"] = name
                raw["thick"] = thick
                raw["u_val"] = u_val
                raw["inc_r"] = inc_r
                raw["mu"] = mu_val
                raw["lam"] = lam_eff
                
                new_layer = {
                    "Type": "Solid",
                    "Material": name, 
                    "Tjocklek (mm)": thick, 
                    "Parts": [{"fraction": 1.0, "lambda": lam_eff}],
                    "Lambda_eff": lam_eff,
                    "Color": get_material_color(name),
                    "RawData": raw
                }
                
            elif "Oventilerad" in val:
                name = self.air_name_var.get()
                r_val = float(self.air_r_var.get().replace(',', '.'))
                thick = float(self.air_thick_var.get().replace(',', '.'))
                
                raw["name"] = name
                raw["r"] = r_val
                raw["thick"] = thick
                
                new_layer = {
                    "Type": "Air",
                    "Material": name, 
                    "Tjocklek (mm)": thick, 
                    "R": r_val, 
                    "Lambda_eff": "-", 
                    "Color": get_material_color(name),
                    "RawData": raw
                }
                
            elif "Ventilerad" in val:
                name = self.air_vent_name_var.get()
                thick = float(self.air_vent_thick_var.get().replace(',', '.'))
                
                raw["name"] = name
                raw["thick"] = thick
                
                new_layer = {
                    "Type": "Air",
                    "Material": name, 
                    "Tjocklek (mm)": thick, 
                    "R": 0.0, 
                    "Lambda_eff": "-", 
                    "Color": get_material_color(name),
                    "is_ventilated": True,
                    "RawData": raw
                }

            if thick <= 0: raise ValueError("Tjocklek måste vara över 0")

            if self.editing_layer_index is not None:
                self.current_layers[self.editing_layer_index] = new_layer
                self.listbox_layers.delete(self.editing_layer_index)
                if new_layer["Type"] == "Air":
                    temp_r = new_layer["R"]
                else:
                    temp_r = (thick / 1000) / new_layer["Lambda_eff"]
                self.listbox_layers.insert(self.editing_layer_index, f"{new_layer.get('Tjocklek (mm)', 0):g} mm   |   {new_layer['Material']}   |   R: {temp_r:.2f}")
                self.listbox_layers.selection_set(self.editing_layer_index)
                self.cancel_edit() 
            else:
                self.current_layers.append(new_layer)
                if new_layer["Type"] == "Air":
                    temp_r = new_layer["R"]
                else:
                    temp_r = (thick / 1000) / new_layer["Lambda_eff"]
                self.listbox_layers.insert(tk.END, f"{new_layer.get('Tjocklek (mm)', 0):g} mm   |   {new_layer['Material']}   |   R: {temp_r:.2f}")
                
            self.update_canvas()
            
        except ValueError as e:
            messagebox.showerror("Fel inmatning", f"Kontrollera inmatningen.\n({e})")

    def reverse_engineer_raw(self, layer):
        raw = {"thick": layer["Tjocklek (mm)"]}
        if layer["Type"] == "Air":
            if layer.get("is_ventilated"):
                raw["type"] = "Ventilerad luftspalt (R = 0)"
                raw["name"] = layer["Material"]
            else:
                raw["type"] = "Oventilerad luftspalt (Ange R-värde)"
                raw["name"] = layer["Material"]
                raw["r"] = layer["R"]
            return raw
        elif layer["Type"] == "Solid":
            if len(layer.get("Parts", [])) == 1:
                for full_name, lam_val in MATERIALS.items():
                    if lam_val is not None and layer["Material"] in full_name and abs(lam_val - layer["Lambda_eff"]) < 0.001:
                        raw["type"] = "Standardmaterial"
                        raw["mat"] = full_name
                        return raw
                raw["type"] = "Eget material"
                raw["name"] = layer["Material"]
                raw["lam"] = layer["Lambda_eff"]
                raw["mu"] = 50.0 
                return raw
        return None 

    def edit_layer_mode(self):
        sel = self.listbox_layers.curselection()
        if not sel:
            messagebox.showwarning("Inget valt", "Markera skiktet du vill redigera i listan ovan först.")
            return
            
        idx = sel[0]
        layer = self.current_layers[idx]
        raw = layer.get("RawData")
        
        if not raw:
            raw = self.reverse_engineer_raw(layer)
            if not raw:
                messagebox.showwarning("Äldre version", "Detta regelverksskykt skapades i en äldre version av programmet och kan tyvärr inte laddas in automatiskt. Ta bort skiktet och skapa ett nytt.")
                return

        self.editing_layer_index = idx
        l_type = raw["type"]
        
        # Återskapa display_type om det är en fusk-sparad panel
        display_type = l_type
        if l_type == "Eget material" and raw.get("is_panel"):
            display_type = "Färdig produkt / Sandwichpanel (Ange U-värde)"
            
        self.layer_type_var.set(display_type)
        self.on_layer_type_change(None)

        if display_type == "Standardmaterial":
            self.std_mat_var.set(raw["mat"])
            self.std_thick_var.set(raw["thick"])
        elif display_type == "Regelverk / Blandat skikt":
            self.reg_m1_var.set(raw["m1"])
            self.reg_m2_var.set(raw["m2"])
            self.reg_thick_var.set(raw["thick"])
            self.reg_width_var.set(raw["width"])
            self.reg_cc_var.set(raw["cc"])
        elif display_type == "Eget material":
            self.cst_name_var.set(raw.get("name", layer["Material"]))
            self.cst_lam_var.set(raw.get("lam", layer["Lambda_eff"]))
            self.cst_mu_var.set(raw.get("mu", "50.0"))
            self.cst_thick_var.set(raw["thick"])
        elif display_type == "Färdig produkt / Sandwichpanel (Ange U-värde)":
            self.panel_name_var.set(raw.get("name", layer["Material"]))
            self.panel_thick_var.set(raw["thick"])
            self.panel_u_var.set(raw.get("u_val", "0.20"))
            self.panel_inc_r_var.set(raw.get("inc_r", "Ja"))
            self.panel_mu_var.set(raw.get("mu", "100000"))
        elif "Oventilerad" in display_type:
            self.air_name_var.set(raw.get("name", layer["Material"]))
            self.air_r_var.set(raw.get("r", layer.get("R", 0.15)))
            self.air_thick_var.set(raw["thick"])
        elif "Ventilerad" in display_type:
            self.air_vent_name_var.set(raw.get("name", layer["Material"]))
            self.air_vent_thick_var.set(raw["thick"])

        self.btn_add_layer.config(text="✅ Spara ändring")
        self.btn_cancel_edit.pack(side="left")

    def cancel_edit(self):
        self.editing_layer_index = None
        self.btn_add_layer.config(text="⬇ Lägg till skikt (Insida först)")
        self.btn_cancel_edit.pack_forget()

    def move_layer_up(self):
        sel = self.listbox_layers.curselection()
        if not sel: return
        i = sel[0]
        if i > 0:
            self.current_layers[i], self.current_layers[i-1] = self.current_layers[i-1], self.current_layers[i]
            val = self.listbox_layers.get(i)
            self.listbox_layers.delete(i)
            self.listbox_layers.insert(i-1, val)
            self.listbox_layers.selection_set(i-1)
            self.update_canvas()

    def move_layer_down(self):
        sel = self.listbox_layers.curselection()
        if not sel: return
        i = sel[0]
        if i < len(self.current_layers) - 1:
            self.current_layers[i], self.current_layers[i+1] = self.current_layers[i+1], self.current_layers[i]
            val = self.listbox_layers.get(i)
            self.listbox_layers.delete(i)
            self.listbox_layers.insert(i+1, val)
            self.listbox_layers.selection_set(i+1)
            self.update_canvas()

    def remove_layer(self):
        vald_index = self.listbox_layers.curselection()
        if not vald_index: return
        index = vald_index[0]
        self.listbox_layers.delete(index)
        self.current_layers.pop(index)
        self.update_canvas()

    def update_canvas(self):
        self.canvas.update_idletasks()
        canvas_width = 700 
            
        self.canvas.delete("all")
        if not self.current_layers:
            self.canvas.create_text(canvas_width/2, 25, text="Inget material tillagt ännu", fill="gray")
            return
            
        total_thick = sum(layer["Tjocklek (mm)"] for layer in self.current_layers)
        if total_thick == 0: return
        
        canvas_height = 50
        current_x = 0
        
        for layer in self.current_layers:
            thick = layer["Tjocklek (mm)"]
            width_px = (thick / total_thick) * canvas_width
            color = layer.get("Color", "#FFFFFF")
            
            self.canvas.create_rectangle(current_x, 0, current_x + width_px, canvas_height, fill=color, outline="black")
            if width_px > 25:
                self.canvas.create_text(current_x + (width_px/2), canvas_height/2, text=f"{int(thick)}", font=("Arial", 8))
            current_x += width_px

    # =====================================================================
    # MATEMATIK & BERÄKNING
    # =====================================================================
    def save_building_part(self):
        namn = self.bygg_name_var.get().strip()
        flode = self.flow_var.get()
        
        if not namn:
            messagebox.showwarning("Saknar namn", "Du måste ge byggnadsdelen ett namn.")
            return
        if not self.current_layers and "Fönster" not in flode:
            messagebox.showwarning("Inga skikt", "Du måste lägga till minst ett skikt.")
            return

        try:
            b_text = self.b_factor_var.get().split()[0].replace(',', '.')       
            b_factor = float(b_text) if b_text else 1.0
            
            du_text = self.delta_u_var.get().split()[0].replace(',', '.')      
            delta_u = float(du_text) if du_text else 0.0
            
            r_si = float(self.rsi_var.get().replace(',', '.'))
            r_se = float(self.rse_var.get().replace(',', '.'))
        except ValueError:
            messagebox.showwarning("Fel inmatning", "Ange giltiga siffror för b-faktor, Delta U, och ytmotstånd.")
            return

        if flode not in HEAT_FLOWS:
            messagebox.showwarning("Fel", "Välj ett giltigt värde för Riktning i rullistan.")
            return

        if "Fönster" in flode:
            self.app_data["saved_parts"].append({
                "namn": namn, "flode": flode, "is_window": True,
                "area_net": 0.0, "area_win": 0.0, "u_win": 1.0, "u_value": 1.0, "layers": [] 
            })
            self.bygg_name_var.set("")
            self.b_factor_var.set(B_FACTORS[0])
            self.delta_u_var.set(DELTA_U_OPTIONS[0])
            self.refresh_parts_list()
            if hasattr(self.app_data.get("main_app_instance"), "sync_all_lists"):
                self.app_data["main_app_instance"].sync_all_lists()
            return

        effective_layers = []
        has_vent = False
        for layer in self.current_layers:
            if layer.get("is_ventilated") or "Ventilerad" in layer["Material"]: 
                has_vent = True
                break
            effective_layers.append(layer)

        if has_vent: r_se = r_si                                                 

        if not effective_layers:
            r_tot_lower = r_si + r_se
            r_tot_upper = r_si + r_se
            r_tot_final = r_si + r_se
        else:
            r_tot_lower = r_si + r_se
            for layer in effective_layers:
                if layer["Type"] == "Air": r_tot_lower += layer["R"]                                    
                else: r_tot_lower += (layer["Tjocklek (mm)"] / 1000) / layer["Lambda_eff"] 

            layer_parts_lists = []
            for layer in effective_layers:
                if layer["Type"] == "Air":
                    layer_parts_lists.append([{"fraction": 1.0, "R": layer["R"]}])
                else:
                    parts = []
                    for part in layer["Parts"]:                                  
                        d_m = layer["Tjocklek (mm)"] / 1000
                        r_part = d_m / part["lambda"]
                        parts.append({"fraction": part["fraction"], "R": r_part})
                    layer_parts_lists.append(parts)

            upper_u_sum = 0
            for path in itertools.product(*layer_parts_lists):
                path_fraction = 1.0
                path_r = r_si + r_se
                for part in path:
                    path_fraction *= part["fraction"]                            
                    path_r += part["R"]                                          
                upper_u_sum += path_fraction / path_r

            r_tot_upper = 1 / upper_u_sum
            r_tot_final = (r_tot_lower + r_tot_upper) / 2
        
        is_ground = False
        is_basement = False
        B_prime = 0.0
        area = 0.0
        perim = 0.0
        wall_w = 0.0
        depth_z = 0.0
        height_above = 0.0
        u_mark = 0.0
        u_luft = 0.0

        if "Platta på mark" in flode:
            try:
                area = float(self.area_var.get().replace(',', '.'))
                perim = float(self.perim_var.get().replace(',', '.'))
                wall_w = float(self.wall_w_var.get().replace(',', '.'))
                if area <= 0 or perim <= 0 or wall_w <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Fel inmatning", "Ange en giltig area, omkrets och väggtjocklek för plattan.")
                return
                
            is_ground = True
            B_prime = area / (0.5 * perim)                                      
            lambda_gr = 2.0                                                     
            d_t = wall_w + lambda_gr * r_tot_final                              
            
            if d_t < B_prime:                                                   
                u_base = (2 * lambda_gr / (math.pi * B_prime + d_t)) * math.log((math.pi * B_prime / d_t) + 1)
            else:                                                               
                u_base = lambda_gr / (0.457 * B_prime + d_t)
                
        elif "Källarvägg" in flode:
            try:
                depth_z = float(self.depth_var.get().replace(',', '.'))
                height_above = float(self.height_above_var.get().replace(',', '.'))
                if depth_z < 0 or height_above < 0 or (depth_z + height_above) <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Fel inmatning", "Ange giltiga värden för djup och höjd över mark.")
                return

            is_basement = True
            r_w = r_tot_final - r_si - r_se 
            lambda_gr = 2.0
            d_w = lambda_gr * (r_si + r_w) 
            
            u_luft = 1 / r_tot_final if height_above > 0 else 0.0                
            
            if depth_z > 0:                                                     
                u_mark = (2 * lambda_gr / (math.pi * depth_z)) * math.log(1 + (math.pi * depth_z / d_w))
            else:
                u_mark = 0.0
                
            u_base = ((depth_z * u_mark) + (height_above * u_luft)) / (depth_z + height_above) 

        else:
            u_base = 1 / r_tot_final

        u_corr = u_base + delta_u                                               
        u_final = u_corr * b_factor                                             

        self.app_data["saved_parts"].append({
            "namn": namn,
            "flode": flode,
            "b_factor": b_factor,
            "delta_u": delta_u,
            "r_si": r_si,
            "r_se": r_se, 
            "r_lower": r_tot_lower,
            "r_upper": r_tot_upper,
            "r_tot": r_tot_final,
            "is_ground": is_ground,
            "is_basement": is_basement, 
            "is_window": False,
            "area_net": area if is_ground else 0.0,
            "area_win": 0.0,
            "u_win": 1.0,
            "perim": perim if is_ground else 0.0,
            "wall_w": wall_w if is_ground else 0.0,
            "depth_z": depth_z,
            "height_above": height_above,
            "u_mark": u_mark,
            "u_luft": u_luft,
            "B_prime": B_prime,
            "u_base": u_base,
            "u_value": u_final,
            "layers": list(self.current_layers) 
        })

        self.bygg_name_var.set("")
        self.b_factor_var.set(B_FACTORS[0])
        self.delta_u_var.set(DELTA_U_OPTIONS[0])
        self.current_layers = []
        self.listbox_layers.delete(0, tk.END)
        self.update_canvas()
        self.refresh_parts_list()
        if hasattr(self.app_data.get("main_app_instance"), "sync_all_lists"):
            self.app_data["main_app_instance"].sync_all_lists()

    def set_bfactor_string(self, b_val):
        b_str = f"{b_val:.2f}"
        full_b_str = b_str
        for opt in B_FACTORS:
            if opt.startswith(b_str):
                full_b_str = opt
                break
        self.b_factor_var.set(full_b_str)

    def set_deltau_string(self, du_val):
        du_str = f"{du_val:.2f}"
        full_du_str = du_str
        for opt in DELTA_U_OPTIONS:
            if opt.startswith(du_str):
                full_du_str = opt
                break
        self.delta_u_var.set(full_du_str)

    def edit_part(self):
        vald_index = self.listbox_parts.curselection()
        if not vald_index: return
        if self.current_layers:
            if not messagebox.askyesno("Varning", "Skriva över osparade ändringar på ritbordet?"): return

        index = vald_index[0]
        part = self.app_data["saved_parts"][index]

        self.bygg_name_var.set(part["namn"])
        self.flow_var.set(part["flode"])
        
        self.set_bfactor_string(part.get("b_factor", 1.00))
        self.set_deltau_string(part.get("delta_u", 0.00))
        
        self.on_flow_change("force_update") 
        self.rsi_var.set(str(part.get("r_si", HEAT_FLOWS.get(part["flode"], {}).get("R_si", 0.13))))
        self.rse_var.set(str(part.get("r_se", HEAT_FLOWS.get(part["flode"], {}).get("R_se", 0.04))))
        
        if part.get("is_ground"):
            self.area_var.set(str(part.get("area_net", "100")))
            self.perim_var.set(str(part.get("perim", "40")))
            self.wall_w_var.set(str(part.get("wall_w", "0.30")))
            
        if part.get("is_basement"):
            self.depth_var.set(str(part.get("depth_z", "1.5")))
            self.height_above_var.set(str(part.get("height_above", "1.0")))
            
        self.current_layers = list(part["layers"])
        
        self.listbox_layers.delete(0, tk.END)
        for layer in self.current_layers:
            if layer["Type"] == "Air":
                temp_r = layer["R"]
            else:
                temp_r = (layer["Tjocklek (mm)"] / 1000) / layer["Lambda_eff"]
            self.listbox_layers.insert(tk.END, f"{layer.get('Tjocklek (mm)', 0):g} mm   |   {layer['Material']}   |   R: {temp_r:.2f}")

        self.app_data["saved_parts"].pop(index)
        self.refresh_parts_list()
        
        if hasattr(self.app_data.get("main_app_instance"), "sync_all_lists"):
            self.app_data["main_app_instance"].sync_all_lists()
            
        self.app_data["moisture_indices"].clear()
        if hasattr(self.app_data.get("main_app_instance"), "tab4_logic") and hasattr(self.app_data["main_app_instance"].tab4_logic, "refresh_moisture_list"):
            self.app_data["main_app_instance"].tab4_logic.refresh_moisture_list()
            
        self.update_canvas()

    def copy_part(self):
        vald_index = self.listbox_parts.curselection()
        if not vald_index: return
        if self.current_layers:
            if not messagebox.askyesno("Varning", "Skriva över osparade ändringar på ritbordet?"): return

        index = vald_index[0]
        part = self.app_data["saved_parts"][index]

        self.bygg_name_var.set(part["namn"] + " (Kopia)")
        self.flow_var.set(part["flode"])
        
        self.set_bfactor_string(part.get("b_factor", 1.00))
        self.set_deltau_string(part.get("delta_u", 0.00))
        
        self.on_flow_change("force_update") 
        self.rsi_var.set(str(part.get("r_si", HEAT_FLOWS.get(part["flode"], {}).get("R_si", 0.13))))
        self.rse_var.set(str(part.get("r_se", HEAT_FLOWS.get(part["flode"], {}).get("R_se", 0.04))))
        
        if part.get("is_ground"):
            self.area_var.set(str(part.get("area_net", "100")))
            self.perim_var.set(str(part.get("perim", "40")))
            self.wall_w_var.set(str(part.get("wall_w", "0.30")))
            
        if part.get("is_basement"):
            self.depth_var.set(str(part.get("depth_z", "1.5")))
            self.height_above_var.set(str(part.get("height_above", "1.0")))
            
        self.current_layers = copy.deepcopy(part["layers"])
        
        self.listbox_layers.delete(0, tk.END)
        for layer in self.current_layers:
            if layer["Type"] == "Air":
                temp_r = layer["R"]
            else:
                temp_r = (layer["Tjocklek (mm)"] / 1000) / layer["Lambda_eff"]
            self.listbox_layers.insert(tk.END, f"{layer.get('Tjocklek (mm)', 0):g} mm   |   {layer['Material']}   |   R: {temp_r:.2f}")

        self.update_canvas()

    def delete_part(self):
        vald_index = self.listbox_parts.curselection()
        if not vald_index: return
        index = vald_index[0]
        self.app_data["saved_parts"].pop(index)
        self.refresh_parts_list()
        
        if hasattr(self.app_data.get("main_app_instance"), "sync_all_lists"):
            self.app_data["main_app_instance"].sync_all_lists()
            
        self.app_data["moisture_indices"].clear()
        if hasattr(self.app_data.get("main_app_instance"), "tab4_logic") and hasattr(self.app_data["main_app_instance"].tab4_logic, "refresh_moisture_list"):
            self.app_data["main_app_instance"].tab4_logic.refresh_moisture_list()

    def refresh_parts_list(self):
        self.listbox_parts.delete(0, tk.END)
        
        for i, part in enumerate(self.app_data["saved_parts"]):
            anet = part.get("area_net", 0.0)
            awin = part.get("area_win", 0.0)
            
            if self.app_data["um_expanded"] and (anet > 0 or awin > 0):
                ext = f"   |   [Area: {anet}m² | Fönster: {awin}m²]"
            else:
                ext = ""
            
            total_thick = sum(layer.get("Tjocklek (mm)", 0) for layer in part.get("layers", []))
                
            self.listbox_parts.insert(tk.END, f"{part['namn']}   |   {total_thick:g} mm   |   U: {part['u_value']:.3f}{ext}")

    def show_guide(self):
        messagebox.showinfo(
            "Guide: Byggnadsdelar & Ritbord",
            "Här skapar du de väggar, tak och golv som utgör din byggnads klimatskärm.\n\n"
            "Lägg alltid till skikten inifrån (varma sidan) och utåt (kalla sidan). Rätt ordning är helt avgörande för fukt- och kondensriskanalysen!\n\n"
            "Klicka på 'Spara färdig Byggnadsdel' när tvärsnittet ser rätt ut."
        )

    def show_r_help(self):
        messagebox.showinfo(
            "Vägledning: Ytmotstånd (Rsi / Rse)",
            "Ytmotståndet representerar det tunna skikt av stillastående luft som finns precis vid ytan på in- och utsidan av byggnadsdelen. Värdena är standardiserade enligt SS-EN ISO 6946:\n\n"
            "• Horisontellt värmeflöde (t.ex. yttervägg): Rsi = 0.13, Rse = 0.04\n"
            "• Uppåtriktat värmeflöde (t.ex. yttertak): Rsi = 0.10, Rse = 0.04\n"
            "• Nedåtriktat värmeflöde (t.ex. golv): Rsi = 0.17, Rse = 0.04\n\n"
            "För Platta på mark och Källarväggar sätts Rse till 0.00, eftersom det inte finns något yttre luftskikt (marken ligger dikt an mot konstruktionen).\n\n"
            "Dessa fält fylls i automatiskt baserat på vilken riktning du har valt, men du kan ändra dem manuellt vid behov."
        )

    def show_b_help(self):
        messagebox.showinfo(
            "Vägledning: Temperaturreduktion (b-faktor)",
            "b-faktorn används för att justera U-värdet för byggnadsdelar som inte gränsar direkt mot utomhusluften, till exempel en innervägg mot en kallvind eller ett golv över en sluten krypgrund.\n\n"
            "Eftersom det ouppvärmda utrymmet fungerar som en isolerande buffertzon blir temperaturdifferensen lägre. b-faktorn minskar därmed den teoretiska värmeförlusten proportionerligt.\n\n"
            "• 1.00 = Direkt mot utomhusluft (Ingen reduktion)\n"
            "• 0.80 = Ouppvärmd vind\n"
            "• 0.70 = Sluten krypgrund\n"
            "• 0.60 = Ouppvärmd källare\n\n"
            "OBS: För Platta på mark och Källarväggar ska b-faktorn alltid vara 1.00. Programmet räknar redan ut markens isolerande effekt via specifika formler (SS-EN ISO 13370), och att sänka b-faktorn skulle leda till att värmemotståndet räknas dubbelt.\n\n"
            "Är du osäker på vad du ska välja, behåll 1.00 för att vara på den säkra sidan."
        )

    def show_du_help(self):
        messagebox.showinfo(
            "Vägledning: Delta U-tillägg (ΔU)",
            "I verkligheten är en vägg sällan lika perfekt som i en teoretisk beräkning. Enligt branschstandarden (SS-EN ISO 6946) gör man därför ett Delta U-tillägg för att kompensera för skruvar, fästdon och luftspringor som oundvikligen försämrar isoleringen.\n\n"
            "Välj det värde som bäst stämmer överens med din konstruktion:\n\n"
            "• 0.00 (Optimalt - Brutna köldbryggor)\n"
            "Används när konstruktionen är mycket välisolerad. Du har till exempel minimerat köldbryggor genom att använda dubbla lager isolering med korslagda reglar, förskjutna skarvar, och du har inga metallskruvar som går rakt igenom isolerskiktet.\n\n"
            "• 0.01 (Liten påverkan - Genomgående reglar)\n"
            "Detta är standard för en vanlig trästomme. Isoleringen ligger i ett enda skikt mellan genomgående träreglar (vilket skapar små köldbryggor längs med trät). Används även om isoleringen fästs med plast- eller rostfria fästdon.\n\n"
            "• 0.03 (Måttlig påverkan - Springor & stålskruvar)\n"
            "Används när du monterar styva isolerskivor där små luftspringor lätt kan uppstå, eller när konstruktionen innehåller vanliga fästskruvar av stål som leder in utekylan rakt genom fasaden.\n\n"
            "• 0.04 (Hög påverkan - Oskyddat tegel)\n"
            "Ett specialvärde för murning. Används vid isolerade dubbla tegelväggar där man inte har lufttätat insidan ordentligt (t.ex. genom slammning). Kall luft kan då röra sig inne i konstruktionen och kyla ner isoleringen.\n\n"
            "• 0.05 (Mycket hög påverkan - Metallreglar)\n"
            "Används vid kraftiga köldbryggor. Typiskt för industribyggnader eller fasader där genomgående metallreglar (t.ex. Z-profiler i stål) skär rakt igenom isoleringen. Stål leder kyla extremt effektivt!\n\n"
            "Tips: Välj antingen ett branschvärde från menyn, eller skriv in ett eget exakt uträknat värde."
        )

    def show_air_r_help(self):
        messagebox.showinfo(
            "Vägledning: R-värde (Oventilerad luftspalt)",
            "En oventilerad (sluten) luftspalt fungerar som isolering eftersom luften står stilla. Värdet beror på hur tjock spalten är och åt vilket håll värmen flödar.\n\n"
            "Enligt SS-EN ISO 6946 gäller följande standardvärden för horisontellt flöde (t.ex. i en yttervägg):\n\n"
            "• 5 mm tjock: R = 0.11 m²K/W\n"
            "• 10 mm tjock: R = 0.15 m²K/W\n"
            "• 15 mm tjock: R = 0.17 m²K/W\n"
            "• 25 mm eller tjockare: R = 0.18 m²K/W\n\n"
            "Obs: Luft isolerar inte bättre bara för att spalten görs tjockare än 25 mm. Om spalten är för tjock börjar luften rotera, vilket flyttar värme och sänker motståndet."
        )