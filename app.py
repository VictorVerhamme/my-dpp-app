import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO

# --- 0. CONFIGURATIE & KLEUREN ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL = f"{SUPABASE_URL}/rest/v1/Batteries"

# Jouw kleurenpalet
COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_CARD = "#E3ECE6" # Lichtgroen

st.set_page_config(page_title="EU Battery Passport", page_icon="🔋", layout="wide")

# --- 1. CSS STYLING (De "Regels van de Kunst") ---
# Hier injecteren we eigen CSS om Streamlit mooier te maken
st.markdown(f"""
    <style>
    /* Algemene achtergrond iets zachter maken */
    .stApp {{
        background-color: #f9fbf9;
    }}
    
    /* Headers (H1, H2, H3) in de accentkleur */
    h1, h2, h3, .st-emotion-cache-10trblm {{
        color: {COLOR_ACCENT} !important;
        font-family: 'Helvetica Neue', sans-serif;
    }}

    /* Styling voor de 'Passport Card' (consumenten view) */
    .passport-card {{
        background-color: {COLOR_BG_CARD};
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-top: 5px solid {COLOR_ACCENT};
        margin-bottom: 20px;
    }}

    /* Styling voor metrics (de grote getallen) */
    [data-testid="stMetricLabel"] {{
        color: #555;
        font-size: 0.9rem;
    }}
    [data-testid="stMetricValue"] {{
        color: {COLOR_ACCENT};
        font-weight: 700;
    }}
    
    /* Knoppen een accent geven */
    .stButton button {{
        border: 2px solid {COLOR_ACCENT};
        color: {COLOR_ACCENT};
        font-weight: 600;
        border-radius: 8px;
    }}
    .stButton button:hover {{
        border: 2px solid {COLOR_ACCENT};
        background-color: {COLOR_ACCENT};
        color: white;
    }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_BG_CARD};
        border-right: 1px solid {COLOR_ACCENT};
    }}
    </style>
""", unsafe_allow_html=True)


headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Session state initialization
if 'qr_data' not in st.session_state: st.session_state.qr_data = None
if 'temp_name' not in st.session_state: st.session_state.temp_name = ""

# --- 2. LOGICA: PASPOORT OF ADMIN? ---
query_params = st.query_params

if "id" in query_params:
    # ============================================
    # --- DEEL 1: PASPOORT PAGINA (Consument) ---
    # ============================================
    battery_id = query_params["id"]
    with httpx.Client() as client:
        resp = client.get(f"{API_URL}?id=eq.{battery_id}", headers=headers)
        if resp.status_code == 200 and len(resp.json()) > 0:
            data = resp.json()[0]
            
            # We gebruiken kolommen om het te centreren op grote schermen
            col_spacer1, col_content, col_spacer2 = st.columns([1, 2, 1])
            
            with col_content:
                # Start van de "Card"
                st.markdown(f"""<div class="passport-card">""", unsafe_allow_html=True)
                
                st.caption("✅ Officieel Geverifieerd EU Product Paspoort")
                st.title(f"🔋 {data.get('name', 'Onbekend')}")
                st.subheader(f"Fabrikant: {data.get('manufacturer', 'Onbekend')}")
                
                st.divider()
                
                # Metrics in een rij
                m1, m2 = st.columns(2)
                m1.metric("🌍 CO2 Voetafdruk", f"{data.get('carbon_footprint', 0)} kg CO2e")
                m2.metric("♻️ Circulair Materiaal", f"{data.get('recycled_content', 0)}%")
                
                st.divider()
                
                # Extra info in een uitklapmenu voor een rustiger beeld
                with st.expander("📄 Bekijk Compliance Details & Richtlijnen"):
                    st.markdown("""
                    **EU Batterijverordening (2023/1542)**
                    Dit product voldoet aan de eisen voor duurzaamheid, veiligheid en etikettering zoals vastgesteld door de Europese Unie.
                    * *Status:* Actief geregistreerd
                    * *Dataleverancier:* Geverifieerde fabrikant
                    """)
                    st.button("Download Officieel Certificaat (PDF)")

                st.markdown("</div>", unsafe_allow_html=True) # Einde Card
                st.caption(f"Paspoort ID: {battery_id} • Powered by Secured Ledger Tech")

        else:
            st.error("❌ Paspoort niet gevonden in het register.")
