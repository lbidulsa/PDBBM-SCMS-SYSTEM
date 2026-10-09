import streamlit as st
import sqlite3
import pandas as pd
import secrets
import string
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from io import BytesIO

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="PDBBM SCMS Beneficiary Management System",
    page_icon="🕊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. EMAIL SENDER HELPER
# ==========================================
def send_credentials_email(recipient_email, recipient_name, temp_password):
    sender_email = os.environ.get("SMTP_EMAIL", "lbidulsa.fo10@dswd.gov.ph")
    sender_password = os.environ.get("SMTP_PASSWORD", "")
    
    if not sender_password:
        return False, "SMTP Password not configured in environment variables."
        
    try:
        msg = MIMEMultipart()
        msg['From'] = f"PDBBM SCMS Portal <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = "PDBBM SCMS Portal Account Credentials"
        
        body = f"""
Hello {recipient_name},

Your user account for the PDBBM SCMS Beneficiary Management System has been configured.

Login Email: {recipient_email}
Temporary Password: {temp_password}

Please login at the PDBBM SCMS Portal and change your temporary password upon first access.

Best regards,
PDBBM SCMS System Administrator
DSWD Field Office X
        """
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

# ==========================================
# 3. DATABASE CONNECTIONS & FULL SCHEMAS
# ==========================================
conn = sqlite3.connect('pdbbm_scms.db', check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT)")

c.execute("""
    CREATE TABLE IF NOT EXISTS family_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER,
        full_name TEXT,
        age INTEGER,
        birthdate TEXT,
        gender TEXT,
        relationship TEXT,
        civil_status TEXT,
        ethnicity TEXT,
        skills TEXT,
        occupation TEXT,
        monthly_income REAL,
        birth_cert TEXT,
        pwd_status TEXT,
        disability_kind TEXT,
        maintenance_meds TEXT,
        philhealth_status TEXT,
        philhealth_id TEXT,
        govt_programs TEXT,
        attending_school TEXT,
        education_details TEXT,
        living_in_household TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS deceased_family_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER,
        full_name TEXT,
        relationship TEXT,
        date_of_death TEXT,
        reason_of_death TEXT,
        has_death_cert TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS user_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        middle_name TEXT,
        last_name TEXT,
        province TEXT,
        user_role TEXT,
        email TEXT UNIQUE,
        password TEXT,
        require_change_pass INTEGER DEFAULT 0
    )
""")

# DELETION REQUESTS & AUTO-BACKUP ARCHIVE TABLES
c.execute("""
    CREATE TABLE IF NOT EXISTS deletion_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER,
        control_no TEXT,
        client_name TEXT,
        requested_by TEXT,
        reason TEXT,
        request_date TEXT,
        status TEXT DEFAULT 'PENDING'
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS deleted_cases_archive (
        archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_case_id INTEGER,
        control_no TEXT,
        client_name TEXT,
        requested_by TEXT,
        deletion_reason TEXT,
        deleted_by TEXT,
        archived_at TEXT,
        raw_case_data_json TEXT
    )
""")
conn.commit()

def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

SUPERUSER_EMAIL = "lbidulsa.fo10@dswd.gov.ph"
SUPERUSER_PASS = "P@ssw0rd"

c.execute("SELECT COUNT(*) FROM user_accounts WHERE lower(email) = lower(?)", (SUPERUSER_EMAIL,))
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO user_accounts (first_name, middle_name, last_name, province, user_role, email, password, require_change_pass) VALUES ('Super', 'Dev', 'Admin', 'RPMO', 'Superuser', ?, ?, 0)", (SUPERUSER_EMAIL, SUPERUSER_PASS))
else:
    c.execute("UPDATE user_accounts SET password = ?, user_role = 'Superuser' WHERE lower(email) = lower(?)", (SUPERUSER_PASS, SUPERUSER_EMAIL))
conn.commit()

# KUMPLETONG LISTAHAN SA TANAN FIELDS GIKAN SA FINAL EGIS EXCEL
required_columns = {
    "control_no": "TEXT", "gis_date": "TEXT", "client_id": "TEXT", "last_name": "TEXT", "first_name": "TEXT", 
    "middle_name": "TEXT", "ext_name": "TEXT", "alias": "TEXT", "phone_no": "TEXT", "birthdate": "TEXT", 
    "age": "INTEGER", "sex": "TEXT", "civil_status": "TEXT", "crn_number": "TEXT", "vot_status": "TEXT", 
    "ciac_status": "TEXT", "marriage_details": "TEXT", "num_wives": "INTEGER", "wife_order": "TEXT", 
    "affiliated_group": "TEXT", "fve_specify": "TEXT", "pag_specify": "TEXT", "rank_role": "TEXT", 
    "duration_involvement": "TEXT", "activity_locations": "TEXT", "activity_types": "TEXT", "purok": "TEXT", 
    "barangay": "TEXT", "city_muni": "TEXT", "province": "TEXT", "region": "TEXT", "place_of_birth": "TEXT", 
    "ethnicity": "TEXT", "place_of_integration": "TEXT", "physical_disability": "TEXT", "health_conditions_maint": "TEXT", 
    "education_type": "TEXT", "school_name_dates": "TEXT", "education_level": "TEXT", "occupation_before": "TEXT", 
    "current_occupation": "TEXT", "motivations_joining": "TEXT", "reasons_leaving": "TEXT", "intentions_motivations": "TEXT", 
    "dialects_spoken": "TEXT", "birth_cert_status": "TEXT", "birth_cert_registry": "TEXT", "marriage_cert_status": "TEXT", 
    "philhealth_status": "TEXT", "philhealth_id": "TEXT", "philhealth_category": "TEXT", "encoded_by": "TEXT", "staff_email": "TEXT", 
    "prob_desc": "TEXT", "assist_requested": "TEXT", "house_ownership": "TEXT", "house_ownership_specify": "TEXT", 
    "housing_condition": "TEXT", "house_renovate_pref": "TEXT", "roofing_material": "TEXT", "walling_material": "TEXT", 
    "flooring_material": "TEXT", "water_source": "TEXT", "sanitation_toilet": "TEXT", "illness_6months": "TEXT", 
    "illness_duration": "TEXT", "illness_severity": "TEXT", "govt_assistance_received": "TEXT", "govt_assistance_usage": "TEXT", 
    "govt_assistance_impact": "TEXT", "land_ownership": "TEXT", "land_ownership_type": "TEXT", "land_location": "TEXT", "land_area": "TEXT", 
    "agri_equipment": "TEXT", "agri_cultivation_involvement": "TEXT", "agri_sectors": "TEXT", "crops_specify": "TEXT", 
    "livestock_specify": "TEXT", "fisheries_specify": "TEXT", "support_services_specify": "TEXT", "farming_interest": "TEXT", 
    "farming_assistance_needed": "TEXT", "farming_infra_needed": "TEXT", "farming_skills_desired": "TEXT", 
    "vehicles_owned": "TEXT", "occupation_status": "TEXT", "occupation_specify": "TEXT", "desired_future_occ": "TEXT", 
    "coop_membership": "TEXT", "coop_name": "TEXT", "coop_position": "TEXT", "coop_duration": "TEXT", 
    "business_type": "TEXT", "business_duration": "TEXT", "business_goal": "TEXT", "business_assets_owned": "TEXT", 
    "preferred_business": "TEXT", "business_skills_experience": "TEXT", "business_opportunities": "TEXT", 
    "uniformed_service_interest": "TEXT", "cfw_interest": "TEXT", "cfw_preferred_work": "TEXT", 
    "mental_health_impact": "TEXT", "psychological_mgmt": "TEXT", "family_rel_change": "TEXT", "support_system": "TEXT", 
    "feeling_safety": "TEXT", "uniformed_personnel_feeling": "TEXT", "threats_perceived": "TEXT", "current_time_spent": "TEXT", 
    "hopes_aspirations": "TEXT", "transformation_challenges": "TEXT", "coping_mechanisms": "TEXT", "personal_growth": "TEXT", 
    "barangay_council_member": "TEXT", "pending_legal_cases": "TEXT", "arrest_history": "TEXT", "message_to_govt": "TEXT", 
    "existing_skills": "TEXT", "skills_acquisition_mode": "TEXT", "skills_training_wish": "TEXT", "skills_training_pref": "TEXT", 
    "formal_education_wish": "TEXT", "als_enrollment_wish": "TEXT", "education_docs_available": "TEXT", 
    "dependents_education_wish": "TEXT", "study_grant_dependents": "TEXT", "skills_training_desired_list": "TEXT", 
    "skills_training_dependents": "TEXT", "sw_assessment": "TEXT", "place_of_interview": "TEXT", "interviewed_by": "TEXT", "approved_by": "TEXT"
}

c.execute("PRAGMA table_info(cases)")
existing_cols = [row[1] for row in c.fetchall()]
for col_name, col_type in required_columns.items():
    if col_name not in existing_cols:
        c.execute(f"ALTER TABLE cases ADD COLUMN {col_name} {col_type}")
conn.commit()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}
if "autofill_data" not in st.session_state:
    st.session_state["autofill_data"] = {}
