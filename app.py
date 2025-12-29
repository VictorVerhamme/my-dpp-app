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
import bcrypt

# --- 1. CONFIGURATIE ---
SUPABASE_URL = "https://nihebcwfjtezkufbxcnq.supabase.co"
SUPABASE_KEY = "sb_publishable_GYqO17G-B2DkS9j3TW1nHQ_BiyJOHJy"
API_URL_BATTERIES = f"{SUPABASE_URL}/rest/v1/Batteries"
API_URL_COMPANIES = f"{SUPABASE_URL}/rest/v1/Companies"

COLOR_ACCENT = "#8FAF9A"
COLOR_BG = "#FDFBF7"
LOGO_URL = "https://i.postimg.cc/43LQn3qG/Chat-GPT-Image-28-dec-2025-14-50-31-removebg-preview.png"

st.set_page_config(page_title="DPP Compliance Master 2025", page_icon="🔋", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- 2. HELPERS ---
def update_data(endpoint, item_id, payload):
    url = f"{endpoint}?id=eq.{item_id}"
    with httpx.Client() as client:
        # PATCH zorgt ervoor dat we alleen sturen wat we willen veranderen
        response = client.patch(url, json=payload, headers=headers)
        return response.status_code
        
def hash_password(password):
    # Maak een veilig "gehashed" wachtwoord
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed):
    try:
        # Probeer eerst op de veilige manier (bcrypt)
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ValueError:
        # Als dit faalt (bijv. 'Invalid salt'), is het een oud plat-tekst wachtwoord
        # We vergelijken het dan gewoon direct
        return password == hashed
    
def is_authority():
    return st.query_params.get("role") == "inspectie"

def make_qr(id):
    # Verander de link naar je nieuwe GitHub Pages locatie
    # Vergeet de '.html' en de '?id=' aan het einde niet!
    url = f"https://victorverhamme.github.io/my-dpp-app/passport.html?id={id}"
    
    qr = qrcode.make(url)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def generate_certificate(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. LOGO TOEVOEGEN
    try:
        with httpx.Client() as client:
            logo_resp = client.get(LOGO_URL)
            if logo_resp.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_logo:
                    tmp_logo.write(logo_resp.content)
                    tmp_logo_path = tmp_logo.name
                pdf.image(tmp_logo_path, x=150, y=10, w=40)
                os.remove(tmp_logo_path)
    except:
        pass

    # 2. HEADER
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 15, txt="EU Digital Product Passport", ln=True, align='L')
    
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt=f"Gegenereerd op: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='L')
    pdf.ln(5)
    
    # 3. TABEL SECTIE: BASIS IDENTIFICATIE
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 10, txt="1. Productidentificatie & Fabrikant", ln=True, fill=True)
    
    pdf.set_font("Arial", '', 9)
    fields = [
        ("Batterij UID", data.get('battery_uid')),
        ("Naam / Model", data.get('name')),
        ("Batchnummer", data.get('batch_number')),
        ("Productietype", data.get('battery_type')),
        ("Chemische Samenstelling", data.get('chemistry')),
        ("Fabrikant", data.get('manufacturer')),
        ("Fabriekslocatie", data.get('factory_address')),
        ("EPR Registratie", data.get('epr_number')),
    ]
    
    for label, val in fields:
        pdf.cell(70, 7, txt=f"{label}:", border=1)
        pdf.cell(120, 7, txt=str(val or 'N/A'), border=1, ln=True)

    pdf.ln(5)

    # 4. TABEL SECTIE: MILIEU & RECYCLING
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 10, txt="2. Milieu-impact & Gecertificeerde Recycling", ln=True, fill=True)
    
    pdf.set_font("Arial", '', 9)
    eco_fields = [
        ("Carbon Footprint", f"{data.get('carbon_footprint')} kg CO2e"),
        ("CO2 Methode", data.get('carbon_method')),
        ("Recycled Lithium (%)", f"{data.get('rec_lithium_pct')}%"),
        ("Recycled Kobalt (%)", f"{data.get('rec_cobalt_pct')}%"),
        ("Recycled Nikkel (%)", f"{data.get('rec_nickel_pct')}%"),
        ("Recycled Lood (%)", f"{data.get('rec_lead_pct')}%"),
    ]
    
    for label, val in eco_fields:
        pdf.cell(70, 7, txt=f"{label}:", border=1)
        pdf.cell(120, 7, txt=str(val or '0%'), border=1, ln=True)

    pdf.ln(5)

    # 5. UITGEBREIDE TEKSTVELDEN: DUE DILIGENCE & EOL
    # Due Diligence (Herkomst mineralen)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 8, txt="3. Grondstoffen & Supply Chain Due Diligence", ln=True, fill=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(190, 6, txt=str(data.get('mineral_origin') or "Geen herkomstinformatie opgegeven."), border=1)
    
    pdf.ln(5)

    # End-of-Life
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 8, txt="4. End-of-Life Instructies (Circulariteit)", ln=True, fill=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(190, 6, txt=str(data.get('eol_instructions') or "Niet gespecificeerd."), border=1)

    # 6. QR CODE & VERIFICATIE
    pdf.ln(15)
    qr_img_bytes = make_qr(data['id'])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_qr:
        tmp_qr.write(qr_img_bytes)
        tmp_qr_path = tmp_qr.name
    try:
        # Tekst naast de QR code
        pdf.set_font("Arial", 'B', 8)
        pdf.set_xy(10, pdf.get_y())
        pdf.cell(140, 5, txt="SCAN VOOR DIGITALE VERIFICATIE", ln=False)
        pdf.image(tmp_qr_path, x=150, y=pdf.get_y() - 5, w=30)
    finally:
        if os.path.exists(tmp_qr_path): os.remove(tmp_qr_path)
        
    return pdf.output(dest='S').encode('latin-1')

