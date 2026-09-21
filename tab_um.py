import tkinter as tk
from tkinter import ttk, messagebox
from core_logic import KB_TEMPLATES

class TabUm:
    def __init__(self, parent, app_data):
        self.parent = parent
        self.app_data = app_data

        # --- FLIK 3: UM-BERÄKNING ---
        self.frame_um = ttk.LabelFrame(parent, text="Areor & Klimatskärm", padding=10)
        self.frame_um.pack(fill="x", padx=15, pady=15)
        self.frame_um.columnconfigure(3, weight=1)

        frame_um_top = ttk.Frame(self.frame_um)
        frame_um_top.grid(row=0, column=0, columnspan=4, sticky="we", pady=(0, 10))

        ttk.Label(frame_um_top, text="Välj byggnadsdel:", font=("Arial", 9, "bold"), foreground="#D35400").pack(side="left")
        self.um_part_var = tk.StringVar()
        self.um_part_cb = ttk.Combobox(frame_um_top, textvariable=self.um_part_var, state="readonly", width=50)
        self.um_part_cb.pack(side="left", padx=(10, 0))
        self.um_part_cb.bind("<<ComboboxSelected>>", self.on_um_part_select)

        ttk.Button(frame_um_top, text="❓ Guide", command=self.show_guide).pack(side="right", padx=(0, 10))

        ttk.Label(self.frame_um, text="Nettoarea (m²):").grid(row=1, column=0, sticky="w")
        self.um_area_var = tk.StringVar(value="0.0")
        ttk.Entry(self.frame_um, textvariable=self.um_area_var, width=10).grid(row=1, column=1, sticky="w", padx=(0,15))

        ttk.Label(self.frame_um, text="Fönster/Dörrar i denna del (Area m²):").grid(row=1, column=2, sticky="w")
        self.um_win_area_var = tk.StringVar(value="0.0")
        ttk.Entry(self.frame_um, textvariable=self.um_win_area_var, width=8).grid(row=1, column=3, sticky="w")

        ttk.Label(self.frame_um, text="Fönster/Dörrar (U-värde):").grid(row=2, column=2, sticky="w", pady=5)
        self.um_win_u_var = tk.StringVar(value="1.0")
        ttk.Entry(self.frame_um, textvariable=self.um_win_u_var, width=8).grid(row=2, column=3, sticky="w", pady=5)

        ttk.Button(self.frame_um, text="⬇ Spara areor till markerad del", command=self.save_um_to_part).grid(row=3, column=0, columnspan=4, pady=5)

        ttk.Label(self.frame_um, text="Sparade areor (Hela klimatskärmen):", font=("Arial", 9, "bold")).grid(row=4, column=0, columnspan=4, sticky="w", pady=(10,0))
        self.listbox_um_areas = tk.Listbox(self.frame_um, height=5, width=110, exportselection=False)
        self.listbox_um_areas.grid(row=5, column=0, columnspan=4, pady=(2, 5), sticky="w")

        ttk.Separator(self.frame_um, orient="horizontal").grid(row=6, column=0, columnspan=4, sticky="we", pady=10)

        # --- KÖLDBRYGGOR ---
        ttk.Label(self.frame_um, text="Köldbryggor (Hela huset):", font=("Arial", 9, "bold")).grid(row=7, column=0, sticky="w")

        frame_kb_top = ttk.Frame(self.frame_um)
        frame_kb_top.grid(row=8, column=0, sticky="w", pady=5)

        self.kb_type_cb = ttk.Combobox(frame_kb_top, textvariable=self.app_data["kb_type_var"], values=["Schablon (% påslag)", "Manuellt (Specificerade)"], state="readonly", width=25)
        self.kb_type_cb.pack(side="left")
        self.kb_type_cb.bind("<<ComboboxSelected>>", self.on_kb_type_change)
        ttk.Button(frame_kb_top, text="?", width=3, command=self.show_kb_help).pack(side="left", padx=(5,0))

        self.frame_kb_schablon = ttk.Frame(self.frame_um)
        ttk.Label(self.frame_kb_schablon, text="Påslag (%):").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.frame_kb_schablon, textvariable=self.app_data["kb_val_var"], width=10).grid(row=0, column=1, sticky="w", padx=(5,0))
        self.frame_kb_schablon.grid(row=8, column=1, columnspan=3, sticky="w", pady=5)

        self.frame_kb_manual = ttk.Frame(self.frame_um)

        ttk.Label(self.frame_kb_manual, text="Typ / Namn:").grid(row=0, column=0, sticky="w")
        self.kb_name_var = tk.StringVar(value="--- Skriv eget namn ---")
        self.kb_name_cb = ttk.Combobox(self.frame_kb_manual, textvariable=self.kb_name_var, values=list(KB_TEMPLATES.keys()), width=35)
        self.kb_name_cb.grid(row=1, column=0, sticky="w", padx=(0,5))
        self.kb_name_cb.bind("<<ComboboxSelected>>", self.on_kb_template_change)

        ttk.Label(self.frame_kb_manual, text="Längd/Antal:").grid(row=0, column=1, sticky="w")
        self.kb_len_var = tk.StringVar()
        ttk.Entry(self.frame_kb_manual, textvariable=self.kb_len_var, width=8).grid(row=1, column=1, sticky="w", padx=(0,5))

        ttk.Label(self.frame_kb_manual, text="Värde (W/mK):").grid(row=0, column=2, sticky="w")
        self.kb_psi_var = tk.StringVar()
        ttk.Entry(self.frame_kb_manual, textvariable=self.kb_psi_var, width=8).grid(row=1, column=2, sticky="w", padx=(0,5))

        ttk.Button(self.frame_kb_manual, text="Lägg till", command=self.add_bridge).grid(row=1, column=3, sticky="w")

        self.listbox_kb = tk.Listbox(self.frame_kb_manual, height=4, width=90, exportselection=False)
        self.listbox_kb.grid(row=2, column=0, columnspan=4, pady=(5,2), sticky="w")
        ttk.Button(self.frame_kb_manual, text="Ta bort vald köldbrygga", command=self.remove_bridge, style="LeftAligned.TButton").grid(row=3, column=0, columnspan=4, sticky="w")

        ttk.Separator(self.frame_um, orient="horizontal").grid(row=10, column=0, columnspan=4, sticky="we", pady=10)

        ttk.Label(self.frame_um, text="Krav på Um-värde (W/m²K):", font=("Arial", 9, "bold")).grid(row=11, column=0, sticky="w")
        ttk.Entry(self.frame_um, textvariable=self.app_data["um_req_var"], width=10).grid(row=11, column=1, sticky="w", pady=5)

        # Starta UI
        self.on_kb_type_change()
        self.refresh_kb_list()
        self.update_lists()

    def update_lists(self):
        """Denna kallas av main.py när en vägg läggs till i Flik 2."""
        self.listbox_um_areas.delete(0, tk.END)
        part_names = []

        for i, part in enumerate(self.app_data["saved_parts"]):
            anet = part.get("area_net", 0.0)
            awin = part.get("area_win", 0.0)
            orient = part.get("orientation", "Ospecifierat")
            ori_str = f" [{orient.split(' ')[0]}]" if orient != "Ospecifierat" else ""

            part_names.append(f"{i+1}. {part['namn']}")

            um_str = f"{part['namn']}{ori_str}   |   U-värde: {part['u_value']:.3f} W/m²K"
            if anet > 0 or awin > 0:
                um_str += f"   |   Area: {anet} m²"
                if awin > 0:
                    um_str += f" (varav Fönster/Dörr: {awin} m², U-fönster: {part.get('u_win', 1.0):.2f})"
            else:
                um_str += "   |   [Ingen area sparad]"
            self.listbox_um_areas.insert(tk.END, um_str)

        self.um_part_cb['values'] = part_names
        if hasattr(self.um_part_cb, "_full_list"):
            self.um_part_cb._full_list = part_names

        if not part_names:
            self.um_part_var.set("")

    def on_um_part_select(self, _event=None):
        idx = self.um_part_cb.current()
        if idx < 0: return
        part = self.app_data["saved_parts"][idx]
        self.um_area_var.set(part.get("area_net", 0.0))
        self.um_win_area_var.set(part.get("area_win", 0.0))
        self.um_win_u_var.set(part.get("u_win", 1.0))

    def save_um_to_part(self):
        idx = self.um_part_cb.current()
        if idx < 0:
            messagebox.showwarning("Inget valt", "Du måste välja en byggnadsdel i rullistan först!")
            return
        try:
            anet = float(self.um_area_var.get().replace(',', '.'))
            awin = float(self.um_win_area_var.get().replace(',', '.'))
            uwin = float(self.um_win_u_var.get().replace(',', '.'))
            if anet < 0 or awin < 0 or uwin <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Fel", "Ange giltiga siffror för area och u-värde.")
            return

        self.app_data["saved_parts"][idx]["area_net"] = anet
        self.app_data["saved_parts"][idx]["area_win"] = awin
        self.app_data["saved_parts"][idx]["u_win"] = uwin

        # Uppdatera listorna i alla flikar
        if hasattr(self.app_data.get("main_app_instance"), "sync_all_lists"):
            self.app_data["main_app_instance"].sync_all_lists()

        self.um_part_cb.current(idx)

    def on_kb_type_change(self, _event=None):
        if "Schablon" in self.app_data["kb_type_var"].get():
            self.frame_kb_manual.grid_remove()
            self.frame_kb_schablon.grid(row=8, column=1, columnspan=3, sticky="w", pady=5)
        else:
            self.frame_kb_schablon.grid_remove()
            self.frame_kb_manual.grid(row=9, column=0, columnspan=4, sticky="w", pady=5)

        if hasattr(self.app_data.get("main_app_instance"), "scrollable_frame"):
            self.app_data["main_app_instance"].scrollable_frame.update_idletasks()
            self.app_data["main_app_instance"].main_canvas.configure(scrollregion=self.app_data["main_app_instance"].main_canvas.bbox("all"))

    def on_kb_template_change(self, _event=None):
        val = self.kb_name_var.get()
        psi = KB_TEMPLATES.get(val, "")
        if psi != "":
            self.kb_psi_var.set(str(psi))

    def add_bridge(self):
        name = self.kb_name_var.get().strip()
        if name == "--- Skriv eget namn ---" or not name:
            messagebox.showwarning("Fel", "Ange ett giltigt namn på köldbryggan.")
            return
        try:
            length = float(self.kb_len_var.get().replace(',', '.'))
            psi = float(self.kb_psi_var.get().replace(',', '.'))
        except ValueError:
            messagebox.showwarning("Fel inmatning", "Längd och värde måste vara siffror.")
            return

        self.app_data["thermal_bridges"].append({"name": name, "length": length, "psi": psi})
        self.refresh_kb_list()
        self.kb_name_var.set("--- Skriv eget namn ---")
        self.kb_len_var.set("")
        self.kb_psi_var.set("")

    def remove_bridge(self):
        selection = self.listbox_kb.curselection()
        if not selection: return
        self.app_data["thermal_bridges"].pop(selection[0])
        self.refresh_kb_list()

    def refresh_kb_list(self):
        self.listbox_kb.delete(0, tk.END)
        for kb in self.app_data["thermal_bridges"]:
            self.listbox_kb.insert(tk.END, f"{kb['name']} | Längd: {kb['length']} | Värde: {kb['psi']} | Tot: {kb['length']*kb['psi']:.2f} W/K")

    def show_guide(self):
        messagebox.showinfo(
            "Guide: Um-beräkning",
            "Här sammanställer du hela byggnadens klimatskärm för att få fram det genomsnittliga U-värdet (Um).\n\n"
            "1. Välj en sparad byggnadsdel i rullistan.\n"
            "2. Skriv in ytans nettoarea i kvadratmeter (exklusive fönster/dörrar).\n"
            "3. Om ytan har fönster eller dörrar i sig, fyll i deras totala area och genomsnittliga U-värde.\n"
            "4. Tryck 'Spara areor till markerad del'. Då dyker den upp i sammanställningen nedanför.\n"
            "5. Lägg därefter till köldbryggor för hela huset (antingen som ett procentuellt påslag eller genom att manuellt knappa in dem)."
        )

    def show_kb_help(self):
        messagebox.showinfo(
            "Vägledning: Köldbryggor",
            "Köldbryggor är lokala svaga punkter i klimatskärmen där värme lättare kan smita ut, till exempel i vägghörn, fönstersmygar, syllar eller balkonginfästningar.\n\n"
            "Här har du två val för att ta hänsyn till dessa i den slutgiltiga Um-beräkningen:\n\n"
            "1. Schablon (% påslag)\n"
            "Det enklaste sättet. Programmet lägger automatiskt på en fast procentsats på hela byggnadens totala värmeförlust.\n\n"
            "2. Manuellt (Specificerade)\n"
            "Det mer exakta och krävande sättet. Här matar du in varje linjär köldbrygga för sig. Du anger köldbryggans totala löpmeter (L) och dess linjära värmegenomgångskoefficient (Psi-värde, Ψ)."
        )