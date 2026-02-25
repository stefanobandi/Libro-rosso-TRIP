import streamlit as st
import pandas as pd
import calendar
import os
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

DB_FILE = "database.csv"
ANA_FILE = "anagrafica.csv"

# --- 1. OTTIMIZZAZIONE CACHE E CARICAMENTO ---
@st.cache_data
def get_db_columns():
    return ["Marittimo", "Qualifica", "Anno", "Mese", "Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]

def load_data(file, columns):
    if not os.path.exists(file):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df
    return pd.read_csv(file)

# Carichiamo i dati in Session State per velocità immediata
if 'db_memoria' not in st.session_state:
    st.session_state.db_memoria = load_data(DB_FILE, get_db_columns())
if 'ana_memoria' not in st.session_state:
    st.session_state.ana_memoria = load_data(ANA_FILE, ["Marittimo", "Qualifica"])

def save_to_disk():
    st.session_state.db_memoria.to_csv(DB_FILE, index=False)
    st.session_state.ana_memoria.to_csv(ANA_FILE, index=False)

# --- CSS ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem !important; }
    .header-box { background-color: #f2f2f2; border: 1px solid #999; text-align: center; font-weight: bold; font-size: 10px; height: 40px; display: flex; align-items: center; justify-content: center; }
    .data-cell { height: 35px; border: 1px solid #ccc; font-size: 12px; display: flex; align-items: center; justify-content: center; background-color: white; }
    .violation { background-color: #ff4b4b !important; color: white !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("🚢 Gestione Personale")

# Selezione Marittimo
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

    # Crea Nuovo Marittimo (Spostato sotto)
    with st.sidebar.expander("➕ Aggiungi Anagrafica"):
        n_n = st.text_input("Nome").upper()
        n_q = st.text_input("Qualifica").upper()
        if st.button("Registra"):
            new_row = pd.DataFrame([{"Marittimo": n_n, "Qualifica": n_q}])
            st.session_state.ana_memoria = pd.concat([st.session_state.ana_memoria, new_row], ignore_index=True)
            save_to_disk()
            st.rerun()

    if st.sidebar.button("💾 SALVA TUTTO IL MESE", use_container_width=True):
        # La logica di salvataggio è ora integrata nel loop della tabella tramite session_state
        save_to_disk()
        st.sidebar.success("Database aggiornato su disco!")

    # --- LOGICA TABELLA ---
    num_giorni = calendar.monthrange(a_comp, mesi_ita.index(m_comp)+1)[1]
    
    # Preparazione dati del mese corrente per calcoli veloci
    # Creiamo un dizionario ore[giorno] = list(24 ore)
    ore_mese = {}
    comm_mese = {}
    for g in range(1, num_giorni + 1):
        row = st.session_state.db_memoria[(st.session_state.db_memoria['Marittimo'] == nome_corrente) & 
                                         (st.session_state.db_memoria['Mese'] == m_comp) & 
                                         (st.session_state.db_memoria['Anno'] == a_comp) & 
                                         (st.session_state.db_memoria['Giorno'] == g)]
        if not row.empty:
            ore_mese[g] = [bool(row[f"H{i:02d}"].values[0]) for i in range(1, 25)]
            comm_mese[g] = str(row['Commenti'].values[0]) if str(row['Commenti'].values[0]) != 'nan' else ""
        else:
            ore_mese[g] = [False]*24
            comm_mese[g] = ""

    st.write(f"### Registro: {nome_corrente} - {m_comp} {a_comp}")
    
    # Header
    col_w = [0.8] + [0.5]*24 + [1, 2, 1, 1.2]
    h = st.columns(col_w)
    labels = ["GG"] + [f"{i:02d}" for i in range(1, 25)] + ["RIP", "Commenti", "LAV", "LAV 7g"]
    for i, l in enumerate(labels): h[i].markdown(f"<div class='header-box'>{l}</div>", unsafe_allow_html=True)

    # LOOP GIORNI
    for g in range(1, num_giorni + 1):
        r = st.columns(col_w)
        r[0].markdown(f"<div class='data-cell'><b>{g:02d}</b></div>", unsafe_allow_html=True)
        
        nuove_ore = []
        for ora in range(1, 25):
            with r[ora]:
                # Chiave univoca globale per evitare lag e conflitti
                k = f"check_{nome_corrente}_{m_comp}_{g}_{ora}"
                val = st.checkbox("", value=ore_mese[g][ora-1], key=k, label_visibility="collapsed")
                nuove_ore.append(val)
        
        # AGGIORNAMENTO IN TEMPO REALE NELLA MEMORIA (Senza scrivere su disco)
        # Cerchiamo se la riga esiste già in session_state e la aggiorniamo
        mask = (st.session_state.db_memoria['Marittimo'] == nome_corrente) & \
               (st.session_state.db_memoria['Mese'] == m_comp) & \
               (st.session_state.db_memoria['Anno'] == a_comp) & \
               (st.session_state.db_memoria['Giorno'] == g)
        
        with r[26]:
            nuovo_comm = st.text_input("", value=comm_mese[g], key=f"c_{nome_corrente}_{g}", label_visibility="collapsed")

        # Se i dati sono diversi, aggiorniamo il dataframe in memoria
        if nuove_ore != ore_mese[g] or nuovo_comm != comm_mese[g]:
            if not st.session_state.db_memoria[mask].empty:
                idx = st.session_state.db_memoria[mask].index[0]
                for i, v in enumerate(nuove_ore): st.session_state.db_memoria.at[idx, f"H{i+1:02d}"] = v
                st.session_state.db_memoria.at[idx, 'Commenti'] = nuovo_comm
            else:
                nuova_riga = {"Marittimo": nome_corrente, "Qualifica": qual_corrente, "Anno": a_comp, "Mese": m_comp, "Giorno": g, "Commenti": nuovo_comm}
                for i, v in enumerate(nuove_ore): nuova_riga[f"H{i+1:02d}"] = v
                st.session_state.db_memoria = pd.concat([st.session_state.db_memoria, pd.DataFrame([nuova_riga])], ignore_index=True)

        # --- CALCOLI CONFORMITÀ (SCORREVOLI) ---
        lav_24 = sum(nuove_ore)
        rip_24 = 24 - lav_24
        
        # Logica Riposo 6h continuative (qui andrebbe estesa al giorno prima per essere perfetta)
        rip_bin = "".join(['0' if x else '1' for x in nuove_ore])
        v_rip = "111111" not in rip_bin # Violazione se non trova 6 '1' (riposo)
        
        lav_7g = 0 # Placeholder per calcolo settimanale (necessita di finestra scorrevole su DF)

        # Visualizzazione con classi CSS per violazioni
        c_lav = "violation" if lav_24 > 14 else ""
        c_rip = "violation" if v_rip else ""

        r[25].markdown(f"<div class='data-cell {c_rip}'>{rip_24}</div>", unsafe_allow_html=True)
        r[27].markdown(f"<div class='data-cell {c_lav}'>{lav_24}</div>", unsafe_allow_html=True)
        r[28].markdown(f"<div class='data-cell'>-</div>", unsafe_allow_html=True)

    st.info("💡 I dati vengono salvati temporaneamente in memoria per velocità. Premi il tasto 'SALVA' nella barra laterale prima di chiudere.")

else:
    st.info("👈 Seleziona un marittimo per iniziare.")
