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
    battery_id = query_params["id"]
    
    with httpx.Client() as client:
        resp = client.get(f"{API_URL}?id=eq.{battery_id}", headers=headers)
        
        if resp.status_code == 200 and len(resp.json()) > 0:
            data = resp.json()[0]
            
            # --- STYLING ---
            st.markdown(f"### 🔋 Product Paspoort: {data['name']}")
            st.caption(f"Geregistreerd door {data['manufacturer']} • ID: {battery_id}")
            
            st.divider()
            
            # Hoofd-stats in kaartjes
            col1, col2 = st.columns(2)
            with col1:
                st.write("🌍 **Ecologische Voetafdruk**")
                st.metric(label="CO2 Impact", value=f"{data['carbon_footprint']} kg")
            with col2:
                st.write("♻️ **Circulair Materiaal**")
                st.metric(label="Gerecycled", value=f"{data['recycled_content']}%")
            
            st.divider()
            
            # Extra details in een uitklapmenu
            with st.expander("📄 Compliance & EU Richtlijnen"):
                st.write("""
                Dit product voldoet aan de Europese Batterijverordening (EU) 2023/1542.
                - **Categorie:** Industriële Batterij
                - **Status:** Actief op de markt
                - **Documentatie:** [Download CE-certificaat](#)
                """)
            
            # Contact knop
            st.button(f"📧 Contacteer {data['manufacturer']} voor service")
            
            st.success("✅ Dit is een geverifieerd digitaal paspoort.")
        else:
            st.error("Oeps! Dit paspoort lijkt niet (meer) te bestaan.")
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

