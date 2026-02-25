import streamlit as st
import pandas as pd
import calendar
import os
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

DB_FILE = "database.csv"
ANA_FILE = "anagrafica.csv"

# --- FUNZIONI DATABASE ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            return pd.read_csv(file)
        except:
            return pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df

def save_new_marittimo(nome, qualifica):
    df_ana = load_data(ANA_FILE, ["Marittimo", "Qualifica"])
    if not ((df_ana['Marittimo'] == nome) & (df_ana['Qualifica'] == qualifica)).any():
        new_row = pd.DataFrame([{"Marittimo": nome, "Qualifica": qualifica}])
        df_ana = pd.concat([df_ana, new_row], ignore_index=True)
        df_ana.to_csv(ANA_FILE, index=False)
        return True
    return False

def save_all_month(nome, qualifica, anno, mese, data_grid, commenti_grid):
    cols = ["Marittimo", "Qualifica", "Anno", "Mese", "Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]
    df = load_data(DB_FILE, cols)
    df = df[~((df['Marittimo'] == nome) & (df['Anno'] == anno) & (df['Mese'] == mese))]
    new_rows = []
    for gg, ore in data_grid.items():
        row = {"Marittimo": nome, "Qualifica": qualifica, "Anno": anno, "Mese": mese, "Giorno": gg, "Commenti": commenti_grid.get(gg, "")}
        for i, v in enumerate(ore): row[f"H{i+1:02d}"] = v
        new_rows.append(row)
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
    st.sidebar.success(f"✅ Registro di {mese} {anno} salvato correttamente!")

# --- CSS CUSTOM ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 3rem !important; }
    .header-box { background-color: #f2f2f2; border: 1px solid #999; text-align: center; font-weight: bold; font-size: 11px; height: 45px; display: flex; align-items: center; justify-content: center; }
    .data-cell { height: 35px; display: flex; align-items: center; justify-content: center; border: 1px solid #ccc; font-size: 13px; background-color: white; }
    [data-testid="stCheckbox"] { display: flex; justify-content: center; align-items: center; height: 35px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("🚢 Gestione Personale")

df_ana = load_data(ANA_FILE, ["Marittimo", "Qualifica"])
opzioni_marittimi = (df_ana['Marittimo'] + " - " + df_ana['Qualifica']).tolist()

selezione = st.sidebar.selectbox("Selezione Marittimo", ["---"] + opzioni_marittimi)

# Crea Nuovo Marittimo
with st.sidebar.expander("➕ Crea Nuovo Marittimo"):
    nuovo_nome = st.text_input("Nome e Cognome").upper().strip()
    nuova_qual = st.text_input("Qualifica").upper().strip()
    if st.button("Registra Marittimo"):
        if nuovo_nome and nuova_qual:
            if save_new_marittimo(nuovo_nome, nuova_qual):
                st.sidebar.success(f"✅ Marittimo {nuovo_nome} salvato!")
                st.rerun()
            else:
                st.sidebar.warning("Marittimo già esistente.")
        else:
            st.sidebar.error("Compila tutti i campi.")

st.sidebar.divider()

if selezione != "---":
    nome_corrente = selezione.split(" - ")[0]
    qual_corrente = selezione.split(" - ")[1]
    
    # Carica database per filtri dinamici
    cols_db = ["Marittimo", "Qualifica", "Anno", "Mese", "Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]
    df_main = load_data(DB_FILE, cols_db)
    
    # Trova mesi/anni già salvati per questo marittimo
    storico = df_main[df_main['Marittimo'] == nome_corrente][['Mese', 'Anno']].drop_duplicates()
    opzioni_periodo = [f"{r['Mese']} {r['Anno']}" for _, r in storico.iterrows()]
    opzioni_periodo.append("➕ Inizia nuovo mese...")
    
    periodo_sel = st.sidebar.selectbox("Periodo di riferimento", opzioni_periodo)
    
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    
    if periodo_sel == "➕ Inizia nuovo mese...":
        col_m, col_a = st.sidebar.columns(2)
        mese_compila = col_m.selectbox("Mese", mesi_ita, index=datetime.now().month-1)
        anno_compila = col_a.selectbox("Anno", [2024, 2025, 2026, 2027], index=1)
    else:
        mese_compila = periodo_sel.split(" ")[0]
        anno_compila = int(periodo_sel.split(" ")[1])

    st.sidebar.divider()
    save_btn = st.sidebar.button("💾 SALVA TUTTO IL MESE", use_container_width=True)

    # --- DISEGNO TABELLA ---
    st.markdown(f"## Registro: {nome_corrente} ({qual_corrente})")
    st.caption(f"Visualizzazione: {mese_compila} {anno_compila}")

    current_db = df_main[(df_main['Marittimo'] == nome_corrente) & (df_main['Mese'] == mese_compila) & (df_main['Anno'] == anno_compila)]
    
    mese_num = mesi_ita.index(mese_compila) + 1
    num_giorni = calendar.monthrange(anno_compila, mese_num)[1]

    temp_registro = {}
    temp_commenti = {}

    col_widths = [0.8] + [0.6]*24 + [1, 2.5, 1]
    h_cols = st.columns(col_widths)
    h_cols[0].markdown("<div class='header-box'>GG</div>", unsafe_allow_html=True)
    for i in range(1, 25): h_cols[i].markdown(f"<div class='header-box'>{i:02d}</div>", unsafe_allow_html=True)
    h_cols[25].markdown("<div class='header-box'>RIP</div>", unsafe_allow_html=True)
    h_cols[26].markdown("<div class='header-box'>Commenti</div>", unsafe_allow_html=True)
    h_cols[27].markdown("<div class='header-box'>LAV</div>", unsafe_allow_html=True)

    for gg in range(1, num_giorni + 1):
        r_cols = st.columns(col_widths)
        row_db = current_db[current_db['Giorno'] == gg]
        
        r_cols[0].markdown(f"<div class='data-cell'><b>{gg:02d}</b></div>", unsafe_allow_html=True)
        
        ore_giorno = []
        for ora in range(1, 25):
            with r_cols[ora]:
                def_val = bool(row_db[f"H{ora:02d}"].values[0]) if not row_db.empty else False
                val = st.checkbox("", value=def_val, key=f"ch_{gg}_{ora}_{mese_compila}", label_visibility="collapsed")
                ore_giorno.append(val)
        
        temp_registro[gg] = ore_giorno
        lav = sum(ore_giorno)
        rip = 24 - lav
        
        with r_cols[26]:
            def_comm = str(row_db['Commenti'].values[0]) if not row_db.empty and str(row_db['Commenti'].values[0]) != "nan" else ""
            comm = st.text_input("", value=def_comm, key=f"c_{gg}_{mese_compila}", label_visibility="collapsed")
            temp_commenti[gg] = comm
        
        r_cols[25].markdown(f"<div class='data-cell'>{rip}</div>", unsafe_allow_html=True)
        r_cols[27].markdown(f"<div class='data-cell'>{lav}</div>", unsafe_allow_html=True)

    if save_btn:
        save_all_month(nome_corrente, qual_corrente, anno_compila, mese_compila, temp_registro, temp_commenti)
else:
    st.info("👈 Seleziona un marittimo o creane uno nuovo per iniziare.")
