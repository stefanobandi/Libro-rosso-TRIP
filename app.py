import streamlit as st
import pandas as pd
import calendar
import os
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

DB_FILE = "database.csv"

# --- FUNZIONI DATABASE ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return create_empty_df()
    else:
        return create_empty_df()

def create_empty_df():
    cols = ["Marittimo", "Qualifica", "Anno", "Mese", "Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]
    df = pd.DataFrame(columns=cols)
    df.to_csv(DB_FILE, index=False)
    return df

def save_all_month(nome, qualifica, anno, mese, data_grid, commenti_grid):
    df = load_data()
    # Rimuoviamo i dati vecchi di questo specifico marittimo/periodo per sovrascriverli
    df = df[~((df['Marittimo'] == nome) & (df['Anno'] == anno) & (df['Mese'] == mese))]
    
    new_rows = []
    for gg, ore in data_grid.items():
        row = {
            "Marittimo": nome, "Qualifica": qualifica, "Anno": anno, "Mese": mese, "Giorno": gg,
            "Commenti": commenti_grid.get(gg, "")
        }
        for i, v in enumerate(ore):
            row[f"H{i+1:02d}"] = v
        new_rows.append(row)
    
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
    st.sidebar.success(f"✅ Registro di {mese} salvato!")

# --- CSS CUSTOM ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .header-box { background-color: #f2f2f2; border: 1px solid #999; text-align: center; font-weight: bold; font-size: 11px; height: 40px; display: flex; align-items: center; justify-content: center; }
    .data-cell { height: 35px; display: flex; align-items: center; justify-content: center; border: 1px solid #ccc; font-size: 13px; background-color: white; }
    [data-testid="stCheckbox"] { display: flex; justify-content: center; align-items: center; height: 35px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: Selezione e Salvataggio ---
with st.sidebar:
    st.header("📂 Gestione Registro")
    nome_sel = st.text_input("Marittimo", "ROSSI MARIO").upper()
    qual_sel = st.text_input("Qualifica", "UFFICIALE").upper()
    
    oggi = datetime.now()
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    mese_sel = st.selectbox("Mese", mesi_ita, index=oggi.month - 1)
    anno_sel = st.selectbox("Anno", [2024, 2025, 2026], index=1)
    
    st.divider()
    # Il bottone di salvataggio viene messo qui in fondo
    save_btn = st.button("💾 SALVA TUTTO IL MESE", use_container_width=True)

# --- LOGICA CARICAMENTO ---
mese_num = mesi_ita.index(mese_sel) + 1
num_giorni = calendar.monthrange(anno_sel, mese_num)[1]
full_db = load_data()
current_db = full_db[(full_db['Marittimo'] == nome_sel) & (full_db['Mese'] == mese_sel) & (full_db['Anno'] == anno_sel)]

# --- GRIGLIA DATI ---
st.markdown(f"### Registro: {nome_sel} - {mese_sel} {anno_sel}")

# Strutture temporanee per raccogliere i dati della griglia
temp_registro = {}
temp_commenti = {}

# Header Tabella
col_widths = [0.8] + [0.6]*24 + [1, 2.5, 1]
h_cols = st.columns(col_widths)
h_cols[0].markdown("<div class='header-box'>GG</div>", unsafe_allow_html=True)
for i in range(1, 25): h_cols[i].markdown(f"<div class='header-box'>{i:02d}</div>", unsafe_allow_html=True)
h_cols[25].markdown("<div class='header-box'>RIP</div>", unsafe_allow_html=True)
h_cols[26].markdown("<div class='header-box'>Commenti</div>", unsafe_allow_html=True)
h_cols[27].markdown("<div class='header-box'>LAV</div>", unsafe_allow_html=True)

# Generazione Giorni
for gg in range(1, num_giorni + 1):
    r_cols = st.columns(col_widths)
    row_db = current_db[current_db['Giorno'] == gg]
    
    # Giorno
    r_cols[0].markdown(f"<div class='data-cell'><b>{gg:02d}</b></div>", unsafe_allow_html=True)
    
    # Ore
    ore_giorno = []
    for ora in range(1, 25):
        with r_cols[ora]:
            # Valore di default dal DB
            def_val = bool(row_db[f"H{ora:02d}"].values[0]) if not row_db.empty else False
            val = st.checkbox("", value=def_val, key=f"ch_{gg}_{ora}", label_visibility="collapsed")
            ore_giorno.append(val)
    
    temp_registro[gg] = ore_giorno
    
    # Calcoli riga
    lav = sum(ore_giorno)
    rip = 24 - lav
    
    # Commenti
    with r_cols[26]:
        def_comm = str(row_db['Commenti'].values[0]) if not row_db.empty and str(row_db['Commenti'].values[0]) != "nan" else ""
        comm = st.text_input("", value=def_comm, key=f"c_{gg}", label_visibility="collapsed")
        temp_commenti[gg] = comm
    
    # Totali riga
    r_cols[25].markdown(f"<div class='data-cell'>{rip}</div>", unsafe_allow_html=True)
    r_cols[27].markdown(f"<div class='data-cell'>{lav}</div>", unsafe_allow_html=True)

# --- AZIONE DI SALVATAGGIO ---
if save_btn:
    save_all_month(nome_sel, qual_sel, anno_sel, mese_sel, temp_registro, temp_commenti)
