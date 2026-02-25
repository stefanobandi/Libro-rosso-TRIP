import streamlit as st
import pandas as pd
import calendar
import os
from datetime import datetime

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

if 'db_memoria' not in st.session_state:
    cols = ["Marittimo", "Qualifica", "Anno", "Mese", "Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]
    st.session_state.db_memoria = load_data(DB_FILE, cols)
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
    .promemoria-tab { width: 100%; border-collapse: collapse; margin-top: 30px; border: 2px solid #333; }
    .promemoria-tab td, .promemoria-tab th { border: 1px solid #999; padding: 10px; font-size: 14px; }
    .promemoria-header { background-color: #333; color: white; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("🚢 Personale")
opzioni = (st.session_state.ana_memoria['Marittimo'] + " - " + st.session_state.ana_memoria['Qualifica']).tolist()
selezione = st.sidebar.selectbox("Selezione Marittimo", ["---"] + opzioni)

mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
oggi = datetime.now()

if selezione != "---":
    nome_corrente, qual_corrente = selezione.split(" - ")
    
    # Logica Mese Corrente Automatico
    df_m = st.session_state.db_memoria[st.session_state.db_memoria['Marittimo'] == nome_corrente]
    storico = df_m[['Mese', 'Anno']].drop_duplicates()
    opzioni_p = [f"{r['Mese']} {r['Anno']}" for _, r in storico.iterrows()]
    
    # Se il mese attuale non è nello storico, lo aggiungiamo come opzione
    mese_attuale_str = f"{mesi_ita[oggi.month-1]} {oggi.year}"
    if mese_attuale_str not in opzioni_p:
        opzioni_p.insert(0, mese_attuale_str)
    
    opzioni_p.append("➕ Altro periodo...")
    
    periodo_sel = st.sidebar.selectbox("Periodo", opzioni_p, index=0)
    
    if periodo_sel == "➕ Altro periodo...":
        col1, col2 = st.sidebar.columns(2)
        m_comp, a_comp = col1.selectbox("Mese", mesi_ita, index=oggi.month-1), col2.selectbox("Anno", [2024, 2025, 2026], index=1)
    else:
        m_comp, a_comp = periodo_sel.split(" ")[0], int(periodo_sel.split(" ")[1])

    # Sezione Nuova Anagrafica
    with st.sidebar.expander("➕ Aggiungi Anagrafica"):
        n_n, n_q = st.text_input("Nome").upper(), st.text_input("Qualifica").upper()
        if st.button("Registra"):
            new_row = pd.DataFrame([{"Marittimo": n_n, "Qualifica": n_q}])
            st.session_state.ana_memoria = pd.concat([st.session_state.ana_memoria, new_row], ignore_index=True)
            save_to_disk()
            st.rerun()

    # --- REGISTRO CON FORM (SOLUZIONE VELOCITÀ) ---
    num_giorni = calendar.monthrange(a_comp, mesi_ita.index(m_comp)+1)[1]
    st.write(f"### Registro: {nome_corrente} - {m_comp} {a_comp}")
    
    # Creiamo un form per bloccare i ricalcoli continui
    with st.form("registro_form"):
        st.info("⚡ MODALITÀ VELOCE: Compila le ore e premi 'CALCOLA E SALVA' in fondo per aggiornare i dati e vedere le violazioni.")
        
        col_w = [0.8] + [0.5]*24 + [1, 2, 1, 1.2]
        h = st.columns(col_w)
        labels = ["GG"] + [f"{i:02d}" for i in range(1, 25)] + ["RIP", "Commenti", "LAV", "LAV 7g"]
        for i, l in enumerate(labels): h[i].markdown(f"<div class='header-box'>{l}</div>", unsafe_allow_html=True)

        dati_input = {}
        comm_input = {}

        for g in range(1, num_giorni + 1):
            r = st.columns(col_w)
            r[0].markdown(f"<div class='data-cell'><b>{g:02d}</b></div>", unsafe_allow_html=True)
            
            # Recupero dati esistenti per default
            mask = (st.session_state.db_memoria['Marittimo'] == nome_corrente) & \
                   (st.session_state.db_memoria['Mese'] == m_comp) & \
                   (st.session_state.db_memoria['Anno'] == a_comp) & \
                   (st.session_state.db_memoria['Giorno'] == g)
            row_db = st.session_state.db_memoria[mask]
            
            nuove_ore = []
            for ora in range(1, 25):
                with r[ora]:
                    def_val = bool(row_db[f"H{ora:02d}"].values[0]) if not row_db.empty else False
                    val = st.checkbox("", value=def_val, key=f"fch_{g}_{ora}", label_visibility="collapsed")
                    nuove_ore.append(val)
            dati_input[g] = nuove_ore
            
            with r[26]:
                def_c = str(row_db['Commenti'].values[0]) if not row_db.empty and str(row_db['Commenti'].values[0]) != 'nan' else ""
                comm_input[g] = st.text_input("", value=def_c, key=f"fc_{g}", label_visibility="collapsed")

            # Visualizzazione statica (verrà aggiornata solo al submit)
            lav_24h = sum([bool(row_db[f"H{i:02d}"].values[0]) for i in range(1, 25)]) if not row_db.empty else 0
            rip_24h = 24 - lav_24h
            r[25].markdown(f"<div class='data-cell'>{rip_24h}</div>", unsafe_allow_html=True)
            r[27].markdown(f"<div class='data-cell'>{lav_24h}</div>", unsafe_allow_html=True)
            r[28].markdown(f"<div class='data-cell'>-</div>", unsafe_allow_html=True)

        submit = st.form_submit_button("💾 CALCOLA E SALVA TUTTO IL MESE", use_container_width=True)

    if submit:
        # 1. Aggiornamento massivo del dataframe in memoria
        for g in range(1, num_giorni + 1):
            mask = (st.session_state.db_memoria['Marittimo'] == nome_corrente) & \
                   (st.session_state.db_memoria['Mese'] == m_comp) & \
                   (st.session_state.db_memoria['Anno'] == a_comp) & \
                   (st.session_state.db_memoria['Giorno'] == g)
            
            if not st.session_state.db_memoria[mask].empty:
                idx = st.session_state.db_memoria[mask].index[0]
                for i, v in enumerate(dati_input[g]): 
                    st.session_state.db_memoria.at[idx, f"H{i+1:02d}"] = v
                st.session_state.db_memoria.at[idx, 'Commenti'] = comm_input[g]
            else:
                nuova_riga = {"Marittimo": nome_corrente, "Qualifica": qual_corrente, "Anno": a_comp, "Mese": m_comp, "Giorno": g, "Commenti": comm_input[g]}
                for i, v in enumerate(dati_input[g]): nuova_riga[f"H{i+1:02d}"] = v
                st.session_state.db_memoria = pd.concat([st.session_state.db_memoria, pd.DataFrame([nuova_riga])], ignore_index=True)
        
        save_to_disk()
        st.success(f"Dati di {m_comp} {a_comp} salvati correttamente!")
        st.rerun() # Ricarica per mostrare i colori/calcoli aggiornati

    # --- TABELLA REGOLE ---
    st.markdown("""
    <table class="promemoria-tab">
        <tr class="promemoria-header"><th colspan="2">TEST ESEGUITI SUL REGISTRO (CONFORMITÀ D.Lgs 271/99)</th></tr>
        <tr><td><b>1) MAX 72 ORE / 7 GIORNI</b></td><td>Il lavoro totale in ogni arco di 7 giorni non deve superare le 72 ore.</td></tr>
        <tr><td><b>2) MAX 14 ORE / 24 ORE</b></td><td>Il lavoro in un periodo di 24 ore non deve superare le 14 ore.</td></tr>
        <tr><td><b>3) MIN 6 ORE RIPOSO CONTINUATO</b></td><td>Deve essere garantito almeno un blocco di riposo ininterrotto di 6 ore.</td></tr>
    </table>
    """, unsafe_allow_html=True)

else:
    st.info("👈 Seleziona un marittimo per iniziare.")
