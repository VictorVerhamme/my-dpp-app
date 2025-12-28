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
    st.write("Gebruik dit formulier om een nieuwe batterij te registreren.")

    # We maken een variabele om de QR-data tijdelijk in op te slaan
    qr_data = None
    new_battery_name = ""

    with st.form("add_battery_form", clear_on_submit=True):
        name = st.text_input("Product Naam / Modelnummer", placeholder="bv. Tesla Model 3")
        mfr = st.text_input("Fabrikant", placeholder="bv. Panasonic")
        
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
                        new_battery_name = name
                        
                        # De URL voor het paspoort
                        # PAS DIT AAN NAAR JE EIGEN URL:
                        base_url = "https://jouw-app-naam.streamlit.app" 
                        passport_url = f"{base_url}/?id={new_id}"
                        
                        # QR Code genereren en opslaan in een variabele
                        qr = qrcode.make(passport_url)
                        buf = BytesIO()
                        qr.save(buf, format="PNG")
                        qr_data = buf.getvalue()
                        
                        st.balloons()
                        st.success(f"Batterij succesvol geregistreerd! ID: {new_id}")
                    else:
                        st.error(f"Database fout: {response.text}")
            else:
                st.warning("Vul a.u.b. alle velden in.")

    # --- QR CODE WEERGAVE (BUITEN HET FORMULIER) ---
    if qr_data:
        st.divider()
        st.subheader(f"Download QR voor {new_battery_name}")
        st.image(qr_data, caption="Scan deze code voor het paspoort")
        st.download_button(
            label="Download QR-code voor verpakking",
            data=qr_data,
            file_name=f"QR_{new_battery_name}.png",
            mime="image/png"
        )
