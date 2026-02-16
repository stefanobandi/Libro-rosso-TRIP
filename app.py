import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

# --- CSS CUSTOM PER REPLICARE IL REGISTRO ---
st.markdown("""
    <style>
    /* Rimpiccioliamo i bottoni e gestiamo il font */
    div.stButton > button {
        width: 100% !important;
        height: 45px !important;
        padding: 0px !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 0px !important;
        background-color: white !important;
        transition: none !important;
    }
    
    /* Stile per la R (Riposo) */
    .stButton > button p {
        color: #d3d3d3 !important; /* Grigio tenue */
        font-weight: normal !important;
        font-size: 14px !important;
    }

    /* Stile per la X (Lavoro) - Quando cliccato lo stato cambia */
    /* Nota: Usiamo una logica di colore basata sul contenuto del tasto */
    
    /* Intestazioni e celle calcoli */
    .header-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 5px;
        text-align: center;
        font-weight: bold;
        font-size: 11px;
    }
    .calc-cell {
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #dee2e6;
        font-weight: bold;
        background-color: #ffffff;
    }
    .row-violation {
        background-color: #ffebee; /* Sfondo rossastro per violazioni */
    }
    </style>
    """, unsafe_allow_html=True)

# --- INTESTAZIONE ---
st.title("🚢 Registro Ore di Lavoro e Riposo")
st.caption("Conforme ai requisiti D.Lgs 271/99 e 108/2005")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    nome = st.text_input("Nome/Cognome Marittimo", "ROSSI MARIO")
    qualifica = st.text_input("Qualifica/Grado", "UFFICIALE")
    
    oggi = datetime.now()
    anno_sel = st.number_input("Anno", 2024, 2030, oggi.year)
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    mese_sel = st.selectbox("Mese", mesi_ita, index=oggi.month - 1)
    mese_num = mesi_ita.index(mese_sel) + 1

# --- LOGICA DATI ---
num_giorni = calendar.monthrange(anno_sel, mese_num)[1]

if 'registro' not in st.session_state:
    # Inizializziamo 31 giorni per sicurezza
    st.session_state.registro = {g: [False]*24 for g in range(1, 32)}

# --- GRIGLIA PRINCIPALE ---
# Definizione larghezze colonne: Giorno(1.2), 24 ore(1 ciascuna), Lavoro(1.5), Riposo(1.5)
col_widths = [1.2] + [1]*24 + [1.5, 1.5]
cols_h = st.columns(col_widths)

with cols_h[0]: st.markdown("<div class='header-box'>GIORNO</div>", unsafe_allow_html=True)
for i in range(24):
    with cols_h[i+1]: st.markdown(f"<div class='header-box'>{i:02d}</div>", unsafe_allow_html=True)
with cols_h[25]: st.markdown("<div class='header-box'>LAVORO</div>", unsafe_allow_html=True)
with cols_h[26]: st.markdown("<div class='header-box'>RIPOSO</div>", unsafe_allow_html=True)

total_lavoro_mese = 0
total_riposo_mese = 0

for giorno in range(1, num_giorni + 1):
    c = st.columns(col_widths)
    
    # Colonna Data
    c[0].markdown(f"<div class='calc-cell' style='font-size:12px;'>{giorno:02d}/{mese_num:02d}</div>", unsafe_allow_html=True)
    
    # 24 Ore
    for ora in range(24):
        with c[ora+1]:
            is_lavoro = st.session_state.registro[giorno][ora]
            
            # Etichetta dinamica: X grande e nera, R piccola e grigia
            label = "X" if is_lavoro else "R"
            
            # CSS inline specifico per il tasto "X" (sovrascrive il default)
            btn_style = "font-weight: 900 !important; font-size: 22px !important; color: #000000 !important;" if is_lavoro else ""
            
            if st.button(label, key=f"b_{giorno}_{ora}"):
                st.session_state.registro[giorno][ora] = not is_lavoro
                st.rerun()
    
    # Calcoli riga
    ore_l = sum(st.session_state.registro[giorno])
    ore_r = 24 - ore_l
    total_lavoro_mese += ore_l
    total_riposo_mese += ore_r

    # Colonne Totali Giornalieri
    c[25].markdown(f"<div class='calc-cell' style='color:blue;'>{ore_l}</div>", unsafe_allow_html=True)
    c[26].markdown(f"<div class='calc-cell' style='color:green;'>{ore_r}</div>", unsafe_allow_html=True)

# --- FOOTER TOTALI ---
st.divider()
f1, f2, f3 = st.columns([15, 3, 3])
with f2: st.metric("TOT. LAVORO", f"{total_lavoro_mese}h")
with f3: st.metric("TOT. RIPOSO", f"{total_riposo_mese}h")

# --- AZIONI ---
st.sidebar.divider()
if st.sidebar.button("🧹 Svuota Registro"):
    st.session_state.registro = {g: [False]*24 for g in range(1, 32)}
    st.rerun()
