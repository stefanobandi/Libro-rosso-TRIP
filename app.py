import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

# --- CSS CUSTOM PER GRIGLIA PULITA E VELOCE ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    
    .official-header {
        border-bottom: 2px solid black;
        margin-bottom: 20px;
        padding-bottom: 10px;
    }

    /* Stile per le Checkbox nella griglia */
    [data-testid="stCheckbox"] {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 35px;
        margin: 0;
        padding: 0;
    }

    /* Header Tabella */
    .header-box {
        background-color: #f2f2f2;
        border: 1px solid #999999;
        text-align: center;
        font-weight: bold;
        font-size: 11px;
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Celle Dati/Calcoli */
    .data-cell {
        height: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #cccccc;
        font-size: 13px;
        background-color: white;
    }
    
    /* Input Commenti */
    .stTextInput input {
        border-radius: 0px !important;
        border: 1px solid #cccccc !important;
        height: 35px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INTESTAZIONE SUPERIORE ---
with st.container():
    col_tit1, col_tit2 = st.columns([1, 4])
    with col_tit1:
        st.write("🚢 **Libro-rosso-TRIP**")
    with col_tit2:
        st.markdown("<div class='official-header'><h3>Registrazione delle Ore di Lavoro e di Riposo dei Marittimi</h3>"
                    "<p>Conforme al D.Lgs. 271/99 e D.Lgs. 108/2005</p></div>", unsafe_allow_html=True)

# --- BARRA DATI ---
d1, d2, d3, d4 = st.columns(4)
with d1: nome = st.text_input("Nome/Cognome", "ROSSI MARIO")
with d2: qualifica = st.text_input("Qualifica/Grado", "UFFICIALE")
with d3: 
    oggi = datetime.now()
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    mese_sel = st.selectbox("Mese di riferimento", mesi_ita, index=oggi.month - 1)
with d4: anno_sel = st.selectbox("Anno", [2024, 2025, 2026], index=1)

mese_num = mesi_ita.index(mese_sel) + 1
num_giorni = calendar.monthrange(anno_sel, mese_num)[1]

# --- INIZIALIZZAZIONE / CARICAMENTO DATI ---
# In questa fase usiamo session_state. In futuro qui caricheremo dal file esterno.
if 'registro' not in st.session_state:
    st.session_state.registro = {g: [False]*24 for g in range(1, 32)}
if 'commenti' not in st.session_state:
    st.session_state.commenti = {g: "" for g in range(1, 32)}

# --- GRIGLIA REGISTRO ---
col_widths = [1] + [0.7]*24 + [1.2, 2.5, 1.2, 1.2]
h_cols = st.columns(col_widths)

with h_cols[0]: st.markdown("<div class='header-box'>GG</div>", unsafe_allow_html=True)
for i in range(1, 25):
    with h_cols[i]: st.markdown(f"<div class='header-box'>{i:02d}</div>", unsafe_allow_html=True)
with h_cols[25]: st.markdown("<div class='header-box'>Riposo<br>24h</div>", unsafe_allow_html=True)
with h_cols[26]: st.markdown("<div class='header-box'>Commenti</div>", unsafe_allow_html=True)
with h_cols[27]: st.markdown("<div class='header-box'>Lavoro<br>24h</div>", unsafe_allow_html=True)
with h_cols[28]: st.markdown("<div class='header-box'>Lavoro<br>7gg</div>", unsafe_allow_html=True)

# Loop Giorni
for gg in range(1, num_giorni + 1):
    r_cols = st.columns(col_widths)
    
    # 1. Colonna Giorno
    r_cols[0].markdown(f"<div class='data-cell'><b>{gg:02d}</b></div>", unsafe_allow_html=True)
    
    # 2. 24 Ore (Checkbox invece di Button per velocità)
    for ora in range(24):
        with r_cols[ora + 1]:
            # La checkbox aggiorna direttamente lo stato senza ricaricare tutto forzatamente
            st.session_state.registro[gg][ora] = st.checkbox(
                "", 
                value=st.session_state.registro[gg][ora], 
                key=f"ch_{gg}_{ora}", 
                label_visibility="collapsed"
            )

    # 3. Calcoli
    ore_l = sum(st.session_state.registro[gg])
    ore_r = 24 - ore_l
    
    lav_7gg = 0
    for p in range(max(1, gg-6), gg + 1):
        lav_7gg += sum(st.session_state.registro[p])

    # 4. Colonne Risultati
    r_cols[25].markdown(f"<div class='data-cell'>{ore_r}</div>", unsafe_allow_html=True)
    with r_cols[26]:
        st.session_state.commenti[gg] = st.text_input("", value=st.session_state.commenti[gg], key=f"c_{gg}", label_visibility="collapsed")
    r_cols[27].markdown(f"<div class='data-cell'>{ore_l}</div>", unsafe_allow_html=True)
    r_cols[28].markdown(f"<div class='data-cell' style='background-color:#f9f9f9'>{lav_7gg}</div>", unsafe_allow_html=True)

# --- FOOTER ---
st.divider()
col_f1, col_f2 = st.columns([8, 2])
with col_f2:
    if st.button("💾 Salva Sessione"):
        # Placeholder per la funzione di salvataggio file esterno
        st.success("Dati pronti per il salvataggio!")
