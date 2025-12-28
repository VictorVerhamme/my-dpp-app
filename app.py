import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import tempfile

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"
COLOR_BG_BROKEN_WHITE = "#FDFBF7"
LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="Digital Product Passport", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. FUNCTIES: QR & PDF ---
def make_qr(id):
    url = f"https://digitalpassport.streamlit.app/?id={id}"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def generate_certificate(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Logo (Optioneel, als je een lokaal bestand hebt)
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(143, 175, 154)
    pdf.cell(200, 20, txt="EU Digital Product Passport", ln=True, align='C')
    
    # Product Data
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, txt=f"Product Details:", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt=f"Naam: {data['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Fabrikant: {data['manufacturer']}", ln=True)
    pdf.cell(200, 10, txt=f"CO2 Impact: {data['carbon_footprint']} kg", ln=True)
    pdf.cell(200, 10, txt=f"Recycled: {data['recycled_content']}%", ln=True)
    
    # QR Code toevoegen aan PDF
    qr_img_bytes = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(qr_img_bytes)
        tmp_path = tmp.name
    
    pdf.ln(10)
    pdf.image(tmp_path, x=75, y=pdf.get_y(), w=60) # Centreer de QR code
    
    pdf.set_y(pdf.get_y() + 65)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(200, 10, txt="Scan de code om het digitale register te raadplegen.", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. HELPERS ---
def get_data(url):
    with httpx.Client() as client:
        r = client.get(url, headers=headers)
        return r.json() if r.status_code == 200 else []

def delete_item(item_id):
    with httpx.Client() as client:
        client.delete(f"{API_URL_BATTERIES}?id=eq.{item_id}", headers=headers)
    st.rerun()

# --- 4. STYLING ---
st.markdown(f"<style>.stApp {{ background-color: {COLOR_BG_BROKEN_WHITE}; }} header, footer {{visibility: hidden;}} h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}</style>", unsafe_allow_html=True)

# --- 5. LOGICA ---
query_params = st.query_params

if "id" in query_params:
    # --- PUBLIEKE PASPOORT PAGINA ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{query_params['id']}")
    if res:
        d = res[0]
        # Update views
        httpx.patch(f"{API_URL_BATTERIES}?id=eq.{d['id']}", json={"views": (d.get('views') or 0) + 1}, headers=headers)
        st.markdown(f"<div style='background:white; padding:50px; border-radius:20px; text-align:center; border-top:8px solid {COLOR_ACCENT}'><h1>{d['name']}</h1><p>Fabrikant: {d['manufacturer']}</p><h2>{d['carbon_footprint']} kg CO2</h2></div>", unsafe_allow_html=True)
else:
    if 'company' not in st.session_state: st.session_state.company = None
    if 'last_qr' not in st.session_state: st.session_state.last_qr = None

    if not st.session_state.company:
        # --- LOGIN ---
        _, col, _ = st.columns([1.2, 1, 1.2])
        with col:
            st.image(LOGO_URL)
            u = st.text_input("Username", placeholder="Naam")
            p = st.text_input("Password", type="password")
            if st.button("Inloggen"):
                res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
                if res and res[0]['password'] == p:
                    st.session_state.company = res[0]['name']
                    st.rerun()
    else:
        # --- DASHBOARD ---
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=150)
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        if user == "SuperAdmin":
            t1, t2 = st.tabs(["📊 Systeem Data", "🏢 Bedrijven"])
            with t1:
                df = pd.DataFrame(get_data(API_URL_BATTERIES))
                if not df.empty: st.dataframe(df[['id', 'name', 'manufacturer', 'views']], use_container_width=True)
            with t2:
                st.table(pd.DataFrame(get_data(API_URL_COMPANIES))[['name', 'password']])
        else:
            st.title(f"Portaal: {user}")
            t1, t2 = st.tabs(["✨ Registratie", "📊 Voorraadbeheer"])
            
            with t1:
                with st.form("add"):
                    n = st.text_input("Model")
                    c = st.number_input("CO2 Impact", min_value=0.0)
                    r = st.slider("Recycled %", 0, 100)
                    if st.form_submit_button("Opslaan & Genereer QR"):
                        resp = httpx.post(API_URL_BATTERIES, json={"name":n, "manufacturer":user, "carbon_footprint":c, "recycled_content":r}, headers=headers)
                        if resp.status_code == 201:
                            new_id = resp.json()[0]['id']
                            st.session_state.last_qr = make_qr(new_id)
                            st.success("Geregistreerd!")
                
                if st.session_state.last_qr:
                    st.image(st.session_state.last_qr, width=200, caption="QR Code voor uw product")
                    st.download_button("Download QR-Code", st.session_state.last_qr, "product_qr.png")
            
            with t2:
                data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df[['id', 'name', 'carbon_footprint', 'views']], use_container_width=True, hide_index=True)
                    st.divider()
                    sel = st.selectbox("Selecteer product voor acties", df['name'].tolist())
                    item = df[df['name'] == sel].iloc[0]
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        # Laat QR zien
                        st.image(make_qr(item['id']), width=150)
                    with c2:
                        # PDF Download
                        pdf_data = generate_certificate(item)
                        st.download_button(f"📄 Download PDF + QR", pdf_data, f"DPP_{sel}.pdf")
                    with c3:
                        # Verwijderen
                        if st.button(f"🗑️ Verwijder {sel}"): delete_item(item['id'])
