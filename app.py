import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

# --- CSS CUSTOM PER STILE REGISTRO ---
st.markdown("""
    <style>
    /* Rimpiccioliamo i bottoni e gestiamo il font */
    div.stButton > button {
        width: 100% !important;
        height: 40px !important;
        padding: 0px !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 0px !important;
        background-color: white !important;
    }
    
    /* Stile per la R (Riposo) - Grigio tenue */
    .stButton > button p {
        color: #d3d3d3 !important;
        font-weight: normal !important;
        font-size: 14px !important;
    }

    /* Override per la X (Lavoro) - Nero e Grassetto */
    /* Usiamo un selettore basato sul testo del bottone se possibile o logica di stato */
    
    .header-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 5px;
        text-align: center;
        font-weight: bold;
        font-size: 10px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .calc-cell {
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #dee2e6;
        font-weight: bold;
        font-size: 13px;
    }
    /* Input commenti */
    .stTextInput input {
        border-radius: 0px !important;
        height: 40px !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 Libro-rosso-TRIP")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Parametri")
    nome = st.text_input("Nome/Cognome", "ROSSI MARIO")
    qualifica = st.text_input("Qualifica", "UFFICIALE")
    oggi = datetime.now()
    anno_sel = st.number_input("Anno", 2024, 2030, oggi.year)
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    mese_sel = st.selectbox("Mese", mesi_ita, index=oggi.month - 1)
    mese_num = mesi_ita.index(mese_sel) + 1

# --- LOGICA DATI ---
num_giorni = calendar.monthrange(anno_sel, mese_num)[1]

if 'registro' not in st.session_state:
    st.session_state.registro = {g: [False]*24 for g in range(1, 32)}
if 'commenti' not in st.session_state:
    st.session_state.commenti = {g: "" for g in range(1, 32)}

# --- HEADER TABELLA ---
# Giorno(1) + 24 ore(0.8 cad) + Riposo(1.2) + Commenti(2) + Lav24(1.2) + Lav7g(1.2)
col_widths = [1] + [0.8]*24 + [1.2, 2, 1.2, 1.2]
cols_h = st.columns(col_widths)

with cols_h[0]: st.markdown("<div class='header-box'>GG</div>", unsafe_allow_html=True)
for i in range(1, 25):
    with cols_h[i]: st.markdown(f"<div class='header-box'>{i:02d}</div>", unsafe_allow_html=True)
with cols_h[25]: st.markdown("<div class='header-box'>Riposo<br>24h</div>", unsafe_allow_html=True)
with cols_h[26]: st.markdown("<div class='header-box'>Commenti</div>", unsafe_allow_html=True)
with cols_h[27]: st.markdown("<div class='header-box'>Lavoro<br>24h</div>", unsafe_allow_html=True)
with cols_h[28]: st.markdown("<div class='header-box'>Lavoro<br>7gg</div>", unsafe_allow_html=True)

# --- CORPO TABELLA ---
for giorno in range(1, num_giorni + 1):
    c = st.columns(col_widths)
    
    # Giorno
    c[0].markdown(f"<div class='calc-cell'>{giorno:02d}</div>", unsafe_allow_html=True)
    
    # 24 Ore (da 01 a 24)
    for ora_index in range(24):
        with c[ora_index + 1]:
            is_lavoro = st.session_state.registro[giorno][ora_index]
            label = "X" if is_lavoro else "R"
            
            # Applichiamo stile nero/grassetto solo se è X
            if is_lavoro:
                # Usiamo markdown per iniettare il pulsante con stile specifico
                if st.button(label, key=f"b_{giorno}_{ora_index}"):
                    st.session_state.registro[giorno][ora_index] = not is_lavoro
                    st.rerun()
                st.markdown(f"<script>document.getElementById('b_{giorno}_{ora_index}').style.color='black';</script>", unsafe_allow_html=True)
                # Nota: Streamlit non permette facilmente il cambio colore dinamico del testo del bottone via CSS standard per singola istanza
                # Per garantire il nero/grassetto, usiamo un trucco di stile nell'etichetta se supportato o un widget diverso.
            else:
                if st.button(label, key=f"b_{giorno}_{ora_index}"):
                    st.session_state.registro[giorno][ora_index] = not is_lavoro
                    st.rerun()

    # Calcoli
    ore_l = sum(st.session_state.registro[giorno])
    ore_r = 24 - ore_l
    
    # Calcolo Lavoro 7 giorni (somma dei 6 giorni precedenti + corrente)
    lav_7gg = 0
    for g_prec in range(max(1, giorno-6), giorno + 1):
        lav_7gg += sum(st.session_state.registro[g_prec])

    # 1. Ore di riposo 24h
    c[25].markdown(f"<div class='calc-cell'>{ore_r}</div>", unsafe_allow_html=True)
    
    # 2. Commenti
    with c[26]:
        st.session_state.commenti[giorno] = st.text_input("", value=st.session_state.commenti[giorno], key=f"com_{giorno}", label_visibility="collapsed")
    
    # 3. Ore di lavoro 24h
    c[27].markdown(f"<div class='calc-cell'>{ore_l}</div>", unsafe_allow_html=True)
    
    # 4. Ore di lavoro 7gg
    c[28].markdown(f"<div class='calc-cell'>{lav_7gg}</div>", unsafe_allow_html=True)

# CSS finale per forzare le X nere e grasse (Hack per bottoni Streamlit)
st.markdown("""
    <script>
    const buttons = window.parent.document.querySelectorAll('button p');
    buttons.forEach(p => {
        if (p.innerText === 'X') {
            p.style.color = 'black';
            p.style.fontWeight = '900';
            p.style.fontSize = '20px';
        }
    });
    </script>
    """, unsafe_allow_html=True)
