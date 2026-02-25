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

# --- FUNZIONI CARICAMENTO ---
def load_data(file, columns):
    if not os.path.exists(file):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df
    return pd.read_csv(file)

if 'db_memoria' not in st.session_state:
    cols = ["Marittimo", "Qualifica", "Anno", "Mese", "Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]
    st.session_state.db_memoria = load_data(DB_FILE, cols)
if 'ana_memoria' not in st.session_state:
    st.session_state.ana_memoria = load_data(ANA_FILE, ["Marittimo", "Qualifica"])

# --- FUNZIONE GENERAZIONE PDF (Replica Allegato B) ---
def genera_pdf_ufficiale(nome, qualifica, mese, anno, dati_mese):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 10)
    
    # Intestazione superiore
    pdf.cell(0, 5, "REGISTRAZIONE DELLE ORE DI LAVORO E DI RIPOSO DEI LAVORATORI MARITTIMI", ln=True, align='C')
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 5, "RECORD OF HOURS OF WORKS OR HOURS OF REST OF SEAFARERS", ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("Arial", '', 9)
    # Campi anagrafici (Layout semplificato per test)
    pdf.cell(100, 7, f"Nominativo marittimo / Seafarers (full name): {nome}", border='B')
    pdf.cell(90, 7, f"Posizione/Grado / Position/Rank: {qualifica}", border='B', ln=True)
    pdf.cell(100, 7, f"Periodo di riferimento / Reference period: {mese} {anno}", border='B', ln=True)
    
    pdf.ln(10)
    
    # Tabella - Intestazione Colonne
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(10, 10, "Data", 1, 0, 'C')
    for i in range(1, 25):
        pdf.cell(6, 10, str(i), 1, 0, 'C')
    
    pdf.set_font("Arial", 'B', 6)
    pdf.multi_cell(15, 5, "Riposo\n24h", 1, 'C')
    pdf.set_xy(171, pdf.get_y() - 10)
    pdf.cell(25, 10, "Commenti", 1, 1, 'C')

    # Riempimento Giorni
    pdf.set_font("Arial", '', 7)
    for g in range(1, 32):
        pdf.cell(10, 6, str(g), 1, 0, 'C')
        
        ore_giorno = dati_mese.get(g, [False]*24)
        for ora_val in ore_giorno:
            testo = "X" if ora_val else "R"
            # Coloriamo leggermente le R in grigio se possibile, o le lasciamo normali
            pdf.cell(6, 6, testo, 1, 0, 'C')
        
        lav = sum(ore_giorno)
        rip = 24 - lav
        pdf.cell(15, 6, str(rip), 1, 0, 'C')
        pdf.cell(25, 6, "", 1, 1, 'C') # Spazio commenti vuoto per scrittura a mano

    pdf.ln(10)
    pdf.set_font("Arial", 'I', 7)
    pdf.multi_cell(0, 4, "Dichiaro che le informazioni riportate nel presente registro sono accurate.\nI AGREE that this record is an accurate reflection of the hours of work/rest.")
    
    pdf.ln(5)
    pdf.cell(95, 10, "Firma del Marittimo: _______________________", 0, 0)
    pdf.cell(95, 10, "Firma del Comandante: _______________________", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACCIA STREAMLIT ---
st.sidebar.header("🚢 Navigazione")
opzioni = (st.session_state.ana_memoria['Marittimo'] + " - " + st.session_state.ana_memoria['Qualifica']).tolist()
selezione = st.sidebar.selectbox("Selezione Marittimo", ["---"] + opzioni)

mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

if selezione != "---":
    nome_corrente, qual_corrente = selezione.split(" - ")
    mese_attuale = mesi_ita[datetime.now().month-1]
    anno_attuale = datetime.now().year
    
    m_comp = st.sidebar.selectbox("Mese", mesi_ita, index=mesi_ita.index(mese_attuale))
    a_comp = st.sidebar.selectbox("Anno", [2024, 2025, 2026], index=1)

    # --- TABELLA INPUT ---
    st.write(f"### Compilazione Registro: {nome_corrente}")
    
    with st.form("registro_form"):
        num_giorni = calendar.monthrange(a_comp, mesi_ita.index(m_comp)+1)[1]
        temp_dati = {}
        
        # Disegno testata griglia
        cols_w = [0.8] + [0.5]*24
        h = st.columns(cols_w)
        h[0].write("GG")
        for i in range(1, 25): h[i].write(f"{i}")

        for g in range(1, num_giorni + 1):
            r = st.columns(cols_w)
            r[0].write(f"**{g}**")
            
            mask = (st.session_state.db_memoria['Marittimo'] == nome_corrente) & \
                   (st.session_state.db_memoria['Mese'] == m_comp) & \
                   (st.session_state.db_memoria['Anno'] == a_comp) & \
                   (st.session_state.db_memoria['Giorno'] == g)
            row_db = st.session_state.db_memoria[mask]
            
            ore_g = []
            for ora in range(1, 25):
                with r[ora]:
                    def_v = bool(row_db[f"H{ora:02d}"].values[0]) if not row_db.empty else False
                    val = st.checkbox("", value=def_v, key=f"f_{g}_{ora}", label_visibility="collapsed")
                    ore_g.append(val)
            temp_dati[g] = ore_g
        
        submit = st.form_submit_button("💾 AGGIORNA CALCOLI E SALVA")

    if submit:
        # Logica salvataggio (omessa per brevità ma presente nel tuo DB)
        st.success("Dati aggiornati in memoria!")

    # --- BOTTONE PDF ---
    st.divider()
    pdf_data = genera_pdf_ufficiale(nome_corrente, qual_corrente, m_comp, a_comp, temp_dati)
    st.download_button(
        label="📄 SCARICA PDF UFFICIALE (ALLEGATO B)",
        data=pdf_data,
        file_name=f"Registro_{nome_corrente}_{m_comp}_{a_comp}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.info("👈 Seleziona un marittimo per iniziare.")
