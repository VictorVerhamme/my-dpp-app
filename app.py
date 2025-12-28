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

# Kleuren uit je huisstijl
COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_CARD = "#E3ECE6" # Lichtgroen

# !!! BELANGRIJK: VERVANG DEZE LINK DOOR DE LINK VAN JE NIEUWE LOGO !!!
LOGO_URL = "https://i.postimg.cc/sXHV1JHy/Chat-GPT-Image-28-dec-2025-14-50-31.png"

st.set_page_config(page_title="EU Battery Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. MODERNE STYLING (CSS) ---
st.markdown(f"""
    <style>
    /* Een zachte, professionele achtergrond voor de hele app */
    .stApp {{
        background-color: #F5F7F6; 
    }}
    
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}

    /* --- STYLING VOOR HET NIEUWE INLOGSCHERM --- */
    /* Dit centreert de login kaart op het scherm */
    .login-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        padding-top: 50px;
    }}
    
    /* De moderne witte kaart */
    .login-card {{
        background-color: #FFFFFF;
        padding: 40px 50px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); /* Zachte schaduw voor diepte */
        text-align: center;
        max-width: 550px;
        width: 100%;
        border-top: 6px solid {COLOR_ACCENT}; /* Subtiel kleuraccent bovenaan */
    }}
    
    /* Zorgt dat je nieuwe logo mooi uitkomt */
    .login-logo-img {{
        max-width: 90%; /* Past zich aan de breedte aan */
        height: auto;
        margin-bottom: 30px; /* Ruimte tussen logo en formulier */
    }}

    /* Styling voor het paspoort (voor de consument) */
    .passport-card {{
        background-color: #FFFFFF;
        border-radius: 15px;
        padding: 40px;
        border-left: 8px solid {COLOR_ACCENT};
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
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
                <img src="{LOGO_URL}" style="height: 50px; margin-bottom: 20px;">
                <p style="color:{COLOR_ACCENT}; font-weight:bold; margin-bottom:0; text-transform: uppercase; letter-spacing: 1px;">Officieel EU Paspoort</p>
                <h1 style="margin-top: 5px;">🔋 {d['name']}</h1>
                <p style="font-size: 1.1em;">Geproduceerd door: <strong>{d['manufacturer']}</strong></p>
                <hr style="opacity:0.2; margin: 30px 0;">
                <div style="display: flex; gap: 50px;">
                    <div><p style="font-size:0.9em; margin:0; color:#888;">CO2 IMPACT</p><h2 style="margin-top:5px;">{d['carbon_footprint']} kg</h2></div>
                    <div><p style="font-size:0.9em; margin:0; color:#888;">GERECYCLED</p><h2 style="margin-top:5px;">{d['recycled_content']}%</h2></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden.")

else:
    # --- LOGIN & DASHBOARD ---
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        # --- HET NIEUWE INLOGSCHERM ---
        companies = get_data(API_URL_COMPANIES)
        
        # We gebruiken kolommen om de kaart te centreren
        c1, c2, c3 = st.columns([1, 3, 1])
        with c2:
            # Start van de moderne kaart
            st.markdown('<div class="login-container"><div class="login-card">', unsafe_allow_html=True)
            
            # JOUW NIEUWE LOGO
            st.markdown(f'<img src="{LOGO_URL}" class="login-logo-img">', unsafe_allow_html=True)
            
            st.markdown("### Bedrijfsportaal")
            st.write("Log in om uw producten te beheren.")
            
            co_names = [c['name'] for c in companies]
            selected_co = st.selectbox("Selecteer Organisatie", options=co_names)
            pwd_input = st.text_input("Wachtwoord", type="password")
            
            st.markdown('<br>', unsafe_allow_html=True) # Beetje witruimte
            
            if st.button("Veilig Inloggen", use_container_width=True):
                match = next((c for c in companies if c['name'] == selected_co), None)
                if match and match['password'] == pwd_input:
                    st.session_state.company = selected_co
                    st.rerun()
                else: st.error("Toegang geweigerd: Controleer uw wachtwoord.")
            
            st.markdown('</div></div>', unsafe_allow_html=True)
            # Einde van de kaart

    else:
        # --- HET DASHBOARD (ALS JE BENT INGELOGD) ---
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=150) # Logo ook in de zijbalk
        st.sidebar.divider()
        st.sidebar.write(f"Ingelogd als:")
        st.sidebar.title(f"{user}")
        if st.sidebar.button("🚪 Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            # --- SUPERADMIN INTERFACE ---
            t1, t2 = st.tabs(["📊 Global Data", "🏢 Beheer Bedrijven"])
            with t1:
                st.subheader("Systeem Totaaloverzicht")
                all_bats = get_data(API_URL_BATTERIES)
                if all_bats:
                    df = pd.DataFrame(all_bats)
                    st.dataframe(df[['id', 'name', 'manufacturer', 'carbon_footprint']], use_container_width=True)
            with t2:
                st.subheader("Toegangsbeheer")
                cos = get_data(API_URL_COMPANIES)
                st.table(pd.DataFrame(cos)[['name', 'password']])
                st.divider()
                st.subheader("➕ Nieuwe Organisatie")
                with st.form("new_co"):
                    n = st.text_input("Naam")
                    p = st.text_input("Wachtwoord")
                    if st.form_submit_button("Toevoegen"):
                        with httpx.Client() as client:
                            client.post(API_URL_COMPANIES, json={"name":n, "password":p}, headers=headers)
                        st.rerun()
        else:
            # --- GEWOON BEDRIJF DASHBOARD ---
            st.title(f"Welkom, {user}")
            t1, t2, t3 = st.tabs(["✨ Nieuwe Batterij", "📊 Mijn Voorraad", "📂 Bulk Upload"])

            with t1:
                with st.container(border=True):
                    with st.form("add_bat", clear_on_submit=True):
                        name = st.text_input("Modelnaam")
                        co2 = st.number_input("CO2 (kg)", min_value=0.0)
                        recycled = st.slider("Gerecycled %", 0, 100, 25)
                        if st.form_submit_button("Registreer Product"):
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
                                    st.balloons()
                                    st.success(f"Product geregistreerd! ID: {new_id}")

                if st.session_state.qr_data:
                    st.divider()
                    c1, c2 = st.columns([1,3])
                    with c1: st.image(st.session_state.qr_data, width=150)
                    with c2:
                         st.subheader(f"QR voor {st.session_state.temp_name}")
                         st.download_button("Download PNG", st.session_state.qr_data, f"QR_{st.session_state.temp_name}.png")

            with t2:
                st.subheader(f"Voorraad van {user}")
                my_bats = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if my_bats:
                    st.dataframe(pd.DataFrame(my_bats)[['id', 'name', 'carbon_footprint', 'recycled_content']], use_container_width=True)
                else: st.info("Nog geen producten geregistreerd.")

            with t3:
                 with st.container(border=True):
                    st.subheader("Bulk Import")
                    file = st.file_uploader("Upload CSV bestand", type="csv")
                    if file:
                        df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
                        df.columns = [c.lower().strip() for c in df.columns]
                        if st.button("Start Import 🚀"):
                            with httpx.Client() as client:
                                for _, row in df.iterrows():
                                    payload = {"name": str(row['name']), "manufacturer": user, "carbon_footprint": float(row.get('carbon_footprint', 0)), "recycled_content": int(row.get('recycled_content', 0))}
                                    client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            st.success("Import succesvol afgerond!")
