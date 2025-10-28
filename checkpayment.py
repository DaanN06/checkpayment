import streamlit as st
import pandas as pd
from io import StringIO
from coda import CodaFile

st.set_page_config(page_title="Soepverkoop Betaalchecker", layout="wide")
st.title("Soepverkoop Betaalchecker")

st.markdown("""
Upload hieronder je drie bestanden:
1. Bestellingen (.xlsx)  
2. Payconiq-export (.csv)  
3. CODA-bestand (.coda)
""")

col1, col2, col3 = st.columns(3)
with col1:
    bestellingen_file = st.file_uploader("Bestellingen", type=["xlsx"])
with col2:
    payconiq_file = st.file_uploader("Payconiq CSV", type=["csv"])
with col3:
    coda_file = st.file_uploader("CODA-bestand", type=["coda"])

if bestellingen_file and (payconiq_file or coda_file):
    if bestellingen_file.name.endswith(".xlsx"):
        bestellingen = pd.read_excel(bestellingen_file)
    else:
        bestellingen = pd.read_csv(bestellingen_file)

    payconiq_mededelingen = []
    if payconiq_file:
        payconiq_df = pd.read_csv(payconiq_file, sep=";")
        payconiq_mededelingen = payconiq_df['Message'].dropna().astype(str).tolist()

    coda_mededelingen = []
    if coda_file:
        coda_bytes = coda_file.read()
        coda = CodaFile(coda_bytes)
        for tx in coda.transactions:
            if tx.communication:
                coda_mededelingen.append(tx.communication)

    alle_betalingen = payconiq_mededelingen + coda_mededelingen

    def is_betaald(mededeling):
        if not isinstance(mededeling, str):
            return False
        return any(mededeling.lower() in b.lower() for b in alle_betalingen)

    bestellingen["Betaald"] = bestellingen["Mededeling"].apply(is_betaald)

    st.subheader("Resultaten")
    def highlight_betaald(val):
        color = '#b6f2b6' if val else '#f5b7b1'
        return f'background-color: {color}'

    st.dataframe(bestellingen.style.applymap(highlight_betaald, subset=['Betaald']))

    st.download_button(
        "Download",
        data=bestellingen.to_csv(index=False).encode('utf-8'),
        file_name="betaalcontrole.csv",
        mime="text/csv"
    )
else:
    st.info("Upload minstens de bestellingen en één betalingsbron (Payconiq of CODA).")
