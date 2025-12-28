import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_CARD = "#E3ECE6" # Lichtgroen

# --- LOGO URL (Placeholder - Wit icoon) ---
# ### HIER JOUW LOGO ###
# Vervang deze link later door een link naar je eigen witte logo (PNG of SVG)
LOGO_URL = "https://i.postimg.cc/sXHV1JHy/Chat-GPT-Image-28-dec-2025-14-50-31.png"

st.set_page_config(page_title="EU Battery Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #fdfdfd; }}
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}
    .login-box {{ 
        background-color: {COLOR_BG_CARD}; 
        padding: 40px; 
        border-radius: 20px; 
        border: 1px solid {COLOR_ACCENT};
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }}
    /* De groene balk is nu een flex-container om het logo te centreren */
    .green-header {{
        background-color: {COLOR_ACCENT};
        height: 50px; /* Iets hoger gemaakt voor het logo */
        border-radius: 10px 10px 0 0;
        margin: -40px -40px 30px -40px;
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    /* Styling voor het logo in de header */
    .header-logo {{
        height: 60px;
        width: auto;
    }}
    .passport-card {{
        background-color: {COLOR_BG_CARD};
        border-radius: 12px;
        padding: 30px;
        border-left: 8px solid {COLOR_ACCENT};
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPERS ---
def get_data(url):
    with httpx.Client() as client:
        r = client.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []

# --- 4. LOGICA ---
if 'qr_data' not in st.session_state: st.session_state.qr_data = None
if 'temp_name' not in st.session_state: st.session_state.temp_name = ""

query_params = st.query_params

if "id" in query_params:
    # --- PASPOORT VIEW (PUBLIEK) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{query_params['id']}")
    if res:
        d = res[0]
        st.markdown(f"""
            <div class="passport-card">
                <p style="color:{COLOR_ACCENT}; font-weight:bold; margin-bottom:0;">OFFICIEEL EU PASPOORT</p>
                <h1>🔋 {d['name']}</h1>
                <p>Geregistreerde Fabrikant: <strong>{d['manufacturer']}</strong></p>
                <hr style="opacity:0.2;">
                <div style="display: flex; gap: 40px;">
                    <div><p style="font-size:0.8em; margin:0;">CO2 IMPACT</p><h3>{d['carbon_footprint']} kg</h3></div>
                    <div><p style="font-size:0.8em; margin:0;">GERECYCLED</p><h3>{d['recycled_content']}%</h3></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden.")

else:
    # --- LOGIN & DASHBOARD ---
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        companies = get_data(API_URL_COMPANIES)
        _, col, _ = st.columns([1, 2, 1])
        with col:
            # Hier voegen we de afbeelding toe in de groene header
            st.markdown(f'<div class="login-box"><div class="green-header"><img src="{LOGO_URL}" class="header-logo"></div>', unsafe_allow_html=True)
            st.subheader("Bedrijfs Portaal")
            co_names = [c['name'] for c in companies]
            selected_co = st.selectbox("Selecteer uw bedrijf", options=co_names)
            pwd_input = st.text_input("Wachtwoord", type="password")
            if st.button("Inloggen"):
                match = next((c for c in companies if c['name'] == selected_co), None)
                if match and match['password'] == pwd_input:
                    st.session_state.company = selected_co
                    st.rerun()
                else: st.error("Onjuist wachtwoord")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        user = st.session_state.company
        st.sidebar.title(f"👤 {user}")
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            # --- SUPERADMIN INTERFACE ---
            t1, t2 = st.tabs(["📊 Global Data", "🏢 Beheer Bedrijven"])
            with t1:
                st.subheader("Alle batterijen in het systeem")
                all_bats = get_data(API_URL_BATTERIES)
                if all_bats:
                    df = pd.DataFrame(all_bats)
                    st.dataframe(df[['id', 'name', 'manufacturer', 'carbon_footprint']], use_container_width=True)
            with t2:
                st.subheader("Bedrijven & Wachtwoorden")
                cos = get_data(API_URL_COMPANIES)
                st.table(pd.DataFrame(cos)[['name', 'password']])
                
                st.divider()
                st.subheader("➕ Nieuw Bedrijf Toevoegen")
                with st.form("new_co"):
                    n = st.text_input("Naam")
                    p = st.text_input("Wachtwoord")
                    if st.form_submit_button("Opslaan"):
                        with httpx.Client() as client:
                            client.post(API_URL_COMPANIES, json={"name":n, "password":p}, headers=headers)
                        st.rerun()
        else:
            # --- GEWOON BEDRIJF DASHBOARD (Panasonic, Tesla, etc.) ---
            st.title(f"Dashboard: {user}")
            t1, t2, t3 = st.tabs(["✨ Nieuwe Batterij", "📊 Mijn Voorraad", "📂 Bulk Upload"])

            with t1:
                with st.form("add_bat", clear_on_submit=True):
                    name = st.text_input("Modelnaam")
                    co2 = st.number_input("CO2 (kg)", min_value=0.0)
                    recycled = st.slider("Gerecycled %", 0, 100, 25)
                    if st.form_submit_button("Registreer"):
                        payload = {"name": name, "manufacturer": user, "carbon_footprint": co2, "recycled_content": recycled}
                        with httpx.Client() as client:
                            res = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            if res.status_code == 201:
                                new_id = res.json()[0]['id']
                                passport_url = f"https://digitalpassport.streamlit.app/?id={new_id}"
                                qr = qrcode.make(passport_url)
                                buf = BytesIO()
                                qr.save(buf, format="PNG")
                                st.session_state.qr_data = buf.getvalue()
                                st.session_state.temp_name = name
                                st.success(f"Batterij toegevoegd! ID: {new_id}")

                if st.session_state.qr_data:
                    st.image(st.session_state.qr_data, width=200)
                    st.download_button("Download QR", st.session_state.qr_data, f"QR_{st.session_state.temp_name}.png")

            with t2:
                st.subheader(f"Geregistreerd door {user}")
                my_bats = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if my_bats:
                    st.dataframe(pd.DataFrame(my_bats)[['id', 'name', 'carbon_footprint', 'recycled_content']], use_container_width=True)
                else: st.info("Nog geen batterijen geregistreerd.")

            with t3:
                st.subheader("Bulk Import")
                file = st.file_uploader("Upload CSV", type="csv")
                if file:
                    df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
                    df.columns = [c.lower().strip() for c in df.columns]
                    if st.button("Start Import"):
                        with httpx.Client() as client:
                            for _, row in df.iterrows():
                                payload = {"name": str(row['name']), "manufacturer": user, "carbon_footprint": float(row.get('carbon_footprint', 0)), "recycled_content": int(row.get('recycled_content', 0))}
                                client.post(API_URL_BATTERIES, json=payload, headers=headers)
                        st.success("Import klaar!")



