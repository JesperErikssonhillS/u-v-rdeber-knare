import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json

from pdf_reports import PDFGenerator
from tab_project import TabProject
from tab_parts import TabParts
from tab_um import TabUm
from tab_moisture import TabMoisture

class UValueApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hillstatik byggfysik")
        self.root.geometry("950x900")
        
        self.style = ttk.Style()
        self.style.configure("LeftAligned.TButton", anchor="w")
        
        self.app_data = {
            "current_filepath": None,
            "company_var": tk.StringVar(value="Hillstatik AB"), 
            "proj_name_var": tk.StringVar(),
            "proj_num_var": tk.StringVar(),
            "sig_var": tk.StringVar(),
            "kund_var": tk.StringVar(),
            "saved_parts": [],
            "thermal_bridges": [],
            "moisture_indices": [],
            "climate_data": None,
            "climate_filename": "",
            "um_expanded": True,        
            "um_req_var": tk.StringVar(value="0.40"),
            "kb_type_var": tk.StringVar(value="Schablon (% påslag)"),
            "kb_val_var": tk.StringVar(value="20"),
            "main_app_instance": self
        }
        
        self.skapa_scroll_area()
        self.skapa_ui()

    def skapa_scroll_area(self):
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        self.main_canvas = tk.Canvas(self.main_container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.main_canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.main_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all")
            )
        )

        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.main_canvas.bind('<Configure>', self._on_canvas_configure)
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.main_canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        try:
            widget = event.widget
            widget_str = str(widget).lower()
            if 'popdown' in widget_str: return
            if 'listbox' in widget_str:
                if isinstance(widget, str):
                    widget = self.root.nametowidget(widget)
                widget.yview_scroll(int(-1*(event.delta/120)), "units")
                return
        except Exception:
            return
            
        if self.scrollbar.get() != (0.0, 1.0):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def sync_all_lists(self):
        if hasattr(self, "tab2_logic"):
            self.tab2_logic.refresh_parts_list()
            
        if hasattr(self, "tab3_logic"):
            self.tab3_logic.update_lists()
            
        if hasattr(self, "tab4_logic"):
            self.tab4_logic.update_lists()
            self.tab4_logic.refresh_moisture_list()

    def skapa_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arkiv", menu=file_menu)
        file_menu.add_command(label="📂 Öppna projekt", command=self.load_project)
        file_menu.add_command(label="💾 Spara projekt", command=self.save_project)
        file_menu.add_command(label="💾 Spara projekt som...", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Avsluta", command=self.root.quit)

        self.notebook = ttk.Notebook(self.scrollable_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab1_frame = ttk.Frame(self.notebook)
        self.tab2_frame = ttk.Frame(self.notebook)
        self.tab3_frame = ttk.Frame(self.notebook)
        self.tab4_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1_frame, text="1. Projektinfo")
        self.notebook.add(self.tab2_frame, text="2. Byggnadsdelar")
        self.notebook.add(self.tab3_frame, text="3. Um-beräkning")
        self.notebook.add(self.tab4_frame, text="4. Fuktanalys")

        self.tab1_logic = TabProject(self.tab1_frame, self.app_data)
        self.tab2_logic = TabParts(self.tab2_frame, self.app_data)
        self.tab3_logic = TabUm(self.tab3_frame, self.app_data)
        self.tab4_logic = TabMoisture(self.tab4_frame, self.app_data)

        self.pdf_gen = PDFGenerator(self.app_data, calc_moisture_func=self.tab4_logic._calc_moisture)
        
        self.frame_pdf_btns = ttk.Frame(self.scrollable_frame)
        self.frame_pdf_btns.pack(pady=(5, 30))
        
        self.btn_pdf = ttk.Button(self.frame_pdf_btns, text="📄 Generera PDF-rapport (Sammanställning)", command=self.pdf_gen.generate_summary)
        self.btn_pdf.pack(pady=2)
        
        self.btn_tech_pdf = ttk.Button(self.frame_pdf_btns, text="📐 Generera Teknisk Beräkningsrapport", command=self.pdf_gen.generate_technical)
        self.btn_tech_pdf.pack(pady=2)

    def save_project(self):
        if not self.app_data["current_filepath"]:
            self.save_project_as()
            return
            
        data_to_save = {
            "company": self.app_data["company_var"].get(), 
            "proj_name": self.app_data["proj_name_var"].get(),
            "proj_num": self.app_data["proj_num_var"].get(),
            "signature": self.app_data["sig_var"].get(),
            "kund": self.app_data["kund_var"].get(),
            "um_expanded": self.app_data["um_expanded"],
            "um_req": self.app_data["um_req_var"].get(),
            "kb_type": self.app_data["kb_type_var"].get(),
            "kb_val": self.app_data["kb_val_var"].get(),
            "thermal_bridges": self.app_data["thermal_bridges"],
            "saved_parts": self.app_data["saved_parts"],
            "moisture_indices": self.app_data["moisture_indices"]
        }
        try:
            with open(self.app_data["current_filepath"], 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Sparat", "Projektet har sparats!")
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spara projektet:\n{e}")

    def save_project_as(self):
        data_to_save = {
            "company": self.app_data["company_var"].get(), 
            "proj_name": self.app_data["proj_name_var"].get(),
            "proj_num": self.app_data["proj_num_var"].get(),
            "signature": self.app_data["sig_var"].get(),
            "kund": self.app_data["kund_var"].get(),
            "um_expanded": self.app_data["um_expanded"],
            "um_req": self.app_data["um_req_var"].get(),
            "kb_type": self.app_data["kb_type_var"].get(),
            "kb_val": self.app_data["kb_val_var"].get(),
            "thermal_bridges": self.app_data["thermal_bridges"],
            "saved_parts": self.app_data["saved_parts"],
            "moisture_indices": self.app_data["moisture_indices"]
        }
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("U-värdesprojekt", "*.json")], title="Spara projekt som...")
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, indent=4, ensure_ascii=False)
                self.app_data["current_filepath"] = filepath
                messagebox.showinfo("Sparat", "Projektet har sparats!")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte spara projektet:\n{e}")

    def load_project(self):
        filepath = filedialog.askopenfilename(filetypes=[("U-värdesprojekt", "*.json")], title="Öppna projekt...")
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                loaded_company = data.get("company", "")
                self.app_data["company_var"].set(loaded_company if loaded_company else "Hillstatik AB") 
                self.app_data["proj_name_var"].set(data.get("proj_name", ""))
                self.app_data["proj_num_var"].set(data.get("proj_num", ""))
                self.app_data["sig_var"].set(data.get("signature", ""))
                self.app_data["kund_var"].set(data.get("kund", ""))
                self.app_data["um_req_var"].set(data.get("um_req", "0.40"))
                
                self.app_data["kb_type_var"].set(data.get("kb_type", "Schablon (% påslag)"))
                self.app_data["kb_val_var"].set(data.get("kb_val", "20"))
                self.app_data["thermal_bridges"] = data.get("thermal_bridges", [])
                self.app_data["saved_parts"] = data.get("saved_parts", [])
                self.app_data["moisture_indices"] = data.get("moisture_indices", [])
                
                self.app_data["current_filepath"] = filepath
                
                self.sync_all_lists()
                if hasattr(self.tab3_logic, "on_kb_type_change"):
                    self.tab3_logic.on_kb_type_change()
                    self.tab3_logic.refresh_kb_list()
                
                messagebox.showinfo("Laddat", "Projektet har laddats in!")
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte ladda projektet.\n{e}")

if __name__ == "__main__":
    main_root = tk.Tk()
    app = UValueApp(main_root)
    main_root.mainloop()