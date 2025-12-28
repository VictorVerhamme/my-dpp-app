import streamlit as st
import qrcode
import httpx
from io import BytesIO

# --- 1. CONFIGURATIE ---
# Jouw unieke Supabase gegevens
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL = f"{SUPABASE_URL}/rest/v1/Batteries"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

st.set_page_config(page_title="EU Digital Battery Passport", page_icon="🔋", layout="centered")

# --- 2. LOGICA: WELKE PAGINA LATEN WE ZIEN? ---
# We kijken of er een 'id' in de URL staat (bijv. myapp.com/?id=10)
query_params = st.query_params

if "id" in query_params:
    # --- PASPOORT PAGINA (Wat de consument ziet) ---
    battery_id = query_params["id"]
    
    with httpx.Client() as client:
        # Haal de specifieke batterij op uit je Supabase tabel
        resp = client.get(f"{API_URL}?id=eq.{battery_id}", headers=headers)
        
        if resp.status_code == 200 and len(resp.json()) > 0:
            data = resp.json()[0]
            
            st.success("✅ Officieel EU Product Paspoort")
            st.title(f"🔋 {data['name']}")
            st.write(f"**Fabrikant:** {data['manufacturer']}")
            
            st.divider()
            
            # Mooie weergave van de technische data
            col1, col2 = st.columns(2)
            with col1:
                st.metric("CO2 Voetafdruk", f"{data['carbon_footprint']} kg CO2e")
            with col2:
                st.metric("Gerecycled Materiaal", f"{data['recycled_content']}%")
            
            st.divider()
            st.info("ℹ️ Dit product voldoet aan de Europese Batterijverordening (EU) 2023/1542. Scan de fysieke QR-code op het product voor de meest recente status.")
        else:
            st.error("❌ Paspoort niet gevonden. Controleer de QR-code.")
            if st.button("Terug naar home"):
                st.query_params.clear()

else:
    # --- ADMIN PAGINA (Jouw dashboard om data in te voeren) ---
    st.title("🏗️ DPP Generator")
    st.write("Gebruik dit formulier om een nieuwe batterij te registreren in de blockchain-database.")

    with st.form("add_battery_form", clear_on_submit=True):
        name = st.text_input("Product Naam / Modelnummer", placeholder="bv. Tesla Model 3 Long Range")
        mfr = st.text_input("Fabrikant", placeholder="bv. Panasonic Energy")
        
        c1, c2 = st.columns(2)
        with c1:
            co2 = st.number_input("CO2 Voetafdruk (kg)", min_value=0.0, step=0.1)
        with c2:
            recycled = st.slider("Gerecycled materiaal (%)", 0, 100, 25)
            
        submitted = st.form_submit_button("Genereer Digitaal Paspoort")

        if submitted:
            if name and mfr:
                payload = {
                    "name": name,
                    "manufacturer": mfr,
                    "carbon_footprint": co2,
                    "recycled_content": recycled
                }

                with httpx.Client() as client:
                    response = client.post(API_URL, json=payload, headers=headers)
                    
                    if response.status_code == 201:
                        new_data = response.json()[0]
                        new_id = new_data['id']
                        
                        st.balloons()
                        st.success(f"Batterij succesvol geregistreerd! ID: {new_id}")

                        # URL genereren (voor nu localhost, later je echte website)
                        # Als je hem straks online zet, vervang je 'localhost:8501' door je eigen URL
                        passport_url = f"http://localhost:8501/?id={new_id}"
                        
                        # QR Code genereren
                        qr = qrcode.make(passport_url)
                        buf = BytesIO()
                        qr.save(buf, format="PNG")
                        
                        st.image(buf, caption=f"Scan deze code voor het paspoort van {name}")
                        st.download_button("Download QR-code voor verpakking", buf.getvalue(), f"QR_{name}.png", "image/png")
                    else:
                        st.error(f"Database fout: {response.text}")
            else:
                st.warning("Vul a.u.b. alle velden in.")
