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

COLOR_ACCENT = "#8FAF9A"  # Saliegroen
COLOR_BG_BROKEN_WHITE = "#FDFBF7"
LOGO_URL = "https://i.postimg.cc/D0K876Sm/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="DPP Compliance Master", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. JURIDISCHE LOGICA & HELPERS ---
def is_authority():
    """Checkt of de kijker een autoriteit is via de URL: ?id=...&role=inspectie"""
    return st.query_params.get("role") == "inspectie"

def make_qr(id):
    url = f"https://digitalpassport.streamlit.app/?id={id}"
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def generate_certificate(data):
    """Genereert een formeel PDF certificaat met alle compliance data"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(143, 175, 154)
    pdf.cell(200, 15, txt="EU Digital Product Passport - Compliance Certificate", ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    pdf.set_fill_color(245, 247, 246)
    pdf.cell(190, 8, txt="Wettelijke Productgegevens (Verordening EU 2023/1542)", ln=True, align='L', fill=True)
    pdf.set_font("Arial", '', 9)
    
    # Mapping van data naar leesbare labels voor de PDF
    fields = [
        ("Uniek ID (UUID)", data.get('battery_uid')),
        ("Naam / Model", data.get('name')),
        ("Batch / Serie", data.get('batch_number')),
        ("Productiedatum", data.get('production_date')),
        ("Gewicht (kg)", data.get('weight_kg')),
        ("Batterij Type", data.get('battery_type')),
        ("CO2 Impact", f"{data.get('carbon_footprint')} kg CO2-eq"),
        ("EPR Nummer", data.get('epr_number')),
        ("CE DoC Ref", data.get('ce_doc_reference')),
        ("CE Module", data.get('ce_module')),
        ("Recycled Li (%)", data.get('rec_lithium_pct')),
        ("Recycled Co (%)", data.get('rec_cobalt_pct')),
        ("Recycled Ni (%)", data.get('rec_nickel_pct')),
        ("Recycled Pb (%)", data.get('rec_lead_pct')),
        ("Ref. Jaar Recycling", data.get('rec_reference_year')),
        ("Laadcycli tot 80%", data.get('cycles_to_80')),
        ("Cap. Retentie (%)", data.get('capacity_retention_pct')),
        ("Laatste Verificatie", data.get('last_verification_date')),
        ("Eigenaar Data", data.get('data_owner'))
    ]
    
    for label, val in fields:
        pdf.cell(70, 7, txt=f"{label}:", border=1)
        pdf.cell(120, 7, txt=str(val or 'N/A'), border=1, ln=True)

    # QR Code onderaan toevoegen
    qr_img_bytes = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(qr_img_bytes)
        tmp_path = tmp.name
    
    try:
        pdf.ln(10)
        pdf.image(tmp_path, x=75, y=pdf.get_y(), w=50)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        
    return pdf.output(dest='S').encode('latin-1')

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
    .login-container {{ display: flex; flex-direction: column; align-items: center; max-width: 400px; margin: 0 auto; padding-top: 10vh; }}
    .stButton button {{ background-color: {COLOR_ACCENT} !important; color: white !important; border-radius: 12px !important; width: 100% !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. APP LOGICA ---
q_params = st.query_params

if "id" in q_params:
    # --- GELAAGDE PASPOORT WEERGAVE (Consument & Autoriteit) ---
    res = get_data(f"{API_URL_BATTERIES}?id=eq.{q_params['id']}")
    if res:
        d = res[0]
        authority = is_authority()
        
        # Tracking van views
        httpx.patch(f"{API_URL_BATTERIES}?id=eq.{d['id']}", json={"views": (d.get('views') or 0) + 1}, headers=headers)

        st.markdown(f"<div style='background:white; padding:40px; border-radius:20px; text-align:center; border-top:8px solid {COLOR_ACCENT}; box-shadow: 0 4px 12px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        st.image(LOGO_URL, width=150)
        st.title(d.get('name', 'Product Paspoort'))
        st.write(f"Fabrikant: **{d['manufacturer']}**")
        st.divider()
        
        # Publieke data
        c1, c2, c3 = st.columns(3)
        c1.metric("CO2 Voetafdruk", f"{d.get('carbon_footprint', 0)} kg")
        c2.metric("Gewicht", f"{d.get('weight_kg', 0)} kg")
        c3.metric("State of Health", f"{d.get('soh_pct', 100)}%")
        
        # Technische data (Publiek toegankelijk)
        st.markdown("### Technische Details")
        st.write(f"Type: {d.get('battery_type')} | Chemie: {d.get('chemistry')}")
        
        # Rol-gebaseerde data (Alleen voor autoriteiten)
        if authority:
            st.divider()
            st.subheader("🕵️ Vertrouwelijke Inspectie Gegevens")
            st.json({
                "Uniek ID (UUID)": d.get("battery_uid"),
                "Batch Number": d.get("batch_number"),
                "EPR Nummer": d.get("epr_number"),
                "CE DoC Referentie": d.get("ce_doc_reference"),
                "CE Module": d.get("ce_module"),
                "Recycled Ni": f"{d.get('rec_nickel_pct')}%",
                "Recycled Pb": f"{d.get('rec_lead_pct')}%",
                "Referentiejaar Recycling": d.get("rec_reference_year"),
                "Laatste Verificatie": d.get("last_verification_date"),
                "Data Eigenaar": d.get("data_owner")
            })
        else:
            st.info("ℹ️ Scan met een geautoriseerd inspectie-device voor volledige audit-gegevens.")
        st.markdown("</div>", unsafe_allow_html=True)
    else: st.error("Paspoort niet gevonden.")

else:
    # --- DASHBOARD & LOGIN ---
    if 'company' not in st.session_state: st.session_state.company = None

    if not st.session_state.company:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.image(LOGO_URL, width=350)
        u = st.text_input("Gebruikersnaam", placeholder="Gebruikersnaam", label_visibility="collapsed")
        p = st.text_input("Wachtwoord", type="password", placeholder="Wachtwoord", label_visibility="collapsed")
        if st.button("Inloggen"):
            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
            if res and res[0]['password'] == p:
                st.session_state.company = res[0]['name']
                st.rerun()
            else: st.error("Inloggegevens onjuist.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        user = st.session_state.company
        st.sidebar.image(LOGO_URL)
        st.sidebar.title(f"Welkom, {user}")
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None
            st.rerun()

        st.title(f"Compliance Portaal: {user}")
        tab1, tab2 = st.tabs(["✨ Nieuwe Registratie (Wizard)", "📊 Voorraad & Audit"])

        with tab1:
            st.info("Vul alle velden in om een conform EU 2023/1542 paspoort te genereren.")
            with st.form("master_compliance_wizard"):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown("##### 1. Identificatie")
                    f_name = st.text_input("Productnaam (Publiek)")
                    f_model = st.text_input("Model ID")
                    f_batch = st.text_input("Batch / Serienummer")
                    f_date = st.date_input("Productiedatum") # NIEUW
                    f_weight = st.number_input("Gewicht (kg)", min_value=0.0) # NIEUW
                with c2:
                    st.markdown("##### 2. Producent & CE")
                    f_addr = st.text_input("Adres Fabriek")
                    f_epr = st.text_input("EPR Nummer")
                    f_doc = st.text_input("CE DoC Referentie")
                    f_ce = st.checkbox("CE Status Bevestigd", value=True)
                with c3:
                    st.markdown("##### 3. Milieu (LCA)")
                    f_co2 = st.number_input("Carbon footprint (kg CO2-eq)", min_value=0.0)
                    f_meth = st.selectbox("CO2 Methode", ["EU PEF", "ISO 14067", "GREET"]) # NIEUW
                    f_li = st.number_input("% Rec. Lithium", 0.0, 100.0)
                    f_co = st.number_input("% Rec. Kobalt", 0.0, 100.0)
                with c4:
                    st.markdown("##### 4. Levensduur & Audit")
                    f_cycles = st.number_input("Cycli tot 80%", min_value=0) # NIEUW
                    f_ret = st.number_input("Capaciteitsretentie (%)", 0, 100) # NIEUW
                    f_last_v = st.date_input("Laatste verificatiedatum")

    st.divider()
    f_eol = st.text_area("End-of-life instructies (Hoe moet de consument dit inleveren?)") # NIEUW
    f_origin = st.text_area("Grondstoffen Herkomst (Due Diligence)")

                st.divider()
                st.markdown("##### 5. Grondstoffen & Systeem")
                f_origin = st.text_area("Herkomst kritieke grondstoffen (Due Diligence)")
                f_ver = st.text_input("DPP Systeem Versie", "1.0.0")

                if st.form_submit_button("Valideren & Registreren", use_container_width=True):
                    # Harde Compliance Check (Lithium 2027 norm)
                    if f_li < 6.0:
                        st.error("❌ Lithium gehalte te laag voor EU 2027 norm (min. 6%)")
                    elif not f_ce:
                        st.error("❌ CE-markering is verplicht voor registratie.")
                    else:
                        payload = {
                            "name": f_name, "model_name": f_model, "batch_number": f_batch,
                            "battery_uid": str(uuid.uuid4()), "production_date": datetime.now().strftime("%Y-%m-%d"),
                            "weight_kg": f_weight, "battery_type": f_type, "manufacturer": user,
                            "manufacturer_address": f_addr, "epr_number": f_epr, "ce_doc_reference": f_doc,
                            "ce_module": f_mod, "ce_status": f_ce, "carbon_footprint": f_co2,
                            "rec_lithium_pct": f_li, "rec_cobalt_pct": f_co, "rec_nickel_pct": f_ni,
                            "rec_lead_pct": f_pb, "rec_reference_year": 2025, "capacity_kwh": f_cap,
                            "soh_pct": f_soh, "cycles_to_80": f_cycles, "capacity_retention_pct": f_ret,
                            "mineral_origin": f_origin, "last_verification_date": str(f_last_v),
                            "data_owner": user, "dpp_version": f_ver, "views": 0
                        }
                        with httpx.Client() as client:
                            resp = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                            if resp.status_code == 201:
                                st.success(f"✅ Product {f_name} succesvol geregistreerd in het EU register!")
                                st.balloons()
                                st.rerun()
                            else: st.error(f"Fout bij opslaan: {resp.text}")

        with tab2:
            st.subheader("Overzicht Vloot & Audit Logs")
            raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{user}")
            if raw_data:
                df = pd.DataFrame(raw_data)
                # Volledige tabel voor overzicht
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.divider()
                sel_name = st.selectbox("Product selecteren voor officiële acties", df['name'].tolist())
                item = df[df['name'] == sel_name].iloc[0]
                
                c_pdf, c_json, c_del = st.columns(3)
                c_pdf.download_button("📥 Download Audit PDF", generate_certificate(item), f"Audit_{sel_name}.pdf")
                c_json.download_button("🤖 Download Machine JSON", df[df['name']==sel_name].to_json(), f"DPP_{sel_name}.json")
                if c_del.button("🗑️ Verwijder uit register"):
                    httpx.delete(f"{API_URL_BATTERIES}?id=eq.{item['id']}", headers=headers)
                    st.rerun()
            else: st.info("Nog geen producten geregistreerd.")



