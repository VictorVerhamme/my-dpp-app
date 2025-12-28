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

# --- 2. HELPERS (ONGEWIJZIGD) ---
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
        ("Geregistreerd door", data.get('modified_by')),
        ("Registratie Datum", data.get('registration_date'))
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
    # PASPOORT PAGINA (SCAN VIEW)
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
            st.json({"UUID": d.get("battery_uid"), "Batch": d.get("batch_number"), "User": d.get("modified_by"), "Datum": d.get("registration_date")})
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # LOGIN & NAVIGATION LOGIC
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        # LOGIN SCREEN
        st.markdown('<div style="text-align:center; padding-top:10vh;">', unsafe_allow_html=True)
        st.image(LOGO_URL, width=350)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Inloggen"):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
            if res and res[0]['password'] == p:
                st.session_state.company = res[0]['name']; st.rerun()
    else:
        # --- SIDEBAR NAVIGATION ---
        st.sidebar.image(LOGO_URL, width=120)
        st.sidebar.title(f"Welkom, {st.session_state.company}")
        nav_choice = st.sidebar.radio("Navigatie", ["🏠 Dashboard", "📖 Compliance Gids"])
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None; st.rerun()

        if nav_choice == "📖 Compliance Gids":
            # --- PAGINA: COMPLIANCE GIDS ---
            st.title("📖 Compliance Gids: Uitleg Parameters")
            st.markdown("""
            In dit gedeelte vindt u de volledige uitleg over de parameters die vereist zijn voor de EU-batterijverordening 2023/1542.
            
            ---
            ### 1. Identificatie & Traceerbaarheid
            * **Productnaam:** De commerciële naam zoals deze op de markt verschijnt.
            * **Model ID:** De technische code van de fabrikant voor dit specifieke ontwerp.
            * **Batch / Serienummer:** Identificatie van de specifieke productie-run voor traceerbaarheid bij defecten.
            * **Productiedatum:** De exacte datum waarop de assemblage van de batterij is voltooid.
            * **Gewicht:** Het fysieke gewicht van de batterij in kilogram, essentieel voor recycling-berekeningen.
            * **UUID:** Een door het systeem automatisch gegenereerde unieke code voor deze specifieke batterij-eenheid.
            
            ### 2. Markttoegang
            * **EPR Nummer:** Registratienummer voor de uitgebreide producentenverantwoordelijkheid (afvalbeheer).
            * **CE DoC Referentie:** Verwijzing naar het officiële document van de 'Declaration of Conformity'.
            
            ### 3. Milieu & CO₂
            * **Carbon Footprint:** De totale uitstoot (Cradle-to-gate) in kg CO2-equivalent over de levenscyclus.
            * **CO₂ Methode:** De gehanteerde rekenstandaard. De Europese standaard is **EU PEF** (Product Environmental Footprint).
            * **Recycling %:** Het gewichtspercentage van materialen (zoals Lithium) dat is herwonnen uit afval.
            
            ### 4. Levensduur & Prestatie
            * **Cycli tot 80%:** Het aantal laad- en ontlaadcycli voordat de batterijcapaciteit onder de 80% van de originele waarde zakt.
            * **SoH (State of Health):** De actuele conditie van de batterij ten opzichte van de nieuwstaat.
            
            ### 5. Circulariteit & EOL
            * **End-of-life instructies:** Verplichte instructies die de consument vertellen hoe en waar zij de batterij aan het einde van de levensduur veilig moeten inleveren.
            """)
        
        else:
            # --- PAGINA: DASHBOARD ---
            st.title(f"Management Dashboard - {st.session_state.company}")
            tab1, tab2 = st.tabs(["✨ Nieuwe Registratie", "📊 Vlootoverzicht"])

            with tab1:
                st.image(LOGO_URL, width=300)
                with st.form("master_wizard"):
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown("##### 1. Identificatie")
                        f_name = st.text_input("Productnaam *")
                        f_model = st.text_input("Model ID *")
                        f_batch = st.text_input("Batchnummer *")
                        f_date = st.date_input("Productiedatum")
                        f_weight = st.number_input("Gewicht (kg) *", min_value=0.1)
                    with c2:
                        st.markdown("##### 2. Markttoegang")
                        f_epr = st.text_input("EPR Nummer")
                        f_doc = st.text_input("CE DoC Referentie")
                        f_ce = st.checkbox("CE Bevestigd", value=True)
                    with c3:
                        st.markdown("##### 3. Milieu")
                        f_co2 = st.number_input("Carbon footprint (kg CO2)", min_value=0.0)
                        f_meth = st.selectbox("CO2 Methode", ["EU PEF", "ISO 14067"])
                        f_li = st.number_input("% Rec. Lithium", 0.0, 100.0)
                    with c4:
                        st.markdown("##### 4. Levensduur")
                        f_cycles = st.number_input("Cycli tot 80%", min_value=0)
                        f_soh = st.slider("State of Health (%)", 0, 100, 100)

                    st.divider()
                    f_eol = st.text_area("End-of-life instructies (Verplicht)")

                    if st.form_submit_button("Valideren & Registreren", use_container_width=True):
                        # DUPLICAAT CHECK LOGICA
                        check_url = f"{API_URL_BATTERIES}?model_name=eq.{f_model}&batch_number=eq.{f_batch}"
                        existing = get_data(check_url)
                        
                        if existing:
                            st.error(f"❌ Fout: Product met Model '{f_model}' en Batch '{f_batch}' bestaat al.")
                        elif f_li < 6.0:
                            st.error("❌ Lithium-gehalte te laag (min. 6%).")
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
                                    st.success("✅ Succesvol geregistreerd!"); st.balloons(); st.rerun()

            with tab2:
                raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{st.session_state.company}")
                if raw_data:
                    df = pd.DataFrame(raw_data)
                    st.dataframe(df[['battery_uid', 'name', 'batch_number', 'registration_date']], use_container_width=True, hide_index=True)
                    st.divider()
                    sel = st.selectbox("Selecteer product voor PDF", df['name'].tolist())
                    item = df[df['name'] == sel].iloc[0]
                    st.download_button("📥 Download Audit PDF", generate_certificate(item), f"Audit_{sel}.pdf", use_container_width=True)
                else: st.info("Geen producten gevonden.")
