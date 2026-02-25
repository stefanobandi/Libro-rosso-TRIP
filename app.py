import streamlit as st
import pandas as pd
import calendar
import os
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

DB_FILE = "database.csv"
ANA_FILE = "anagrafica.csv"

# --- OTTIMIZZAZIONE CACHE ---
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

def save_to_disk():
    st.session_state.db_memoria.to_csv(DB_FILE, index=False)
    st.session_state.ana_memoria.to_csv(ANA_FILE, index=False)

# --- CSS AGGIORNATO ---
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

# --- SIDEBAR ---
st.sidebar.header("🚢 Gestione Personale")

opzioni = (st.session_state.ana_memoria['Marittimo'] + " - " + st.session_state.ana_memoria['Qualifica']).tolist()
selezione = st.sidebar.selectbox("Selezione Marittimo", ["---"] + opzioni)

if selezione != "---":
    nome_corrente, qual_corrente = selezione.split(" - ")
    
    # Filtro Periodo
    df_m = st.session_state.db_memoria[st.session_state.db_memoria['Marittimo'] == nome_corrente]
    storico = df_m[['Mese', 'Anno']].drop_duplicates()
    opzioni_p = [f"{r['Mese']} {r['Anno']}" for _, r in storico.iterrows()]
    opzioni_p.append("➕ Inizia nuovo mese...")
    
    periodo_sel = st.sidebar.selectbox("Periodo", opzioni_p)
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    
    if periodo_sel == "➕ Inizia nuovo mese...":
        col1, col2 = st.sidebar.columns(2)
        m_comp, a_comp = col1.selectbox("Mese", mesi_ita), col2.selectbox("Anno", [2025, 2026])
    else:
        m_comp, a_comp = periodo_sel.split(" ")[0], int(periodo_sel.split(" ")[1])

    with st.sidebar.expander("➕ Aggiungi Anagrafica"):
        n_n, n_q = st.text_input("Nome").upper(), st.text_input("Qualifica").upper()
        if st.button("Registra"):
            new_row = pd.DataFrame([{"Marittimo": n_n, "Qualifica": n_q}])
            st.session_state.ana_memoria = pd.concat([st.session_state.ana_memoria, new_row], ignore_index=True)
            save_to_disk()
            st.rerun()

    if st.sidebar.button("💾 SALVA DEFINITIVAMENTE", use_container_width=True):
        save_to_disk()
        st.sidebar.success("Salvato su disco!")

    # --- LOGICA TABELLA ---
    num_giorni = calendar.monthrange(a_comp, mesi_ita.index(m_comp)+1)[1]
    
    # Creazione della griglia dati estraendo tutto il mese in un colpo solo
    st.write(f"### Registro: {nome_corrente} - {m_comp} {a_comp}")
    
    col_w = [0.8] + [0.5]*24 + [1, 2, 1, 1.2]
    h = st.columns(col_w)
    labels = ["GG"] + [f"{i:02d}" for i in range(1, 25)] + ["RIP", "Commenti", "LAV", "LAV 7g"]
    for i, l in enumerate(labels): h[i].markdown(f"<div class='header-box'>{l}</div>", unsafe_allow_html=True)

    # Dizionario per i calcoli delle 24h scorrevoli
    tutte_le_ore = {}

    for g in range(1, num_giorni + 1):
        r = st.columns(col_w)
        r[0].markdown(f"<div class='data-cell'><b>{g:02d}</b></div>", unsafe_allow_html=True)
        
        mask = (st.session_state.db_memoria['Marittimo'] == nome_corrente) & \
               (st.session_state.db_memoria['Mese'] == m_comp) & \
               (st.session_state.db_memoria['Anno'] == a_comp) & \
               (st.session_state.db_memoria['Giorno'] == g)
        
        row_db = st.session_state.db_memoria[mask]
        
        nuove_ore = []
        for ora in range(1, 25):
            with r[ora]:
                def_val = bool(row_db[f"H{ora:02d}"].values[0]) if not row_db.empty else False
                val = st.checkbox("", value=def_val, key=f"ch_{nome_corrente}_{g}_{ora}", label_visibility="collapsed")
                nuove_ore.append(val)
        
        tutte_le_ore[g] = nuove_ore
        
        with r[26]:
            def_c = str(row_db['Commenti'].values[0]) if not row_db.empty and str(row_db['Commenti'].values[0]) != 'nan' else ""
            nuovo_comm = st.text_input("", value=def_c, key=f"c_{nome_corrente}_{g}", label_visibility="collapsed")

        # Aggiornamento Session State immediato
        if nuove_ore != ([bool(row_db[f"H{i:02d}"].values[0]) for i in range(1, 25)] if not row_db.empty else [False]*24) or \
           nuovo_comm != def_c:
            if not row_db.empty:
                idx = row_db.index[0]
                for i, v in enumerate(nuove_ore): st.session_state.db_memoria.at[idx, f"H{i+1:02d}"] = v
                st.session_state.db_memoria.at[idx, 'Commenti'] = nuovo_comm
            else:
                nuova_riga = {"Marittimo": nome_corrente, "Qualifica": qual_corrente, "Anno": a_comp, "Mese": m_comp, "Giorno": g, "Commenti": nuovo_comm}
                for i, v in enumerate(nuove_ore): nuova_riga[f"H{i+1:02d}"] = v
                st.session_state.db_memoria = pd.concat([st.session_state.db_memoria, pd.DataFrame([nuova_riga])], ignore_index=True)

        # --- CALCOLI E VIOLAZIONI ---
        lav_24h = sum(nuove_ore)
        rip_24h = 24 - lav_24h
        
        # Logica 6h continuative (Analisi stringa binaria)
        rip_bin = "".join(['0' if x else '1' for x in nuove_ore])
        # Nota: per ora calcolata sul giorno singolo, implementeremo il 'lookback' nel prossimo step
        v_rip = "111111" not in rip_bin 
        
        c_lav = "violation" if lav_24h > 14 else ""
        c_rip = "violation" if v_rip else ""

        r[25].markdown(f"<div class='data-cell {c_rip}'>{rip_24h}</div>", unsafe_allow_html=True)
        r[27].markdown(f"<div class='data-cell {c_lav}'>{lav_24h}</div>", unsafe_allow_html=True)
        
        # Calcolo 7 giorni (Semplificato al mese corrente)
        lav_7g = 0
        for i in range(max(1, g-6), g + 1):
            if i in tutte_le_ore: lav_7g += sum(tutte_le_ore[i])
        
        c_7g = "violation" if lav_7g > 72 else ""
        r[28].markdown(f"<div class='data-cell {c_7g}'>{lav_7g}</div>", unsafe_allow_html=True)

    # --- TABELLA REGOLE (Reinserita) ---
    st.markdown(f"""
    <table class="promemoria-tab">
        <tr class="promemoria-header"><th colspan="2">TEST ESEGUITI SUL REGISTRO (CONFORMITÀ D.Lgs 271/99)</th></tr>
        <tr><td><b>1) MAX 72 ORE / 7 GIORNI</b></td><td>Il lavoro totale in ogni arco di 7 giorni non deve superare le 72 ore.</td></tr>
        <tr><td><b>2) MAX 14 ORE / 24 ORE</b></td><td>Il lavoro in un periodo di 24 ore non deve superare le 14 ore.</td></tr>
        <tr><td><b>3) MIN 6 ORE RIPOSO CONTINUATO</b></td><td>Deve essere garantito almeno un blocco di riposo ininterrotto di 6 ore.</td></tr>
    </table>
    """, unsafe_allow_html=True)

else:
    st.info("👈 Seleziona un marittimo per iniziare.")
