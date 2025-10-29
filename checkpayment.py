import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Betaalchecker", layout="wide")
st.title("Soepverkoop Betaalchecker")

st.markdown("""
Upload hieronder je bestanden:
1. **Bestellingen** (.xlsx of .csv)  
2. **Payconiq-export** (.csv)  
3. **Argenta-export (CODA)** (.xlsx, .csv of .coda)
""")

col1, col2, col3 = st.columns(3)
with col1:
    bestellingen_file = st.file_uploader("Bestellingen", type=["xlsx", "csv"])
with col2:
    payconiq_file = st.file_uploader("Payconiq CSV", type=["csv"])
with col3:
    coda_file = st.file_uploader("Argenta-bestand", type=["xlsx", "csv", "coda"])

def normalize_text(text):
    """Verwijdert hoofdletters en niet-alfanumerieke tekens."""
    return re.sub(r'\W+', '', str(text).lower())

def coda_to_list(coda_file):
    """Leest Argenta- of CODA-bestand en zoekt de juiste kolom."""
    # Probeer automatisch scheidingsteken te detecteren
    if coda_file.name.endswith(".xlsx"):
        df = pd.read_excel(coda_file)
    else:
        df = pd.read_csv(coda_file, sep=None, engine='python')

    # Kolomnamen strippen
    df.columns = [c.strip() for c in df.columns]

    # Gebruik 'Mededeling' indien aanwezig, anders fallback
    for col in ["Mededeling", "Communication", "Omschrijving", "Beschrijving"]:
        if col in df.columns:
            return df[col].dropna().astype(str).str.strip().tolist()
    return []

if bestellingen_file and (payconiq_file or coda_file):
    # Bestellingen inlezen
    if bestellingen_file.name.endswith(".xlsx"):
        bestellingen = pd.read_excel(bestellingen_file)
    else:
        bestellingen = pd.read_csv(bestellingen_file)
    bestellingen.columns = [c.strip() for c in bestellingen.columns]

    # Kolom kiezen waarin de bestelcode staat
    bestelkolom = st.selectbox(
        "Selecteer de kolom met de bestelcode/mededeling (uit je bestellingenbestand)",
        bestellingen.columns.tolist()
    )

    alle_betalingen = []

    # Payconiq
    if payconiq_file:
        payconiq_df = pd.read_csv(payconiq_file, sep=None, engine='python')
        payconiq_df.columns = [c.strip() for c in payconiq_df.columns]
        for col in ["Message", "Mededeling", "Omschrijving"]:
            if col in payconiq_df.columns:
                alle_betalingen += payconiq_df[col].dropna().astype(str).str.strip().tolist()
                break

    # Argenta / CODA
    if coda_file:
        alle_betalingen += coda_to_list(coda_file)

    def is_betaald(code):
        code_norm = normalize_text(code)
        for b in alle_betalingen:
            if normalize_text(b) in code_norm or code_norm in normalize_text(b):
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
    st.info("Upload minstens de bestellingen en één betalingsbron (Payconiq of Argenta).")
