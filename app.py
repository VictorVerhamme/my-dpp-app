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

# --- 2. HELPERS ---
def make_qr(id):
    url = f"https://digitalpassport.streamlit.app/?id={id}"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except: return []

# --- 3. STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {COLOR_BG_BROKEN_WHITE}; }}
    header, footer {{visibility: hidden;}}
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}
    /* Styling voor de pijlers */
    .pijler-box {{
        background-color: white; padding: 20px; border-radius: 10px; 
        border: 1px solid #eee; margin-bottom: 20px; min-height: 350px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGICA ---
if 'company' not in st.session_state: st.session_state.company = None

q_params = st.query_params
if "id" in q_params:
    # --- PUBLIEK PASPOORT ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        st.markdown(f"<div style='background:white; padding:40px; border-radius:20px; text-align:center; border-top:8px solid {COLOR_ACCENT}'>", unsafe_allow_html=True)
        st.image(LOGO_URL, width=150)
        st.title(f"🔋 {d.get('name', 'Onbekende Batterij')}")
        st.write(f"Model: {d.get('model_name', 'N/A')} | Type: {d.get('battery_type', 'N/A')}")
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("CO2 Impact", f"{d.get('carbon_footprint', 0)} kg")
        c2.metric("Recycled Li", f"{d.get('rec_lithium_pct', 0)}%")
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
            if st.button("Inloggen", use_container_width=True):
                res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
                if res and res[0]['password'] == p:
                    st.session_state.company = res[0]['name']
                    st.rerun()
    else:
        # --- DASHBOARD ---
        user = st.session_state.company
        st.sidebar.image(LOGO_URL)
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        st.title(f"Compliance Wizard: {user}")
        tab1, tab2 = st.tabs(["✨ Nieuwe Registratie", "📊 Voorraad & Export"])

        with tab1:
            with st.form("wizard_form"):
                # Rij 1: Pijler 1 t/m 4
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown("##### 1. Identificatie")
                    f_name = st.text_input("Productnaam")
                    f_model = st.text_input("Model ID")
                    f_type = st.selectbox("Type", ["EV", "LMT", "Industrieel", "Draagbaar"])
                    f_chem = st.text_input("Chemie (bijv. NMC)")
                
                with col2:
                    st.markdown("##### 2. Producent")
                    f_addr = st.text_input("Adres Fabriek")
                    f_epr = st.text_input("EPR Nummer")
                    f_ce = st.checkbox("CE Gecertificeerd", value=True)
                
                with col3:
                    st.markdown("##### 3. Milieu (CO2)")
                    f_co2 = st.number_input("kg CO2-eq", min_value=0.0)
                    f_scope = st.selectbox("Scope", ["Cradle-to-gate", "Cradle-to-grave"])
                
                with col4:
                    st.markdown("##### 4. Recycled Content")
                    f_li = st.number_input("% Lithium", 0.0, 100.0)
                    f_co = st.number_input("% Kobalt", 0.0, 100.0)
                    f_ni = st.number_input("% Nikkel", 0.0, 100.0)

                st.divider()

                # Rij 2: Pijler 5 t/m 8
                col5, col6, col7, col8 = st.columns(4)
                with col5:
                    st.markdown("##### 5. Prestatie")
                    f_cap = st.number_input("Capaciteit (kWh)", min_value=0.0)
                    f_soh = st.slider("SoH (%)", 0, 100, 100)
                    f_cycles = st.number_input("Cycli", min_value=0)
                
                with col6:
                    st.markdown("##### 6. Circulariteit")
                    f_rem = st.checkbox("Verwijderbaar", value=True)
                    f_eol = st.selectbox("EOL Route", ["Recycling", "Reuse"])
                
                with col7:
                    st.markdown("##### 7. Due Diligence")
                    f_origin = st.text_area("Grondstof herkomst")
                    f_audit = st.checkbox("Audit uitgevoerd")
                
                with col8:
                    st.markdown("##### 8. DPP Systeem")
                    f_ver = st.text_input("Versie", "1.0.0")
                    st.info("QR & JSON worden na opslaan gegenereerd.")

                # DE KNOP
                submit = st.form_submit_button("Valideren & Registreren", use_container_width=True)
                
                if submit:
                    # COMPLIANCE CHECK
                    if f_li < 6.0:
                        st.error("❌ Lithium gehalte te laag voor EU 2027 norm (min. 6%)")
                    elif not f_ce:
                        st.error("❌ CE-markering is verplicht.")
                    else:
                        # PAYLOAD: Exacte match met SQL kolomnamen
                        payload = {
                            "name": f_name,
                            "manufacturer": user,
                            "model_name": f_model,
                            "battery_type": f_type,
                            "chemistry": f_chem,
                            "capacity_kwh": f_cap,
                            "manufacturer_address": f_addr,
                            "epr_number": f_epr,
                            "ce_status": f_ce,
                            "carbon_footprint": f_co2,
                            "carbon_scope": f_scope,
                            "rec_lithium_pct": f_li,
                            "rec_cobalt_pct": f_co,
                            "rec_nickel_pct": f_ni,
                            "soh_pct": f_soh,
                            "cycle_count": f_cycles,
                            "is_removable": f_rem,
                            "eol_route": f_eol,
                            "mineral_origin": f_origin,
                            "due_diligence_audit": f_audit,
                            "dpp_version": f_ver,
                            "views": 0
                        }
                        
                        with httpx.Client() as client:
                            resp = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            if resp.status_code == 201:
                                st.success(f"✅ {f_name} succesvol geregistreerd!")
                                st.balloons()
                            else:
                                st.error(f"Fout bij opslaan: {resp.text}")

        with tab2:
            data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
            if data:
                st.dataframe(pd.DataFrame(data)[['id', 'name', 'battery_type', 'carbon_footprint']], use_container_width=True)
