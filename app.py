import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL = f"{SUPABASE_URL}/rest/v1/Batteries" # Let op: hoofdletter B gehouden zoals in je DB

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

st.set_page_config(page_title="EU Digital Battery Passport", page_icon="🔋")

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
            st.title(f"🔋 {data['name']}")
            st.write(f"**Fabrikant:** {data['manufacturer']}")
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("CO2 Voetafdruk", f"{data['carbon_footprint']} kg")
            c2.metric("Gerecycled Materiaal", f"{data['recycled_content']}%")
            st.divider()
            st.info("ℹ️ Voldoet aan EU 2023/1542.")
        else:
            st.error("Paspoort niet gevonden.")
else:
    # --- ADMIN PAGINA ---
    st.title("🏗️ DPP Admin & Bulk Generator")
    
    tab1, tab2 = st.tabs(["Enkele Batterij", "Bulk Upload (CSV)"])

    with tab1:
        with st.form("single_entry", clear_on_submit=True):
            name = st.text_input("Product Naam")
            mfr = st.text_input("Fabrikant")
            co2 = st.number_input("CO2 (kg)", min_value=0.0)
            recycled = st.slider("Gerecycled %", 0, 100)
            submit = st.form_submit_button("Sla op & Genereer QR")

            if submit and name and mfr:
                payload = {"name": name, "manufacturer": mfr, "carbon_footprint": co2, "recycled_content": recycled}
                with httpx.Client() as client:
                    res = client.post(API_URL, json=payload, headers=headers)
                    if res.status_code == 201:
                        new_id = res.json()[0]['id']
                        # NIEUWE URL GEBRUIKT:
                        passport_url = f"https://digitalpassport.streamlit.app/?id={new_id}"
                        qr = qrcode.make(passport_url)
                        buf = BytesIO()
                        qr.save(buf, format="PNG")
                        st.success(f"Geregistreerd! ID: {new_id}")
                        st.image(buf, width=200)
                        st.download_button("Download QR", buf.getvalue(), f"QR_{name}.png")

    with tab2:
        st.write("Upload een CSV-bestand met kolommen: `name`, `manufacturer`, `carbon_footprint`, `recycled_content`")
        uploaded_file = st.file_uploader("Kies een CSV bestand", type="csv")
        
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.write("Voorvertoning van data:", df.head())
            
            if st.button("Start Bulk Registratie"):
                with httpx.Client() as client:
                    success_count = 0
                    for index, row in df.iterrows():
                        payload = {
                            "name": row['name'],
                            "manufacturer": row['manufacturer'],
                            "carbon_footprint": float(row['carbon_footprint']),
                            "recycled_content": int(row['recycled_content'])
                        }
                        res = client.post(API_URL, json=payload, headers=headers)
                        if res.status_code == 201:
                            success_count += 1
                    
                    st.success(f"Klaar! {success_count} batterijen toegevoegd aan de database.")