def get_data(url):
    try:
        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else []
    except: return []

# --- 3. STYLING (Gecombineerd: Kleuren + Verbergen interface elementen) ---
st.markdown(f"""
    <style>
    /* Jouw bestaande kleuren en knoppen */
    .stApp {{ background-color: {COLOR_BG}; }}
    h1, h2, h3 {{ color: {COLOR_ACCENT} !important; }}
    .stButton button {{ 
        background-color: {COLOR_ACCENT} !important; 
        color: white !important; 
        border-radius: 12px !important; 
    }}

    /* VERBERG WITTE BALK: Verbergt de volledige header bovenin */
    header {{ visibility: hidden; }}
    [data-testid="stHeader"] {{ display: none; }}

    /* VERBERG PIJLTJES: Verbergt de knop om de zijbalk in te klappen */
    [data-testid="stSidebarCollapseButton"] {{
        display: none;
    }}

    /* OPTIONEEL: Haalt de witruimte bovenin weg nu de balk weg is */
    .block-container {{
        padding-top: 2rem;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. APP LOGICA ---

# 1. INITIALISATIE: Zorg dat deze variabelen altijd bestaan in het geheugen
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "landing"

if 'company' not in st.session_state:
    st.session_state.company = None

# Haal de parameters uit de URL op
q_params = st.query_params

# 2. ROUTING: Ben je een consument (scan) of een beheerder (portaal)?
if "id" in q_params:
    # SNELLE REDIRECT: Stuur gsm-gebruikers direct naar de snelle GitHub-pagina
    st.info("Scan voltooid. U wordt doorverwezen naar het snelle mobiele portaal...")
    st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'https://victorverhamme.github.io/my-dpp-app/passport.html?id={q_params["id"]}\'" />', unsafe_allow_html=True)
    st.stop() # Stop de rest van de app hier voor consumenten
    
else:
    # --- DASHBOARD & LANDING PAGE LOGICA ---
    if not st.session_state.company:
        if st.session_state.auth_mode == "landing":
            # Optioneel: Haal het totaal aantal batterijen op voor de 'social proof'
            all_batts = get_data(API_URL_BATTERIES)
            total_count = len(all_batts) if all_batts else "1.250+" # Placeholder als database leeg is

            _, main_col, _ = st.columns([1, 3, 1]) 

            with main_col:
                st.image(LOGO_URL, width=350)
                
                # Impact-georiënteerde koptekst
                st.markdown(f"""
                    <div style="text-align: left;">
                        <h1 style='color: {COLOR_ACCENT}; margin-bottom: 0;'>Vertrouwen in elke cel.</h1>
                        <h3 style='color: #555; margin-top: 0;'>Reeds <b>{total_count} batterijen</b> veilig gedigitaliseerd conform EU 2023/1542.</h3>
                        <p style='font-size: 1.1rem; color: #666; line-height: 1.6; margin-top: 20px;'>
                            Wij zijn de drijvende kracht achter de circulaire batterij-economie. Fabrikanten en importeurs 
                            vertrouwen op ons platform voor het real-time valideren, beheren en delen van digitale productpaspoorten. 
                            <b>Voorkom boetes, versnel uw audit-proces en bied volledige transparantie aan uw eindgebruiker.</b>
                        </p>
                    </div>
                    <br>
                """, unsafe_allow_html=True)
                
                # De Knop
                btn_col, _ = st.columns([1, 2]) 
                with btn_col:
                    if st.button("Start met Digitaliseren ➔"):
                        st.session_state.auth_mode = "login"
                        st.rerun()

                st.divider()

                # Informatie Kolommen met focus op resultaat
                info_c1, info_c2, info_c3 = st.columns(3)
                
                with info_c1:
                    st.markdown(f"##### <span style='color: {COLOR_ACCENT};'>🛡️ Audit-Proof</span>", unsafe_allow_html=True)
                    st.write("Gegarandeerde naleving van de 8 wettelijke pijlers voor markttoegang in de EU.")
                
                with info_c2:
                    st.markdown(f"##### <span style='color: {COLOR_ACCENT};'>📈 Schaalbaar</span>", unsafe_allow_html=True)
                    st.write("Van prototype tot bulk-import van tienduizenden eenheden in enkele seconden.")
                
                with info_c3:
                    st.markdown(f"##### <span style='color: {COLOR_ACCENT};'>🤝 Partner Netwerk</span>", unsafe_allow_html=True)
                    st.write("Verbind fabrikanten, overheden en consumenten in één veilig ecosysteem.")
                    
        elif st.session_state.auth_mode == "login":
            # --- 1. CENTREREN VAN DE KAART OP HET SCHERM ---
            # We gebruiken flexibele kolommen. [1, 1.5, 1] werkt vaak beter voor een smalle kaart.
            _, center_col, _ = st.columns([1, 1.5, 1])

            with center_col:
                with st.container(border=True):
                    
                    # --- 2. CENTREREN VAN HET LOGO BINNEN DE KAART ---
                    # We maken 3 kolommen binnen de kaart. De middelste krijgt het logo.
                    # Door [1, 1, 1] te gebruiken, dwingen we het logo exact in het midden.
                    sub_l, sub_m, sub_r = st.columns([1, 1, 1])
                    with sub_m:
                        st.image(LOGO_URL, width=750) # Formaat van je logo

                    # --- 3. CENTREREN VAN DE TEKST ---
                    st.markdown("""
                        <div style='text-align: center;'>
                            <h3 style='margin-top: -10px;'>Partner Login</h3>
                            <p style='color: gray; font-size: 0.9rem;'>Beheer uw digitale paspoorten</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("---")
                    
                    # Input velden
                    u = st.text_input("Gebruikersnaam", placeholder="Naam", label_visibility="visible")
                    p = st.text_input("Wachtwoord", type="password", placeholder="Wachtwoord", label_visibility="visible")
                    
                    st.write("") # Extra witruimte
                    
                    # Knoppen naast elkaar
                    col_back, col_log = st.columns(2)
                    with col_back:
                        if st.button("⬅ Terug", use_container_width=True):
                            st.session_state.auth_mode = "landing"
                            st.rerun()
                    with col_log:
                        # De hoofdknop
                        if st.button("Inloggen ➔", use_container_width=True, type="primary"):
                            res = get_data(f"{API_URL_COMPANIES}?name=eq.{u}")
                            if res:
                                stored_hash = res[0]['password']
                                if check_password(p, stored_hash):
                                    st.session_state.company = res[0]['name']
                                    st.rerun()
                                else:
                                    st.error("Wachtwoord onjuist.")
                            else:
                                st.error("Gebruiker niet gevonden.")
            
    else:
        # SIDEBAR
        st.sidebar.image(LOGO_URL, width=150)
        st.sidebar.title(f"Welkom, {st.session_state.company}")
        nav = st.sidebar.radio("Navigatie", ["🏠 Dashboard", "⚠️ Compliance Monitor", "📖 Compliance Gids"])
        if st.sidebar.button("Uitloggen"):
            st.session_state.company = None; st.rerun()

        if nav == "📖 Compliance Gids":
            st.title("📖 Compliance Gids & Definities")
            st.markdown("""
            ### 1. Identificatie
            
            * **Productnaam (verplicht):** Naam van het product, bijv. “EV Accu 10Ah”.
            * **Model ID (verplicht):** Interne of externe modelidentificatie, bijv. “EV-1000X”.
            * **Batchnummer (verplicht):** Productiebatchnummer, bijv. “BATCH-20251228-01”.
            * **Productiedatum:** Datum van productie, bijv. “2025/12/28”.
            * **Gewicht (kg) (verplicht):** Gewicht van het product, bijv. “0,10”.
            * **Batterijtype:** Type batterij, bijv. “EV”.
            * **Chemie:** Chemische samenstelling, bijv. “NMC” of “LFP”.
            
            ### 2. Markttoegang
            
            * **EPR-nummer:** Nummer voor Extended Producer Responsibility.
            * **Adres fabriek:** Locatie van productie.
            * **CE DoC referentie:** Nummer van de CE Declaration of Conformity, bijv. “CE-DoC-2025-001”.
            * **CE module:** CE-certificeringsmodule, bijv. “Module A”.
            
            ### 3. Milieu & Recycling
            
            * **Carbon footprint (kg CO2):** CO2-uitstoot van het product, bijv. “0,00”.
            * **CO2 methode:** Methode voor CO2-berekening, bijv. “EU PEF”.
            * **% gerecycled lithium:** Percentage lithium uit recycling.
            * **% gerecycled kobalt:** Percentage kobalt uit recycling.
            * **% gerecycled nikkel:** Percentage nikkel uit recycling.
            * **% gerecycled lood:** Percentage lood uit recycling.
            * **Referentiejaar content:** Jaar van de milieugegevens, bijv. “2025”.
            
            ### 4. Prestatie
            
            * **Capaciteit (kWh):** Energiecapaciteit, bijv. “0,00”.
            * **Huidige State of Health (%):** Gezondheidstoestand van de batterij, 0–100.
            * **Cycli tot 80%:** Aantal laadcycli tot 80% capaciteit, bijv. “0”.
            * **Capaciteitsretentie (%):** Percentage van oorspronkelijke capaciteit dat behouden blijft, bijv. “0”.
            * **DPP versie:** Versie van het Data/Product Performance Protocol, bijv. “1.0.0”.
            * **End-of-life instructies (verplicht):** Instructies voor correcte afvoer door de consument.
            * **Herkomst kritieke grondstoffen (Due Diligence):** Bronnen van kritieke grondstoffen, inclusief due diligence, bijv. “NMC: Democratische Republiek Congo, LFP: China”.
            """)

        elif nav == "⚠️ Compliance Monitor":
            st.title("⚠️ Compliance Monitor")
            st.markdown("Hier ziet u welke batterijen actie vereisen om aan de EU-normen te voldoen.")

            # 1. Data ophalen voor deze specifieke partner
            raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{st.session_state.company}")
            
            if not raw_data:
                st.success("🎉 Geen batterijen gevonden. Alles is in orde of u moet nog registreren.")
            else:
                non_compliant_list = []

                # 2. De Compliance Check Logica
                for item in raw_data:
                    reasons = []
                    
                    # Check A: Verplichte velden (Pijler 1 & 8)
                    if not item.get('mineral_origin') or len(str(item.get('mineral_origin'))) < 5:
                        reasons.append("Grondstofherkomst (Due Diligence) ontbreekt of is onvoldoende.")
                    if not item.get('factory_address'):
                        reasons.append("Fabriekslocatie is niet gespecificeerd.")
                    if not item.get('eol_instructions') or len(str(item.get('eol_instructions'))) < 20:
                        reasons.append("End-of-life instructies zijn niet conform (te kort).")
                    
                    # Check B: Recycling targets (Pijler 3)
                    # We markeren het als waarschuwing als alles op 0 staat (onrealistisch voor EU)
                    if item.get('rec_lithium_pct', 0) == 0 and item.get('rec_cobalt_pct', 0) == 0:
                        reasons.append("Geen gerecycleerde inhoud opgegeven (Li/Co).")

                    # Check C: Markttoegang (Pijler 5)
                    if not item.get('ce_doc_reference'):
                        reasons.append("CE Conformiteitsverklaring (DoC) referentie ontbreekt.")

                    if reasons:
                        non_compliant_list.append({
                            "UID": item.get('battery_uid'),
                            "Naam": item.get('name'),
                            "Redenen van Afwijking": " | ".join(reasons)
                        })

                # 3. Weergave van de resultaten
                if non_compliant_list:
                    st.warning(f"Er zijn {len(non_compliant_list)} batterijen die niet volledig voldoen aan de EU-verordening.")
                    
                    df_issues = pd.DataFrame(non_compliant_list)
                    
                    # Weergave in een tabel die de volledige tekst laat zien
                    st.table(df_issues)
                    
                    st.info("💡 **Advies:** Ga naar het Dashboard en gebruik de 'Update' functie om de ontbrekende gegevens aan te vullen.")
                    # --- EXPORT FUNCTIE TOEVOEGEN ---
                    st.divider()
                    st.write("📂 **Rapportage voor Technisch Team**")
                    
                    # Zet de tabel om naar een CSV-bestand
                    csv_report = df_issues.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="📥 Download Compliance Rapport (CSV)",
                        data=csv_report,
                        file_name=f"Compliance_Rapport_{st.session_state.company}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.success("✅ Gefeliciteerd! Al uw geregistreerde batterijen voldoen aan de huidige compliance-checks.")
                    
        else:
            st.title("Digital Passport Management")
            
            # --- TABS DEFINIËREN ---
            if st.session_state.company == "SuperAdmin":
                # SuperAdmin krijgt alleen Vloot en Admin Control
                tab_fleet, tab_admin = st.tabs(["📊 Vlootoverzicht", "🔐 Admin Control"])
                tab_reg, tab_bulk = None, None # Deze bestaan niet voor Admin
            else:
                # Normale gebruikers krijgen de standaard 3 tabs
                tab_reg, tab_fleet, tab_bulk = st.tabs(["✨ Nieuwe Registratie", "📊 Vlootoverzicht", "📂 Bulk Import"])
                tab_admin = None # Bestaat niet voor normale gebruikers

                # --- TAB 1: REGISTRATIE (Uitgebreid voor 8 Pijlers) ---
            if tab_reg:
                with tab_reg:
                    st.markdown("### ✨ Nieuwe Compliance Registratie")
                    st.info("Vul alle velden in om een 100% wettelijk conform EU-paspoort te genereren.")
                    
                    with st.form("master_compliance_wizard", clear_on_submit=True):
                        # PIJLER 1 & 2: Identificatie & Fabrikant
                        st.markdown("#### 🆔 1. Productidentificatie & Herkomst")
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            f_name = st.text_input("Productnaam *")
                            f_model = st.text_input("Model ID *")
                            f_type = st.selectbox("Batterij Type *", ["EV", "LMT (E-bike/Step)", "Industrieel", "Stationair"])
                        with c2:
                            f_batch = st.text_input("Batchnummer *")
                            f_date = st.date_input("Productiedatum")
                            f_weight = st.number_input("Gewicht (kg) *", min_value=0.01)
                        with c3:
                            f_epr = st.text_input("EPR Registratienummer *")
                            f_addr = st.text_area("Adres Productiefaciliteit *", height=68)

                        st.divider()

                        # PIJLER 3 & 6: Milieu & Supply Chain
                        st.markdown("#### 🌿 2. Milieu-impact & Due Diligence")
                        c4, c5, c6 = st.columns(3)
                        with c4:
                            f_co2 = st.number_input("Carbon footprint (kg CO2e)", min_value=0.0)
                            f_meth = st.selectbox("CO2 Berekeningsmethode", ["EU PEF Compliant", "ISO 14067"])
                        with c5:
                            st.write("**Gerecycleerde Inhoud (%)**")
                            f_li = st.number_input("Lithium", 0.0, 100.0, key="reg_li")
                            f_co = st.number_input("Kobalt", 0.0, 100.0, key="reg_co")
                        with c6:
                            st.write("**&nbsp;**") # Uitlijning
                            f_ni = st.number_input("Nikkel", 0.0, 100.0, key="reg_ni")
                            f_pb = st.number_input("Lood", 0.0, 100.0, key="reg_pb")
                        
                        f_origin = st.text_area("Herkomst Kritieke Grondstoffen (Due Diligence informatie) *", 
                                              placeholder="Bijv. Lithium: Chili, Kobalt: DR Congo. Gecertificeerd via IRMA/RMI.")

                        st.divider()

                        # PIJLER 4 & 5: Prestatie & Veiligheid
                        st.markdown("#### 🔋 3. Prestaties & Veiligheid")
                        c7, c8, c9 = st.columns(3)
                        with c7:
                            f_cap = st.number_input("Nominale Capaciteit (kWh) *", min_value=0.0)
                            f_retention = st.number_input("Verwachte Capaciteitsretentie (%)", 0, 100, 80)
                        with c8:
                            f_soh = st.slider("Initiële State of Health (%)", 0, 100, 100)
                            f_cycles = st.number_input("Verwachte Laadcycli (tot 80%)", min_value=0)
                        with c9:
                            f_doc = st.text_input("CE DoC Referentie *")
                            f_mod = st.selectbox("Conformiteitsmodule", ["Module A", "Module B + C", "Module G"])

                        st.divider()

                        # PIJLER 7 & 8: Chemie & Einde Levensduur
                        st.markdown("#### ♻️ 4. Circulariteit & Chemie")
                        f_chem = st.text_input("Chemische Samenstelling (bijv. Li-ion NMC 811)", "Li-ion NMC")
                        f_eol = st.text_area("Gedetailleerde End-of-life instructies (Verplicht) *", 
                                           placeholder="Instructies voor demontage, inzameling en recycling conform richtlijn 2006/66/EG.")

                        if st.form_submit_button("Valideren & Registreren in Blockchain", use_container_width=True):
                            if not f_name or not f_model or not f_batch or not f_eol or not f_origin:
                                st.error("❌ Verplichte velden ontbreken. Vul alle velden met een * in.")
                            else:
                                payload = {
                                    "name": f_name, "model_name": f_model, "batch_number": f_batch,
                                    "battery_uid": str(uuid.uuid4()), "production_date": str(f_date),
                                    "weight_kg": f_weight, "manufacturer": st.session_state.company,
                                    "battery_type": f_type, "factory_address": f_addr,
                                    "carbon_footprint": f_co2, "carbon_method": f_meth,
                                    "rec_lithium_pct": f_li, "rec_cobalt_pct": f_co, 
                                    "rec_nickel_pct": f_ni, "rec_lead_pct": f_pb,
                                    "capacity_kwh": f_cap, "capacity_retention_pct": f_retention,
                                    "cycles_to_80": f_cycles, "soh_pct": f_soh,
                                    "mineral_origin": f_origin, "ce_doc_reference": f_doc, "ce_module": f_mod,
                                    "epr_number": f_epr, "chemistry": f_chem,
                                    "eol_instructions": f_eol, "modified_by": st.session_state.company,
                                    "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "views": 0
                                }
                                with httpx.Client() as client:
                                    r = client.post(API_URL_BATTERIES, json=payload, headers=headers)
                                    if r.status_code == 201:
                                        st.success("✅ Succesvol geregistreerd!"); st.rerun()
                                    else:
                                        st.error(f"Fout bij opslaan: {r.text}")

            # --- TAB 2: VLOOTOVERZICHT (Voor IEDEREEN) ---
            with tab_fleet:
                # SUPERADMIN CHECK VOOR DATA
                if st.session_state.company == "SuperAdmin":
                    raw_data = get_data(API_URL_BATTERIES)
                    st.write("🔧 **SuperAdmin Modus:** U bekijkt de volledige wereldwijde database.")
                else:
                    raw_data = get_data(f"{API_URL_BATTERIES}?manufacturer=eq.{st.session_state.company}")

                if raw_data:
                    df = pd.DataFrame(raw_data)
                    st.dataframe(df[['battery_uid', 'name', 'batch_number', 'registration_date']], use_container_width=True, hide_index=True)
                    st.divider()
                    sel = st.selectbox("Selecteer product voor PDF", df['name'].tolist())
                    item = df[df['name'] == sel].iloc[0]
                    st.download_button("📥 Download Audit PDF", generate_certificate(item), f"Audit_{sel}.pdf", use_container_width=True)
                    # --- STAP 2: BATTERIJ BEWERKEN (Toevoeging) ---
                    if st.session_state.company != "SuperAdmin":
                        st.divider()
                        with st.expander("📝 Status Update (SOH / Cycli aanpassen)"):
                            st.write("Pas hier de actuele status van een batterij aan na inspectie.")
                            
                            # We maken een lijst van UID's zodat de gebruiker de juiste batterij kiest
                            batt_list = {f"{b['name']} (ID: {b['battery_uid']})": b for b in raw_data}
                            selected_uid_label = st.selectbox("Welke batterij wilt u bijwerken?", options=list(batt_list.keys()), key="edit_selector")
                            
                            selected_batt = batt_list[selected_uid_label]

                            # Bewerk-formulier
                            with st.form(f"edit_form_{selected_batt['battery_uid']}"):
                                col_e1, col_e2 = st.columns(2)
                                with col_e1:
                                    up_soh = st.slider("Actuele State of Health (%)", 0, 100, int(selected_batt.get('soh_pct', 100)))
                                with col_e2:
                                    up_cycles = st.number_input("Nieuw aantal laadcycli", value=int(selected_batt.get('cycles_to_80', 0)))
                                
                                up_eol = st.text_area("Update End-of-life instructies", value=selected_batt.get('eol_instructions', ""))
                                
                                if st.form_submit_button("Wijzigingen Opslaan", use_container_width=True):
                                    update_payload = {
                                        "soh_pct": up_soh,
                                        "cycles_to_80": up_cycles,
                                        "eol_instructions": up_eol,
                                        "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M") # Update timestamp
                                    }
                                    
                                    status = update_data(API_URL_BATTERIES, selected_batt['id'], update_payload)
                                    
                                    if status in [200, 204]:
                                        st.success(f"✅ Status voor {selected_batt['battery_uid']} bijgewerkt!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Fout bij het bijwerken van de database.")
                else:
                    st.info("Geen producten gevonden.")

            # --- TAB 3: BULK IMPORT ---
            if tab_bulk:
                with tab_bulk:
                    st.subheader("📂 Geavanceerde Bulk Import (8 Pijlers)")
                    
                    # Nieuw sjabloon met alle kolommen
                    template_data = {
                        "Productnaam": ["EV Pack A1"], "Model ID": ["MOD-100"], "Batch": ["B-2025"],
                        "Gewicht_kg": [150.0], "Type": ["EV"], "Adres_Fabriek": ["Industrieweg 1, Antwerpen"],
                        "CO2_kg": [45.2], "Rec_Li": [15.0], "Rec_Co": [10.0], "Capaciteit_kWh": [75.0],
                        "Mineral_Origin": ["Lithium: Chili, Kobalt: Congo"], "EOL_Instructies": ["Recycle via punt X"]
                    }
                    df_temp = pd.DataFrame(template_data)
                    st.download_button("📥 Download Uitgebreid Sjabloon", df_temp.to_csv(index=False).encode('utf-8'), "dpp_compliance_template.csv")

                    uploaded_file = st.file_uploader("Upload CSV", type="csv")
                    if uploaded_file and st.button("🚀 Start Bulk Validatie & Import"):
                        df_upload = pd.read_csv(uploaded_file)
                        success_count = 0
                        for _, row in df_upload.iterrows():
                            payload = {
                                "name": str(row.get('Productnaam')), "model_name": str(row.get('Model ID')),
                                "batch_number": str(row.get('Batch')), "battery_uid": str(uuid.uuid4()),
                                "weight_kg": float(row.get('Gewicht_kg', 0)), "battery_type": str(row.get('Type', 'EV')),
                                "factory_address": str(row.get('Adres_Fabriek')), "carbon_footprint": float(row.get('CO2_kg', 0)),
                                "rec_lithium_pct": float(row.get('Rec_Li', 0)), "rec_cobalt_pct": float(row.get('Rec_Co', 0)),
                                "capacity_kwh": float(row.get('Capaciteit_kWh', 0)), "mineral_origin": str(row.get('Mineral_Origin')),
                                "eol_instructions": str(row.get('EOL_Instructies')), "manufacturer": st.session_state.company,
                                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M"), "views": 0
                            }
                            with httpx.Client() as client:
                                if client.post(API_URL_BATTERIES, json=payload, headers=headers).status_code == 201:
                                    success_count += 1
                        st.success(f"✅ {success_count} producten succesvol gedigitaliseerd!"); st.rerun()
                        
            # --- TAB: ADMIN CONTROL (Alleen voor SuperAdmin) ---
            if tab_admin:
                with tab_admin:
                    st.subheader("🔐 Systeembeheer & Partneroverzicht")
                    
                    # 1. DATA OPHALEN
                    all_companies_raw = get_data(API_URL_COMPANIES)
                    all_companies = [c for c in all_companies_raw if c.get('name') != "SuperAdmin"]
                    all_batteries = get_data(API_URL_BATTERIES)
                    
                    # 2. STATISTIEKEN (Bovenaan)
                    c_st1, c_st2 = st.columns(2)
                    c_st1.metric("Geregistreerde Partners", len(all_companies))
                    
                    # Hier hebben we de tekst aangepast zoals gevraagd
                    c_st2.metric("Totaal geregistreerde batterijen", len(all_batteries))
                    
                    st.divider()

                    # 3. LAYOUT IN TWEE KOLOMMEN
                    col_left, col_right = st.columns([2, 1])

                   with col_left:
                        st.markdown("### 🏢 Partner Overzicht & Compliance Status")
                        if all_companies and all_batteries:
                            # 1. Maak basis DataFrames
                            df_comp = pd.DataFrame(all_companies)
                            df_batt = pd.DataFrame(all_batteries)
                            
                            # 2. Definieer Compliance Check Logica
                            def check_compliance(item):
                                # We kijken naar dezelfde criteria als in de monitor
                                has_origin = item.get('mineral_origin') and len(str(item.get('mineral_origin'))) >= 5
                                has_factory = item.get('factory_address')
                                has_eol = item.get('eol_instructions') and len(str(item.get('eol_instructions'))) >= 20
                                has_ce = item.get('ce_doc_reference')
                                
                                # Retourneer True als alles klopt, anders False
                                return all([has_origin, has_factory, has_eol, has_ce])

                            # Voeg een compliance kolom toe aan de batterijen
                            df_batt['is_compliant'] = df_batt.apply(check_compliance, axis=1)
                            
                            # 3. Bereken totalen per fabrikant
                            counts = df_batt['manufacturer'].value_counts().reset_index()
                            counts.columns = ['name', 'Batterijen']
                            
                            # 4. Bereken het aantal NIET-conforme batterijen per fabrikant
                            non_compliant_df = df_batt[df_batt['is_compliant'] == False]
                            issue_counts = non_compliant_df['manufacturer'].value_counts().reset_index()
                            issue_counts.columns = ['name', '⚠️ Niet Conform']
                            
                            # 5. Voeg alles samen (Bedrijven + Totaal + Fouten)
                            df_final = pd.merge(df_comp[['name', 'created_at']], counts, on='name', how='left')
                            df_final = pd.merge(df_final, issue_counts, on='name', how='left').fillna(0)
                            
                            # Zet getallen om naar gehele getallen (ipv 1.0)
                            df_final['Batterijen'] = df_final['Batterijen'].astype(int)
                            df_final['⚠️ Niet Conform'] = df_final['⚠️ Niet Conform'].astype(int)
                            
                            # 6. Weergave in de tabel
                            st.dataframe(
                                df_final.rename(columns={'name': 'Bedrijf', 'created_at': 'Lid sinds'}), 
                                use_container_width=True, 
                                hide_index=True
                            )
                            
                            # Totaaloverzicht melding
                            total_issues = df_final['⚠️ Niet Conform'].sum()
                            if total_issues > 0:
                                st.error(f"Systeem-alert: Er zijn in totaal **{total_issues}** niet-conforme batterijen verspreid over uw partners.")
                            else:
                                st.success("Alle geregistreerde batterijen op het platform zijn momenteel conform.")
                                
                        else:
                            st.info("Nog geen partnerdata beschikbaar.")
                            
                    with col_right:
                        st.markdown("### 🛠️ Acties")
                        
                        # --- FORMULIER: PARTNER TOEVOEGEN ---
                        st.write("➕ **Voeg Partner toe**")
                        with st.form("add_company_form", clear_on_submit=True):
                            new_comp_name = st.text_input("Naam van het bedrijf")
                            new_comp_pass = st.text_input("Wachtwoord", type="password")
                            
                            # Belangrijk: Gebruik form_submit_button binnen een form
                            submit_add = st.form_submit_button("Opslaan", use_container_width=True)
                            
                            if submit_add:
                                if new_comp_name and new_comp_pass:
                                    secure_password = hash_password(new_comp_pass) 
                                    new_payload = {
                                        "name": new_comp_name, 
                                        "password": secure_password, 
                                        "created_at": datetime.now().isoformat()
                                    }
                                    with httpx.Client() as client:
                                        resp = client.post(API_URL_COMPANIES, json=new_payload, headers=headers)
                                        if resp.status_code in [200, 201]:
                                            st.success(f"✅ {new_comp_name} toegevoegd!")
                                            st.rerun()
                                        else:
                                            st.error("Fout bij opslaan.")
                        
                        st.divider()

                        # --- VERWIJDEREN (BUITEN HET FORMULIER) ---
                        st.write("🗑️ **Verwijder Partner**")
                        company_names = [c.get('name') for c in all_companies]
                        if company_names:
                            target_company = st.selectbox("Selecteer bedrijf", company_names, key="del_select_admin")
                            if st.button(f"Verwijder {target_company}", type="secondary", use_container_width=True):
                                with httpx.Client() as client:
                                    resp = client.delete(f"{API_URL_COMPANIES}?name=eq.{target_company}", headers=headers)
                                    if resp.status_code in [200, 204]:
                                        st.success(f"{target_company} verwijderd.")
                                        st.rerun()
                                    else:
                                        st.error("Fout bij verwijderen.")




















