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

# --- 2. LOGICA: PASPOORT OF ADMIN? ---
query_params = st.query_params

if "id" in query_params:
    # --- PASPOORT PAGINA (Consument) ---
    battery_id = query_params["id"]
    with httpx.Client() as client:
        resp = client.get(f"{API_URL}?id=eq.{battery_id}", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            data = resp.json()[0]
            st.success("✅ Officieel EU Product Paspoort")
            st.title(f"🔋 Model: {data['name']}")
            st.write(f"**Fabrikant:** {data['manufacturer']}")
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("CO2 Voetafdruk", f"{data['carbon_footprint']} kg")
            c2.metric("Gerecycled Materiaal", f"{data['recycled_content']}%")
        else:
            st.error("Paspoort niet gevonden.")
else:
    # --- ADMIN PAGINA ---
    st.title("🏗️ DPP Management System")
    
    tab1, tab2 = st.tabs(["Nieuwe Batterij", "Bulk Upload (CSV)"])

    with tab1:
        st.subheader("Voeg één batterij toe")
        qr_data = None
        temp_name = ""

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
                        # QR Genereren
                        passport_url = f"https://digitalpassport.streamlit.app/?id={new_id}"
                        qr = qrcode.make(passport_url)
                        buf = BytesIO()
                        qr.save(buf, format="PNG")
                        qr_data = buf.getvalue()
                        temp_name = name
                        st.success(f"Batterij opgeslagen! ID: {new_id}")
                    else:
                        st.error(f"Fout: {res.text}")

        # De downloadknop staat nu VEILIG buiten het formulier
        if qr_data:
            st.image(qr_data, width=200)
            st.download_button("Download QR Code", qr_data, f"QR_{temp_name}.png", "image/png")

    with tab2:
        st.subheader("Meerdere batterijen tegelijk uploaden")
        st.write("Upload een CSV met de kolommen: `name`, `manufacturer`, `carbon_footprint`, `recycled_content`")
        
        file = st.file_uploader("Kies CSV bestand", type="csv")
        if file:
            df = pd.read_csv(file)
            st.dataframe(df.head())
            
            if st.button("Start Bulk Import"):
                with httpx.Client() as client:
                    count = 0
                    for _, row in df.iterrows():
                        payload = {
                            "name": str(row['name']),
                            "manufacturer": str(row['manufacturer']),
                            "carbon_footprint": float(row['carbon_footprint']),
                            "recycled_content": int(row['recycled_content'])
                        }
                        client.post(API_URL, json=payload, headers=headers)
                        count += 1
                st.success(f"Succes! {count} batterijen toegevoegd.")
