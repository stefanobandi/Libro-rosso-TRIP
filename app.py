import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="Libro-rosso-TRIP", layout="wide")

# CSS Custom per la griglia e le X/R
st.markdown("""
    <style>
    .stCheckbox label {
        display: none;
    }
    .stCheckbox {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .grid-cell {
        text-align: center;
        font-weight: bold;
        font-size: 18px;
    }
    .text-r { color: #d3d3d3; } /* Grigio tenue per R */
    .text-x { color: #ff4b4b; font-size: 22px; } /* Rosso per X */
    </style>
    """, unsafe_allow_html=True)

st.title("🚢 Libro-rosso-TRIP")
st.subheader("Registro Mensile delle Ore di Lavoro e Riposo")

# --- SIDEBAR: Dati Marittimo e Selezione Mese ---
with st.sidebar:
    st.header("Anagrafica & Periodo")
    nome = st.text_input("Nome e Cognome Marittimo", "Mario Rossi")
    qualifica = st.text_input("Qualifica", "Ufficiale di Coperta")
    
    # Selezione Mese e Anno
    oggi = datetime.now()
    anno_sel = st.selectbox("Anno", range(oggi.year - 1, oggi.year + 2), index=1)
    mesi = list(calendar.month_name)[1:] # Lista mesi in inglese (o puoi tradurli)
    mese_sel_nome = st.selectbox("Mese di Registro", mesi, index=oggi.month - 1)
    mese_num = mesi.index(mese_sel_nome) + 1

st.info(f"Registro di: **{mese_sel_nome} {anno_sel}** | Personale: **{nome}** ({qualifica})")

# --- GENERAZIONE GRIGLIA MENSILE ---
num_giorni = calendar.monthrange(anno_sel, mese_num)[1]
ore_cols = [f"{i:02d}" for i in range(24)]

# Intestazione Colonne (Ore)
cols_header = st.columns([1.5] + [1]*24)
cols_header[0].write("**Giorno**")
for i, h in enumerate(ore_cols):
    cols_header[i+1].write(f"**{h}**")

st.divider()

# Dizionario per salvare lo stato delle celle (in una app reale questo andrebbe su DB/File)
if 'registro_dati' not in st.session_state:
    st.session_state.registro_dati = {}

# Ciclo per ogni giorno del mese
for giorno in range(1, num_giorni + 1):
    c = st.columns([1.5] + [1]*24)
    
    # Colonna Giorno
    data_str = f"{giorno:02d}/{mese_num:02d}"
    c[0].write(f"**{data_str}**")
    
    for ora in range(24):
        key = f"cell_{anno_sel}_{mese_num}_{giorno}_{ora}"
        
        # Inizializziamo lo stato se non esiste
        if key not in st.session_state:
            st.session_state[key] = False
            
        with c[ora+1]:
            # Checkbox per selezionare il lavoro
            lavoro = st.checkbox("", key=key, label_visibility="collapsed")
            
            # Visualizzazione R o X sotto il checkbox
            if lavoro:
                st.markdown('<div class="grid-cell text-x">X</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="grid-cell text-r">R</div>', unsafe_allow_html=True)

st.divider()

# --- FOOTER ---
col_f1, col_f2 = st.columns(2)
with col_f1:
    if st.button("💾 Salva Registro Mensile"):
        st.success(f"Dati di {mese_sel_nome} salvati correttamente!")

with col_f2:
    st.download_button(
        label="📥 Esporta in CSV",
        data="Esempio dati CSV", # Qui andrà la logica di conversione del dizionario session_state
        file_name=f"Libro_Rosso_{mese_sel_nome}_{anno_sel}.csv",
        mime="text/csv",
    )
