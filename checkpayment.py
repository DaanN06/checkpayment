import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Soepverkoop Betaalchecker", layout="wide")
st.title("Soepverkoop Betaalchecker")

st.markdown("""
Upload hieronder je bestanden:
1. Bestellingen (.xlsx of .csv)  
2. Payconiq-export (.csv)  
3. CODA-bestand (.coda of .csv)
""")

col1, col2, col3 = st.columns(3)
with col1:
    bestellingen_file = st.file_uploader("Bestellingen", type=["xlsx", "csv"])
with col2:
    payconiq_file = st.file_uploader("Payconiq CSV", type=["csv"])
with col3:
    coda_file = st.file_uploader("CODA-bestand", type=["coda", "csv"])

def normalize_text(text):
    return re.sub(r'\W+', '', str(text).lower())

def coda_to_list(coda_file):
    # coda_file is CSV voor test (of echte CODA, gewoon als CSV)
    df = pd.read_csv(coda_file, sep=None, engine='python')  # automatisch separator detecteren
    if 'Communication' in df.columns:
        return df['Communication'].dropna().astype(str).str.strip().tolist()
    return []

if bestellingen_file and (payconiq_file or coda_file):
    if bestellingen_file.name.endswith(".xlsx"):
        bestellingen = pd.read_excel(bestellingen_file)
    else:
        bestellingen = pd.read_csv(bestellingen_file)
    bestellingen["Mededeling"] = bestellingen["Mededeling"].astype(str).str.strip()

    alle_betalingen = []

    if payconiq_file:
        payconiq_df = pd.read_csv(payconiq_file, sep=";")
        if 'Message' in payconiq_df.columns:
            alle_betalingen += payconiq_df['Message'].dropna().astype(str).str.strip().tolist()

    if coda_file:
        alle_betalingen += coda_to_list(coda_file)

    def is_betaald(mededeling):
        m_norm = normalize_text(mededeling)
        for b in alle_betalingen:
            if normalize_text(b) in m_norm:
                return True
        return False

    if 'Mededeling' not in bestellingen.columns:
        st.error("Kolom 'Mededeling' ontbreekt in bestellingen")
    else:
        bestellingen["Betaald"] = bestellingen["Mededeling"].apply(is_betaald)

        st.subheader("Resultaten")
        def highlight_betaald(val):
            color = '#b6f2b6' if val else '#f5b7b1'
            return f'background-color: {color}'

        st.dataframe(bestellingen.style.applymap(highlight_betaald, subset=['Betaald']))

        st.download_button(
            "Download resultaat",
            data=bestellingen.to_csv(index=False).encode('utf-8'),
            file_name="betaalcontrole.csv",
            mime="text/csv"
        )
else:
    st.info("Upload minstens de bestellingen en één betalingsbron (Payconiq of CODA).")