else:
    # ============================================
    # --- DEEL 2: ADMIN PAGINA (Beveiligd) ---
    # ============================================
    st.sidebar.header("🔐 Beheerder Toegang")
    st.sidebar.markdown(f"Voer uw wachtwoord in om toegang te krijgen tot het **DPP Management System**.")
    admin_password = st.sidebar.text_input("Wachtwoord", type="password")
    
    if admin_password != "batterij2024": 
        # Publieke landingspagina als je niet bent ingelogd
        col1, col2 = st.columns(2)
        with col1:
             st.title("EU Digital Product Passport System")
             st.markdown(f"""
             <div style="background-color:{COLOR_BG_CARD}; padding:20px; border-radius:10px; border-left:4px solid {COLOR_ACCENT}">
             Welkom bij het centrale register voor batterijpaspoorten.<br><br>
             <strong>Voor consumenten:</strong> Scan de QR-code op uw product om het paspoort te bekijken.<br>
             <strong>Voor fabrikanten:</strong> Log in via de zijbalk om producten te beheren.
             </div>
             """, unsafe_allow_html=True)
        with col2:
            # Een placeholder plaatje voor de look & feel
            st.image("https://cdn-icons-png.flaticon.com/512/2875/2875878.png", width=300, caption="Scan & Verify")
        st.stop()

    # --- ADMIN INTERFACE (Na inloggen) ---
    st.title("🏗️ DPP Management Dashboard")
    st.markdown(f"Ingelogd als beheerder. Gebruik de tabbladen hieronder om de database te beheren.")
    
    tab1, tab2, tab3 = st.tabs(["✨ Nieuwe Batterij", "📂 Bulk Upload", "🗃️ Database Overzicht"])

    with tab1:
        st.subheader("Enkelvoudige Registratie")
        st.markdown("Voer de gegevens in om een nieuw paspoort en QR-code te genereren.")
        
        with st.container(border=True): # Een nette omlijsting om het formulier
            with st.form("single_entry", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    name = st.text_input("📦 Product Naam / Model")
                    mfr = st.text_input("🏭 Fabrikant")
                with col_b:
                    co2 = st.number_input("🌍 CO2 Voetafdruk (kg)", min_value=0.0, step=0.1)
                    recycled = st.slider("♻️ Gerecycled materiaal (%)", 0, 100, 30)
                
                st.markdown("<br>", unsafe_allow_html=True) # Wat witruimte
                submit = st.form_submit_button("✅ Registreer & Genereer QR")

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
                            st.toast(f"Succesvol geregistreerd! ID: {new_id}", icon="🎉") # Een moderne 'toast' melding
                        else:
                            st.error(f"Database fout: {res.text}")

        if st.session_state.qr_data:
            st.divider()
            cols = st.columns([1,3])
            with cols[0]:
                st.image(st.session_state.qr_data, width=180, caption="Gegenereerde QR")
            with cols[1]:
                st.subheader(f"QR-code voor: {st.session_state.temp_name}")
                st.write("Download deze afbeelding om op de productverpakking te printen.")
                st.download_button("📥 Download PNG", st.session_state.qr_data, f"QR_{st.session_state.temp_name}.png")

    with tab2:
        st.subheader("Bulk Import via CSV")
        st.markdown(f"""
        <div style="background-color:{COLOR_BG_CARD}; padding:15px; border-radius:8px; font-size:0.9em;">
        ℹ️ <strong>Instructie:</strong> Upload een CSV-bestand. De app herkent automatisch komma's of puntkomma's.
        Verplichte kolomnamen: <code>name</code>, <code>manufacturer</code>, <code>carbon_footprint</code>, <code>recycled_content</code>.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        file = st.file_uploader("Sleep je CSV bestand hierheen", type="csv")
        if file:
            df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.lower().strip() for c in df.columns]
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button("🚀 Start Import"):
                progress_bar = st.progress(0) # Een voortgangsbalkje
                success_count = 0
                with httpx.Client() as client:
                    total = len(df)
                    for i, (_, row) in enumerate(df.iterrows()):
                        try:
                            payload = {"name": str(row['name']), "manufacturer": str(row['manufacturer']), "carbon_footprint": float(row.get('carbon_footprint',0)), "recycled_content": int(row.get('recycled_content',0))}
                            client.post(API_URL, json=payload, headers=headers)
                            success_count += 1
                            progress_bar.progress((i + 1) / total) # Update balk
                        except Exception as e: st.warning(f"Rij {i} fout: {e}")
                st.success(f"Import afgerond! {success_count} van de {total} batterijen geïmporteerd.")

    with tab3:
        st.subheader("Live Database Overzicht")
        col1, col2 = st.columns([3,1])
        with col2:
            if st.button("🔄 Verversen"):
                st.rerun()
        
        with httpx.Client() as client:
            resp = client.get(API_URL, headers=headers)
            if resp.status_code == 200:
                df_db = pd.DataFrame(resp.json())
                # We laten alleen de relevante kolommen zien voor een netter overzicht
                st.dataframe(
                    df_db[['id', 'name', 'manufacturer', 'carbon_footprint', 'recycled_content', 'created_at']],
                    use_container_width=True,
                    hide_index=True
                )
