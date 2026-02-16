import streamlit as st
import pandas as pd
from datetime import datetime, time

# Configurazione Pagina
st.set_page_config(page_title="Registro Ore Lavoro/Riposo (Libro Rosso)", layout="wide")

st.title("🚢 Gestione Ore di Lavoro e Riposo Marittimi")
st.subheader("Conformità D.Lgs. 271/99 e 108/2005 (STCW/MLC 2006)")

# --- SIDEBAR: Dati Marittimo ---
with st.sidebar:
    st.header("Dati Personali")
    nome = st.text_input("Nome e Cognome Marittimo", "Mario Rossi")
    qualifica = st.text_input("Qualifica", "Ufficiale di Coperta")
    data_registro = st.date_input("Data del Registro", datetime.now())

st.info(f"Registrazione per il giorno: **{data_registro}** - Marittimo: **{nome}** ({qualifica})")

# --- LOGICA DI CALCOLO ---
# Creiamo una lista di 24 ore (00:00 - 23:00)
ore = [f"{i:02d}:00" for i in range(24)]

st.write("### Inserimento Orario Giornaliero")
st.caption("Seleziona le ore in cui il marittimo era IN SERVIZIO (Lavoro). Le restanti verranno calcolate come RIPOSO.")

# Visualizzazione a griglia per simulare il "Libro Rosso" cartaceo
cols = st.columns(12)
stato_ore = []

for i in range(24):
    with cols[i % 12]:
        # Checkbox per ogni ora del giorno
        lavoro = st.checkbox(f"{ore[i]}", key=f"ora_{i}")
        stato_ore.append(lavoro)

# --- ANALISI DEI DATI ---
# 1 indica Lavoro, 0 indica Riposo
ore_riposo_binary = [0 if x else 1 for x in stato_ore]
totale_riposo = sum(ore_riposo_binary)

# Calcolo periodi consecutivi di riposo
riposo_consecutivo = []
count = 0
for bit in ore_riposo_binary:
    if bit == 1:
        count += 1
    else:
        if count > 0:
            riposo_consecutivo.append(count)
        count = 0
if count > 0:
    riposo_consecutivo.append(count)

riposo_consecutivo.sort(reverse=True)
max_riposo = riposo_consecutivo[0] if riposo_consecutivo else 0
num_periodi = len(riposo_consecutivo)

# --- VERIFICA CONFORMITÀ (D.Lgs 271/99 & 108/2005) ---
st.divider()
st.header("📊 Verifica Requisiti Minimi")

col1, col2, col3 = st.columns(3)

with col1:
    # Regola 1: Almeno 10 ore di riposo totali nelle 24h
    if totale_riposo >= 10:
        st.success(f"✅ Riposo Totale: {totale_riposo}h / 10h")
    else:
        st.error(f"❌ Riposo Totale: {totale_riposo}h / 10h (VIOLAZIONE)")

with col2:
    # Regola 2: Almeno un periodo di 6 ore consecutive
    if max_riposo >= 6:
        st.success(f"✅ Riposo Continuo: {max_riposo}h / 6h")
    else:
        st.error(f"❌ Riposo Continuo: {max_riposo}h / 6h (VIOLAZIONE)")

with col3:
    # Regola 3: Non più di 2 periodi di riposo
    if num_periodi <= 2:
        st.success(f"✅ Frazionamento: {num_periodi} periodi")
    else:
        st.warning(f"⚠️ Frazionamento: {num_periodi} periodi (Max 2)")

# --- OUTPUT GRAFICO ---
st.divider()
st.subheader("Rappresentazione Visiva Giornaliera")
# Creiamo un dataframe per il grafico a barre
df_grafico = pd.DataFrame({
    'Ora': ore,
    'Stato': ["Lavoro" if x else "Riposo" for x in stato_ore],
    'Valore': [1] * 24
})

color_map = {"Lavoro": "#FF4B4B", "Riposo": "#00CC96"}
st.bar_chart(df_grafico, x="Ora", y="Valore", color="Stato")

st.button("Salva Registro nel Database (GitHub)")
