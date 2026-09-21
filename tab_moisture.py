import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import os
from core_logic import RAW_MATERIALS_DB

class TabMoisture:
    def __init__(self, parent, app_data):
        self.parent = parent
        self.app_data = app_data
        
        # --- FLIK 4: KLIMATDATA FÖR FUKTBERÄKNING ---
        self.frame_climate = ttk.LabelFrame(parent, text="Klimatdata & Fuktsimulering", padding=10)
        self.frame_climate.pack(fill="x", padx=15, pady=15)
        self.frame_climate.columnconfigure(2, weight=1)

        ttk.Label(self.frame_climate, text="Innetemp (°C):").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.t_in_var = tk.StringVar(value="21.0")
        ttk.Entry(self.frame_climate, textvariable=self.t_in_var, width=8).grid(row=0, column=1, sticky="w", pady=(0, 5))

        ttk.Button(self.frame_climate, text="❓ Guide", command=self.show_guide).grid(row=0, column=2, sticky="e", pady=(0, 5))

        ttk.Label(self.frame_climate, text="Fukttillskott (Max Δv i g/m³):").grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.delta_v_var = tk.StringVar(value="3.0")
        ttk.Entry(self.frame_climate, textvariable=self.delta_v_var, width=10).grid(row=1, column=1, sticky="w", pady=(0, 5))
        ttk.Button(self.frame_climate, text="?", width=3, command=self.show_fukt_help).grid(row=1, column=2, sticky="w", pady=(0, 5))

        self.lbl_climate = ttk.Label(self.frame_climate, text="Ingen klimatfil laddad.", font=("Arial", 9, "italic"))
        self.lbl_climate.grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 5))

        self.btn_load_epw = ttk.Button(self.frame_climate, text="⛅ Ladda Klimatfil (.epw)", command=self.load_epw_file)
        self.btn_load_epw.grid(row=3, column=0, sticky="w")
        
        frame_fukt_top = ttk.Frame(self.frame_climate)
        frame_fukt_top.grid(row=4, column=0, columnspan=3, sticky="w", pady=(15, 5))
        ttk.Label(frame_fukt_top, text="Välj byggnadsdel att lägga till:", font=("Arial", 9, "bold")).pack(side="left")
        self.fukt_part_var = tk.StringVar()
        self.fukt_part_cb = ttk.Combobox(frame_fukt_top, textvariable=self.fukt_part_var, state="readonly", width=50)
        self.fukt_part_cb.pack(side="left", padx=(10, 0))

        ttk.Label(self.frame_climate, text="Valda delar för analys:", font=("Arial", 9, "bold")).grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 0))
        
        self.listbox_moisture = tk.Listbox(self.frame_climate, height=4, width=110, exportselection=False)
        self.listbox_moisture.grid(row=6, column=0, columnspan=3, pady=(2, 5), sticky="w")
        
        frame_m_btns = ttk.Frame(self.frame_climate)
        frame_m_btns.grid(row=7, column=0, columnspan=3, sticky="w")
        
        ttk.Button(frame_m_btns, text="➕ Lägg till vald del", command=self.add_to_moisture).pack(side="left", padx=(0,5))
        ttk.Button(frame_m_btns, text="🗑️ Ta bort vald", command=self.remove_from_moisture, style="LeftAligned.TButton").pack(side="left", padx=(0,5))
        
        self.btn_sim_fukt = ttk.Button(self.frame_climate, text="💧 Kör fuktanalys", command=self.run_moisture_simulation)
        self.btn_sim_fukt.grid(row=8, column=0, columnspan=3, sticky="w", pady=(10, 5))

    def update_lists(self):
        """Uppdaterar rullgardinsmenyn när nya väggar sparas."""
        part_names = [f"{i+1}. {p['namn']}" for i, p in enumerate(self.app_data["saved_parts"])]
        self.fukt_part_cb['values'] = part_names
        if hasattr(self.fukt_part_cb, "_full_list"):
            self.fukt_part_cb._full_list = part_names
        if not part_names:
            self.fukt_part_var.set("")

    def refresh_moisture_list(self):
        self.listbox_moisture.delete(0, tk.END)
        for idx in self.app_data["moisture_indices"]:
            self.listbox_moisture.insert(tk.END, self.app_data["saved_parts"][idx]["namn"])

    def add_to_moisture(self):
        idx = self.fukt_part_cb.current()
        if idx < 0: 
            messagebox.showwarning("Inget valt", "Du måste välja en byggnadsdel i rullistan först!")
            return
        if idx not in self.app_data["moisture_indices"]:
            self.app_data["moisture_indices"].append(idx)
            self.refresh_moisture_list()

    def remove_from_moisture(self):
        sel = self.listbox_moisture.curselection()
        if not sel: return
        list_idx = sel[0]
        self.app_data["moisture_indices"].pop(list_idx)
        self.refresh_moisture_list()

    def load_epw_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("EnergyPlus Weather", "*.epw")], title="Välj klimatfil...")
        if not filepath: return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            data_lines = lines[8:]                                      
            if len(data_lines) < 8760:
                messagebox.showwarning("Varning", "Filen innehåller färre än 8760 timmar. Är det ett helt år?")
            
            parsed_data = []
            for line in data_lines:
                cols = line.split(',')                                  
                if len(cols) > 8:
                    temp = float(cols[6])                               
                    rh = float(cols[8])                                 
                    parsed_data.append({"temp": temp, "rh": rh})        
            
            self.app_data["climate_data"] = parsed_data
            self.app_data["climate_filename"] = os.path.basename(filepath)
            
            avg_temp = sum(d['temp'] for d in parsed_data) / len(parsed_data)
            self.lbl_climate.config(text=f"Laddad fil: {self.app_data['climate_filename']} ({len(parsed_data)} timmar hittades)\nÅrsmedeltemperatur: {avg_temp:.1f}°C")
            messagebox.showinfo("Laddat", f"Klimatfil '{self.app_data['climate_filename']}' inläst med framgång!")
            
        except Exception as e:
            messagebox.showerror("Fel vid inläsning", f"Kunde inte läsa .epw-filen:\n{e}")

    def _get_v_sat(self, temp_c):
        if temp_c >= 0:
            return 610.5 * math.exp((17.269 * temp_c) / (237.3 + temp_c))
        else:
            return 610.5 * math.exp((21.875 * temp_c) / (265.5 + temp_c))

    def _hour_to_date_str(self, h):
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        months = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]
        day_of_year = int(h // 24)
        hour_of_day = int(h % 24)
        
        m_idx = 0
        while day_of_year >= days_in_month[m_idx] and m_idx < 11:
            day_of_year -= days_in_month[m_idx]
            m_idx += 1
            
        return f"{day_of_year + 1} {months[m_idx]} kl {hour_of_day:02d}:00"

    def _calc_moisture(self, part_idx):
        part = self.app_data["saved_parts"][part_idx]
        layers = part.get("layers", [])
        
        try:
            t_in = float(self.t_in_var.get().replace(',', '.'))         
            delta_v = float(self.delta_v_var.get().replace(',', '.'))   
        except ValueError:
            return None, "Ange giltiga värden för innetemperatur och fukttillskott."

        delta_p_max = (delta_v / 1000.0) * 461.5 * (t_in + 273.15)      
        v_sat_in = self._get_v_sat(t_in)                                

        r_si = part.get("r_si", 0.13)
        r_se = part.get("r_se", 0.04)
        
        thermal_resistances = []                                        
        vapor_resistances = []                                          
        layer_names = []
        effective_layers_for_graph = []
        mu_values = []
        
        for layer in layers:
            if layer.get("is_ventilated") or "Ventilerad" in layer["Material"]: 
                break
                
            layer_names.append(layer["Material"])
            effective_layers_for_graph.append(layer)
            
            if layer["Type"] == "Air":
                thermal_resistances.append(layer["R"])
                vapor_resistances.append(0.0)                           
                mu_values.append(0.0)
            else:
                d_m = layer["Tjocklek (mm)"] / 1000.0                   
                lam_val = layer["Lambda_eff"]
                thermal_resistances.append(d_m / lam_val)               
                
                mu_val = None
                raw_mat_name = layer["Material"]
                raw_data = layer.get("RawData", {})
                
                if raw_data.get("type") == "Eget material" and "mu" in raw_data:
                    mu_val = raw_data["mu"]
                elif "+" in raw_mat_name and "(c/c" in raw_mat_name:
                    m1_name = raw_mat_name.split(" + ")[0].strip()
                    if m1_name in RAW_MATERIALS_DB:
                        mu_val = RAW_MATERIALS_DB[m1_name].get("mu")
                elif raw_mat_name in RAW_MATERIALS_DB:
                    mu_val = RAW_MATERIALS_DB[raw_mat_name].get("mu")
                elif raw_data.get("mat"):
                    full_mat_name = raw_data["mat"]
                    base_mat_name = full_mat_name.split(" [λ=")[0]
                    if base_mat_name in RAW_MATERIALS_DB:
                        mu_val = RAW_MATERIALS_DB[base_mat_name].get("mu")
                
                if mu_val is None:                                      
                    return None, f"Beräkningen avbröts.\n\nÅnggenomgångsmotstånd (µ-värde) saknas för materialet:\n'{raw_mat_name}'"
                
                vapor_resistances.append(mu_val * d_m)                  
                mu_values.append(mu_val)

        r_tot = r_si + sum(thermal_resistances) + r_se                  
        z_tot = sum(vapor_resistances)                                  

        num_interfaces = len(thermal_resistances) + 1                   
        condensation_hours = [0] * num_interfaces
        mold_risk_hours = [0] * num_interfaces
        
        cond_events = [[] for _ in range(num_interfaces)]               
        mold_events = [[] for _ in range(num_interfaces)]
        
        cond_start = [None] * num_interfaces
        mold_start = [None] * num_interfaces
        
        climate_data = self.app_data["climate_data"]
        for h, hour_data in enumerate(climate_data):
            t_out = hour_data["temp"]
            rh_out = hour_data["rh"] / 100.0 
            if rh_out > 1.0: rh_out = 1.0
            
            if t_out <= 0.0:
                current_delta_p = delta_p_max
            elif t_out >= 20.0:
                current_delta_p = 0.0
            else:
                current_delta_p = delta_p_max * (1.0 - (t_out / 20.0))
            
            v_out = self._get_v_sat(t_out) * rh_out
            v_in_calc = v_out + current_delta_p
            v_in = min(v_in_calc, v_sat_in)
            
            current_thermal_R = r_si
            current_vapor_Z = 0.0
            
            for i in range(num_interfaces):
                t_interface = t_in - (t_in - t_out) * (current_thermal_R / r_tot)
                v_sat_interface = self._get_v_sat(t_interface)
                
                if z_tot > 0:
                    v_interface = v_in - (v_in - v_out) * (current_vapor_Z / z_tot)
                else:
                    v_interface = v_out
                
                rh_interface = v_interface / v_sat_interface if v_sat_interface > 0 else 1.0
                
                if v_interface > v_sat_interface:
                    condensation_hours[i] += 1
                    if cond_start[i] is None:
                        cond_start[i] = h
                else:
                    if cond_start[i] is not None:
                        duration = h - cond_start[i]
                        cond_events[i].append({"start": cond_start[i], "duration": duration})
                        cond_start[i] = None
                        
                if rh_interface >= 0.85 and t_interface >= 5.0:
                    mold_risk_hours[i] += 1
                    if mold_start[i] is None:
                        mold_start[i] = h
                else:
                    if mold_start[i] is not None:
                        duration = h - mold_start[i]
                        mold_events[i].append({"start": mold_start[i], "duration": duration})
                        mold_start[i] = None
                
                if i < len(thermal_resistances):
                    current_thermal_R += thermal_resistances[i]
                    current_vapor_Z += vapor_resistances[i]

        total_hours = len(climate_data)
        for i in range(num_interfaces):
            if cond_start[i] is not None:
                cond_events[i].append({"start": cond_start[i], "duration": total_hours - cond_start[i]})
            if mold_start[i] is not None:
                mold_events[i].append({"start": mold_start[i], "duration": total_hours - mold_start[i]})

        max_cond_streak = [max((e["duration"] for e in cond_events[i]), default=0) for i in range(num_interfaces)]
        max_mold_streak = [max((e["duration"] for e in mold_events[i]), default=0) for i in range(num_interfaces)]

        res = {                                                         
            "part": part,
            "layer_names": layer_names,
            "effective_layers": effective_layers_for_graph,
            "t_in": t_in,
            "delta_v": delta_v,
            "num_interfaces": num_interfaces,
            "condensation_hours": condensation_hours,
            "mold_risk_hours": mold_risk_hours,
            "cond_events": cond_events,
            "mold_events": mold_events,
            "max_cond_streak": max_cond_streak,
            "max_mold_streak": max_mold_streak,
            "z_tot": z_tot,
            "mu_values": mu_values
        }
        return res, None

    def run_moisture_simulation(self):
        if not self.app_data.get("climate_data"):
            messagebox.showwarning("Ingen klimatfil", "Du måste ladda en .epw klimatfil först (Sida 4).")
            return
            
        selection = self.listbox_moisture.curselection()
        if not selection:
            messagebox.showwarning("Ingen vägg vald", "Markera en byggnadsdel i fuktlistan (Sida 4) först.")
            return
            
        list_idx = selection[0]
        real_idx = self.app_data["moisture_indices"][list_idx]
        
        res, error_msg = self._calc_moisture(real_idx)
        if error_msg:
            messagebox.showwarning("Fel", error_msg)
            return
            
        self.show_moisture_graph(res["part"], res["effective_layers"], res["condensation_hours"], res["mold_risk_hours"], res["max_cond_streak"], res["max_mold_streak"])

        result_msg = f"Fukt & Kondensrisk (Förenklad Glaser)\nByggnadsdel: {res['part']['namn']}\n"
        result_msg += f"Inomhusklimat: {res['t_in']}°C, Fuktklass tillägg (Max): +{res['delta_v']} g/m³\n\n"
        result_msg += f"Totalt antal simuleringstimmar: {len(self.app_data['climate_data'])}\n"
        result_msg += "-" * 50 + "\n"
        result_msg += "[Insida]\n"
        
        for i in range(res["num_interfaces"]):
            c_hours = res["condensation_hours"][i]
            m_hours = res["mold_risk_hours"][i]
            
            if c_hours > 0 or m_hours > 0:
                result_msg += f" ⚠️ Snitt {i}:\n"
                
                if m_hours > 0:
                    result_msg += f"    Mögelrisk (>85% RF, >5°C): {m_hours}h totalt.\n"
                    top_m = sorted(res["mold_events"][i], key=lambda x: x['duration'], reverse=True)[:5]
                    result_msg += "      Topp 5 längsta perioder:\n"
                    for idx, ev in enumerate(top_m, 1):
                        result_msg += f"      {idx}. {ev['duration']}h (Började: {self._hour_to_date_str(ev['start'])})\n"
                        
                if c_hours > 0:
                    result_msg += f"    Kondensrisk (100% RF): {c_hours}h totalt.\n"
                    top_c = sorted(res["cond_events"][i], key=lambda x: x['duration'], reverse=True)[:5]
                    result_msg += "      Topp 5 längsta perioder:\n"
                    for idx, ev in enumerate(top_c, 1):
                        result_msg += f"      {idx}. {ev['duration']}h (Började: {self._hour_to_date_str(ev['start'])})\n"
            else:
                result_msg += f" ✅ Snitt {i}: OK (0h kondens, 0h mögel)\n"
                
            if i < len(res["layer_names"]):
                result_msg += f"   --- {res['layer_names'][i]} ---\n"
                
        result_msg += "[Utsida / Ventilerad spalt]"
        
        res_win = tk.Toplevel(self.parent)
        res_win.title("Detaljerad Fuktrapport")
        res_win.geometry("500x700")
        
        txt = tk.Text(res_win, wrap="word", font=("Courier", 9))
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", result_msg)
        txt.config(state="disabled")

    def show_moisture_graph(self, part, effective_layers, cond_hours, mold_hours, max_cond, max_mold):
        win = tk.Toplevel(self.parent)
        win.title(f"Grafisk Fuktprofil - {part['namn']}")
        win.geometry("900x750")
        
        canvas = tk.Canvas(win, bg="white")
        canvas.pack(fill="both", expand=True, padx=20, pady=20)
        
        tot_thick = sum(l.get("Tjocklek (mm)", 0) for l in effective_layers)
        if tot_thick == 0: tot_thick = 1
        
        c_width = 800
        c_height = 150
        start_y = 200
        current_x = 50
        
        canvas.create_text(current_x - 30, start_y + c_height/2, text="INSIDA", font=("Arial", 10, "bold"), angle=90)
        canvas.create_text(current_x + c_width + 30, start_y + c_height/2, text="UTSIDA", font=("Arial", 10, "bold"), angle=270)
        
        for i in range(len(effective_layers) + 1):
            lvl = i % 4                                                 
            y_top = start_y - 20 - (lvl * 35)
            y_bot = start_y + c_height + 20 + (lvl * 75)
            
            canvas.create_line(current_x, start_y, current_x, start_y + c_height, fill="black", dash=(4, 4))
            
            canvas.create_line(current_x, start_y, current_x, y_top + 10, fill="gray", dash=(2, 2))
            canvas.create_text(current_x, y_top, text=f"Snitt {i}", font=("Arial", 9, "bold"), anchor="s")
            
            canvas.create_line(current_x, start_y + c_height, current_x, y_bot, fill="gray", dash=(2, 2))
            
            if mold_hours[i] > 0 or cond_hours[i] > 0:                  
                text_str = f"Mögel: {mold_hours[i]}h\n(Max i sträck: {max_mold[i]}h)\nKondens: {cond_hours[i]}h\n(Max i sträck: {max_cond[i]}h)"
                canvas.create_text(current_x, y_bot + 5, text=text_str, fill="red", font=("Arial", 8, "bold"), anchor="n", justify="center")
            else:
                canvas.create_text(current_x, y_bot + 5, text="OK", fill="green", font=("Arial", 8, "bold"), anchor="n")
            
            if i < len(effective_layers):
                layer = effective_layers[i]
                w = (layer.get("Tjocklek (mm)", 0) / tot_thick) * c_width 
                color = layer.get("Color", "#FFFFFF")
                canvas.create_rectangle(current_x, start_y, current_x + w, start_y + c_height, fill=color, outline="black")
                
                name = layer["Material"]
                if len(name) > 20: name = name[:17] + "..."
                angle = 90 if w < 60 else 0                             
                canvas.create_text(current_x + w/2, start_y + c_height/2, text=name, font=("Arial", 8), angle=angle)
                
                current_x += w

    def show_guide(self):
        messagebox.showinfo(
            "Guide: Fuktanalys",
            "Här körs en avancerad fukt- och kondensriskanalys enligt Glaser-metoden (SS-EN ISO 13788).\n\n"
            "1. Ladda ner och välj en lokal klimatfil (.epw). Detta ger programmet verklig väderdata timme för timme, under ett helt referensår.\n"
            "2. Ställ in innetemperatur och fukttillskott (beroende på vilken verksamhet som pågår i huset).\n"
            "3. Välj vilka av dina byggnadsdelar du vill testa och lägg till dem i listan.\n"
            "4. Tryck på 'Kör fuktanalys' för att generera en visuell graf. Du ser direkt om och var i väggen det finns risk för kondens eller mögeltillväxt."
        )

    def show_fukt_help(self):
        messagebox.showinfo(
            "Vägledning: Fukttillskott inomhus",
            "Enligt SS-EN ISO 13788 kan följande maxvärden (Δv) antas beroende på verksamhet:\n\n"
            "• Klass 1 (Förråd / Oanvända utrymmen): +1.0 g/m³\n"
            "• Klass 2 (Kontor, Butiker): +2.0 g/m³\n"
            "• Klass 3 (Bostäder med normal ventilation): +3.0 g/m³\n"
            "• Klass 4 (Bostäder med låg ventilation / Trångboddhet): +4.0 g/m³\n"
            "• Klass 5 (Särskilda byggnader, t.ex. bryggerier, badhus): +6.0 g/m³\n\n"
            "Programmet räknar automatiskt ner detta tillägg till 0 g/m³ när utetemperaturen överstiger +20 °C."
        )