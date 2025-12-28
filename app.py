import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL = f"{SUPABASE_URL}/rest/v1/Batteries"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

st.set_page_config(page_title="EU Battery Passport", page_icon="🔋", layout="wide")

# Session state voor QR codes
if 'qr_data' not in st.session_state:
    st.session_state.qr_data = None
if 'temp_name' not in st.session_state:
    st.session_state.temp_name = ""

# --- 2. LOGICA: PASPOORT OF ADMIN? ---
query_params = st.query_params

if "id" in query_params:
    battery_id = query_params["id"]
    with httpx.Client() as client:
        resp = client.get(f"{API_URL}?id=eq.{battery_id}", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            data = resp.json()[0]
            st.success("✅ Officieel EU Product Paspoort")
            st.title(f"🔋 Model: {data.get('name', 'Onbekend')}")
            st.write(f"**Fabrikant:** {data.get('manufacturer', 'Onbekend')}")
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("CO2 Voetafdruk", f"{data.get('carbon_footprint', 0)} kg")
            c2.metric("Gerecycled Materiaal", f"{data.get('recycled_content', 0)}%")
        else:
            st.error("Paspoort niet gevonden.")
else:
    st.title("🏗️ DPP Management System")
    
    tab1, tab2 = st.tabs(["Nieuwe Batterij", "Bulk Upload (CSV)"])

    with tab1:
        st.subheader("Voeg één batterij toe")
        with st.form("single_entry", clear_on_submit=True):
            name = st.text_input("Product Naam")
            mfr = st.text_input("Fabrikant")
            co2 = st.number_input("CO2 (kg)", min_value=0.0)
            recycled = st.slider("Gerecycled %", 0, 100, 25)
            submit = st.form_submit_button("Opslaan in Database")

            if submit and name and mfr:
                payload = {"name": name, "manufacturer": mfr, "carbon_footprint": co2, "recycled_content": recycled}
                with httpx.Client() as client:
                    res = client.post(API_URL, json=payload, headers=headers)
                    if res.status_code == 201:
                        new_id = res.json()[0]['id']
                        passport_url = f"https://digitalpassport.streamlit.app/?id={new_id}"
                        qr = qrcode.make(passport_url)
                        buf = BytesIO()
                        qr.save(buf, format="PNG")
                        st.session_state.qr_data = buf.getvalue()
                        st.session_state.temp_name = name
                        st.success(f"Batterij opgeslagen! ID: {new_id}")
                    else:
                        st.error(f"Fout: {res.text}")

        if st.session_state.qr_data:
            st.divider()
            st.image(st.session_state.qr_data, width=200)
            st.download_button("Download QR Code", st.session_state.qr_data, f"QR_{st.session_state.temp_name}.png", "image/png")

    with tab2:
        st.subheader("Bulk Import")
        st.info("Zorg dat de eerste regel van je CSV deze koppen heeft: name, manufacturer, carbon_footprint, recycled_content")
        
        file = st.file_uploader("Upload je CSV bestand", type="csv")
        if file:
            # utf-8-sig haalt onzichtbare Excel-tekentjes (BOM) weg
            df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
            
            # Schoon kolomnamen op
            df.columns = [c.lower().strip() for c in df.columns]
            
            st.write("Gevonden kolommen in je bestand:", list(df.columns))
            st.dataframe(df.head())
            
            # Check of de cruciale kolom 'name' wel bestaat
            if 'name' not in df.columns:
                st.error("⚠️ Fout: Ik kan de kolom 'name' niet vinden. Staan de kolomnamen wel op de eerste regel?")
            else:
                if st.button("Start Bulk Import"):
                    with httpx.Client() as client:
                        success_count = 0
                        for index, row in df.iterrows():
                            try:
                                payload = {
                                    "name": str(row['name']),
                                    "manufacturer": str(row.get('manufacturer', 'Onbekend')),
                                    "carbon_footprint": float(row.get('carbon_footprint', 0)),
                                    "recycled_content": int(row.get('recycled_content', 0))
                                }
                                res = client.post(API_URL, json=payload, headers=headers)
                                if res.status_code == 201:
                                    success_count += 1
                                else:
                                    st.warning(f"Rij {index+1} mislukt: {res.text}")
                            except Exception as e:
                                st.warning(f"Rij {index+1} overgeslagen: {e}")
                                
                        st.success(f"Klaar! {success_count} batterijen succesvol toegevoegd.")
