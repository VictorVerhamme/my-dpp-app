import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_BROKEN_WHITE = "#FDFBF7"

LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="Digital Product Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. PDF GENERATOR FUNCTIE ---
def generate_certificate(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(143, 175, 154) # Saliegroen
    pdf.cell(200, 20, txt="EU Digital Product Passport", ln=True, align='C')
    
    # Inhoud
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Product Naam: {data['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Fabrikant: {data['manufacturer']}", ln=True)
    pdf.cell(200, 10, txt=f"Product ID: {data['id']}", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"CO2 Voetafdruk: {data['carbon_footprint']} kg CO2e", ln=True)
    pdf.cell(200, 10, txt=f"Gerecycled Materiaal: {data['recycled_content']}%", ln=True)
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 10, txt="Dit certificaat bevestigt dat het product is geregistreerd in het centrale EU register en voldoet aan verordening 2023/1542.")
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. STYLING (CSS) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG_BROKEN_WHITE}; }}
    header, footer {{visibility: hidden;}}
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; text-align: center; }}
    .central-container {{ display: flex; flex-direction: column; align-items: center; max-width: 450px; margin: 0 auto; padding-top: 5vh; }}
    .centered-logo {{ display: block; height: 220px; margin: 0 auto 30px auto; }}
    div[data-baseweb="input"] {{ background-color: white !important; border: 1px solid #e0ddd7 !important; border-radius: 12px !important; }}
    .stButton button {{ background-color: {COLOR_ACCENT} !important; color: white !important; border-radius: 12px !important; height: 50px !important; width: 100% !important; }}
    .passport-card {{ background-color: white; padding: 50px; border-radius: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.02); text-align: center; max-width: 600px; margin: 40px auto; border: 1px solid #f2f0eb; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA HELPERS ---
def get_data(url):
    with httpx.Client() as client:
        r = client.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []

def delete_item(url, item_id):
    with httpx.Client() as client:
        client.delete(f"{url}?id=eq.{item_id}", headers=headers)
    st.toast("Item succesvol verwijderd", icon="🗑️")
    st.rerun()

# --- 5. LOGICA ---
if 'company' not in st.session_state: st.session_state.company = None

query_params = st.query_params

if "id" in query_params:
    # --- PASPOORT VIEW (PUBLIEK + SCAN TELLER) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{query_params['id']}")
    if res:
        d = res[0]
        # Update view count in database
        new_views = d.get('views', 0) + 1
        httpx.patch(f"{API_URL_BATTERIES}?id=eq.{d['id']}", json={"views": new_views}, headers=headers)
        
        st.markdown(f"""
            <div class="passport-card">
                <img src="{LOGO_URL}" style="height: 90px; margin-bottom: 25px;">
                <h1>{d['name']}</h1>
                <p>Geverifieerde fabrikant: <strong>{d['manufacturer']}</strong></p>
                <div style="display: flex; justify-content: space-around; margin-top: 40px; border-top: 1px solid #f5f5f5; padding-top: 30px;">
                    <div><p style="font-size:0.8em; color:#999;">CO2 IMPACT</p><h2>{d['carbon_footprint']} kg</h2></div>
                    <div><p style="font-size:0.8em; color:#999;">RECYCLED</p><h2>{d['recycled_content']}%</h2></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden.")

else:
    # --- LOGIN ---
    if not st.session_state.company:
        st.markdown(f'<div class="central-container">', unsafe_allow_html=True)
        st.markdown(f'<img src="{LOGO_URL}" class="centered-logo">', unsafe_allow_html=True)
        username = st.text_input("User", placeholder="Gebruikersnaam", label_visibility="collapsed")
        password = st.text_input("Pass", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
        if st.button("Inloggen"):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{username}")
            if res and res[0]['password'] == password:
                st.session_state.company = res[0]['name']
                st.rerun()
            else: st.error("Login mislukt.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=150)
        if st.sidebar.button("🚪 Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            t1, t2 = st.tabs(["📊 Global Data", "🏢 Bedrijven"])
            with t1:
                data = get_data(API_URL_BATTERIES)
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df[['id', 'name', 'manufacturer', 'views']], use_container_width=True)
                    del_id = st.text_input("ID om te verwijderen")
                    if st.button("Verwijder Batterij"): delete_item(API_URL_BATTERIES, del_id)
        else:
            st.title(f"Portaal {user}")
            t1, t2 = st.tabs(["✨ Registratie", "📊 Mijn Voorraad"])
            with t1:
                with st.form("add"):
                    n = st.text_input("Model")
                    c = st.number_input("CO2", min_value=0.0)
                    r = st.slider("Recycled %", 0, 100)
                    if st.form_submit_button("Opslaan"):
                        httpx.post(API_URL_BATTERIES, json={"name":n, "manufacturer":user, "carbon_footprint":c, "recycled_content":r}, headers=headers)
                        st.success("Geregistreerd!")
            with t2:
                items = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if items:
                    for i in items:
                        with st.expander(f"📦 {i['name']} (Gescand: {i.get('views', 0)}x)"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                pdf_data = generate_certificate(i)
                                st.download_button(f"📄 Certificaat PDF", pdf_data, f"Certificaat_{i['name']}.pdf")
                            with col_b:
                                if st.button(f"🗑️ Verwijder {i['name']}", key=i['id']):
                                    delete_item(API_URL_BATTERIES, i['id'])
