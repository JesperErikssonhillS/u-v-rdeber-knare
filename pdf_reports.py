import os
import sys
import base64
import subprocess
import math
from tkinter import messagebox, filedialog
from fpdf import FPDF
from datetime import date

# =====================================================================
# LOGGA OCH HJÄLPFUNKTIONER
# =====================================================================
LOGO_BASE64 = ""  # Lägg in text-kodad bild här för PDF-loggan

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _hour_to_date_str(h):
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    months = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]
    day_of_year = int(h // 24)
    hour_of_day = int(h % 24)
    m_idx = 0
    while day_of_year >= days_in_month[m_idx] and m_idx < 11:
        day_of_year -= days_in_month[m_idx]
        m_idx += 1
    return f"{day_of_year + 1} {months[m_idx]} kl {hour_of_day:02d}:00"


# =====================================================================
# PDF-GENERATOR KLASSEN
# =====================================================================
class PDFGenerator:
    def __init__(self, app_data, calc_moisture_func=None):
        self.app_data = app_data
        # Vi kan koppla in fuktberäkningsfunktionen senare när vi bygger flik 4
        self.calc_moisture_func = calc_moisture_func 

    def generate_summary(self):
        data = self.app_data
        
        if not data["saved_parts"]:
            messagebox.showwarning("Tom rapport", "Rapporten är tom.")
            return
            
        if data["um_expanded"]:
            missing = [p['namn'] for p in data["saved_parts"] if p.get('area_net', 0.0) == 0.0]
            if missing:
                svar = messagebox.askyesno(
                    "Varning", 
                    f"Följande delar saknar nettoarea:\n\n{', '.join(missing)}\n\nVill du generera rapporten ändå? (Um-värdet blir felaktigt)"
                )
                if not svar: return
        
        proj_namn = data["proj_name_var"].get().strip() or "Projektnamn"
        foreslaget_filnamn = f"{proj_namn.replace(' ', '_')}_U-värden_Sammanställning.pdf"
        
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=foreslaget_filnamn)
        if not filepath: return 
            
        pdf = FPDF()
        pdf.add_page()
        har_bild = False
        temp_logo_path = "temp_logo_for_pdf.png"
        
        if LOGO_BASE64:
            try:
                with open(temp_logo_path, "wb") as fh:
                    fh.write(base64.b64decode(LOGO_BASE64))
                pdf.image(temp_logo_path, x=75, y=30, w=60)
                har_bild = True
                os.remove(temp_logo_path)
            except Exception: pass 
                
        if not har_bild:
            foretag = data["company_var"].get().strip()
            if foretag:
                pdf.set_y(40)
                pdf.set_font("helvetica", size=24, style="B")
                pdf.cell(0, 10, foretag, new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_y(100)
        pdf.set_font("helvetica", size=24, style="B")
        pdf.cell(0, 15, "Sammanställning: U-värden", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("helvetica", size=14, style="I")
        pdf.cell(0, 10, "Beräkning av värmegenomgångskoefficient", new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_y(160)
        pdf.set_left_margin(60) 

        if data["company_var"].get().strip():
            pdf.set_font("helvetica", size=12, style="B")
            pdf.cell(50, 8, "Företag:", align="L")
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 8, f"{data['company_var'].get()}", new_x="LMARGIN", new_y="NEXT")

        if data["kund_var"].get().strip():
            pdf.set_font("helvetica", size=12, style="B")
            pdf.cell(50, 8, "Kund:", align="L")
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 8, f"{data['kund_var'].get()}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=12, style="B")
        pdf.cell(50, 8, "Projektnamn:", align="L")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, f"{data['proj_name_var'].get()}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=12, style="B")
        pdf.cell(50, 8, "Projektnummer:", align="L")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, f"{data['proj_num_var'].get()}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=12, style="B")
        pdf.cell(50, 8, "Beräknad av:", align="L")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, f"{data['sig_var'].get()}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=12, style="B")
        pdf.cell(50, 8, "Datum:", align="L")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, f"{date.today().strftime('%Y-%m-%d')}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_left_margin(10)

        pdf.add_page()
        
        for part in data["saved_parts"]:
            if part.get("is_window"): continue

            estim_height = 95 + (len(part['layers']) * 6)
            if pdf.get_y() + estim_height > 275:
                pdf.add_page()
                
            pdf.set_font("helvetica", size=14, style="B")
            pdf.cell(0, 10, f"Byggnadsdel: {part['namn']}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", size=10, style="I")
            
            orient = part.get("orientation", "Ospecifierat")
            ori_text = f" | Väderstreck: {orient}" if orient != "Ospecifierat" else ""
            pdf.cell(0, 6, f"Typ: {part['flode']} (Rsi = {part['r_si']}, Rse = {part['r_se']}){ori_text}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            
            pdf.set_font("helvetica", size=11, style="B")
            pdf.cell(0, 6, "Tvärsnitt och skiktuppbyggnad:", new_x="LMARGIN", new_y="NEXT")
            
            total_thick = sum(layer["Tjocklek (mm)"] for layer in part["layers"])
            if total_thick > 0:
                pdf.ln(6) 
                start_y = pdf.get_y()
                current_x = 10
                pdf_max_width = 150 
                rect_height = 12    
                
                pdf.set_font("helvetica", size=9, style="BI")
                pdf.set_text_color(0, 0, 0) 
                pdf.text(current_x, start_y - 1, "INSIDA")
                utsida_w = pdf.get_string_width("UTSIDA")
                pdf.text(current_x + pdf_max_width - utsida_w, start_y - 1, "UTSIDA")
                
                for layer in part["layers"]:
                    w = (layer["Tjocklek (mm)"] / total_thick) * pdf_max_width
                    r, g, b = hex_to_rgb(layer.get("Color", "#FFFFFF"))
                    pdf.set_fill_color(r, g, b)
                    pdf.rect(current_x, start_y, w, rect_height, style="DF")
                    if w > 10:
                        pdf.set_xy(current_x, start_y)
                        pdf.set_text_color(0, 0, 0) 
                        pdf.set_font("helvetica", size=8)
                        pdf.cell(w, rect_height, f"{int(layer['Tjocklek (mm)'])}", align="C")
                    current_x += w
                pdf.set_y(start_y + rect_height + 4)
            
            pdf.set_text_color(0, 0, 0) 
            pdf.set_font("helvetica", size=10)
            
            is_excluded = False
            for i, layer in enumerate(part['layers'], 1):
                if layer.get("is_ventilated") or "Ventilerad" in layer["Material"]:
                    is_excluded = True
                    
                if layer["Type"] == "Air":
                    text = f"  {i}. {layer['Material']} | {layer['Tjocklek (mm)']} mm | R-värde: {layer['R']:.3f}"
                else:
                    lam_val = f"{layer['Lambda_eff']:.3f}" if isinstance(layer['Lambda_eff'], float) else layer['Lambda_eff']
                    r_part = (layer['Tjocklek (mm)'] / 1000) / layer['Lambda_eff']
                    text = f"  {i}. {layer['Material']} | {layer['Tjocklek (mm)']} mm | Lambda (eff): {lam_val} | R-värde: {r_part:.3f}"
                
                if is_excluded:
                    pdf.set_text_color(150, 150, 150) 
                    text += "  [Exkluderad enl. ISO 6946]"
                else:
                    pdf.set_text_color(0, 0, 0)
                    
                pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
                
            pdf.set_text_color(0, 0, 0) 
                
            pdf.ln(3)
            pdf.set_font("helvetica", size=10, style="I")
            
            if part.get("is_ground"):
                pdf.cell(0, 6, "Beräknat enligt SS-EN ISO 6946 samt SS-EN ISO 13370:", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 5, f"Area: {part.get('area_net')} m², Omkrets: {part.get('perim')} m, Yttervägg: {part.get('wall_w', 0.3)} m", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 5, f"Karakteristisk dim B': {part.get('B_prime'):.2f} m", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 5, f"Golvskiktens motstånd (R_tot): {part['r_tot']:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
            elif part.get("is_basement"):
                pdf.cell(0, 6, "Beräknat enligt SS-EN ISO 6946 samt SS-EN ISO 13370 (Källarvägg):", new_x="LMARGIN", new_y="NEXT")
                z = part.get('depth_z', 0)
                h = part.get('height_above', 0)
                pdf.cell(0, 5, f"Djup under mark (z): {z:.2f} m | Höjd över mark: {h:.2f} m", new_x="LMARGIN", new_y="NEXT")
                if z > 0:
                    pdf.cell(0, 5, f"U-värde under mark (U_mark): {part.get('u_mark', 0):.3f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
                if h > 0:
                    pdf.cell(0, 5, f"U-värde över mark (U_luft): {part.get('u_luft', 0):.3f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 5, f"Väggskiktens totala värmemotstånd (R_tot): {part['r_tot']:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(0, 6, "Beräknat enligt SS-EN ISO 6946:", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 5, f"Undre gräns för värmemotstånd (R'' / Isoterm): {part['r_lower']:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 5, f"Övre gräns för värmemotstånd (R' / Parallell): {part['r_upper']:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 5, f"Totalt värmemotstånd (R_tot): {part['r_tot']:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
            
            du = part.get("delta_u", 0.0)
            b = part.get("b_factor", 1.0)
            u_base = part.get("u_base", part.get("u_value"))
            
            if du > 0 or b != 1.0:
                pdf.ln(2)
                pdf.set_font("helvetica", size=10, style="B")
                pdf.cell(0, 5, f"Grund U-värde (U_c): {u_base:.3f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", size=10, style="I")
                if du > 0:
                    pdf.cell(0, 5, f"Korrektionsterm (Delta U): +{du:.3f} W/(m²K) (Fästdon/Spalter)", new_x="LMARGIN", new_y="NEXT")
                if b != 1.0:
                    pdf.cell(0, 5, f"Temperaturreduktion (b-faktor): {b:.2f} (Mot ouppvärmt utrymme)", new_x="LMARGIN", new_y="NEXT")

            pdf.ln(3)
            pdf.set_font("helvetica", size=12, style="B")
            area_text = f"  [Area: {part.get('area_net', 0)} m²]" if data["um_expanded"] else ""
            pdf.cell(0, 8, f"U-värde för {part['namn']}: {part['u_value']:.3f} W/(m²K){area_text}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        if data["um_expanded"]:
            pdf.add_page()
            pdf.set_font("helvetica", size=16, style="B")
            pdf.cell(0, 10, "Sammanställning: Genomsnittligt U-värde (Um)", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)

            pdf.set_font("helvetica", size=10, style="B")
            pdf.cell(80, 8, "Byggnadsdel", border=1)
            pdf.cell(30, 8, "Area (A) [m²]", border=1, align="C")
            pdf.cell(40, 8, "U-värde (U) [W/m²K]", border=1, align="C")
            pdf.cell(40, 8, "U * A [W/K]", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("helvetica", size=10)
            total_area = 0.0
            total_ua = 0.0

            for part in data["saved_parts"]:
                anet = part.get('area_net', 0.0)
                awin = part.get('area_win', 0.0)
                u = part['u_value']
                uwin = part.get('u_win', 1.0)
                
                orient = part.get("orientation", "Ospecifierat")
                ori_suffix = f" ({orient.split(' ')[0]})" if orient != "Ospecifierat" else ""
                
                if anet > 0:
                    ua = anet * u
                    total_area += anet
                    total_ua += ua
                    display_name = (part['namn'][:25] + '..') if len(part['namn']) > 25 else part['namn']
                    display_name += ori_suffix
                    
                    pdf.cell(80, 8, display_name, border=1)
                    pdf.cell(30, 8, f"{anet:.1f}", border=1, align="C")
                    pdf.cell(40, 8, f"{u:.3f}", border=1, align="C")
                    pdf.cell(40, 8, f"{ua:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                
                if awin > 0:
                    uawin = awin * uwin
                    total_area += awin
                    total_ua += uawin
                    pdf.set_text_color(100, 100, 100) 
                    pdf.cell(80, 8, "  -> Fönster/Dörrar i ovanstående", border=1)
                    pdf.cell(30, 8, f"{awin:.1f}", border=1, align="C")
                    pdf.cell(40, 8, f"{uwin:.3f}", border=1, align="C")
                    pdf.cell(40, 8, f"{uawin:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_text_color(0, 0, 0)

            kb_type = data["kb_type_var"].get()
            kb_ua = 0.0
            
            if "%" in kb_type:
                try: kb_val = float(data["kb_val_var"].get())
                except ValueError: kb_val = 0.0
                kb_ua = total_ua * (kb_val / 100)
                
                pdf.set_font("helvetica", size=10, style="I")
                pdf.cell(80, 8, f"Köldbryggor ({kb_val}% påslag)", border=1)
                pdf.cell(30, 8, "-", border=1, align="C")
                pdf.cell(40, 8, "-", border=1, align="C")
                pdf.cell(40, 8, f"{kb_ua:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_font("helvetica", size=10, style="I")
                for kb in data["thermal_bridges"]:
                    b_ua = kb['length'] * kb['psi']
                    kb_ua += b_ua
                    pdf.cell(80, 8, f"Köldbrygga: {kb['name'][:22]}", border=1)
                    pdf.cell(30, 8, f"{kb['length']} m/st", border=1, align="C")
                    pdf.cell(40, 8, f"{kb['psi']} W/mK", border=1, align="C")
                    pdf.cell(40, 8, f"{b_ua:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            
            total_ua += kb_ua
            
            pdf.ln(5)
            # =====================================================================
            # 🧮 BERÄKNING: GENOMSNITTLIGT U-VÄRDE (Um)
            # =====================================================================
            pdf.set_font("helvetica", size=11, style="B")
            pdf.cell(0, 6, "Summering:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("courier", size=9)
            pdf.cell(0, 6, f"Summa(A_i) = Omslutande area (A_om) = {total_area:.2f} m²", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Summa(U*A + Psi*L) = Total specifik värmeförlust = {total_ua:.2f} W/K", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            
            um_result = (total_ua / total_area) if total_area > 0 else 0.0 
            pdf.cell(0, 6, f"Um = {total_ua:.2f} / {total_area:.2f} = {um_result:.4f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(5)
            pdf.set_font("helvetica", size=14, style="B")
            pdf.cell(0, 10, f"RESULTAT Um: {um_result:.3f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
            
            try:
                um_req = float(data["um_req_var"].get())
            except ValueError:
                um_req = 0.0

            requirement_status_value = data.get("print_um_requirement_status")
            if hasattr(requirement_status_value, "get"):
                include_requirement_status = bool(requirement_status_value.get())
            else:
                include_requirement_status = bool(requirement_status_value if requirement_status_value is not None else True)

            if um_req > 0 and include_requirement_status:
                pdf.set_font("helvetica", size=12, style="I")
                pdf.cell(0, 6, f"Krav på Um-värde: {um_req:.3f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")

                if round(um_result, 3) <= round(um_req, 3):
                    pdf.set_text_color(0, 150, 0) 
                    pdf.set_font("helvetica", size=14, style="B")
                    pdf.cell(0, 10, "Bedömning: KRAVET UPPFYLLS", new_x="LMARGIN", new_y="NEXT")
                else:
                    pdf.set_text_color(220, 0, 0) 
                    pdf.set_font("helvetica", size=14, style="B")
                    pdf.cell(0, 10, "Bedömning: KRAVET UPPFYLLS EJ", new_x="LMARGIN", new_y="NEXT")

                pdf.set_text_color(0, 0, 0)

        try:
            pdf.output(filepath)
            messagebox.showinfo("Succé!", "Rapporten sparades!")
            
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.call(["open", filepath])
            else:
                subprocess.call(["xdg-open", filepath])
                
        except Exception as e:
            messagebox.showerror("Fel vid sparning", f"Kunde inte spara filen: {e}")

    def generate_technical(self):
        data = self.app_data
        
        if not data["saved_parts"]:
            messagebox.showwarning("Tom rapport", "Rapporten är tom.")
            return
            
        proj_namn = data["proj_name_var"].get().strip() or "Projektnamn"
        foreslaget_filnamn = f"{proj_namn.replace(' ', '_')}_Teknisk_Beräkningsrapport.pdf"
        
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=foreslaget_filnamn)
        if not filepath: return 
            
        pdf = FPDF()
        
        pdf.add_page()
        pdf.set_y(40)
        foretag = data["company_var"].get().strip()
        if foretag:
            pdf.set_font("helvetica", size=24, style="B")
            pdf.cell(0, 10, foretag, new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_y(100)
        pdf.set_font("helvetica", size=24, style="B")
        pdf.cell(0, 15, "Teknisk Beräkningsrapport", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("helvetica", size=12, style="I")
        pdf.cell(0, 10, "Steg-för-steg beräkning av U-värden enligt SS-EN ISO 6946 / 13370", new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_y(160)
        pdf.set_left_margin(60) 
        pdf.set_font("helvetica", size=12, style="B")
        pdf.cell(50, 8, "Projektnamn:", align="L")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, f"{data['proj_name_var'].get()}", new_x="LMARGIN", new_y="NEXT")

        if data["kund_var"].get().strip():
            pdf.set_font("helvetica", size=12, style="B")
            pdf.cell(50, 8, "Kund:", align="L")
            pdf.set_font("helvetica", size=12)
            pdf.cell(0, 8, f"{data['kund_var'].get()}", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=12, style="B")
        pdf.cell(50, 8, "Projektnummer:", align="L")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, f"{data['proj_num_var'].get()}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=12, style="B")
        pdf.cell(50, 8, "Beräknad av:", align="L")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, f"{data['sig_var'].get()}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=12, style="B")
        pdf.cell(50, 8, "Datum:", align="L")
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 8, f"{date.today().strftime('%Y-%m-%d')}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_left_margin(10)

        for part in data["saved_parts"]:
            if part.get("is_window"): continue
            
            pdf.add_page()
            pdf.set_font("helvetica", size=14, style="B")
            pdf.cell(0, 10, f"Detaljberäkning U-värde: {part['namn']}", new_x="LMARGIN", new_y="NEXT")
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_font("helvetica", size=10, style="I")
            pdf.cell(0, 6, f"Värmeflöde: {part['flode']}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Inre ytmotstånd (R_si) = {part['r_si']} m²K/W", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Yttre ytmotstånd (R_se) = {part['r_se']} m²K/W", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            pdf.set_font("helvetica", size=11, style="B")
            pdf.cell(0, 8, "1. Skiktuppbyggnad och värmemotstånd (R = d / Lambda):", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("courier", size=9) 
            
            sum_r_solid = 0.0
            is_excluded = False
            for i, layer in enumerate(part['layers'], 1):
                if layer.get("is_ventilated") or "Ventilerad" in layer["Material"]:
                    is_excluded = True
                    pdf.set_text_color(150, 150, 150)
                    pdf.cell(0, 5, f"Skikt {i}: {layer['Material']} (Ventilerad luftspalt)", new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 5, "-> Exkluderas från beräkning enligt SS-EN ISO 6946.", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(2)
                    continue
                
                if is_excluded:
                    pdf.set_text_color(150, 150, 150)
                    pdf.cell(0, 5, f"Skikt {i}: {layer['Material']}", new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 5, "-> Exkluderas (Ligger utanför ventilerad luftspalt).", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(2)
                    continue
                    
                pdf.set_text_color(0, 0, 0)
                if layer["Type"] == "Air":
                    r_val = layer['R']
                    pdf.cell(0, 5, f"Skikt {i}: {layer['Material']}", new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 5, f"R_{i} = Fast värde för sluten luftspalt = {r_val:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
                    sum_r_solid += r_val
                else:
                    d_m = layer['Tjocklek (mm)'] / 1000
                    lam_val = layer['Lambda_eff']
                    r_val = d_m / lam_val
                    pdf.cell(0, 5, f"Skikt {i}: {layer['Material']}", new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 5, f"R_{i} = {d_m:.3f} m / {lam_val:.3f} W/mK = {r_val:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
                    sum_r_solid += r_val
                pdf.ln(2)

            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
            
            pdf.set_font("helvetica", size=11, style="B")
            pdf.cell(0, 8, "2. Ekvivalent värmemotstånd (R_tot):", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("courier", size=9)
            
            has_inhomogeneous = any(len(l.get("Parts", [])) > 1 for l in part['layers'] if not l.get("is_ventilated"))
            
            if not has_inhomogeneous:
                pdf.cell(0, 6, "Samtliga skikt är homogena.", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, "R_tot = R_si + Summa(R_i) + R_se", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"R_tot = {part['r_si']} + {sum_r_solid:.3f} + {part['r_se']} = {part['r_tot']:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(0, 6, "Byggnadsdelen innehåller inhomogena skikt (t.ex. regelverk).", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, "Enligt SS-EN ISO 6946 beräknas R_tot som medelvärdet av övre (R') och undre (R'') gräns.", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                pdf.cell(0, 6, f"R'' (Isotermer) = {part['r_lower']:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"R' (Parallella värmeflöden) = {part['r_upper']:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"R_tot = (R'' + R') / 2 = ({part['r_lower']:.3f} + {part['r_upper']:.3f}) / 2 = {part['r_tot']:.3f} m²K/W", new_x="LMARGIN", new_y="NEXT")

            pdf.ln(5)
            
            pdf.set_font("helvetica", size=11, style="B")
            pdf.cell(0, 8, "3. Beräkning av U-värde:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("courier", size=9)

            if part.get("is_ground"):
                A = part.get('area_net', 0)
                P = part.get('perim', 0)
                w = part.get('wall_w', 0.3)
                B_prime = part.get('B_prime', 0)
                
                pdf.cell(0, 6, "SS-EN ISO 13370 - Platta på mark", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, "Karakteristisk dimension (B') = Area / (0.5 * Omkrets)", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"B' = {A} / (0.5 * {P}) = {B_prime:.3f} m", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                
                dt = w + (2.0 * part['r_tot'])
                pdf.cell(0, 6, "Ekvivalent tjocklek (d_t) = w + (Lambda_mark * R_tot)", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"d_t = {w} + (2.0 * {part['r_tot']:.3f}) = {dt:.3f} m", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                
                if dt < B_prime:
                    pdf.cell(0, 6, f"Eftersom d_t < B' ({dt:.3f} < {B_prime:.3f}) används logaritmisk formel:", new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 6, f"U_base = (2 * Lambda_mark / (pi * B' + d_t)) * ln( (pi * B' / d_t) + 1 )", new_x="LMARGIN", new_y="NEXT")
                else:
                    pdf.cell(0, 6, f"Eftersom d_t >= B' ({dt:.3f} >= {B_prime:.3f}) används direkt formel:", new_x="LMARGIN", new_y="NEXT")
                    pdf.cell(0, 6, f"U_base = Lambda_mark / (0.457 * B' + d_t)", new_x="LMARGIN", new_y="NEXT")
                    
                pdf.cell(0, 6, f"U_base = {part.get('u_base'):.4f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")

            elif part.get("is_basement"):
                z = part.get('depth_z', 0)
                h = part.get('height_above', 0)
                u_mark = part.get('u_mark', 0)
                u_luft = part.get('u_luft', 0)
                
                pdf.cell(0, 6, "SS-EN ISO 13370 - Källarvägg (Viktning ovan/under mark)", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"Höjd under mark (z): {z} m", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, "U_mark beräknas via d_w = Lambda_mark * (R_si + R_w)", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"U_mark = {u_mark:.4f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                pdf.cell(0, 6, f"Höjd över mark (h): {h} m", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"U_luft = 1 / R_tot = {u_luft:.4f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                pdf.cell(0, 6, "U_base = (z * U_mark + h * U_luft) / (z + h)", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"U_base = ({z} * {u_mark:.4f} + {h} * {u_luft:.4f}) / ({z+h}) = {part.get('u_base'):.4f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")

            else:
                pdf.cell(0, 6, "Grundekvation för värmegenomgångskoefficient:", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, "U_base = 1 / R_tot", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"U_base = 1 / {part['r_tot']:.3f} = {part.get('u_base', part['u_value']):.4f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(5)
            
            pdf.set_font("helvetica", size=11, style="B")
            pdf.cell(0, 8, "4. Korrektioner och slutgiltigt värde:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("courier", size=9)
            
            du = part.get("delta_u", 0.0)
            b = part.get("b_factor", 1.0)
            u_base = part.get("u_base", part['u_value'])
            
            pdf.cell(0, 6, f"Delta U-tillägg (Fästdon/Spalter) = {du:.4f}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"b-faktor (Temperaturreduktion) = {b:.2f}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            pdf.cell(0, 6, "Slutgiltigt U = (U_base + Delta_U) * b", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Slutgiltigt U = ({u_base:.4f} + {du:.4f}) * {b:.2f}", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(5)
            pdf.set_font("helvetica", size=14, style="B")
            pdf.cell(0, 10, f"U-VÄRDE: {part['u_value']:.4f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")

        if data["um_expanded"]:
            pdf.add_page()
            pdf.set_font("helvetica", size=16, style="B")
            pdf.cell(0, 10, "Sammanställning: Genomsnittligt U-värde (Um)", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)

            pdf.set_font("helvetica", size=10, style="B")
            pdf.cell(80, 8, "Byggnadsdel", border=1)
            pdf.cell(30, 8, "Area (A) [m²]", border=1, align="C")
            pdf.cell(40, 8, "U-värde (U) [W/m²K]", border=1, align="C")
            pdf.cell(40, 8, "U * A [W/K]", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("helvetica", size=10)
            total_area = 0.0
            total_ua = 0.0

            for part in data["saved_parts"]:
                anet = part.get('area_net', 0.0)
                awin = part.get('area_win', 0.0)
                u = part['u_value']
                uwin = part.get('u_win', 1.0)
                
                orient = part.get("orientation", "Ospecifierat")
                ori_suffix = f" ({orient.split(' ')[0]})" if orient != "Ospecifierat" else ""
                
                if anet > 0:
                    ua = anet * u
                    total_area += anet
                    total_ua += ua
                    display_name = (part['namn'][:25] + '..') if len(part['namn']) > 25 else part['namn']
                    display_name += ori_suffix
                    
                    pdf.cell(80, 8, display_name, border=1)
                    pdf.cell(30, 8, f"{anet:.1f}", border=1, align="C")
                    pdf.cell(40, 8, f"{u:.3f}", border=1, align="C")
                    pdf.cell(40, 8, f"{ua:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                
                if awin > 0:
                    uawin = awin * uwin
                    total_area += awin
                    total_ua += uawin
                    pdf.set_text_color(100, 100, 100) 
                    pdf.cell(80, 8, "  -> Fönster/Dörrar i ovanstående", border=1)
                    pdf.cell(30, 8, f"{awin:.1f}", border=1, align="C")
                    pdf.cell(40, 8, f"{uwin:.3f}", border=1, align="C")
                    pdf.cell(40, 8, f"{uawin:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_text_color(0, 0, 0)

            kb_type = data["kb_type_var"].get()
            kb_ua = 0.0
            
            if "%" in kb_type:
                try: kb_val = float(data["kb_val_var"].get())
                except ValueError: kb_val = 0.0
                kb_ua = total_ua * (kb_val / 100)
                
                pdf.set_font("helvetica", size=10, style="I")
                pdf.cell(80, 8, f"Köldbryggor ({kb_val}% påslag)", border=1)
                pdf.cell(30, 8, "-", border=1, align="C")
                pdf.cell(40, 8, "-", border=1, align="C")
                pdf.cell(40, 8, f"{kb_ua:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_font("helvetica", size=10, style="I")
                for kb in data["thermal_bridges"]:
                    b_ua = kb['length'] * kb['psi']
                    kb_ua += b_ua
                    pdf.cell(80, 8, f"Köldbrygga: {kb['name'][:22]}", border=1)
                    pdf.cell(30, 8, f"{kb['length']} m/st", border=1, align="C")
                    pdf.cell(40, 8, f"{kb['psi']} W/mK", border=1, align="C")
                    pdf.cell(40, 8, f"{b_ua:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            
            total_ua += kb_ua
            
            pdf.ln(5)
            # =====================================================================
            # 🧮 BERÄKNING: GENOMSNITTLIGT U-VÄRDE (Um)
            # =====================================================================
            pdf.set_font("helvetica", size=11, style="B")
            pdf.cell(0, 6, "Summering:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("courier", size=9)
            pdf.cell(0, 6, f"Summa(A_i) = Omslutande area (A_om) = {total_area:.2f} m²", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Summa(U*A + Psi*L) = Total specifik värmeförlust = {total_ua:.2f} W/K", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            
            um_result = (total_ua / total_area) if total_area > 0 else 0.0 
            pdf.cell(0, 6, f"Um = {total_ua:.2f} / {total_area:.2f} = {um_result:.4f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(5)
            pdf.set_font("helvetica", size=14, style="B")
            pdf.cell(0, 10, f"RESULTAT Um: {um_result:.3f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")
            
            try:
                um_req = float(data["um_req_var"].get())
            except ValueError:
                um_req = 0.0

            if um_req > 0:
                pdf.set_font("helvetica", size=12, style="I")
                pdf.cell(0, 6, f"Krav på Um-värde: {um_req:.3f} W/(m²K)", new_x="LMARGIN", new_y="NEXT")

                if round(um_result, 3) <= round(um_req, 3):
                    pdf.set_text_color(0, 150, 0) 
                    pdf.set_font("helvetica", size=14, style="B")
                    pdf.cell(0, 10, "Bedömning: KRAVET UPPFYLLS", new_x="LMARGIN", new_y="NEXT")
                else:
                    pdf.set_text_color(220, 0, 0) 
                    pdf.set_font("helvetica", size=14, style="B")
                    pdf.cell(0, 10, "Bedömning: KRAVET UPPFYLLS EJ", new_x="LMARGIN", new_y="NEXT")

                pdf.set_text_color(0, 0, 0)

        # --- FUKTRAPPORT DEL ---
        if data["moisture_indices"] and data["climate_data"] and self.calc_moisture_func:
            for _, real_idx in enumerate(data["moisture_indices"]):
                res, error_msg = self.calc_moisture_func(real_idx)
                if error_msg or not res:
                    continue
                    
                pdf.add_page()
                pdf.set_font("helvetica", size=14, style="B")
                pdf.cell(0, 10, "Teknisk Beräkningsrapport: Fukt- och Kondensrisk", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", size=12, style="I")
                pdf.cell(0, 8, f"Byggnadsdel: {res['part']['namn']}", new_x="LMARGIN", new_y="NEXT")
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
                
                pdf.set_font("helvetica", size=11, style="B")
                pdf.cell(0, 8, "1. Förutsättningar och Randvillkor", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", size=10)
                pdf.multi_cell(0, 6, "Beräkningen är utförd timme för timme över ett referensår (8760 timmar) enligt metoden beskriven i SS-EN ISO 13788.", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"Utomhusklimat: Klimatdata hämtad från {data['climate_filename']} (Temperatur och RF).", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"Inomhustemperatur: {res['t_in']} °C", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"Fukttillskott inomhus (Delta v): Max +{res['delta_v']} g/m³.", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", size=9, style="I")
                pdf.multi_cell(0, 5, "Enligt ISO 13788 reduceras fukttillskottet linjärt när utomhustemperaturen överstiger 0 °C och sätts till 0 g/m³ vid utomhustemperaturer över +20 °C.", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)
                
                pdf.set_font("helvetica", size=11, style="B")
                pdf.cell(0, 8, "2. Beräkningsmetodik och Ekvationer", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", size=10)
                pdf.multi_cell(0, 6, "A. Temperaturprofil (R = Värmemotstånd): \n   Temp_i = Temp_in - (Temp_in - Temp_out) * (Summa_R_i / R_tot)", new_x="LMARGIN", new_y="NEXT")
                pdf.multi_cell(0, 6, "B. Mättnadsångtryck v_sat (Magnus-Tetens formel över vatten/is): \n   v_sat(Temp) = 610.5 * e^(17.269 * Temp / (237.3 + Temp))", new_x="LMARGIN", new_y="NEXT")
                pdf.multi_cell(0, 6, "C. Faktiskt ångtryck v_i (Z = Ångmotstånd, Z = my * d): \n   v_i = v_in - (v_in - v_out) * (Summa_Z_i / Z_tot)", new_x="LMARGIN", new_y="NEXT")
                pdf.multi_cell(0, 6, "D. Kriterier för fuktrisk: \n   - Kondensrisk: v_i > v_sat \n   - Risk för mögeltillväxt: RF (v_i / v_sat) > 85 % OCH Temp_i >= +5 °C", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)
                
                pdf.set_font("helvetica", size=11, style="B")
                pdf.cell(0, 8, "3. Materialens Ånggenomgångsmotstånd", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", size=9, style="B")
                pdf.cell(15, 8, "Skikt", border=1)
                pdf.cell(85, 8, "Material", border=1)
                pdf.cell(30, 8, "Tjocklek (m)", border=1, align="C")
                pdf.cell(30, 8, "My-värde", border=1, align="C")
                pdf.cell(30, 8, "Sd (m)", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font("helvetica", size=9)
                for i, layer in enumerate(res["effective_layers"]):
                    d_m = layer.get("Tjocklek (mm)", 0) / 1000
                    mu = res["mu_values"][i]
                    sd = d_m * mu
                    
                    name = layer["Material"]
                    if len(name) > 40: name = name[:37] + "..."
                    
                    pdf.cell(15, 6, str(i+1), border=1)
                    pdf.cell(85, 6, name, border=1)
                    pdf.cell(30, 6, f"{d_m:.3f}", border=1, align="C")
                    if layer["Type"] == "Air":
                        pdf.cell(30, 6, "-", border=1, align="C")
                        pdf.cell(30, 6, "0.00", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.cell(30, 6, f"{mu:.1f}", border=1, align="C")
                        pdf.cell(30, 6, f"{sd:.2f}", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font("helvetica", size=9, style="B")
                pdf.cell(100, 6, "Totalt Ångmotstånd (Sd_tot):", border=1)
                pdf.cell(90, 6, f"{res['z_tot']:.2f} m", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
                
                pdf.ln(5)
                pdf.set_font("helvetica", size=11, style="B")
                pdf.cell(0, 6, "Tvärsnitt och Snittplacering (Gränssnitt):", new_x="LMARGIN", new_y="NEXT")
                
                tot_thick = sum(layer.get("Tjocklek (mm)", 0) for layer in res["effective_layers"])
                if tot_thick == 0: tot_thick = 1
                
                pdf.ln(4) 
                start_y = pdf.get_y() + 8
                current_x = 20
                pdf_max_width = 150 
                rect_height = 12    
                
                for layer in res["effective_layers"]:
                    w = (layer.get("Tjocklek (mm)", 0) / tot_thick) * pdf_max_width
                    r, g, b = hex_to_rgb(layer.get("Color", "#FFFFFF"))
                    pdf.set_fill_color(r, g, b)
                    pdf.rect(current_x, start_y, w, rect_height, style="DF")
                    current_x += w
                    
                snitt_x = 20
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("helvetica", size=8, style="B")
                for i in range(res["num_interfaces"]):
                    lvl = i % 3
                    y_text = start_y - 2 - (lvl * 4)
                    
                    for dy in range(0, rect_height + 8, 2):
                        if (dy//2) % 2 == 0:
                            pdf.line(snitt_x, y_text + 2 + dy, snitt_x, y_text + 2 + dy + 2)
                            
                    pdf.text(snitt_x - 3, y_text, f"S{i}")
                    
                    if i < len(res["effective_layers"]):
                        w = (res["effective_layers"][i].get("Tjocklek (mm)", 0) / tot_thick) * pdf_max_width
                        snitt_x += w
                        
                pdf.set_y(start_y + rect_height + 5)
                
                pdf.ln(5)
                pdf.set_font("helvetica", size=11, style="B")
                pdf.cell(0, 8, "4. Resultat av Årssimulering (8760 timmar)", new_x="LMARGIN", new_y="NEXT")
                
                found_issues = False
                for i in range(res["num_interfaces"]):
                    c_hours = res["condensation_hours"][i]
                    m_hours = res["mold_risk_hours"][i]
                    
                    if c_hours > 0 or m_hours > 0:
                        found_issues = True
                        pdf.set_font("helvetica", size=10, style="B")
                        pdf.cell(0, 6, f"Snitt {i} (Gränssnitt efter skikt {i}):", new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.set_font("helvetica", size=9)
                        if m_hours > 0:
                            pdf.cell(0, 5, f"  - Mögelrisk (>85% RF, >5 °C): {m_hours} h totalt.", new_x="LMARGIN", new_y="NEXT")
                            top_m = sorted(res["mold_events"][i], key=lambda x: x['duration'], reverse=True)[:5]
                            for idx, ev in enumerate(top_m, 1):
                                pdf.cell(0, 5, f"      Topp {idx}: {ev['duration']} h i sträck (Började: {_hour_to_date_str(ev['start'])})", new_x="LMARGIN", new_y="NEXT")
                                
                        if c_hours > 0:
                            pdf.cell(0, 5, f"  - Kondensrisk (100% RF): {c_hours} h totalt.", new_x="LMARGIN", new_y="NEXT")
                            top_c = sorted(res["cond_events"][i], key=lambda x: x['duration'], reverse=True)[:5]
                            for idx, ev in enumerate(top_c, 1):
                                pdf.cell(0, 5, f"      Topp {idx}: {ev['duration']} h i sträck (Började: {_hour_to_date_str(ev['start'])})", new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(2)
                        
                if not found_issues:
                    pdf.set_font("helvetica", size=10)
                    pdf.cell(0, 6, "Inga kritiska fuktnivåer (varken kondens eller mögelrisk) uppnåddes i något gränssnitt under året.", new_x="LMARGIN", new_y="NEXT")

        # --------------------------------------------------------

        pdf.add_page()
        pdf.set_font("helvetica", size=14, style="B")
        pdf.cell(0, 10, "Källor och Beräkningsantaganden", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Metodik:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Beräkningar är utförda i enlighet med SS-EN ISO 6946 (Byggnadsdelar och byggnadselement - Värmemotstånd och värmegenomgångskoefficient).", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Markkontakt:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Beräknas i tillämpliga fall enligt SS-EN ISO 13370 där markens isolerande förmåga och byggnadens kantförluster beaktas utifrån area och exponerad omkrets (Lambda mark = 2.0). Källarväggars U-värden utgörs av den area-viktade relationen mellan andel över mark och andel under mark.", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Inhomogena skikt:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "För skikt med regelverk beräknas det totala värmemotståndet som medelvärdet av den övre gränsen (parallella värmeflöden, R') och den undre gränsen (isotermer, R'').", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Flera regelverk:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Vid förekomst av flera inhomogena skikt (t.ex. bärande stomme och installationsskikt) beräknas den övre gränsen (R') genom en matrisberäkning av alla teoretiska värmeflödesvägar. Kalkylen klyver upp arean och betraktar skikten som oberoende/korslagda (t.ex. fraktionerna trä/trä, trä/isolering, isolering/isolering) helt i enlighet med SS-EN ISO 6946.", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Ytmotstånd:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Inre och yttre ytmotstånd (Rsi, Rse) ansätts schablonmässigt baserat på valt värmeflöde enligt gällande standard.", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Luftspalter:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Vid väl ventilerad luftspalt exkluderas luftspalten samt alla utanförliggande skikt automatiskt från U-värdesberäkningen, och yttre ytmotstånd (Rse) sätts lika med inre ytmotstånd (Rsi) enligt SS-EN ISO 6946.", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Korrektioner:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Eventuell korrektionsterm (Delta U) för mekaniska fästdon och luftspalter adderas enligt SS-EN ISO 6946. Temperaturreduktionsfaktor (b-faktor) mot ouppvärmda utrymmen reducerar netto U-värdet.", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Materialdata:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Värmeledningsförmåga (Lambda-värden) i standarddatabasen utgörs av generella branschvärden och typvärden.", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Fuktanalys (Glaser):", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Förenklad 1D fukt- och kondensriskanalys utförs i enlighet med SS-EN ISO 13788, baserad på timupplösta klimatdata.", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Klimatdata (TMY):", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Väderdata utgörs inte av ett uträknat matematiskt medelvärde, utan bygger på ett Typiskt Meteorologiskt År (TMY) baserat på mätperioden 2009-2023. De mest representativa, faktiska månaderna från perioden har satts samman till ett typår för att bibehålla naturliga och dynamiska vädervariationer (såsom dygnssvängningar) utan att extremer plattas ut.", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Mättnadsångtryck:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Beräknas via Magnus-Tetens ekvation med anpassade koefficienter för ytor över och under 0 °C.", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Inomhusklimat (Fukt):", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Ångtryckstillskott baseras på fuktklasser i ISO 13788 och anpassas linjärt mot utetemperatur (max vid <= 0 °C, 0 g/m³ vid >= +20 °C).", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=10, style="B")
        pdf.cell(55, 6, "Fukt-begränsningar:", align="L")
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 6, "Metoden beaktar endast ångdiffusion (ekvivalent luftlager sd = my * d) och hanterar ej kapillär vätsketransport eller inbyggd byggfukt.", new_x="LMARGIN", new_y="NEXT")

        try:
            pdf.output(filepath)
            messagebox.showinfo("Succé!", "Teknisk beräkningsrapport sparad!")
            
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.call(["open", filepath])
            else:
                subprocess.call(["xdg-open", filepath])
                
        except Exception as e:
            messagebox.showerror("Fel vid sparning", f"Kunde inte spara filen: {e}")