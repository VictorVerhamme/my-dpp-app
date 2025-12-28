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

st.set_page_config(page_title="DPP Compliance Engine", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. FUNCTIES (QR & PDF) ---
def make_qr(id):
    url = f"https://digitalpassport.streamlit.app/?id={id}"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def generate_certificate(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(143, 175, 154)
    pdf.cell(200, 15, txt="EU Digital Product Passport - Compliance Audit", ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Tabel met alle data
    pdf.set_fill_color(245, 247, 246)
    pdf.cell(190, 8, txt="Wettelijke Productgegevens", ln=True, align='L', fill=True)
    pdf.set_font("Arial", '', 9)
    
    fields = [
        ("Naam / Model", data.get('name')),
        ("Batterij ID", data.get('id')),
        ("Type", data.get('battery_type')),
        ("Chemie", data.get('chemistry')),
        ("CO2 Impact", f"{data.get('carbon_footprint')} kg CO2-eq"),
        ("EPR Nummer", data.get('epr_number')),
        ("CE Status", "Gecertificeerd" if data.get('ce_status') else "Niet Gecertificeerd"),
        ("Recycled Lithium", f"{data.get('rec_lithium_pct')}%"),
        ("Recycled Cobalt", f"{data.get('rec_cobalt_pct')}%"),
        ("State of Health", f"{data.get('soh_pct')}%"),
        ("Grondstof Herkomst", data.get('mineral_origin'))
    ]
    
    for label, val in fields:
        pdf.cell(60, 7, txt=f"{label}:", border=1)
        pdf.cell(130, 7, txt=str(val), border=1, ln=True)

    # QR Code onderaan
    qr_img = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(qr_img)
        pdf.image(tmp.name, x=75, y=pdf.get_y()+10, w=50)
        
    return pdf.output(dest='S').encode('latin-1')

def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except: return []

# --- 3. STYLING ---
st.markdown(f"<style>.stApp {{ background-color: {COLOR_BG_BROKEN_WHITE}; }} header, footer {{visibility: hidden;}} h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}</style>", unsafe_allow_html=True)

# --- 4. LOGICA ---
if 'company' not in st.session_state: st.session_state.company = None

q_params = st.query_params
if "id" in q_params:
    # --- PUBLIEK PASPOORT VIEW ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        httpx.patch(f"{API_URL_BATTERIES}?id=eq.{d['id']}", json={"views": (d.get('views') or 0) + 1}, headers=headers)
        st.markdown(f"<div style='background:white; padding:40px; border-radius:20px; text-align:center; border-top:8px solid {COLOR_ACCENT}'>", unsafe_allow_html=True)
        st.image(LOGO_URL, width=120)
        st.title(d['name'])
        st.write(f"Fabrikant: **{d['manufacturer']}**")
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("CO2 Voetafdruk", f"{d.get('carbon_footprint', 0)} kg")
        c2.metric("Lithium Recycled", f"{d.get('rec_lithium_pct', 0)}%")
        c3.metric("State of Health", f"{d.get('soh_pct', 100)}%")
        st.markdown("</div>", unsafe_allow_html=True)
else:
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
        user = st.session_state.company
        st.sidebar.image(LOGO_URL, width=150)
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        st.title(f"Dashboard {user}")
        tab1, tab2 = st.tabs(["✨ Nieuwe Registratie", "📊 Voorraad & Export"])

        with tab1:
            # (Hier staat je werkende Wizard code van de vorige stap)
            st.info("Gebruik de Wizard om een product conform de EU-wetgeving aan te maken.")
            # ... (wizard code) ...

        with tab2:
            st.subheader("Overzicht Geregistreerde Producten")
            raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
            
            if raw_data:
                df = pd.DataFrame(raw_data)
                # We tonen alleen de belangrijkste kolommen in de tabel voor overzicht
                display_cols = ['id', 'name', 'battery_type', 'carbon_footprint', 'dpp_version', 'views']
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
                
                st.divider()
                st.subheader("Acties & Detailaudit")
                
                sel_name = st.selectbox("Selecteer een product voor export of inspectie", df['name'].tolist())
                item = df[df['name'] == sel_name].iloc[0]
                
                col_info, col_qr = st.columns([2, 1])
                with col_info:
                    st.write(f"**Geselecteerd:** {sel_name}")
                    st.write(f"**Model ID:** {item.get('model_name')}")
                    st.write(f"**Chemie:** {item.get('chemistry')}")
                    st.write(f"**EPR Registratie:** {item.get('epr_number')}")
                    
                    st.markdown("---")
                    c_pdf, c_json, c_del = st.columns(3)
                    c_pdf.download_button("📥 Audit PDF", generate_certificate(item), f"Audit_{sel_name}.pdf")
                    c_json.download_button("🤖 Machine JSON", df[df['name']==sel_name].to_json(), f"DPP_{sel_name}.json")
                    if c_del.button("🗑️ Verwijderen", key="del_btn"):
                        httpx.delete(f"{API_URL_BATTERIES}?id=eq.{item['id']}", headers=headers)
                        st.rerun()

                with col_qr:
                    st.image(make_qr(item['id']), width=180, caption="Scanbare QR-Code")
            else:
                st.info("Nog geen producten in de voorraad.")

