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
        return pd.read_csv(DB_FILE)
    else:
        # Crea dataframe vuoto se il file non esiste
        cols = ["Marittimo", "Qualifica", "Anno", "Mese", "Giorno"] + [f"H{i:02d}" for i in range(1, 25)] + ["Commenti"]
        return pd.DataFrame(columns=cols)

def save_row(row_data):
    df = load_data()
    # Rimuove la riga vecchia se esiste (stesso marittimo, anno, mese, giorno)
    df = df[~((df['Marittimo'] == row_data['Marittimo']) & 
              (df['Anno'] == row_data['Anno']) & 
              (df['Mese'] == row_data['Mese']) & 
              (df['Giorno'] == row_data['Giorno']))]
    # Aggiunge la nuova riga
    df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- INTERFACCIA ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .header-box { background-color: #f2f2f2; border: 1px solid #999; text-align: center; font-weight: bold; font-size: 11px; height: 40px; display: flex; align-items: center; justify-content: center; }
    .data-cell { height: 35px; display: flex; align-items: center; justify-content: center; border: 1px solid #ccc; font-size: 13px; }
    [data-testid="stCheckbox"] { display: flex; justify-content: center; align-items: center; height: 35px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 Libro-rosso-TRIP")

# --- SIDEBAR: Filtri di Caricamento ---
with st.sidebar:
    st.header("📂 Caricamento Dati")
    nome_sel = st.text_input("Marittimo", "ROSSI MARIO").upper()
    qual_sel = st.text_input("Qualifica", "UFFICIALE").upper()
    
    oggi = datetime.now()
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    mese_sel = st.selectbox("Mese", mesi_ita, index=oggi.month - 1)
    anno_sel = st.selectbox("Anno", [2024, 2025, 2026], index=1)

# --- LOGICA DI FRAMMENTO (ANTI-LAG) ---
@st.fragment
def render_registro(nome, qualifica, mese, anno):
    mese_num = mesi_ita.index(mese) + 1
    num_giorni = calendar.monthrange(anno, mese_num)[1]
    
    # Carica dati esistenti dal DB
    full_db = load_data()
    current_data = full_db[(full_db['Marittimo'] == nome) & (full_db['Mese'] == mese) & (full_db['Anno'] == anno)]

    # Header Tabella
    col_widths = [1] + [0.6]*24 + [1.2, 2.5, 1.2]
    h_cols = st.columns(col_widths)
    h_cols[0].markdown("<div class='header-box'>GG</div>", unsafe_allow_html=True)
    for i in range(1, 25): h_cols[i].markdown(f"<div class='header-box'>{i:02d}</div>", unsafe_allow_html=True)
    h_cols[25].markdown("<div class='header-box'>Riposo</div>", unsafe_allow_html=True)
    h_cols[26].markdown("<div class='header-box'>Commenti</div>", unsafe_allow_html=True)
    h_cols[27].markdown("<div class='header-box'>Lav.24h</div>", unsafe_allow_html=True)

    # Griglia Giorni
    for gg in range(1, num_giorni + 1):
        r_cols = st.columns(col_widths)
        
        # Recupera stato riga se esiste nel DB
        row_db = current_data[current_data['Giorno'] == gg]
        
        # Giorno
        r_cols[0].markdown(f"<div class='data-cell'><b>{gg:02d}</b></div>", unsafe_allow_html=True)
        
        # 24 Ore (Checkbox)
        lavoro_ore = []
        for ora in range(1, 25):
            with r_cols[ora]:
                key = f"h_{nome}_{anno}_{mese}_{gg}_{ora}"
                default_val = bool(row_db[f"H{ora:02d}"].values[0]) if not row_db.empty else False
                val = st.checkbox("", value=default_val, key=key, label_visibility="collapsed")
                lavoro_ore.append(val)
        
        # Calcoli veloci di riga
        ore_l = sum(lavoro_ore)
        ore_r = 24 - ore_l
        
        # Commenti e Salvataggio automatico riga
        with r_cols[26]:
            def_comm = str(row_db['Commenti'].values[0]) if not row_db.empty and str(row_db['Commenti'].values[0]) != "nan" else ""
            comm = st.text_input("", value=def_comm, key=f"c_{gg}", label_visibility="collapsed")
        
        # Visualizzazione Totali
        r_cols[25].markdown(f"<div class='data-cell'>{ore_r}</div>", unsafe_allow_html=True)
        r_cols[27].markdown(f"<div class='data-cell'>{ore_l}</div>", unsafe_allow_html=True)

        # Se i dati sono cambiati rispetto al DB, salviamo la riga
        # (Nota: Per semplicità salviamo al click del commento o interazione riga)
        if st.button("💾", key=f"save_{gg}", help="Salva riga"):
            new_row = {
                "Marittimo": nome, "Qualifica": qualifica, "Anno": anno, "Mese": mese, "Giorno": gg,
                "Commenti": comm
            }
            for i, v in enumerate(lavoro_ore): new_row[f"H{i+1:02d}"] = v
            save_row(new_row)
            st.toast(f"Giorno {gg} salvato!")

# Esecuzione del frammento
render_registro(nome_sel, qual_sel, mese_sel, anno_sel)

st.divider()
st.info("I dati vengono isolati per marittimo e periodo. Clicca sul dischetto 💾 a fine riga per confermare il salvataggio nel database.")