if "redirect_to_module" not in st.session_state:
    st.session_state["redirect_to_module"] = None

def export_to_excel_bytes(df):
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report_Data')
    except Exception:
        output.write(df.to_csv(index=False).encode('utf-8'))
    return output.getvalue()

def render_sidebar_logo():
    if os.path.exists("logo.png"):
        st.image("logo.png", width=400)
    elif os.path.exists("Peace and Dev LOGO.jpg"):
        st.image("Peace and Dev LOGO.jpg", width=200)
    else:
        st.markdown("## 🕊️ **DSWD FIELD OFFICE X**")

def render_header_logo(width=200):
    if os.path.exists("Peace and Dev LOGO.jpg"):
        st.image("Peace and Dev LOGO.jpg", width=width)
    elif os.path.exists("logo.png"):
        st.image("logo.png", width=width)
    else:
        st.markdown("## 🕊️ **DSWD FIELD OFFICE X**")

def parse_date_str(date_str, default_date=date(1995, 1, 1)):
    if not date_str or date_str == "None":
        return default_date
    try:
        return datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
    except Exception:
        try:
            return datetime.strptime(str(date_str).strip(), "%m-%d-%Y").date()
        except Exception:
            return default_date

# ==========================================
# 4. LOGIN PORTAL
# ==========================================
if not st.session_state["authenticated"] or not st.session_state.get("user_info"):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", width=600)
        st.title("🏛️ PDBBM SCMS Login Portal")
        st.markdown("##### **Peace and Development: Buong Bansa Mapayapa - SCMS Beneficiary Management System**")
        st.caption("Authorized Field Personnel & Case Managers Registry")
        st.divider()
        
        st.info("⚖ DATA PRIVACY ACT STATEMENT (RA 10173): By logging in, you agree that data processed strictly adheres to RA 10173 terms.")
        privacy_agreed = st.checkbox("I agree to the Data Privacy Act Statement & Policy Terms*")
        
        with st.form("login_form", clear_on_submit=False):
            login_email = st.text_input("User Email Address")
            login_pass = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("🔒 Login to System", use_container_width=True)
            
            if login_submitted:
                if not privacy_agreed:
                    st.error("⚠️ You must check and agree to the Data Privacy Act terms before logging in!")
                else:
                    c.execute("SELECT first_name, last_name, province, user_role, email, require_change_pass FROM user_accounts WHERE lower(email) = lower(?) AND password = ?", (login_email.strip(), login_pass.strip()))
                    user_res = c.fetchone()
                    if user_res:
                        st.session_state["authenticated"] = True
                        st.session_state["user_info"] = {
                            "name": f"{user_res[0]} {user_res[1]}",
                            "province": user_res[2],
                            "role": user_res[3],
                            "email": user_res[4],
                            "must_change_pass": bool(user_res[5])
                        }
                        st.success(f"✅ Welcome {user_res[0]}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid Email or Password.")
    st.stop()

# ==========================================
# 5. USER SESSION & SIDEBAR NAVIGATION
# ==========================================
u_info = st.session_state.get("user_info", {})
user_role = u_info.get("role", "User")
user_province = u_info.get("province", "RPMO")
user_email = u_info.get("email", "")
user_name = u_info.get("name", "User Account")

PROVINCES_LIST = ["Misamis Oriental", "Misamis Occidental", "Bukidnon", "Lanao del Norte", "Lanao del Sur", "RPMO", "CO"]

def get_beneficiary_options():
    if user_role in ["Superuser", "Admin"]:
        query = "SELECT id, client_id, control_no, last_name, first_name, province, staff_email FROM cases ORDER BY id DESC"
        df_c = pd.read_sql_query(query, conn)
    elif user_role == "Team Leader":
        query = "SELECT id, client_id, control_no, last_name, first_name, province, staff_email FROM cases WHERE lower(province) = lower(?) ORDER BY id DESC"
        df_c = pd.read_sql_query(query, conn, params=(user_province,))
    else:
        query = "SELECT id, client_id, control_no, last_name, first_name, province, staff_email FROM cases WHERE lower(staff_email) = lower(?) OR lower(encoded_by) = lower(?) ORDER BY id DESC"
        df_c = pd.read_sql_query(query, conn, params=(user_email, user_email))
        
    if not df_c.empty:
        return {f"ID #{row['id']} [HHID: {row['control_no'] or 'N/A'}]: {row['first_name']} {row['last_name']} ({row['province']})": row['id'] for _, row in df_c.iterrows()}
    return {}

def get_client_record(case_id):
    if not case_id:
        return {}
    df = pd.read_sql_query("SELECT * FROM cases WHERE id = ?", conn, params=(case_id,))
    if not df.empty:
        return df.iloc[0].to_dict()
    return {}

menu_options_list = [
    "📊 Executive Dashboard", "👤 1. Personal & Profiling", "👨‍👩‍👧‍👦 2. Family & Health",
    "📋 3. Prob & Assistance", "🏠 4. Infrastructure & Housing", "🌾 5. Agricultural Info",
    "💼 6. Livelihood & Employment", "🧠 7. Psychosocial Support", "🎓 8. Capacity Building",
    "📝 9. Assessment & Updates", "📊 Masterlist Database"
]

if user_role == "Superuser":
    menu_options_list.append("👥 User Management")

default_menu_idx = 0
if st.session_state.get("redirect_to_module"):
    target_mod = st.session_state["redirect_to_module"]
    for idx, opt in enumerate(menu_options_list):
        if opt.startswith(target_mod):
            default_menu_idx = idx
            break
    st.session_state["redirect_to_module"] = None

with st.sidebar:
    render_sidebar_logo()
    st.title("🏛️ PDBBM SCMS Portal")
    st.caption("Peace & Development: Buong Bansa Mapayapa")
    st.success(f"👤 **{user_name}**")
    st.caption(f"🔑 Role: **{user_role}** | 📍 Jurisdiction: **{user_province}**")
    st.caption(f"📧 Email: `{user_email}`")
    
    df_my_cnt = pd.read_sql_query("SELECT id FROM cases WHERE lower(encoded_by) = lower(?) OR lower(staff_email) = lower(?)", conn, params=(user_email, user_email))
    st.info(f"📝 **Your Encoded Entries:** {len(df_my_cnt)} Beneficiaries")

    # SUPERUSER NOTIFICATION BADGE FOR DELETION REQUESTS
    if user_role in ["Superuser", "Admin"]:
        c.execute("SELECT COUNT(*) FROM deletion_requests WHERE status = 'PENDING'")
        pending_del_cnt = c.fetchone()[0]
        if pending_del_cnt > 0:
            st.error(f"🔔 **Deletion Requests:** {pending_del_cnt} Pending")

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["user_info"] = {}
        st.rerun()
        
    st.divider()
    menu_selection = st.radio("Navigation Menu:", menu_options_list, index=default_menu_idx)

    # DEVELOPER OWNERSHIP CREDIT BADGE
    st.divider()
    st.markdown(
        """
        <div style="text-align: center; font-size: 0.8em; color: #6c757d;">
            💻 <b>System Developer & Architect</b><br>
            Developed with ❤️ by <br><b>LOUIE B. IDULSA - PDBBM ITO I</b><br>
            <i>DSWD FO X - PDBBM SCMS © 2026</i>
        </div>
        """, 
        unsafe_allow_html=True
    )

head_col1, head_col2 = st.columns([2, 7])
with head_col1:
    render_header_logo(width=180)
with head_col2:
    st.title("PDBBM SCMS Beneficiary Management System")
    st.caption("DSWD Field Office X • Peace & Development Program Registry")

st.divider()

# ==========================================
# MODULE 0: EXECUTIVE DASHBOARD
# ==========================================
if menu_selection == "📊 Executive Dashboard":
    st.subheader("📈 Executive Operations & Field Staff Performance Analytics")
    
    if user_role in ["Superuser", "Admin"]:
        df_all_cases = pd.read_sql_query("SELECT * FROM cases", conn)
    elif user_role == "Team Leader":
        df_all_cases = pd.read_sql_query("SELECT * FROM cases WHERE lower(province) = lower(?)", conn, params=(user_province,))
    else:
        df_all_cases = pd.read_sql_query("SELECT * FROM cases WHERE lower(staff_email) = lower(?) OR lower(encoded_by) = lower(?)", conn, params=(user_email, user_email))
    
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.metric("Total Accessible Beneficiaries", len(df_all_cases))
    with col_kpi2:
        st.metric("Active Field Staff/Encoders", len(df_all_cases['staff_email'].dropna().unique()) if not df_all_cases.empty else 0)
    with col_kpi3:
        st.metric("Provinces Covered", len(df_all_cases['province'].dropna().unique()) if not df_all_cases.empty else 0)

    st.divider()
    col_dash1, col_dash2 = st.columns(2)
    with col_dash1:
        st.markdown("### 📍 Total Beneficiaries per Province")
        if not df_all_cases.empty and 'province' in df_all_cases.columns:
            prov_summary = df_all_cases['province'].value_counts().reset_index()
            prov_summary.columns = ['Province', 'Total Entries']
            st.dataframe(prov_summary, use_container_width=True, hide_index=True)
        else:
            st.info("No data available.")

    with col_dash2:
        st.markdown("### 👥 Field Staff Summary Breakdown")
        if not df_all_cases.empty:
            staff_summary = df_all_cases.groupby(['province', 'staff_email']).size().reset_index(name='Total Encoded Entries')
            staff_summary.columns = ['Province Jurisdiction', 'Staff Email / Encoder', 'Encoded Count']
            st.dataframe(staff_summary, use_container_width=True, hide_index=True)
        else:
            st.info("No encoder data recorded.")

