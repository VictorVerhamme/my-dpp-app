import streamlit as st
import qrcode
import httpx
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import tempfile
import uuid
import os
from datetime import datetime

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"
COLOR_BG = "#FDFBF7"
LOGO_URL = "https://i.postimg.cc/43LQn3qG/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="DPP Compliance Master", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. HELPERS (PDF, QR, DATA) ---
def is_authority():
    return st.query_params.get("role") == "inspectie"

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
    pdf.ln(5)
    pdf.set_font("Arial", '', 9)
    fields = [
        ("UUID", data.get('battery_uid')),
        ("Naam", data.get('name')),
        ("Batch", data.get('batch_number')),
        ("Productiedatum", data.get('production_date')),
        ("Gewicht (kg)", data.get('weight_kg')),
        ("CO2 Voetafdruk", f"{data.get('carbon_footprint')} kg"),
        ("CO2 Methode", data.get('carbon_method')),
        ("Geregistreerd door", data.get('modified_by'))
    ]
    for label, val in fields:
        pdf.cell(70, 7, txt=f"{label}:", border=1)
        pdf.cell(120, 7, txt=str(val or 'N/A'), border=1, ln=True)
    
    qr_img_bytes = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(qr_img_bytes)
        tmp_path = tmp.name
    try:
        pdf.ln(10)
        pdf.image(tmp_path, x=75, y=pdf.get_y(), w=50)
    finally:
        if os.path.exists(tmp_path): os.remove(tmp_path)
    return pdf.output(dest='S').encode('latin-1')

def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except: return []

# --- 3. STYLING ---
st.markdown(f"<style>.stApp {{ background-color: {COLOR_BG}; }} h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }} .stButton button {{ background-color: {COLOR_ACCENT} !important; color: white !important; border-radius: 12px !important; }}</style>", unsafe_allow_html=True)

# --- 4. APP LOGICA ---
q_params = st.query_params

