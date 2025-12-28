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

# Kleuren
COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_BROKEN_WHITE = "#FDFBF7" # Achtergrond van je logo

# JOUW LOGO LINK
LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

# Layout op "wide" voor maximale controle over de kolommen
st.set_page_config(page_title="Digital Product Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. PIXEL-PERFECT STYLING (CSS) ---
st.markdown(f"""
    <style>
    /* Achtergrond overal gelijk maken aan logo */
    .stApp {{
        background-color: {COLOR_BG_BROKEN_WHITE};
    }}

    /* Verberg Streamlit menu/balken voor een professionele look */
    header, footer {{visibility: hidden;}}
    
    /* Titels in Saliegroen */
    h1, h2, h3 {{ 
        color: {COLOR_ACCENT} !important; 
        text-align: center;
        font-family: 'Inter', sans-serif;
    }}

    /* Logo perfect centreren en grootte (250px) */
    .centered-logo {{
        display: block;
        margin: 0 auto 30px auto;
        height: 250px; 
        width: auto;
    }}

    /* Schone invoervelden zonder extra Streamlit balken */
    div[data-baseweb="input"] {{
        background-color: white !important;
        border: 1px solid #e0ddd7 !important;
        border-radius: 12px !important;
        padding: 5px !important;
        margin-bottom: 10px;
    }}
    
    .stTextInput input {{
        background-color: white !important;
        border: none !important;
        font-size: 16px !important;
        text-align: center; /* Tekst in de balk centreren */
    }}

    /* De inlogknop - Gecentreerd en compact */
    /* 1. Target de container van de knop om te centreren */
    .stButton {
        display: flex;
        justify-content: center;
    }

    /* 2. De knop zelf */
    .stButton button {
        background-color: #8FAF9A !important;
        color: white !important;
        border: none !important;
        height: 50px !important;
        width: 100% !important; /* Of verander dit naar bijv. 200px als je een kleine knop wilt */
        max-width: 400px;       /* Zorgt dat hij nooit breder wordt dan je velden */
        font-weight: 600 !important;
        border-radius: 12px !important;
        margin-top: 10px !important;
    }
    
    .stButton button:hover {{
        opacity: 0.9;
        color: white !important;
    }}

    /* Paspoort kaart (Consumenten view) */
    .passport-card {{
        background-color: white;
        padding: 50px;
        border-radius: 25px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.02);
        text-align: center;
        max-width: 600px;
        margin: 40px auto;
        border: 1px solid #f2f0eb;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPERS ---
def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except:
        return []

# --- 4. LOGICA ---
if 'company' not in st.session_state: st.session_state.company = None
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
                <img src="{LOGO_URL}" style="height: 100px; margin-bottom: 25px;">
                <h3 style="margin:0; opacity:0.4; font-size: 0.8em; letter-spacing: 2px;">DIGITAL PRODUCT PASSPORT</h3>
                <h1 style="margin-top: 10px;">{d['name']}</h1>
                <p style="color: #666;">Geverifieerde fabrikant: <strong>{d['manufacturer']}</strong></p>
                <div style="display: flex; justify-content: space-around; margin-top: 40px; border-top: 1px solid #f5f5f5; padding-top: 30px;">
                    <div><p style="font-size:0.8em; margin:0; color:#999; letter-spacing:1px;">CO2 IMPACT</p><h2>{d['carbon_footprint']} kg</h2></div>
                    <div><p style="font-size:0.8em; margin:0; color:#999; letter-spacing:1px;">RECYCLED</p><h2>{d['recycled_content']}%</h2></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden.")

else:
    # --- INLOG SCHERM (CENTRALE KOLOM) ---
    if not st.session_state.company:
        # We maken 3 kolommen: links leeg (1.2), midden (1), rechts leeg (1.2)
        # Hierdoor blijven de balken in het midden en zijn ze niet te lang.
        col1, col2, col3 = st.columns([1.2, 1, 1.2])
        
        with col2:
            # Logo
            st.markdown(f'<img src="{LOGO_URL}" class="centered-logo">', unsafe_allow_html=True)
            
            # Inlogvelden zonder dropdown (Username + Password)
            username = st.text_input("Username", placeholder="Gebruikersnaam", label_visibility="collapsed")
            password = st.text_input("Password", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
            
            if st.button("Inloggen op Portaal"):
                with httpx.Client() as client:
                    # Zoek naar de gebruiker in de Companies tabel
                    resp = client.get(f"{API_URL_COMPANIES}?name=eq.{username}", headers=headers)
                    if resp.status_code == 200 and len(resp.json()) > 0:
                        match = resp.json()[0]
                        if match['password'] == password:
                            st.session_state.company = match['name']
                            st.rerun()
                        else:
                            st.error("Wachtwoord onjuist.")
                    else:
                        st.error("Gebruikersnaam niet herkend.")

    else:
        # --- DASHBOARD (Bedrijven / SuperAdmin) ---
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=150)
        st.sidebar.divider()
        st.sidebar.write(f"Sessie: **{user}**")
        if st.sidebar.button("🚪 Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            t1, t2 = st.tabs(["📊 Global Overzicht", "🏢 Beheer Bedrijven"])
            with t1:
                st.subheader("Alle geregistreerde producten")
                all_bats = get_data(API_URL_BATTERIES)
                if all_bats: 
                    st.dataframe(pd.DataFrame(all_bats)[['id', 'name', 'manufacturer', 'carbon_footprint', 'recycled_content']], use_container_width=True, hide_index=True)
            with t2:
                st.subheader("Bedrijfsaccounts & Wachtwoorden")
                cos = get_data(API_URL_COMPANIES)
                if cos: st.table(pd.DataFrame(cos)[['name', 'password']])
                
                st.divider()
                st.subheader("➕ Nieuwe Organisatie Toevoegen")
                with st.form("new_co"):
                    n = st.text_input("Naam Bedrijf")
                    p = st.text_input("Wachtwoord")
                    if st.form_submit_button("Account aanmaken"):
                        with httpx.Client() as client:
                            client.post(API_URL_COMPANIES, json={"name":n, "password":p}, headers=headers)
                        st.success(f"{n} is toegevoegd!")
                        st.rerun()
        else:
            # Bedrijfs Dashboard (Panasonic, Tesla, etc.)
            st.title(f"Portaal: {user}")
            t1, t2, t3 = st.tabs(["✨ Registratie", "📊 Mijn Voorraad", "📂 Bulk Import"])
            
            with t1:
                with st.form("add_product", clear_on_submit=True):
                    st.write("Registreer een nieuwe batterij")
                    name = st.text_input("Modelnaam / Type")
                    co2 = st.number_input("CO2 Impact (kg)", min_value=0.0)
                    rec = st.slider("Percentage gerecycled materiaal", 0, 100, 25)
                    if st.form_submit_button("Product Opslaan"):
                        payload = {"name":name, "manufacturer":user, "carbon_footprint":co2, "recycled_content":rec}
                        with httpx.Client() as client:
                            res = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            if res.status_code == 201:
                                new_id = res.json()[0]['id']
                                # QR genereren
                                passport_url = f"https://digitalpassport.streamlit.app/?id={new_id}"
                                qr = qrcode.make(passport_url)
                                buf = BytesIO()
                                qr.save(buf, format="PNG")
                                st.session_state.qr_data = buf.getvalue()
                                st.session_state.temp_name = name
                                st.success("Product succesvol geregistreerd!")

                if st.session_state.qr_data:
                    st.divider()
                    c_qr1, c_qr2 = st.columns([1,3])
                    with c_qr1: st.image(st.session_state.qr_data, width=150)
                    with c_qr2:
                        st.write(f"**QR-code voor {st.session_state.temp_name}**")
                        st.download_button("Download PNG", st.session_state.qr_data, f"QR_{st.session_state.temp_name}.png")

            with t2:
                st.subheader(f"Voorraad van {user}")
                my_bats = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if my_bats: 
                    st.dataframe(pd.DataFrame(my_bats)[['id','name','carbon_footprint','recycled_content']], use_container_width=True, hide_index=True)
                else: st.info("U heeft nog geen producten geregistreerd.")

            with t3:
                st.subheader("Bulk Import (CSV)")
                file = st.file_uploader("Upload CSV-bestand", type="csv")
                if file:
                    df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
                    df.columns = [c.lower().strip() for c in df.columns]
                    if st.button("Start Bulk Import 🚀"):
                        with httpx.Client() as client:
                            for _, row in df.iterrows():
                                payload = {"name": str(row['name']), "manufacturer": user, "carbon_footprint": float(row.get('carbon_footprint', 0)), "recycled_content": int(row.get('recycled_content', 0))}
                                client.post(API_URL_BATTERIES, json=payload, headers=headers)
                        st.success("Batch-import voltooid!")


