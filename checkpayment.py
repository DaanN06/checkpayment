import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Betaalchecker", layout="wide")
st.title("Betaalchecker")

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
    # CODA als CSV
    df = pd.read_csv(coda_file, sep=None, engine='python')  # auto detect separator
    # Check voor mogelijke kolommen met betalingsreferentie
    for col in ['Communication', 'Omschrijving', 'Message', 'Betaalcode']:
        if col in df.columns:
            return df[col].dropna().astype(str).str.strip().tolist()
    return []

if bestellingen_file and (payconiq_file or coda_file):
    # Bestellingen inlezen
    if bestellingen_file.name.endswith(".xlsx"):
        bestellingen = pd.read_excel(bestellingen_file)
    else:
        bestellingen = pd.read_csv(bestellingen_file)

    # Kolomnamen strippen van spaties
    bestellingen.columns = [col.strip() for col in bestellingen.columns]

    # Dropdown met schone kolomnamen
    bestelkolom = st.selectbox(
    "Selecteer de kolom met de bestelcode/mededeling",
        bestellingen.columns.tolist()
    )

    alle_betalingen = []

    if payconiq_file:
        payconiq_df = pd.read_csv(payconiq_file, sep=None, engine='python')
        for col in ['Message', 'Omschrijving', 'Betalingscode']:
            if col in payconiq_df.columns:
                alle_betalingen += payconiq_df[col].dropna().astype(str).str.strip().tolist()
                break

    if coda_file:
        alle_betalingen += coda_to_list(coda_file)

    def is_betaald(code):
        code_norm = normalize_text(code)
        for b in alle_betalingen:
            if normalize_text(b) in code_norm:
                return True
        return False

    bestellingen["Betaald"] = bestellingen[bestelkolom].apply(is_betaald)

    st.subheader("Resultaten")
    def highlight_betaald(val):
        return 'background-color: #b6f2b6' if val else 'background-color: #f5b7b1'

    st.dataframe(bestellingen.style.applymap(highlight_betaald, subset=['Betaald']))

    st.download_button(
        "Download resultaat",
        data=bestellingen.to_csv(index=False).encode('utf-8'),
        file_name="betaalcontrole.csv",
        mime="text/csv"
    )
else:
    st.info("Upload minstens de bestellingen en één betalingsbron (Payconiq of CODA).")