if "id" in q_params:
    # PASPOORT PAGINA
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        st.markdown(f"<div style='background:white; padding:40px; border-radius:25px; text-align:center; border-top:10px solid {COLOR_ACCENT};'>", unsafe_allow_html=True)
        st.image(LOGO_URL, width=200)
        st.title(d.get('name'))
        st.metric("CO2 Voetafdruk", f"{d.get('carbon_footprint', 0)} kg", help=f"Methode: {d.get('carbon_method')}")
        st.subheader("♻️ End-of-Life Instructies")
        st.info(d.get('eol_instructions') or "Geen instructies opgegeven.")
        if is_authority():
            st.divider(); st.subheader("🕵️ Audit Trail")
            st.json({"UUID": d.get("battery_uid"), "Batch": d.get("batch_number"), "User": d.get("modified_by")})
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # LOGIN & NAVIGATIE
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        st.markdown('<div style="text-align:center; padding-top:10vh;">', unsafe_allow_html=True)
        st.image(LOGO_URL, width=350)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Inloggen"):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
            if res and res[0]['password'] == p:
                st.session_state.company = res[0]['name']; st.rerun()
    else:
        # --- ZIJBALK NAVIGATIE ---
        st.sidebar.image(LOGO_URL, width=120)
        st.sidebar.title(f"Welkom, {st.session_state.company}")
        nav = st.sidebar.radio("Ga naar:", ["🏠 Dashboard", "📖 Compliance Gids"])
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None; st.rerun()

        if nav == "📖 Compliance Gids":
            # --- EXTRA PAGINA: UITLEG ---
            st.title("📖 Compliance Gids & Definities")
            st.markdown("""
            Welkom in de kennisbank van het Digital Product Passport. Hieronder vindt u de gedetailleerde uitleg per veld:
            
            ### 1. Identificatie & Traceerbaarheid
            * **Productnaam:** De commerciële benaming van de batterij.
            * **Model ID:** De unieke technische code van de fabrikant.
            * **Batch / Serienummer:** Identificatie van de specifieke productie-run.
            * **Productiedatum:** De dag waarop de assemblage is voltooid.
            * **Gewicht:** Fysiek gewicht in kg, essentieel voor recyclingberekeningen.
            
            ### 2. Markttoegang
            * **EPR Nummer:** Registratie voor de uitgebreide producentenverantwoordelijkheid.
            * **CE DoC Referentie:** Het nummer van uw officiële conformiteitsverklaring.
            
            ### 3. Milieu (LCA)
            * **Carbon footprint:** De totale uitstoot (Cradle-to-gate) in kg CO2.
            * **CO2 Methode:** De rekenmethode, waarbij **EU PEF** de Europese standaard is.
            * **Recycled Lithium:** Het percentage herwonnen materiaal in de batterij.
            
            ### 4. Levensduur
            * **Cycli tot 80%:** Het aantal keren dat de batterij tot 100% kan laden voordat de capaciteit onder de 80% zakt.
            * **SoH (State of Health):** De huidige conditie vergeleken met nieuwstaat.
            
            ### 5. Instructies
            * **End-of-life instructies:** Verplichte tekst die de consument vertelt hoe ze de batterij veilig moeten afvoeren.
            """)
        else:
            # --- DASHBOARD ---
            st.title("Compliance Dashboard")
            tab1, tab2 = st.tabs(["✨ Nieuwe Registratie", "📊 Vlootoverzicht"])

            with tab1:
                st.image(LOGO_URL, width=280)
                st.info("Hover over het 'i'-icoontje voor directe uitleg. Raadpleeg de gids in de zijbalk voor volledige tekst.")
                with st.form("master_wizard"):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown("##### 1. Identificatie")
                        f_name = st.text_input("Productnaam *", help="De commerciële naam. Zie Gids sectie 1.")
                        f_model = st.text_input("Model ID *", help="Technische code van fabrikant. Zie Gids sectie 1.")
                        f_batch = st.text_input("Batchnummer *", help="Identificeert de specifieke productie-run.")
                        f_date = st.date_input("Productiedatum")
                        f_weight = st.number_input("Gewicht (kg) *", min_value=0.1, help="Vereist voor recycling targets.")
                    with c2:
                        st.markdown("##### 2. Markttoegang")
                        f_epr = st.text_input("EPR Nummer", help="Registratienummer voor afvalbeheer. Zie Gids sectie 2.")
                        f_doc = st.text_input("CE DoC Referentie", help="Referentienummer van de conformiteitsverklaring.")
                        f_ce = st.checkbox("CE Bevestigd", value=True)
                    with c3:
                        st.markdown("##### 3. Milieu")
                        f_co2 = st.number_input("CO2 Voetafdruk (kg)", min_value=0.0, help="Totale emissie over de levenscyclus. Zie Gids sectie 3.")
                        f_meth = st.selectbox("CO2 Methode", ["EU PEF", "ISO 14067"], help="EU PEF is de Europese rekenstandaard.")
                        f_li = st.number_input("% Rec. Lithium", 0.0, 100.0, help="Minimaal 6% vereist vanaf 2027.")
                    with c4:
                        st.markdown("##### 4. Levensduur")
                        f_cycles = st.number_input("Cycli tot 80%", min_value=0, help="Aantal laadbeurten tot degradatie. Zie Gids sectie 4.")
                        f_soh = st.slider("State of Health (%)", 0, 100, 100)

                    st.divider()
                    f_eol = st.text_area("End-of-life instructies (Verplicht)", help="Uitleg voor de consument over inlevering. Zie Gids sectie 5.")

                    if st.form_submit_button("Valideren & Registreren", use_container_width=True):
                        check_url = f"{API_URL_BATTERIES}?model_name=eq.{f_model}&batch_number=eq.{f_batch}"
                        if get_data(check_url):
                            st.error(f"❌ Combinatie Model '{f_model}' en Batch '{f_batch}' bestaat al.")
                        elif f_li < 6.0:
                            st.error("❌ Lithium-gehalte te laag.")
                        else:
                            payload = {
                                "name": f_name, "model_name": f_model, "batch_number": f_batch,
                                "battery_uid": str(uuid.uuid4()), "production_date": str(f_date),
                                "weight_kg": f_weight, "manufacturer": st.session_state.company,
                                "carbon_footprint": f_co2, "carbon_method": f_meth,
                                "rec_lithium_pct": f_li, "cycles_to_80": f_cycles, "soh_pct": f_soh,
                                "eol_instructions": f_eol, "modified_by": st.session_state.company,
                                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "views": 0
                            }
                            with httpx.Client() as client:
                                r = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                                if r.status_code == 201:
                                    st.success("✅ Geregistreerd!"); st.balloons(); st.rerun()

            with t2:
                raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{st.session_state.company}")
                if raw_data:
                    df = pd.DataFrame(raw_data)
                    st.dataframe(df[['battery_uid', 'name', 'batch_number', 'registration_date']], use_container_width=True, hide_index=True)
                    sel = st.selectbox("Selecteer product voor PDF", df['name'].tolist())
                    item = df[df['name'] == sel].iloc[0]
                    st.download_button("📥 Download Audit PDF", generate_certificate(item), f"Audit_{sel}.pdf", use_container_width=True)
