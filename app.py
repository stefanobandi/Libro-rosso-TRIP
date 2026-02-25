import streamlit as st
import pandas as pd
import calendar
import os
from datetime import datetime
from fpdf import FPDF

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

DB_FILE = "database.csv"

# --- CARICAMENTO DATI ---
def load_data():
    cols = ["Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=cols)
        df.to_csv(DB_FILE, index=False)
        return df
    return pd.read_csv(DB_FILE)

if 'db_memoria' not in st.session_state:
    st.session_state.db_memoria = load_data()

def save_to_disk():
    st.session_state.db_memoria.to_csv(DB_FILE, index=False)

# --- FUNZIONE GENERAZIONE PDF (Allegato B) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, 'REGISTRAZIONE DELLE ORE DI LAVORO E DI RIPOSO DEI LAVORATORI MARITTIMI', ln=True, align='C')
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, 'RECORD OF HOURS OF WORKS OR HOURS OF REST OF SEAFARERS', ln=True, align='C')
        self.ln(5)

def crea_pdf_allegato_b(mese, anno, dati_mese, commenti_mese):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", '', 9)
    
    # Intestazione Periodo
    pdf.cell(100, 7, f"Periodo di riferimento / Reference period: {mese} {anno}", border='B', ln=True)
    pdf.ln(5)

    # Intestazione Tabella
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(8, 8, "GG", 1, 0, 'C')
    for i in range(1, 25):
        pdf.cell(5.5, 8, str(i), 1, 0, 'C')
    pdf.cell(12, 8, "RIP 24h", 1, 0, 'C')
    pdf.cell(30, 8, "Commenti", 1, 1, 'C')

    # Righe Giorni
    pdf.set_font("Arial", '', 7)
    for g in range(1, 32):
        pdf.cell(8, 6, str(g), 1, 0, 'C')
        
        ore_giorno = dati_mese.get(g, [False]*24)
        for val in ore_giorno:
            testo = "X" if val else "R"
            pdf.cell(5.5, 6, testo, 1, 0, 'C')
        
        rip = 24 - sum(ore_giorno)
        pdf.cell(12, 6, str(rip), 1, 0, 'C')
        
        comm = commenti_mese.get(g, "")[:18]
        pdf.cell(30, 6, comm, 1, 1, 'C')

    # Footer Firme
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 7)
    pdf.multi_cell(0, 4, "Dichiaro che le informazioni riportate nel presente registro sono accurate. / I AGREE that this record is an accurate reflection.")
    pdf.ln(5)
    pdf.cell(95, 10, "Firma del Marittimo: _______________________", 0, 0)
    pdf.cell(95, 10, "Firma del Comandante: _______________________", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- CSS ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem !important; }
    .header-box { background-color: #f2f2f2; border: 1px solid #999; text-align: center; font-weight: bold; font-size: 10px; height: 40px; display: flex; align-items: center; justify-content: center; }
    .data-cell { height: 35px; border: 1px solid #ccc; font-size: 12px; display: flex; align-items: center; justify-content: center; background-color: white; }
    .violation { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
    .promemoria-tab { width: 100%; border-collapse: collapse; margin-top: 30px; border: 2px solid #333; }
    .promemoria-tab td, .promemoria-tab th { border: 1px solid #999; padding: 10px; font-size: 14px; }
    .promemoria-header { background-color: #333; color: white; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- INTERFACCIA ---
oggi = datetime.now()
mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
mese_attuale = mesi_ita[oggi.month-1]
anno_attuale = oggi.year

st.title(f"🚢 Registro Lavoro e Riposo - {mese_attuale} {anno_attuale}")

with st.form("registro_form"):
    num_giorni = calendar.monthrange(anno_attuale, oggi.month)[1]
    col_w = [0.8] + [0.5]*24 + [1, 2, 1, 1.2]
    h = st.columns(col_w)
    labels = ["GG"] + [f"{i:02d}" for i in range(1, 25)] + ["RIP", "Commenti", "LAV", "LAV 7g"]
    for i, l in enumerate(labels):
        h[i].markdown(f"<div class='header-box'>{l}</div>", unsafe_allow_html=True)

    temp_dati = {}
    temp_comm = {}
    ore_mensili_totali = []

    for g in range(1, num_giorni + 1):
        r = st.columns(col_w)
        r[0].markdown(f"<div class='data-cell'><b>{g:02d}</b></div>", unsafe_allow_html=True)
        
        row_db = st.session_state.db_memoria[st.session_state.db_memoria['Giorno'] == g]
        
        ore_giorno = []
        for ora in range(1, 25):
            with r[ora]:
                def_v = bool(row_db[f"H{ora:02d}"].values[0]) if not row_db.empty else False
                val = st.checkbox("", value=def_v, key=f"f_{g}_{ora}", label_visibility="collapsed")
                ore_giorno.append(val)
        temp_dati[g] = ore_giorno
        
        with r[26]:
            def_c = str(row_db['Commenti'].values[0]) if not row_db.empty and str(row_db['Commenti'].values[0]) != 'nan' else ""
            temp_comm[g] = st.text_input("", value=def_c, key=f"c_{g}", label_visibility="collapsed")

        # Calcoli conformità
        lav_24 = sum(ore_giorno)
        rip_24 = 24 - lav_24
        rip_bin = "".join(['0' if x else '1' for x in ore_giorno])
        violazione_rip = "111111" not in rip_bin
        ore_mensili_totali.append(lav_24)
        lav_7g = sum(ore_mensili_totali[max(0, g-7):g])

        c_lav = "violation" if lav_24 > 14 else ""
        c_rip = "violation" if violazione_rip else ""
        c_7g = "violation" if lav_7g > 72 else ""

        r[25].markdown(f"<div class='data-cell {c_rip}'>{rip_24}</div>", unsafe_allow_html=True)
        r[27].markdown(f"<div class='data-cell {c_lav}'>{lav_24}</div>", unsafe_allow_html=True)
        r[28].markdown(f"<div class='data-cell {c_7g}'>{lav_7g}</div>", unsafe_allow_html=True)

    submit = st.form_submit_button("💾 CALCOLA E SALVA TUTTO IL MESE", use_container_width=True)

if submit:
    new_rows = []
    for g in range(1, num_giorni + 1):
        riga = {"Giorno": g, "Commenti": temp_comm[g]}
        for i, v in enumerate(temp_dati[g]): riga[f"H{i+1:02d}"] = v
        new_rows.append(riga)
    st.session_state.db_memoria = pd.DataFrame(new_rows)
    save_to_disk()
    st.success("Dati salvati!")
    st.rerun()

# --- BOTTONE PDF ---
st.divider()
pdf_data = crea_pdf_allegato_b(mese_attuale, anno_attuale, temp_dati, temp_comm)
st.download_button(
    label="📄 SCARICA REGISTRO PDF (MODELLO ALLEGATO B)",
    data=pdf_data,
    file_name=f"Registro_{mese_attuale}_{anno_attuale}.pdf",
    mime="application/pdf",
    use_container_width=True
)

# --- TABELLA REGOLE ---
st.markdown("""
<table class="promemoria-tab">
    <tr class="promemoria-header"><th colspan="2">TEST DI CONFORMITÀ (D.Lgs 271/99)</th></tr>
    <tr><td><b>1) Max Lavoro / 7 Giorni</b></td><td>Non deve superare le <b>72 ore</b> (Ultima colonna)</td></tr>
    <tr><td><b>2) Max Lavoro / 24 Ore</b></td><td>Non deve superare le <b>14 ore</b> (Colonna LAV)</td></tr>
    <tr><td><b>3) Riposo Continuato</b></td><td>Almeno un blocco da <b>6 ore</b> consecutive (Colonna RIP)</td></tr>
</table>
""", unsafe_allow_html=True)