# ==========================================
# MODULE 1: PERSONAL & PROFILING
# ==========================================
elif menu_selection == "👤 1. Personal & Profiling":
    st.subheader("PART I. IDENTIFYING INFORMATION (Impormasyon ng Kinatawan)")
    b_options = get_beneficiary_options()
    
    col_sel, col_btn1, col_btn2 = st.columns([3, 1, 1])
    with col_sel:
        selected_option = st.selectbox("🔍 Search Client Record or Add New Beneficiary:", ["-- ADD NEW BENEFICIARY --"] + list(b_options.keys()))
    with col_btn1:
        st.write("")
        st.write("")
        if st.button("➕ Add New Client", use_container_width=True):
            st.session_state["autofill_data"] = {}
            st.rerun()
    with col_btn2:
        st.write("")
        st.write("")
        if st.button("❌ Cancel / Clear", use_container_width=True):
            st.session_state["autofill_data"] = {}
            st.rerun()

    c_data = st.session_state.get("autofill_data", {})
    if selected_option != "-- ADD NEW BENEFICIARY --":
        selected_id = b_options[selected_option]
        c_data = get_client_record(selected_id)
        st.info(f"✏ Editing Local Database Beneficiary: **{c_data.get('first_name','')} {c_data.get('last_name','')}**")

    # LIVE DUPLICATE CHECKER PROMPT
    control_no_val = st.text_input("TFDCC Household ID No.*:", value=str(c_data.get("control_no", "") or ""))
    
    if control_no_val.strip() != "":
        current_id = c_data.get("id", 0)
        c.execute("SELECT id, first_name, last_name, staff_email FROM cases WHERE lower(control_no) = lower(?) AND id != ?", (control_no_val.strip(), current_id))
        dup = c.fetchone()
        if dup:
            st.error(f"⚠️ **DUPLICATE DETECTED IN ENGLISH:** TFDCC Household ID No. '{control_no_val}' is already registered in the system under **{dup[1]} {dup[2]}** (Encoded by: {dup[3]}). Please verify before saving!")

    with st.form("personal_info_form"):
        col_hdr1, col_hdr2 = st.columns(2)
        with col_hdr1:
            gis_date_picker = st.date_input("Date:", value=parse_date_str(c_data.get("gis_date"), datetime.today().date()))
        with col_hdr2:
            crn_number = st.text_input("Combatant Reference Number (CRN) / Client ID:", value=str(c_data.get("crn_number", "") or c_data.get("client_id", "") or ""))

        st.markdown("##### 🎖️ INVOLVEMENT (Pakikilahok)")
        col_inv1, col_inv2, col_inv3 = st.columns(3)
        with col_inv1:
            affiliated_group = st.selectbox("Affiliated Group/Organization*", ["MILF", "MNLF", "KAPATIRAN (RPMP-RPA-ABB)", "CPP/NPA/NDF", "CPLA", "Private Armed Group", "FVE", "None"], index=0)
            fve_specify = st.text_input("FVE (pls specify):", value=str(c_data.get("fve_specify", "") or ""))
            pag_specify = st.text_input("Private Armed Group (pls specify):", value=str(c_data.get("pag_specify", "") or ""))
        with col_inv2:
            vot_status = st.selectbox("Victim of Terrorism (VoT)", ["No", "Yes"], index=0)
            ciac_status = st.selectbox("Child Involved in Armed Conflict (CIAC)", ["No", "Yes"], index=0)
        with col_inv3:
            rank_role = st.text_input("Rank / Role within Group:", value=str(c_data.get("rank_role", "") or ""))
            duration_involvement = st.text_input("Duration of Involvement:", value=str(c_data.get("duration_involvement", "") or ""))

        st.divider()
        st.markdown("##### 👤 Client Name & Contact Details")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            last_name = st.text_input("Last Name (Apelyido)*", value=str(c_data.get("last_name", "") or ""))
            first_name = st.text_input("First Name (Unang Pangalan)*", value=str(c_data.get("first_name", "") or ""))
            middle_name = st.text_input("Middle Name", value=str(c_data.get("middle_name", "") or ""))
            ext_name = st.text_input("Ext. Name (Sr, Jr, I, II)", value=str(c_data.get("ext_name", "") or ""))
            alias = st.text_input("Alias / Karaniwang Tawag", value=str(c_data.get("alias", "") or ""))
        with col2:
            purok = st.text_input("Purok/Street", value=str(c_data.get("purok", "") or ""))
            barangay = st.text_input("Barangay", value=str(c_data.get("barangay", "") or ""))
            city_muni = st.text_input("City/Municipality", value=str(c_data.get("city_muni", "") or ""))
            p_idx = PROVINCES_LIST.index(user_province) if user_province in PROVINCES_LIST else 0
            province = st.selectbox("Province/District*", PROVINCES_LIST, index=p_idx)
            region = st.text_input("Region", value=str(c_data.get("region", "Region X") or "Region X"))
        with col3:
            phone_no = st.text_input("Phone No.", value=str(c_data.get("phone_no", "") or ""))
            bday_picker = st.date_input("Birthdate / Birthday*", value=parse_date_str(c_data.get("birthdate"), date(1995, 1, 1)))
            
            today = date.today()
            calc_age = today.year - bday_picker.year - ((today.month, today.day) < (bday_picker.month, bday_picker.day))
            age = st.number_input("Calculated Age", min_value=0, max_value=120, value=int(calc_age))
            
            sex = st.selectbox("Sex*", ["Male", "Female"], index=0 if c_data.get("sex") != "Female" else 1)
            civil_status = st.selectbox("Civil Status", ["Single", "Married", "Widowed", "Separated", "Common Law"], index=0)
        with col4:
            marriage_details = st.selectbox("Marriage Details (if Married)", ["N/A", "Monogamous", "Polygamous"], index=0)
            num_wives = st.number_input("How many wives (if Polygamous)?", min_value=0, max_value=10, value=int(c_data.get("num_wives", 0) or 0))
            wife_order = st.selectbox("For Married Female Combatants:", ["N/A", "First Wife", "Second Wife", "Third Wife"], index=0)

        st.divider()
        st.markdown("##### 📜 Biographical & Social Protection Info")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            place_of_birth = st.text_input("Place of Birth:", value=str(c_data.get("place_of_birth", "") or ""))
            ethnicity = st.text_input("Ethnicity (Lahing Pinanggalingan):", value=str(c_data.get("ethnicity", "") or ""))
            place_of_integration = st.text_input("Place of Integration (Lugar ng Pagbabalik):", value=str(c_data.get("place_of_integration", "") or ""))
            physical_disability = st.selectbox("Physical Disability Status:", ["None", "Visual Impairment", "Hearing Impairment", "Speech Impairment", "Physically Handicapped"], index=0)
            health_conditions_maint = st.text_input("Health Conditions & Maintenance Medicine:", value=str(c_data.get("health_conditions_maint", "") or ""))
        with col_b2:
            education_type = st.selectbox("Education Type:", ["Public", "Private", "Non-Formal", "Religious (Madrasa/Seminarian)", "Informal"], index=0)
            school_name_dates = st.text_input("Name of Educational Institution & Dates:", value=str(c_data.get("school_name_dates", "") or ""))
            education_level = st.text_input("Educational Level Attained:", value=str(c_data.get("education_level", "") or ""))
            occupation_before = st.text_input("Occupation Before Involvement:", value=str(c_data.get("occupation_before", "") or ""))
            current_occupation = st.text_input("Current Occupation (After Disengagement):", value=str(c_data.get("current_occupation", "") or ""))
        with col_b3:
            motivations_joining = st.text_area("Motivations for Joining:", value=str(c_data.get("motivations_joining", "") or ""))
            reasons_leaving = st.text_area("Events Leading to Disengagement:", value=str(c_data.get("reasons_leaving", "") or ""))
            intentions_motivations = st.text_area("Current Intentions & Motivations:", value=str(c_data.get("intentions_motivations", "") or ""))
            dialects_spoken = st.text_input("Dialects Spoken/Read/Written:", value=str(c_data.get("dialects_spoken", "") or ""))

        st.markdown("##### 🛡️ Social Protection Certificates & PhilHealth")
        col_sp1, col_sp2, col_sp3 = st.columns(3)
        with col_sp1:
            birth_cert_status = st.selectbox("Birth Certificate Status:", ["Yes", "No"], index=0)
            birth_cert_registry = st.text_input("Birth Cert Date & Place of Registry:", value=str(c_data.get("birth_cert_registry", "") or ""))
        with col_sp2:
            marriage_cert_status = st.selectbox("Marriage Certificate Status:", ["Yes", "No", "N/A"], index=0)
            philhealth_status = st.selectbox("PhilHealth Member Status:", ["Yes (Active)", "Yes (Inactive)", "No"], index=0)
        with col_sp3:
            philhealth_id = st.text_input("PhilHealth Number:", value=str(c_data.get("philhealth_id", "") or ""))
            philhealth_category = st.selectbox("PhilHealth Category:", ["Direct Contributor", "Indirect Contributor", "Formal Economy", "Informal Economy", "OFW", "Domestic Worker", "Lifetime Member", "Sponsored Member", "Senior Citizen", "Indigent", "Group Enrollment", "4Ps Member"], index=0)

        submit_t1 = st.form_submit_button("💾 Save / Update Personal Record", use_container_width=True)
        if submit_t1:
            birthdate_str = bday_picker.strftime('%Y-%m-%d')
            gis_date_str = gis_date_picker.strftime('%m-%d-%Y')
            
            if last_name and first_name and control_no_val:
                if selected_option == "-- ADD NEW BENEFICIARY --" and not c_data.get("id"):
                    c.execute("""
                        INSERT INTO cases (control_no, gis_date, client_id, last_name, first_name, middle_name, ext_name, alias, phone_no, birthdate, age, sex, civil_status, crn_number, vot_status, ciac_status, marriage_details, num_wives, wife_order, affiliated_group, fve_specify, pag_specify, rank_role, duration_involvement, purok, barangay, city_muni, province, region, place_of_birth, ethnicity, place_of_integration, physical_disability, health_conditions_maint, education_type, school_name_dates, education_level, occupation_before, current_occupation, motivations_joining, reasons_leaving, intentions_motivations, dialects_spoken, birth_cert_status, birth_cert_registry, marriage_cert_status, philhealth_status, philhealth_id, philhealth_category, staff_email, encoded_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (control_no_val, gis_date_str, crn_number, last_name, first_name, middle_name, ext_name, alias, phone_no, birthdate_str, age, sex, civil_status, crn_number, vot_status, ciac_status, marriage_details, num_wives, wife_order, affiliated_group, fve_specify, pag_specify, rank_role, duration_involvement, purok, barangay, city_muni, province, region, place_of_birth, ethnicity, place_of_integration, physical_disability, health_conditions_maint, education_type, school_name_dates, education_level, occupation_before, current_occupation, motivations_joining, reasons_leaving, intentions_motivations, dialects_spoken, birth_cert_status, birth_cert_registry, marriage_cert_status, philhealth_status, philhealth_id, philhealth_category, user_email, user_email))
                else:
                    edit_id = c_data.get("id", selected_id)
                    c.execute("""
                        UPDATE cases SET control_no=?, gis_date=?, last_name=?, first_name=?, middle_name=?, ext_name=?, alias=?, phone_no=?, birthdate=?, age=?, sex=?, civil_status=?, crn_number=?, vot_status=?, ciac_status=?, marriage_details=?, num_wives=?, wife_order=?, affiliated_group=?, fve_specify=?, pag_specify=?, rank_role=?, duration_involvement=?, purok=?, barangay=?, city_muni=?, province=?, region=?, place_of_birth=?, ethnicity=?, place_of_integration=?, physical_disability=?, health_conditions_maint=?, education_type=?, school_name_dates=?, education_level=?, occupation_before=?, current_occupation=?, motivations_joining=?, reasons_leaving=?, intentions_motivations=?, dialects_spoken=?, birth_cert_status=?, birth_cert_registry=?, marriage_cert_status=?, philhealth_status=?, philhealth_id=?, philhealth_category=?, staff_email=? WHERE id=?
                    """, (control_no_val, gis_date_str, last_name, first_name, middle_name, ext_name, alias, phone_no, birthdate_str, age, sex, civil_status, crn_number, vot_status, ciac_status, marriage_details, num_wives, wife_order, affiliated_group, fve_specify, pag_specify, rank_role, duration_involvement, purok, barangay, city_muni, province, region, place_of_birth, ethnicity, place_of_integration, physical_disability, health_conditions_maint, education_type, school_name_dates, education_level, occupation_before, current_occupation, motivations_joining, reasons_leaving, intentions_motivations, dialects_spoken, birth_cert_status, birth_cert_registry, marriage_cert_status, philhealth_status, philhealth_id, philhealth_category, user_email, edit_id))
                conn.commit()
                st.success("✅ Beneficiary record updated successfully!")
                st.session_state["autofill_data"] = {}
                st.rerun()

# ==========================================
# MODULES 2 TO 9: ALWAYS-VISIBLE FULL FORMS
# ==========================================
elif menu_selection in [
    "👨‍👩‍👧‍👦 2. Family & Health", "📋 3. Prob & Assistance", "🏠 4. Infrastructure & Housing", 
    "🌾 5. Agricultural Info", "💼 6. Livelihood & Employment", "🧠 7. Psychosocial Support", 
    "🎓 8. Capacity Building", "📝 9. Assessment & Updates"
]:
    st.subheader(f"Module: {menu_selection}")
    b_options = get_beneficiary_options()
    
    selected_b_label = None
    case_id = None
    c_data = {}

    if b_options:
        selected_b_label = st.selectbox("🔍 Select Beneficiary Record to Manage:", list(b_options.keys()))
        case_id = b_options[selected_b_label]
        c_data = get_client_record(case_id)
        st.info(f"📄 Currently Editing Data Profile for: **{c_data.get('first_name', '')} {c_data.get('last_name', '')}**")
    else:
        st.info("ℹ️ Standard eGIS Form Template. Select or add a client in Module 1 to bind data.")

    if menu_selection == "👨‍👩‍👧‍👦 2. Family & Health":
        st.markdown("##### 🔒 Linked Household Identification")
        st.text_input("Auto-Filled TFDCC Household ID No. (Locked):", value=str(c_data.get("control_no", "NO HH ID LINKED")), disabled=True)
        st.divider()

        st.markdown("##### 👨‍👩‍👧‍👦 Living Family Members Composition (Komposisyon ng Pamilya)")
        
        with st.expander("➕ Add New Living Family Member", expanded=True):
            with st.form("add_living_fam_form", clear_on_submit=True):
                f_name = st.text_input("Complete Name of Family Member*")
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    f_rel = st.text_input("Relationship to Beneficiary")
                    f_bday = st.date_input("Family Member Birthdate*", value=date(2000, 1, 1))
                    today = date.today()
                    f_age = today.year - f_bday.year - ((today.month, today.day) < (f_bday.month, f_bday.day))
                    st.number_input("Calculated Age", value=int(f_age), disabled=True)
                    f_gender = st.selectbox("Gender", ["Male", "Female"])
                with col_f2:
                    f_status = st.selectbox("Civil Status", ["Single", "Married", "Widowed", "Separated"])
                    f_ethnicity = st.text_input("Ethnicity")
                    f_skills = st.text_input("Skills Possessed")
                with col_f3:
                    f_occ = st.text_input("Occupation / Income Source")
                    f_pwd = st.selectbox("PWD Status / Kind of Disability", ["None", "With Disability"])
                    f_meds = st.text_input("Maintenance Medicine if Applicable")
                
                sub_add_fam = st.form_submit_button("➕ Add Living Family Member to List")
                if sub_add_fam:
                    if f_name and case_id:
                        c.execute("""
                            INSERT INTO family_members (case_id, full_name, age, birthdate, gender, relationship, civil_status, ethnicity, skills, occupation, pwd_status, maintenance_meds)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (case_id, f_name, f_age, f_bday.strftime('%Y-%m-%d'), f_gender, f_rel, f_status, f_ethnicity, f_skills, f_occ, f_pwd, f_meds))
                        conn.commit()
                        st.success(f"✅ Added family member: {f_name}")
                        st.rerun()
                    elif not case_id:
                        st.warning("⚠️ Please select a beneficiary record first before adding family members.")

        if case_id:
            df_fam = pd.read_sql_query("SELECT full_name AS 'Full Name', birthdate AS 'Birthdate', age AS 'Age', gender AS 'Gender', relationship AS 'Relationship', civil_status AS 'Civil Status', occupation AS 'Occupation', pwd_status AS 'PWD Status' FROM family_members WHERE case_id = ?", conn, params=(case_id,))
            if not df_fam.empty:
                st.write("##### 📋 Registered Living Family Members History:")
                st.dataframe(df_fam, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("##### ✝️ Deceased Family Members (Yumaong Kamag-anak)")
        
        with st.expander("➕ Add Deceased Family Member", expanded=True):
            with st.form("add_deceased_fam_form", clear_on_submit=True):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    d_name = st.text_input("Deceased Full Name*")
                    d_rel = st.text_input("Relationship to Client")
                with col_d2:
                    d_date_picker = st.date_input("Date of Death*", value=date.today())
                    d_reason = st.text_input("Reason / Cause of Death")
                    d_cert = st.selectbox("Has Death Certificate?", ["Yes", "No"])
                
                sub_add_dec = st.form_submit_button("➕ Add Deceased Family Member to List")
                if sub_add_dec:
                    if d_name and case_id:
                        c.execute("""
                            INSERT INTO deceased_family_members (case_id, full_name, relationship, date_of_death, reason_of_death, has_death_cert)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (case_id, d_name, d_rel, d_date_picker.strftime('%Y-%m-%d'), d_reason, d_cert))
                        conn.commit()
                        st.success(f"✅ Added deceased family member: {d_name}")
                        st.rerun()
                    elif not case_id:
                        st.warning("⚠️ Please select a beneficiary record first before adding family members.")

        if case_id:
            df_dec = pd.read_sql_query("SELECT full_name AS 'Full Name', relationship AS 'Relationship', date_of_death AS 'Date of Death', reason_of_death AS 'Cause of Death', has_death_cert AS 'Death Cert' FROM deceased_family_members WHERE case_id = ?", conn, params=(case_id,))
            if not df_dec.empty:
                st.write("##### 📋 Registered Deceased Family Members History:")
                st.dataframe(df_dec, use_container_width=True, hide_index=True)

    else:
        with st.form("module_general_form"):
            if menu_selection == "📋 3. Prob & Assistance":
                st.markdown("##### 📋 Presenting Problem & Requested Assistance (Part IV)")
                prob_desc = st.text_area("Presenting Problem Description (Include medical, legal, and social issues with consent)", value=str(c_data.get("prob_desc", "")))
                assist_requested = st.text_area("Specific Assistance Requested from DSWD", value=str(c_data.get("assist_requested", "")))

            elif menu_selection == "🏠 4. Infrastructure & Housing":
                st.markdown("##### 🏠 Housing Conditions & Infrastructure Access (Annex A1)")
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    house_ownership = st.selectbox("Housing Ownership Status", ["Owned house and lot", "Owned house only", "Owned lot only", "Rented", "Sharing with parents/relatives", "Informal Settler"])
                    housing_condition = st.selectbox("Housing Condition", ["New house", "Old house", "Dilapidated House"])
                    house_renovate_pref = st.selectbox("Would you like to renovate your house?", ["Yes", "No"])
                    roofing_material = st.selectbox("Roofing Material", ["Concrete", "GI Sheet", "Nipa", "Others"])
                    walling_material = st.selectbox("Walling Material", ["Bamboo", "Concrete", "Nipa", "Wood/Lumber", "Others"])
                with col_h2:
                    flooring_material = st.selectbox("Flooring Material", ["Bamboo", "Concrete", "Soil", "Wood/Lumber", "Others"])
                    water_source = st.text_input("Source of Water (Within/Outside residence, Wells, Rivers, Rain, Public Distributor)", value=str(c_data.get("water_source", "")))
                    sanitation_toilet = st.selectbox("Sanitation (Restroom Access)", ["Yes (Inside home)", "Yes (Outside home)", "No / Communal"])

                st.divider()
                st.markdown("##### 🏥 Health Information & Government Assistance Access")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    illness_6months = st.text_input("Illnesses Encountered in Last 6 Months:", value=str(c_data.get("illness_6months", "")))
                    illness_duration = st.text_input("Duration of Illness:", value=str(c_data.get("illness_duration", "")))
                    illness_severity = st.text_input("Severity / Immediate Attention Needed:", value=str(c_data.get("illness_severity", "")))
                with col_g2:
                    govt_assistance_received = st.text_area("Govt Programs Received in Last 5 Years (4Ps, SLP, AICS, PAMANA, Social Pension, etc.):", value=str(c_data.get("govt_assistance_received", "")))
                    govt_assistance_usage = st.text_area("Usage of Financial Assistance Received (Food, Business, Education, Meds, Debt, etc.):", value=str(c_data.get("govt_assistance_usage", "")))
                    govt_assistance_impact = st.selectbox("Extent Assistance Contributed to Family Well-being:", ["Helped significantly", "Helped to some extent", "Helped only minimally", "Did not help"])

            elif menu_selection == "🌾 5. Agricultural Info":
                st.markdown("##### 🌾 Agricultural Information & Farming Engagement (Annex A2)")
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    land_ownership = st.selectbox("Do you own a land?", ["Yes", "No"])
                    land_ownership_type = st.selectbox("Ownership Type", ["Titled", "Stewardship/Tenant", "Pre-patent", "CADT", "Rented", "N/A"])
                    land_location = st.text_input("Land Location:", value=str(c_data.get("land_location", "")))
                    land_area = st.text_input("Land Area (Hectares / sqm):", value=str(c_data.get("land_area", "")))
                    agri_equipment = st.selectbox("Agricultural Equipment Owned/Acquired:", ["Owned", "Acquired", "None"])
                with col_a2:
                    agri_cultivation_involvement = st.selectbox("Involved in Agricultural Cultivation?", ["Yes", "No"])
                    crops_specify = st.text_input("Crops Produced (Banana, Coconut, Corn, Fruit trees, Rice, Vegetables, etc.):", value=str(c_data.get("crops_specify", "")))
                    livestock_specify = st.text_input("Livestock & Poultry (Carabao, Cattle, Chicken, Duck, Goat, Fish):", value=str(c_data.get("livestock_specify", "")))
                    fisheries_specify = st.text_input("Fisheries Sector (Freshwater, Seawater):", value=str(c_data.get("fisheries_specify", "")))
                    support_services_specify = st.text_input("Agri Support Services (Agri supply, Feeds):", value=str(c_data.get("support_services_specify", "")))

                st.divider()
                col_a3, col_a4 = st.columns(2)
                with col_a3:
                    farming_interest = st.selectbox("Do you want to engage in farming?", ["Yes", "No"])
                    farming_assistance_needed = st.text_input("Specific Farming Assistance Needed (Seedlings, Equipment, Infra, Capital):", value=str(c_data.get("farming_assistance_needed", "")))
                with col_a4:
                    farming_infra_needed = st.text_input("Infra Needed (Farm to Market Road, Irrigation, Solar, Warehouse):", value=str(c_data.get("farming_infra_needed", "")))
                    farming_skills_desired = st.text_input("Farming Skills Enhancement Desired (Cattle fattening, Duck raising, Organic farming):", value=str(c_data.get("farming_skills_desired", "")))

            elif menu_selection == "💼 6. Livelihood & Employment":
                st.markdown("##### 💼 Livelihood Investment & Employment Support (Annex A3)")
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    vehicles_owned = st.text_input("Vehicles Owned & Quantity (Boat, Tricycle, Jeepney, Van, Motorcycle):", value=str(c_data.get("vehicles_owned", "")))
                    occupation_status = st.selectbox("Employment / Occupation Status:", ["Self-employed (Business)", "Wage Earner (Employee)", "Wage Earner (Contract of Service/JO)", "Unemployed", "Not Applicable"])
                    occupation_specify = st.text_input("Specify Current Occupation:", value=str(c_data.get("occupation_specify", "")))
                    desired_future_occ = st.text_input("Desired Future Occupation:", value=str(c_data.get("desired_future_occ", "")))
                with col_l2:
                    coop_membership = st.selectbox("Cooperative / PO / Farmer Org Member?", ["Yes", "No"])
                    coop_name = st.text_input("Name of Cooperative/Organization:", value=str(c_data.get("coop_name", "")))
                    coop_position = st.text_input("Position / Role in Org:", value=str(c_data.get("coop_position", "")))
                    coop_duration = st.text_input("Duration of Membership:", value=str(c_data.get("coop_duration", "")))

                st.divider()
                st.markdown("##### 🏬 Business & Short-Term Employment")
                col_l3, col_l4 = st.columns(2)
                with col_l3:
                    business_type = st.selectbox("Type of Business Engaged In:", ["Manufacturing business", "Merchandise store (Sari-sari/groceries)", "Service shop (Karenderia/repair/salon)", "Others", "None"])
                    business_duration = st.selectbox("Duration in Business:", ["Less than 6 months", "7 months to 1 year", "1 to 2 years", "3 years above", "N/A"])
                    business_goal = st.selectbox("Business Goal:", ["Expand business", "Diversify to a new one", "N/A"])
                    business_assets_owned = st.text_input("Assets/Resources Owned (Capital, Equipment, Location):", value=str(c_data.get("business_assets_owned", "")))
                with col_l4:
                    uniformed_service_interest = st.text_input("Interest in Uniformed Services (AFP, PNP, Coast Guard, BJMP, CAFGU, Forest Guard):", value=str(c_data.get("uniformed_service_interest", "")))
                    cfw_interest = st.selectbox("Interested in Cash for Work (CFW)?", ["Yes", "No"])
                    cfw_preferred_work = st.text_input("Preferred CFW Work (De-clogging, Flood control, Gardening, Road cleaning, Tree planting):", value=str(c_data.get("cfw_preferred_work", "")))

            elif menu_selection == "🧠 7. Psychosocial Support":
                st.markdown("##### 🧠 Psychosocial Support & Community Integration (Annex A4)")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    mental_health_impact = st.text_area("Impact of Group Involvement on Mental/Emotional Well-being:", value=str(c_data.get("mental_health_impact", "")))
                    psychological_mgmt = st.text_area("How Psychological Challenges Are Managed:", value=str(c_data.get("psychological_mgmt", "")))
                    family_rel_change = st.text_area("Relationship Changes with Family & Community:", value=str(c_data.get("family_rel_change", "")))
                    support_system = st.text_area("Current Support System Details:", value=str(c_data.get("support_system", "")))
                    feeling_safety = st.selectbox("Feel Safe in Residence / Community?", ["Yes", "No", "Uncertain"])
                    uniformed_personnel_feeling = st.text_area("Reaction / Feeling When Seeing Uniformed Personnel:", value=str(c_data.get("uniformed_personnel_feeling", "")))
                with col_p2:
                    threats_perceived = st.text_area("Perceived Threats in Community:", value=str(c_data.get("threats_perceived", "")))
                    current_time_spent = st.text_area("How Current Time is Spent (Work, Study, Community):", value=str(c_data.get("current_time_spent", "")))
                    hopes_aspirations = st.text_area("Hopes and Aspirations for the Future:", value=str(c_data.get("hopes_aspirations", "")))
                    transformation_challenges = st.text_area("Challenges Faced in Transformation Process:", value=str(c_data.get("transformation_challenges", "")))
                    coping_mechanisms = st.text_area("Coping Mechanisms for Stress & Difficulties:", value=str(c_data.get("coping_mechanisms", "")))
                    personal_growth = st.text_area("Personal Growth / Changes Proud Of:", value=str(c_data.get("personal_growth", "")))

                st.divider()
                st.markdown("##### 🏛️ Political & Security Landscape")
                col_p3, col_p4 = st.columns(2)
                with col_p3:
                    barangay_council_member = st.selectbox("Member of Barangay Council?", ["Yes", "No"])
                    pending_legal_cases = st.text_input("Awareness of Pending Legal/Criminal Cases:", value=str(c_data.get("pending_legal_cases", "")))
                with col_p4:
                    arrest_history = st.text_input("Apprehension/Arrest History by Law Enforcement:", value=str(c_data.get("arrest_history", "")))
                    message_to_govt = st.text_area("Message / Expression to the Government:", value=str(c_data.get("message_to_govt", "")))

            elif menu_selection == "🎓 8. Capacity Building":
                st.markdown("##### 🎓 Capacity Building & Skills Training Wants (Annex A5)")
                col_cb1, col_cb2 = st.columns(2)
                with col_cb1:
                    existing_skills = st.text_input("Existing Skills Possessed:", value=str(c_data.get("existing_skills", "")))
                    skills_acquisition_mode = st.selectbox("Mode of Skills Acquisition:", ["Experience", "Formal Training", "Both"])
                    skills_training_wish = st.selectbox("Wish to Undergo Skills Training?", ["Yes", "No"])
                    skills_training_pref = st.selectbox("Preferred Training Environment:", ["Community-based", "Center-based"])
                with col_cb2:
                    formal_education_wish = st.selectbox("Wish to Enroll in Formal Education?", ["Yes", "No", "Not Applicable"])
                    als_enrollment_wish = st.selectbox("Willing to Enroll in ALS?", ["Yes", "No", "Not Applicable"])
                    education_docs_available = st.text_input("Requirements Available (Birth Cert, Form 137, College Units, ALS Cert, Valid ID):", value=str(c_data.get("education_docs_available", "")))

                st.divider()
                col_cb3, col_cb4 = st.columns(2)
                with col_cb3:
                    dependents_education_wish = st.text_input("Dependents to Enroll in Formal Ed or ALS:", value=str(c_data.get("dependents_education_wish", "")))
                    study_grant_dependents = st.text_input("Dependents to Avail Study Grant / Scholarship:", value=str(c_data.get("study_grant_dependents", "")))
                with col_cb4:
                    skills_training_desired_list = st.text_area("Desired Skills Training Courses (Baking, Carpentry, Cookery, Driving, Electrical, Masonry, Plumbing, Welding, Solar, etc.):", value=str(c_data.get("skills_training_desired_list", "")))
                    skills_training_dependents = st.text_input("Dependents to Avail Skills Training:", value=str(c_data.get("skills_training_dependents", "")))

            elif menu_selection == "📝 9. Assessment & Updates":
                st.markdown("##### 📝 Case Worker Evaluative Assessment & Progress Notes (Part VI)")
                sw_assessment = st.text_area("Evaluative Case Assessment & Recommendation:", value=str(c_data.get("sw_assessment", "")))
                
                st.info("📜 'I give my free and full consent to voluntarily participate in this activity, the accomplishment of this GIS, and to use the information given herein.'")
                
                col_as1, col_as2, col_as3 = st.columns(3)
                with col_as1:
                    place_of_interview = st.text_input("Place of Interview:", value=str(c_data.get("place_of_interview", "") or ""))
                with col_as2:
                    interviewed_by = st.text_input("Interviewed / Evaluated By:", value=user_email, disabled=True)
                with col_as3:
                    approved_by = st.text_input("Reviewed & Approved By:", value=str(c_data.get("approved_by", "") or ""))

            sub_m = st.form_submit_button("💾 Save / Update Module Record", use_container_width=True)
            if sub_m:
                if case_id:
                    if menu_selection == "📋 3. Prob & Assistance":
                        c.execute("UPDATE cases SET prob_desc=?, assist_requested=? WHERE id=?", (prob_desc, assist_requested, case_id))
                    elif menu_selection == "🏠 4. Infrastructure & Housing":
                        c.execute("UPDATE cases SET house_ownership=?, housing_condition=?, house_renovate_pref=?, roofing_material=?, walling_material=?, flooring_material=?, water_source=?, sanitation_toilet=?, illness_6months=?, illness_duration=?, illness_severity=?, govt_assistance_received=?, govt_assistance_usage=?, govt_assistance_impact=? WHERE id=?", (house_ownership, housing_condition, house_renovate_pref, roofing_material, walling_material, flooring_material, water_source, sanitation_toilet, illness_6months, illness_duration, illness_severity, govt_assistance_received, govt_assistance_usage, govt_assistance_impact, case_id))
                    elif menu_selection == "🌾 5. Agricultural Info":
                        c.execute("UPDATE cases SET land_ownership=?, land_ownership_type=?, land_location=?, land_area=?, agri_equipment=?, agri_cultivation_involvement=?, crops_specify=?, livestock_specify=?, fisheries_specify=?, support_services_specify=?, farming_interest=?, farming_assistance_needed=?, farming_infra_needed=?, farming_skills_desired=? WHERE id=?", (land_ownership, land_ownership_type, land_location, land_area, agri_equipment, agri_cultivation_involvement, crops_specify, livestock_specify, fisheries_specify, support_services_specify, farming_interest, farming_assistance_needed, farming_infra_needed, farming_skills_desired, case_id))
                    elif menu_selection == "💼 6. Livelihood & Employment":
                        c.execute("UPDATE cases SET vehicles_owned=?, occupation_status=?, occupation_specify=?, desired_future_occ=?, coop_membership=?, coop_name=?, coop_position=?, coop_duration=?, business_type=?, business_duration=?, business_goal=?, business_assets_owned=?, uniformed_service_interest=?, cfw_interest=?, cfw_preferred_work=? WHERE id=?", (vehicles_owned, occupation_status, occupation_specify, desired_future_occ, coop_membership, coop_name, coop_position, coop_duration, business_type, business_duration, business_goal, business_assets_owned, uniformed_service_interest, cfw_interest, cfw_preferred_work, case_id))
                    elif menu_selection == "🧠 7. Psychosocial Support":
                        c.execute("UPDATE cases SET mental_health_impact=?, psychological_mgmt=?, family_rel_change=?, support_system=?, feeling_safety=?, uniformed_personnel_feeling=?, threats_perceived=?, current_time_spent=?, hopes_aspirations=?, transformation_challenges=?, coping_mechanisms=?, personal_growth=?, barangay_council_member=?, pending_legal_cases=?, arrest_history=?, message_to_govt=? WHERE id=?", (mental_health_impact, psychological_mgmt, family_rel_change, support_system, feeling_safety, uniformed_personnel_feeling, threats_perceived, current_time_spent, hopes_aspirations, transformation_challenges, coping_mechanisms, personal_growth, barangay_council_member, pending_legal_cases, arrest_history, message_to_govt, case_id))
                    elif menu_selection == "🎓 8. Capacity Building":
                        c.execute("UPDATE cases SET existing_skills=?, skills_acquisition_mode=?, skills_training_wish=?, skills_training_pref=?, formal_education_wish=?, als_enrollment_wish=?, education_docs_available=?, dependents_education_wish=?, study_grant_dependents=?, skills_training_desired_list=?, skills_training_dependents=? WHERE id=?", (existing_skills, skills_acquisition_mode, skills_training_wish, skills_training_pref, formal_education_wish, als_enrollment_wish, education_docs_available, dependents_education_wish, study_grant_dependents, skills_training_desired_list, skills_training_dependents, case_id))
                    elif menu_selection == "📝 9. Assessment & Updates":
                        c.execute("UPDATE cases SET sw_assessment=?, place_of_interview=?, interviewed_by=?, approved_by=? WHERE id=?", (sw_assessment, place_of_interview, user_email, approved_by, case_id))
                    
                    conn.commit()
                    st.success(f"✅ Successfully saved {menu_selection} information for beneficiary ID #{case_id}!")
                else:
                    st.info("ℹ️ Form processed. Select or add a client in Module 1 to bind data.")

# ==========================================
# MASTERLIST DATABASE MODULE (WITH REQUEST TO DELETE & AUTO BACKUP)
# ==========================================
elif menu_selection == "📊 Masterlist Database":
    st.subheader("📊 Masterlist Case Database & User Entries Viewing Panel")
    appsheet_file = "Appsheet Data 10062026.xlsx"

    tabs_list = [
        "📱 Personal Encoding Panel", 
        "🌐 Authorized Regional Masterlist", 
        "📁 Integrated AppSheet Reference Database", 
        "📥 Export Reports"
    ]
    
    if user_role in ["Superuser", "Admin"]:
        tabs_list.append("🗑️ Pending Delete Approvals")
        tabs_list.append("📦 Deleted Cases Archive")

    tabs = st.tabs(tabs_list)

    # TAB 1: PERSONAL ENCODING PANEL & DELETION REQUEST FORM
    with tabs[0]:
        st.markdown(f"### 👤 Personal Encoding Panel ({user_name})")
        
        if user_role in ["Superuser", "Admin"]:
            df_my_entries = pd.read_sql_query("SELECT * FROM cases ORDER BY id DESC", conn)
            st.info("👑 **Super User Mode:** Displaying ALL encoded entries across the system.")
        elif user_role == "Team Leader":
            df_my_entries = pd.read_sql_query("SELECT * FROM cases WHERE lower(province) = lower(?) ORDER BY id DESC", conn, params=(user_province,))
            st.info(f"🔰 **Team Leader Mode:** Displaying entries under **{user_province}** jurisdiction.")
        else:
            df_my_entries = pd.read_sql_query("SELECT * FROM cases WHERE lower(encoded_by) = lower(?) OR lower(staff_email) = lower(?) ORDER BY id DESC", conn, params=(user_email, user_email))
            st.info("🔒 **User Security Restriction:** Displaying STRICTLY your own encoded entries.")

        if not df_my_entries.empty:
            st.success(f"📊 Total Personal Authorized Records: **{len(df_my_entries)} Beneficiaries**")
            st.dataframe(df_my_entries, use_container_width=True)
            
            col_d1, col_d2 = st.columns([1, 1])
            with col_d1:
                my_excel_bytes = export_to_excel_bytes(df_my_entries)
                st.download_button(
                    label="📥 Download My Encoded Entries (.xlsx)",
                    data=my_excel_bytes,
                    file_name=f"My_Entries_{user_name}_{user_province}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # REQUEST TO DELETE FEATURE FOR ENCODERS
            with col_d2:
                with st.expander("🗑️ Request to Delete an Entry"):
                    del_options = {f"ID #{row['id']} - [HHID: {row['control_no'] or 'N/A'}]: {row['first_name']} {row['last_name']}": (row['id'], row['control_no'], f"{row['first_name']} {row['last_name']}") for _, row in df_my_entries.iterrows()}
                    selected_del = st.selectbox("Select Record to Request Deletion:", list(del_options.keys()))
                    del_reason = st.text_area("State Reason for Deletion Request*:", placeholder="e.g. Duplicate entry / Incorrect client details")
                    
                    if st.button("📩 Submit Deletion Request to Admin", use_container_width=True):
                        if del_reason.strip():
                            req_case_id, req_hhid, req_cname = del_options[selected_del]
                            req_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("""
                                INSERT INTO deletion_requests (case_id, control_no, client_name, requested_by, reason, request_date, status)
                                VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
                            """, (req_case_id, req_hhid, req_cname, user_email, del_reason.strip(), req_date))
                            conn.commit()
                            st.success(f"📩 Deletion request for ID #{req_case_id} submitted to Super Admin for approval!")
                        else:
                            st.error("⚠️ Please provide a reason for the deletion request.")
        else:
            st.info("No recorded beneficiary entries found under your user account.")

    # TAB 2: REGIONAL MASTERLIST
    with tabs[1]:
        query = "SELECT * FROM cases WHERE 1=1"
        params = []
        if user_role not in ["Superuser", "Admin"] and user_province not in ["RPMO", "CO"]:
            if user_role == "Team Leader":
                query += " AND lower(province) = lower(?)"
                params.append(user_province)
            else:
                query += " AND (lower(staff_email) = lower(?) OR lower(encoded_by) = lower(?))"
                params.extend([user_email, user_email])

        query += " ORDER BY id DESC"
        df_master = pd.read_sql_query(query, conn, params=params)
        st.metric("Total Authorized Masterlist Records", len(df_master))
        st.dataframe(df_master, use_container_width=True)

    # TAB 3: APPSHEET MIGRATION TOOLKIT
    with tabs[2]:
        st.markdown("### 📁 Reference AppSheet Database View & Module Migration")
        if os.path.exists(appsheet_file):
            df_app_ref = pd.read_excel(appsheet_file)
            if user_role not in ["Superuser", "Admin"]:
                staff_cols = [c for c in df_app_ref.columns if 'staff' in c.lower() or 'email' in c.lower() or 'encoder' in c.lower()]
                if staff_cols:
                    df_app_ref = df_app_ref[df_app_ref[staff_cols[0]].astype(str).str.contains(user_email, case=False, na=False)]
            
            st.dataframe(df_app_ref, use_container_width=True)

            st.divider()
            st.markdown("#### 🔄 Migrate / Edit Selected Record to Module (1-9)")
            
            col_mig1, col_mig2, col_mig3 = st.columns([3, 2, 2])
            with col_mig1:
                ref_options = {f"Row {idx+1}: {row.get('First Name', row.get('first_name', ''))} {row.get('Last Name', row.get('last_name', ''))}": idx for idx, row in df_app_ref.iterrows()} if not df_app_ref.empty else {}
                selected_ref_row = st.selectbox("Select AppSheet Record to Migrate:", list(ref_options.keys()) if ref_options else ["No Records Found"])
            
            with col_mig2:
                target_module_choice = st.selectbox("Select Destination Module:", ["1. Personal & Profiling", "2. Family & Health", "3. Prob & Assistance", "4. Infrastructure & Housing", "5. Agricultural Info", "6. Livelihood & Employment", "7. Psychosocial Support", "8. Capacity Building", "9. Assessment & Updates"])
            
            with col_mig3:
                st.write("")
                st.write("")
                if st.button("🚀 Migrate & Auto-Fill Data", use_container_width=True):
                    if ref_options and selected_ref_row in ref_options:
                        row_idx = ref_options[selected_ref_row]
                        row_data = df_app_ref.iloc[row_idx].to_dict()
                        
                        st.session_state["autofill_data"] = {
                            "first_name": str(row_data.get("First Name", row_data.get("first_name", ""))),
                            "last_name": str(row_data.get("Last Name", row_data.get("last_name", ""))),
                            "middle_name": str(row_data.get("Middle Name", row_data.get("middle_name", ""))),
                            "phone_no": str(row_data.get("Phone", row_data.get("phone_no", ""))),
                            "province": str(row_data.get("Province", row_data.get("province", user_province))),
                            "city_muni": str(row_data.get("City", row_data.get("city_muni", ""))),
                            "barangay": str(row_data.get("Barangay", row_data.get("barangay", ""))),
                            "control_no": str(row_data.get("Control No", row_data.get("control_no", "")))
                        }
                        
                        st.session_state["redirect_to_module"] = target_module_choice[:2]
                        st.success(f"✅ Data migrated! Redirecting to Module {target_module_choice}...")
                        st.rerun()
        else:
            st.info("No external AppSheet reference file loaded.")

    # TAB 4: EXPORT REPORTS PORTAL
    with tabs[3]:
        st.markdown("### 📥 Export Reports Control Portal")
        if user_role in ["Superuser", "Admin"]:
            df_exp_final = pd.read_sql_query("SELECT * FROM cases", conn)
        elif user_role == "Team Leader":
            df_exp_final = pd.read_sql_query("SELECT * FROM cases WHERE lower(province) = lower(?)", conn, params=(user_province,))
        else:
            df_exp_final = pd.read_sql_query("SELECT * FROM cases WHERE lower(encoded_by) = lower(?) OR lower(staff_email) = lower(?)", conn, params=(user_email, user_email))

        if len(df_exp_final) == 0:
            st.warning("⚠️ Access Restricted: Account currently has 0 encoded entries under your scope.")
        else:
            st.success(f"📊 Authorized Export Data Count: **{len(df_exp_final)} Records**")
            excel_bytes = export_to_excel_bytes(df_exp_final)
            st.download_button(
                label="📥 Download Authorized Masterlist Report (.xlsx)",
                data=excel_bytes,
                file_name=f"PDBBM_Report_{user_province}_{user_role}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    # TAB 5: SUPER ADMIN PENDING DELETE APPROVALS (WITH AUTO-BACKUP)
    if user_role in ["Superuser", "Admin"]:
        with tabs[4]:
            st.markdown("### 🗑️ Super Admin Deletion Request Approvals")
            df_req = pd.read_sql_query("SELECT id, case_id AS 'Case ID', control_no AS 'Household ID', client_name AS 'Client Name', requested_by AS 'Requested By', reason AS 'Reason for Deletion', request_date AS 'Request Date' FROM deletion_requests WHERE status = 'PENDING' ORDER BY id DESC", conn)
            
            if not df_req.empty:
                st.dataframe(df_req, use_container_width=True)
                
                req_dict = {f"Req #{r['id']} - Case #{r['Case ID']} ({r['Client Name']})": (r['id'], r['Case ID'], r['Client Name'], r['Household ID'], r['Requested By'], r['Reason for Deletion']) for _, r in df_req.iterrows()}
                selected_req_key = st.selectbox("Select Pending Deletion Request to Act On:", list(req_dict.keys()))
                
                col_act1, col_act2 = st.columns(2)
                req_id, c_id, c_name, c_hhid, c_req_by, c_reason = req_dict[selected_req_key]
                
                with col_act1:
                    if st.button("✅ Approve & Auto-Backup to Archive", use_container_width=True):
                        # 1. Fetch full case row from SQLite
                        df_raw = pd.read_sql_query("SELECT * FROM cases WHERE id = ?", conn, params=(c_id,))
                        raw_json = df_raw.to_json(orient="records") if not df_raw.empty else "{}"
                        
                        # 2. Backup to deleted_cases_archive
                        archived_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("""
                            INSERT INTO deleted_cases_archive (original_case_id, control_no, client_name, requested_by, deletion_reason, deleted_by, archived_at, raw_case_data_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (c_id, c_hhid, c_name, c_req_by, c_reason, user_email, archived_at, raw_json))
                        
                        # 3. Delete from active cases table & family tables
                        c.execute("DELETE FROM cases WHERE id = ?", (c_id,))
                        c.execute("DELETE FROM family_members WHERE case_id = ?", (c_id,))
                        c.execute("DELETE FROM deceased_family_members WHERE case_id = ?", (c_id,))
                        
                        # 4. Update request status to APPROVED
                        c.execute("UPDATE deletion_requests SET status = 'APPROVED' WHERE id = ?", (req_id,))
                        conn.commit()
                        st.success(f"✅ Approved! Case #{c_id} ({c_name}) has been backed up to Archive and deleted from active database.")
                        st.rerun()

                with col_act2:
                    if st.button("❌ Reject Request", use_container_width=True):
                        c.execute("UPDATE deletion_requests SET status = 'REJECTED' WHERE id = ?", (req_id,))
                        conn.commit()
                        st.info(f"❌ Deletion request for Case #{c_id} was rejected.")
                        st.rerun()
            else:
                st.info("🎉 No pending deletion requests at this time.")

        # TAB 6: DELETED CASES ARCHIVE & RESTORE TOOL
        with tabs[5]:
            st.markdown("### 📦 Deleted Cases Recycle Bin & Archive (Auto-Backup)")
            df_arch = pd.read_sql_query("SELECT archive_id AS 'Archive ID', original_case_id AS 'Original Case ID', control_no AS 'Household ID', client_name AS 'Client Name', requested_by AS 'Requested By', deletion_reason AS 'Reason', deleted_by AS 'Approved By', archived_at AS 'Date Deleted' FROM deleted_cases_archive ORDER BY archive_id DESC", conn)
            
            if not df_arch.empty:
                st.dataframe(df_arch, use_container_width=True)
                
                st.divider()
                st.markdown("#### 🔄 Restore Accidental Deletion")
                arch_options = {f"Archive #{r['Archive ID']} - {r['Client Name']} (HHID: {r['Household ID']})": r['Archive ID'] for _, r in df_arch.iterrows()}
                selected_arch_id = st.selectbox("Select Deleted Record to Restore:", list(arch_options.keys()))
                
                if st.button("🔄 Restore Selected Record to Active Database", use_container_width=True):
                    arch_id = arch_options[selected_arch_id]
                    c.execute("SELECT raw_case_data_json FROM deleted_cases_archive WHERE archive_id = ?", (arch_id,))
                    res_json = c.fetchone()
                    if res_json and res_json[0]:
                        df_res = pd.read_json(res_json[0], orient="records")
                        if not df_res.empty:
                            row_dict = df_res.iloc[0].to_dict()
                            del row_dict['id']
                            
                            cols = list(row_dict.keys())
                            vals = list(row_dict.values())
                            placeholders = ", ".join(["?"] * len(cols))
                            col_names = ", ".join(cols)
                            
                            c.execute(f"INSERT INTO cases ({col_names}) VALUES ({placeholders})", vals)
                            c.execute("DELETE FROM deleted_cases_archive WHERE archive_id = ?", (arch_id,))
                            conn.commit()
                            st.success("✅ Record restored successfully back to active cases masterlist!")
                            st.rerun()
            else:
                st.info("No archived deleted records found.")

# ==========================================
# USER MANAGEMENT MODULE
# ==========================================
elif menu_selection == "👥 User Management" and user_role == "Superuser":
    st.subheader("👥 Superuser Panel: User Account Management")
    if "generated_pass" not in st.session_state:
        st.session_state["generated_pass"] = generate_random_password()

    col_user_a, col_user_b = st.columns(2)
    with col_user_a:
        st.markdown("##### ➕ Register New System User")
        with st.form("create_user_form", clear_on_submit=True):
            u_fname = st.text_input("First Name*")
            u_lname = st.text_input("Last Name / Family Name*")
            u_role = st.selectbox("Type of User (Role)", ["User", "Team Leader", "Admin", "Superuser"])
            u_province = st.selectbox("Province Jurisdiction", PROVINCES_LIST)
            u_email = st.text_input("User Email Address*")
            
            st.text_input("Generated Temporary Password:", value=st.session_state["generated_pass"], disabled=True)
            send_via_email = st.checkbox("📧 Send Credentials via Direct Email to User", value=True)
            
            submit_user = st.form_submit_button("➕ Register User", use_container_width=True)
            if submit_user:
                if u_fname and u_lname and u_email:
                    try:
                        c.execute("INSERT INTO user_accounts (first_name, last_name, province, user_role, email, password, require_change_pass) VALUES (?, ?, ?, ?, ?, ?, 1)", (u_fname, u_lname, u_province, u_role, u_email.strip(), st.session_state["generated_pass"]))
                        conn.commit()
                        st.success(f"✅ Registered user: {u_fname} {u_lname}!")
                        
                        if send_via_email:
                            sent_ok, msg_res = send_credentials_email(u_email.strip(), f"{u_fname} {u_lname}", st.session_state["generated_pass"])
                            if sent_ok:
                                st.success("📩 Account credentials emailed directly to user!")
                            else:
                                st.info(f"ℹ️ User saved locally. Note: {msg_res}")
                                
                        st.session_state["generated_pass"] = generate_random_password()
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("⚠️ Email address already registered!")

    with col_user_b:
        st.markdown("##### 🔑 Reset User Password (with Live Search)")
        user_search_term = st.text_input("🔍 Search User Name or Email:")
        
        query_u = "SELECT id, first_name, last_name, email FROM user_accounts WHERE user_role != 'Superuser'"
        params_u = []
        if user_search_term:
            query_u += " AND (lower(first_name) LIKE lower(?) OR lower(last_name) LIKE lower(?) OR lower(email) LIKE lower(?))"
            st_param = f"%{user_search_term.strip()}%"
            params_u.extend([st_param, st_param, st_param])
            
        c.execute(query_u, params_u)
        u_list = c.fetchall()
        
        if u_list:
            u_dict = {f"{r[1]} {r[2]} ({r[3]})": (r[0], r[3], f"{r[1]} {r[2]}") for r in u_list}
            selected_reset_user = st.selectbox("Select Filtered User Account:", list(u_dict.keys()))
            send_reset_via_email = st.checkbox("📧 Email New Password Directly to User", value=True, key="reset_mail_chk")
            
            if st.button("🔄 Reset Password Now", use_container_width=True):
                res_id, res_email, res_full_name = u_dict[selected_reset_user]
                new_temp_pass = generate_random_password()
                c.execute("UPDATE user_accounts SET password = ?, require_change_pass = 1 WHERE id = ?", (new_temp_pass, res_id))
                conn.commit()
                st.success(f"✅ New Temporary Password for {res_email}: `{new_temp_pass}`")
                
                if send_reset_via_email:
                    sent_ok, msg_res = send_credentials_email(res_email, res_full_name, new_temp_pass)
                    if sent_ok:
                        st.success("📩 Reset password emailed directly to user!")
                    else:
                        st.info(f"ℹ️ Password reset locally. Note: {msg_res}")
        else:
            st.warning("No users match your search criteria.")

    st.divider()
    df_users = pd.read_sql_query("SELECT id, first_name || ' ' || last_name AS Name, email AS Email, user_role AS Role, province AS Province FROM user_accounts", conn)
    st.dataframe(df_users, use_container_width=True, hide_index=True)
