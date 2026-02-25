import streamlit as st
import pandas as pd
import calendar
import os
from datetime import datetime
from fpdf import FPDF
import io

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

DB_FILE = "database.csv"
ANA_FILE = "anagrafica.csv"

# --- CARICAMENTO DATI ---
def load_data(file, columns):
    if not os.path.exists(file):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df
    return pd.read_csv(file)

# Inizializzazione Session State
if 'db_memoria' not in st.session_state:
    cols = ["Marittimo", "Qualifica", "Anno", "Mese", "Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]
    st.session_state.db_memoria = load_data(DB_FILE, cols)
if 'ana_memoria' not in st.session_state:
    st.session_state.ana_memoria = load_data(ANA_FILE, ["Marittimo", "Qualifica"])

def save_to_disk():
    st.session_state.db_memoria.to_csv(DB_FILE, index=False)
    st.session_state.ana_memoria.to_csv(ANA_FILE, index=False)

# --- FUNZIONE PDF (REPLICA ALLEGATO B) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, 'REGISTRAZIONE DELLE ORE DI LAVORO E DI RIPOSO DEI LAVORATORI MARITTIMI', ln=True, align='C')
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, 'RECORD OF HOURS OF WORKS OR HOURS OF REST OF SEAFARERS', ln=True, align='C')
        self.ln(5)

def genera_pdf_ufficiale(nome, qualifica, mese, anno, dati_mese, commenti_mese):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", '', 9)
    pdf.cell(100, 7, f"Nominativo marittimo / Seafarers (full name): {nome}", border='B')
    pdf.cell(90, 7, f"Posizione/Grado / Position/Rank: {qualifica}", border='B', ln=True)
    pdf.cell(100, 7, f"Periodo di riferimento / Reference period: {mese} {anno}", border='B', ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(8, 8, "GG", 1, 0, 'C')
    for i in range(1, 25): pdf.cell(5.5, 8, str(i), 1, 0, 'C')
    pdf.cell(12, 8, "RIP 24h", 1, 0, 'C')
    pdf.cell(30, 8, "Commenti", 1, 1, 'C')
    pdf.set_font("Arial", '', 7)
    for g in range(1, 32):
        pdf.cell(8, 6, str(g), 1, 0, 'C')
        ore_giorno = dati_mese.get(g, [False]*24)
        for val in ore_giorno:
            pdf.cell(5.5, 6, "X" if val else "R", 1, 0, 'C')
        rip = 24 - sum(ore_giorno)
        pdf.cell(12, 6, str(rip), 1, 0, 'C')
        pdf.cell(30, 6, commenti_mese.get(g, "")[:18], 1, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 7)
    pdf.multi_cell(0, 4, "I AGREE that this record is an accurate reflection of the hours of work/rest.")
    pdf.ln(5)
    pdf.cell(95, 10, "Firma del Marittimo: _______________________", 0, 0)
    pdf.cell(95, 10, "Firma del Comandante: _______________________", 0, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACCIA ---
st.sidebar.header("🚢 Menu Personale")
opzioni = (st.session_state.ana_memoria['Marittimo'] + " - " + st.session_state.ana_memoria['Qualifica']).tolist()
selezione = st.sidebar.selectbox("Selezione Marittimo", ["---"] + opzioni)

mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

if selezione != "---":
    nome_corrente, qual_corrente = selezione.split(" - ")
    mese_attuale = mesi_ita[datetime.now().month-1]
    
    # Filtro Periodo
    df_m = st.session_state.db_memoria[st.session_state.db_memoria['Marittimo'] == nome_corrente]
    storico = df_m[['Mese', 'Anno']].drop_duplicates()
    opzioni_p = [f"{r['Mese']} {r['Anno']}" for _, r in storico.iterrows()]
    mese_attuale_str = f"{mese_attuale} {datetime.now().year}"
    if mese_attuale_str not in opzioni_p: opzioni_p.insert(0, mese_attuale_str)
    
    periodo_sel = st.sidebar.selectbox("Periodo", opzioni_p)
    m_comp, a_comp = periodo_sel.split(" ")[0], int(periodo_sel.split(" ")[1])

    with st.form("registro_form"):
        st.write(f"### Registro: {nome_corrente} ({m_comp} {a_comp})")
        num_giorni = calendar.monthrange(a_comp, mesi_ita.index(m_comp)+1)[1]
        temp_dati, temp_comm = {}, {}
        cols_w = [0.7] + [0.4]*24 + [1, 2.5]
        h = st.columns(cols_w); h[0].write("GG")
        for i in range(1, 25): h[i].write(str(i))

        for g in range(1, num_giorni + 1):
            r = st.columns(cols_w); r[0].write(f"**{g}**")
            mask = (st.session_state.db_memoria['Marittimo'] == nome_corrente) & (st.session_state.db_memoria['Mese'] == m_comp) & (st.session_state.db_memoria['Anno'] == a_comp) & (st.session_state.db_memoria['Giorno'] == g)
            row_db = st.session_state.db_memoria[mask]
            ore_g = []
            for ora in range(1, 25):
                with r[ora]:
                    def_v = bool(row_db[f"H{ora:02d}"].values[0]) if not row_db.empty else False
                    ore_g.append(st.checkbox("", value=def_v, key=f"f_{g}_{ora}", label_visibility="collapsed"))
            temp_dati[g] = ore_g
            with r[26]:
                def_c = str(row_db['Commenti'].values[0]) if not row_db.empty and str(row_db['Commenti'].values[0]) != 'nan' else ""
                temp_comm[g] = st.text_input("", value=def_c, key=f"c_{g}", label_visibility="collapsed")
        
        submit = st.form_submit_button("💾 SALVA E CALCOLA TUTTO IL MESE")

    if submit:
        for g in range(1, num_giorni + 1):
            mask = (st.session_state.db_memoria['Marittimo'] == nome_corrente) & (st.session_state.db_memoria['Mese'] == m_comp) & (st.session_state.db_memoria['Anno'] == a_comp) & (st.session_state.db_memoria['Giorno'] == g)
            if not st.session_state.db_memoria[mask].empty:
                idx = st.session_state.db_memoria[mask].index[0]
                for i, v in enumerate(temp_dati[g]): st.session_state.db_memoria.at[idx, f"H{i+1:02d}"] = v
                st.session_state.db_memoria.at[idx, 'Commenti'] = temp_comm[g]
            else:
                nuova_riga = {"Marittimo": nome_corrente, "Qualifica": qual_corrente, "Anno": a_comp, "Mese": m_comp, "Giorno": g, "Commenti": temp_comm[g]}
                for i, v in enumerate(temp_dati[g]): nuova_riga[f"H{i+1:02d}"] = v
                st.session_state.db_memoria = pd.concat([st.session_state.db_memoria, pd.DataFrame([nuova_riga])], ignore_index=True)
        save_to_disk()
        st.success("Dati salvati!")
        st.rerun()

    st.divider()
    pdf_out = genera_pdf_ufficiale(nome_corrente, qual_corrente, m_comp, a_comp, temp_dati, temp_comm)
    st.download_button(label="📄 SCARICA REGISTRO PDF (X/R)", data=pdf_out, file_name=f"Registro_{nome_corrente}_{m_comp}.pdf", mime="application/pdf", use_container_width=True)

else:
    st.info("👈 Seleziona un marittimo dal menu a sinistra.")
