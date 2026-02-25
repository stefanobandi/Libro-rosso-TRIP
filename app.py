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
    st.sidebar.success(f"✅ Salvataggio completato!")

# --- CSS CUSTOM (Nuovi stili per violazioni e layout) ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem !important; }
    .header-box { background-color: #f2f2f2; border: 1px solid #999; text-align: center; font-weight: bold; font-size: 10px; height: 40px; display: flex; align-items: center; justify-content: center; }
    .data-cell { height: 35px; display: flex; align-items: center; justify-content: center; border: 1px solid #ccc; font-size: 12px; background-color: white; }
    .violation-cell { background-color: #ffcccc !important; color: #b71c1c; font-weight: bold; }
    .promemoria-tab { width: 100%; border-collapse: collapse; margin-top: 30px; }
    .promemoria-tab td, .promemoria-tab th { border: 1px solid #999; padding: 8px; font-size: 13px; }
    .promemoria-header { background-color: #333; color: white; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("🚢 Gestione Personale")

df_ana = load_data(ANA_FILE, ["Marittimo", "Qualifica"])
opzioni_marittimi = (df_ana['Marittimo'] + " - " + df_ana['Qualifica']).tolist()

selezione = st.sidebar.selectbox("Selezione Marittimo", ["---"] + opzioni_marittimi)

if selezione != "---":
    nome_corrente = selezione.split(" - ")[0]
    qual_corrente = selezione.split(" - ")[1]
    
    # Sezione Periodo
    df_main = load_data(DB_FILE, [])
    storico = df_main[df_main['Marittimo'] == nome_corrente][['Mese', 'Anno']].drop_duplicates()
    opzioni_periodo = [f"{r['Mese']} {r['Anno']}" for _, r in storico.iterrows()]
    opzioni_periodo.append("➕ Inizia nuovo mese...")
    
    periodo_sel = st.sidebar.selectbox("Periodo di riferimento", opzioni_periodo)
    mesi_ita = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    
    if periodo_sel == "➕ Inizia nuovo mese...":
        col_m, col_a = st.sidebar.columns(2)
        mese_compila = col_m.selectbox("Mese", mesi_ita, index=datetime.now().month-1)
        anno_compila = col_a.selectbox("Anno", [2025, 2026, 2027], index=1)
    else:
        mese_compila = periodo_sel.split(" ")[0]
        anno_compila = int(periodo_sel.split(" ")[1])

    # SPOSTAMENTO: Crea Nuovo Marittimo ora è SOTTO il periodo
    st.sidebar.divider()
    with st.sidebar.expander("➕ Crea Nuovo Marittimo"):
        nuovo_nome = st.text_input("Nome e Cognome", key="n_m").upper().strip()
        nuova_qual = st.text_input("Qualifica", key="q_m").upper().strip()
        if st.button("Registra"):
            if nuovo_nome and nuova_qual:
                if save_new_marittimo(nuovo_nome, nuova_qual):
                    st.success("Registrato!")
                    st.rerun()
    
    st.sidebar.divider()
    save_btn = st.sidebar.button("💾 SALVA TUTTO IL MESE", use_container_width=True)

    # --- LOGICA TABELLA ---
    st.markdown(f"## Registro: {nome_corrente} ({qual_corrente})")
    
    current_db = df_main[(df_main['Marittimo'] == nome_corrente) & (df_main['Mese'] == mese_compila) & (df_main['Anno'] == anno_compila)]
    mese_num = mesi_ita.index(mese_compila) + 1
    num_giorni = calendar.monthrange(anno_compila, mese_num)[1]

    temp_registro = {}
    temp_commenti = {}

    col_widths = [0.8] + [0.5]*24 + [1, 2, 1, 1.2]
    h_cols = st.columns(col_widths)
    headers = ["GG"] + [f"{i:02d}" for i in range(1, 25)] + ["RIP", "Commenti", "LAV", "LAV 7g"]
    for idx, name in enumerate(headers):
        h_cols[idx].markdown(f"<div class='header-box'>{name}</div>", unsafe_allow_html=True)

    # Raccolta dati per calcolo 7 giorni e violazioni
    ore_mensili = []
    
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
        ore_mensili.append(sum(ore_giorno))
        
        lav_24 = sum(ore_giorno)
        rip_24 = 24 - lav_24
        
        # Calcolo 7 giorni (Mobile)
        # Nota: In questa versione semplificata calcola sui dati correnti del mese visualizzato
        lav_7g = sum(ore_mensili[max(0, gg-7):gg])

        # Test Violazioni per riga
        # 1) Max 14h lavoro in 24h
        v1 = lav_24 > 14
        # 3) Almeno 6h riposo continuato (Logica semplificata su blocchi)
        rip_bin = [0 if x else 1 for x in ore_giorno]
        max_rip_cont = 0
        curr_rip = 0
        for b in rip_bin:
            if b == 1: curr_rip += 1
            else:
                max_rip_cont = max(max_rip_cont, curr_rip)
                curr_rip = 0
        max_rip_cont = max(max_rip_cont, curr_rip)
        v2 = max_rip_cont < 6
        # 2) Max 72h lavoro in 7gg
        v3 = lav_7g > 72

        with r_cols[26]:
            def_comm = str(row_db['Commenti'].values[0]) if not row_db.empty and str(row_db['Commenti'].values[0]) != "nan" else ""
            temp_commenti[gg] = st.text_input("", value=def_comm, key=f"c_{gg}_{mese_compila}", label_visibility="collapsed")
        
        # Visualizzazione con evidenziazione violazioni
        style_lav = "violation-cell" if v1 else ""
        style_7g = "violation-cell" if v3 else ""
        style_rip = "violation-cell" if v2 else ""

        r_cols[25].markdown(f"<div class='data-cell {style_rip}'>{rip_24}</div>", unsafe_allow_html=True)
        r_cols[27].markdown(f"<div class='data-cell {style_lav}'>{lav_24}</div>", unsafe_allow_html=True)
        r_cols[28].markdown(f"<div class='data-cell {style_7g}'>{lav_7g}</div>", unsafe_allow_html=True)

    # --- PROMEMORIA FISSO IN FONDO ---
    st.markdown(f"""
    <table class="promemoria-tab">
        <tr class="promemoria-header"><th colspan="2">PROMEMORIA TEST DI CONFORMITÀ (D.Lgs 271/99 - 108/05)</th></tr>
        <tr><td><b>1) Max Lavoro / 7 Giorni</b></td><td>Non deve superare le <b>72 ore</b> (Evidenziato in rosso nell'ultima colonna)</td></tr>
        <tr><td><b>2) Max Lavoro / 24 Ore</b></td><td>Non deve superare le <b>14 ore</b> (Evidenziato in rosso nella colonna LAV)</td></tr>
        <tr><td><b>3) Riposo Continuato</b></td><td>Almeno un blocco da <b>6 ore</b> consecutive (Evidenziato in rosso nella colonna RIP)</td></tr>
    </table>
    """, unsafe_allow_html=True)

    if save_btn:
        save_all_month(nome_corrente, qual_corrente, anno_compila, mese_compila, temp_registro, temp_commenti)
else:
    st.info("👈 Seleziona un marittimo per visualizzare il registro.")
