import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
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
    .dialect-box {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DATA PRIVACY ACT (RA 10173) POP-UP MODAL
# ==========================================
if "privacy_accepted" not in st.session_state:
    st.session_state["privacy_accepted"] = False

if hasattr(st, "dialog"):
    @st.dialog("🔒 DATA PRIVACY ACT COMPLIANCE REMINDER (RA 10173)")
    def privacy_modal():
        st.markdown("""
        **DSWD FIELD OFFICE X • PDBBM SCMS BENEFICIARY MANAGEMENT SYSTEM**
        
        Pursuant to **Republic Act No. 10173 (Data Privacy Act of 2012)**:
        
        1. **Official Use Only:** All beneficiary information, profiling records, and family data processed in this portal strictly adhere to RA 10173 confidentiality standards.
        2. **Confidentiality Notice:** Unlawful extraction, downloading, or unauthorized sharing of personal records is strictly prohibited.
        3. **Security Standards:** All system interactions and encoding sessions are timestamped and logged for audit compliance.
        """)
        st.divider()
        if st.button("✅ I Agree & Proceed to System", use_container_width=True):
            st.session_state["privacy_accepted"] = True
            st.rerun()

    if not st.session_state["privacy_accepted"]:
        privacy_modal()

# ==========================================
# 2. EMAIL SENDER HELPER
# ==========================================
def send_credentials_email(recipient_email, recipient_name, temp_password, user_role="User"):
    sender_email = "lbidulsa.fo10@dswd.gov.ph"
    sender_password = "rkgqurmorpvfgktq"
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"DSWD FO X PDBBM SCMS Portal <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = "🔒 Official Account Credentials - PDBBM SCMS Portal"
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #1F4E78; border-radius: 8px;">
              <h2 style="color: #1F4E78; text-align: center;">🕊️ DSWD Field Office X - PDBBM SCMS Portal</h2>
              <hr style="border: 0; border-top: 1px solid #1F4E78;">
              <p>Dear <b>{recipient_name}</b>,</p>
              <p>Your official user account for the <b>PDBBM SCMS Beneficiary Management System</b> has been successfully configured.</p>
              
              <div style="background-color: #F4F6F9; padding: 15px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #1F4E78;">
                <p style="margin: 5px 0;"><b>Login Email:</b> <code style="font-size: 1.1em; color: #1F4E78;">{recipient_email}</code></p>
                <p style="margin: 5px 0;"><b>Assigned Role:</b> {user_role}</p>
                <p style="margin: 5px 0;"><b>Temporary Password:</b> <code style="font-size: 1.2em; color: #C53030; font-weight: bold;">{temp_password}</code></p>
              </div>

              <p><b>Security Notice:</b> Please login to the PDBBM SCMS Portal and change your temporary password upon first system access.</p>
              <br>
              <p style="font-size: 0.85em; color: #6c757d; text-align: center;">
                <i>This is an automated system dispatch. Please do not reply directly to this email.</i><br>
                <b>DSWD FO X Peace & Development Program © 2026</b>
              </p>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

# ==========================================
# 3. DATABASE CONNECTION ENGINE
# ==========================================
DEFAULT_DB_URL = "postgresql+psycopg2://postgres.oxyvjstdncnnefbkilaa:5GLJZg5tWE28Wud9@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

@st.cache_resource
def get_db_engine():
    try:
        db_url = st.secrets.get("SUPABASE_URL", DEFAULT_DB_URL)
    except Exception:
        db_url = DEFAULT_DB_URL
    return create_engine(db_url, pool_pre_ping=True)

engine = get_db_engine()

def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

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
    if not date_str or str(date_str) == "None":
        return default_date
    try:
        return datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
    except Exception:
        try:
            return datetime.strptime(str(date_str).strip(), "%m-%d-%Y").date()
        except Exception:
            return default_date

DIALECTS_LIST_1 = ["English", "Tagalog", "Bikol", "Cebuano", "Hiligaynon", "Ilokano", "Kagan", "Pampango", "Iranun"]
DIALECTS_LIST_2 = ["Pangasinense", "Waray", "Chavacano", "Maranao", "Mindanaoan", "Tausūg", "Yakan"]

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
        
        with st.form("login_form", clear_on_submit=False):
            login_email = st.text_input("User Email Address")
            login_pass = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("🔒 Login to System", use_container_width=True)
            
            if login_submitted:
                try:
                    with engine.connect() as conn:
                        user_res = conn.execute(
                            text("SELECT first_name, last_name, province, user_role, email, require_change_pass FROM user_accounts WHERE lower(email) = lower(:e) AND password = :p"),
                            {"e": login_email.strip(), "p": login_pass.strip()}
                        ).fetchone()
                except Exception:
                    user_res = None
                
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
# MANDATORY FIRST-LOGIN PASSWORD CHANGE MODAL
# ==========================================
if st.session_state.get("user_info", {}).get("must_change_pass"):
    if hasattr(st, "dialog"):
        @st.dialog("🔑 MANDATORY PASSWORD CHANGE REQUIRED")
        def mandatory_change_password_modal():
            st.warning("⚠️ You are currently using a temporary password. Please configure your new custom password to proceed.")
            with st.form("must_change_pass_form_scms"):
                new_p1 = st.text_input("New Password*", type="password")
                new_p2 = st.text_input("Confirm New Password*", type="password")
                submit_chg = st.form_submit_button("💾 Save & Proceed to System", use_container_width=True)
                
                if submit_chg:
                    if new_p1 and new_p1 == new_p2:
                        u_email_curr = st.session_state["user_info"]["email"]
                        with engine.begin() as conn:
                            conn.execute(
                                text("UPDATE user_accounts SET password = :p, require_change_pass = 0 WHERE lower(email) = lower(:e)"),
                                {"p": new_p1, "e": u_email_curr}
                            )
                        st.session_state["user_info"]["must_change_pass"] = False
                        st.success("✅ Password changed successfully!")
                        st.rerun()
                    else:
                        st.error("⚠️ Passwords do not match or field is empty.")
        mandatory_change_password_modal()
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
    try:
        if user_role in ["Superuser", "Admin"]:
            query = text("SELECT id, client_id, control_no, last_name, first_name, province, staff_email, profile_status FROM cases ORDER BY id DESC")
            df_c = pd.read_sql_query(query, engine)
        elif user_role == "Team Leader":
            query = text("SELECT id, client_id, control_no, last_name, first_name, province, staff_email, profile_status FROM cases WHERE lower(province) = lower(:p) ORDER BY id DESC")
            df_c = pd.read_sql_query(query, engine, params={"p": user_province})
        else:
            query = text("SELECT id, client_id, control_no, last_name, first_name, province, staff_email, profile_status FROM cases WHERE lower(staff_email) = lower(:e) OR lower(encoded_by) = lower(:e) ORDER BY id DESC")
            df_c = pd.read_sql_query(query, engine, params={"e": user_email})
    except Exception:
        if user_role in ["Superuser", "Admin"]:
            query = text("SELECT id, client_id, control_no, last_name, first_name, province, staff_email FROM cases ORDER BY id DESC")
            df_c = pd.read_sql_query(query, engine)
        elif user_role == "Team Leader":
            query = text("SELECT id, client_id, control_no, last_name, first_name, province, staff_email FROM cases WHERE lower(province) = lower(:p) ORDER BY id DESC")
            df_c = pd.read_sql_query(query, engine, params={"p": user_province})
        else:
            query = text("SELECT id, client_id, control_no, last_name, first_name, province, staff_email FROM cases WHERE lower(staff_email) = lower(:e) OR lower(encoded_by) = lower(:e) ORDER BY id DESC")
            df_c = pd.read_sql_query(query, engine, params={"e": user_email})
        
    if not df_c.empty:
        res = {}
        for _, row in df_c.iterrows():
            st_icon = "🟢" if str(row.get('profile_status', '')).lower() == 'completed' else "🟡"
            lbl = f"{st_icon} ID #{row['id']} [HHID: {row['control_no'] or 'N/A'}]: {row['first_name']} {row['last_name']} ({row['province']})"
            res[lbl] = row['id']
        return res
    return {}

def get_client_record(case_id):
    if not case_id:
        return {}
    try:
        df = pd.read_sql_query(text("SELECT * FROM cases WHERE id = :id"), engine, params={"id": case_id})
        if not df.empty:
            return df.iloc[0].to_dict()
    except Exception:
        pass
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
    
    try:
        df_my_cnt = pd.read_sql_query(text("SELECT id FROM cases WHERE lower(encoded_by) = lower(:e) OR lower(staff_email) = lower(:e)"), engine, params={"e": user_email})
        cnt_val = len(df_my_cnt)
    except Exception:
        cnt_val = 0
    st.info(f"📝 **Your Encoded Entries:** {cnt_val} Beneficiaries")

    if user_role in ["Superuser", "Admin"]:
        try:
            with engine.connect() as conn:
                pending_del_cnt = conn.execute(text("SELECT COUNT(*) FROM deletion_requests WHERE status = 'PENDING'")).fetchone()[0]
            if pending_del_cnt > 0:
                st.error(f"🔔 **Deletion Requests:** {pending_del_cnt} Pending")
        except Exception:
            pass

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["user_info"] = {}
        st.rerun()

    with st.expander("🔑 Change My Password"):
        with st.form("self_change_pass_scms"):
            old_p = st.text_input("Current Password*", type="password")
            new_p1 = st.text_input("New Password*", type="password")
            new_p2 = st.text_input("Confirm New Password*", type="password")
            if st.form_submit_button("Update Password", use_container_width=True):
                if new_p1 == new_p2 and new_p1 != "":
                    with engine.connect() as conn:
                        res_p = conn.execute(text("SELECT password FROM user_accounts WHERE lower(email) = lower(:e)"), {"e": user_email}).fetchone()
                    if res_p and res_p[0] == old_p:
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE user_accounts SET password = :p, require_change_pass = 0 WHERE lower(email) = lower(:e)"), {"p": new_p1, "e": user_email})
                        st.toast("✅ Password updated successfully!", icon="🔑")
                        st.success("✅ Password successfully updated!")
                    else:
                        st.error("❌ Incorrect current password.")
                else:
                    st.error("⚠️ Passwords do not match or empty.")
        
    st.divider()
    menu_selection = st.radio("Navigation Menu:", menu_options_list, index=default_menu_idx)

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
    
    try:
        if user_role in ["Superuser", "Admin"]:
            df_all_cases = pd.read_sql_query(text("SELECT * FROM cases"), engine)
        elif user_role == "Team Leader":
            df_all_cases = pd.read_sql_query(text("SELECT * FROM cases WHERE lower(province) = lower(:p)"), engine, params={"p": user_province})
        else:
            df_all_cases = pd.read_sql_query(text("SELECT * FROM cases WHERE lower(staff_email) = lower(:e) OR lower(encoded_by) = lower(:e)"), engine, params={"e": user_email})
    except Exception:
        df_all_cases = pd.DataFrame()
    
    total_beneficiaries = len(df_all_cases)
    
    male_cnt = 0
    female_cnt = 0
    if not df_all_cases.empty and 'sex' in df_all_cases.columns:
        male_cnt = len(df_all_cases[df_all_cases['sex'].astype(str).str.lower() == 'male'])
        female_cnt = len(df_all_cases[df_all_cases['sex'].astype(str).str.lower() == 'female'])

    if not df_all_cases.empty and 'profile_status' in df_all_cases.columns:
        completed_cnt = len(df_all_cases[df_all_cases['profile_status'].astype(str).str.lower() == 'completed'])
        incomplete_cnt = total_beneficiaries - completed_cnt
    else:
        completed_cnt = 0
        incomplete_cnt = total_beneficiaries

    col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5, col_kpi6 = st.columns(6)
    with col_kpi1:
        st.metric("Total Beneficiaries", total_beneficiaries)
    with col_kpi2:
        st.metric("👨 Male Clients", male_cnt)
    with col_kpi3:
        st.metric("👩 Female Clients", female_cnt)
    with col_kpi4:
        st.metric("🟢 Completed Profiles", completed_cnt)
    with col_kpi5:
        st.metric("🟡 Incomplete / Drafts", incomplete_cnt)
    with col_kpi6:
        st.metric("Active Field Staff", len(df_all_cases['staff_email'].dropna().unique()) if not df_all_cases.empty and 'staff_email' in df_all_cases.columns else 0)

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
        if not df_all_cases.empty and 'province' in df_all_cases.columns and 'staff_email' in df_all_cases.columns:
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

    control_no_val = st.text_input("TFDCC Household ID No.* / DC Serial Number (for MILF):", value=str(c_data.get("control_no", "") or c_data.get("dc_serial_no", "") or ""))

    if control_no_val.strip() != "":
        current_id = c_data.get("id", 0)
        try:
            with engine.connect() as conn:
                dup = conn.execute(
                    text("SELECT id, first_name, last_name, staff_email FROM cases WHERE lower(control_no) = lower(:c) AND id != :id"),
                    {"c": control_no_val.strip(), "id": current_id}
                ).fetchone()
            if dup:
                st.error(f"⚠️ **DUPLICATE DETECTED:** TFDCC Household ID No. '{control_no_val}' is already registered in the system under **{dup[1]} {dup[2]}** (Encoded by: {dup[3]}). Please verify before saving!")
        except Exception:
            pass

    with st.form("personal_info_form"):
        col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 2, 2])
        with col_hdr1:
            gis_date_picker = st.date_input("Date:", value=parse_date_str(c_data.get("gis_date"), datetime.today().date()))
        with col_hdr2:
            crn_number = st.text_input("Combatant Reference Number (CRN) / Client ID:", value=str(c_data.get("crn_number", "") or c_data.get("client_id", "") or ""))
        with col_hdr3:
            # AUTOMATIC ENCODING COMPLETION STATUS (Computed Read-Only Field)
            sw_assessment_val = str(c_data.get("sw_assessment", "") or "").strip()
            curr_prof_st = "Completed" if sw_assessment_val != "" else "Incomplete / Draft"
            profile_status = st.text_input("📌 Encoding Completion Status (Auto-Computed):", value=curr_prof_st, disabled=True)

        st.markdown("##### 🎖️ INVOLVEMENT (Pakikilahok)")
        col_inv1, col_inv2, col_inv3 = st.columns(3)
        with col_inv1:
            affiliated_group = st.selectbox("Affiliated Group/Organization*", ["MILF", "MNLF", "KAPATIRAN (RPMP-RPA-ABB)", "CPP/NPA/NDF", "CPLA (Cordillera People's Liberation Army)", "Private Armed Group", "FVE", "None"], index=0)
            fve_specify = st.text_input("FVE (pls specify):", value=str(c_data.get("fve_specify", "") or ""))
            pag_specify = st.text_input("Private Armed Group (pls specify):", value=str(c_data.get("pag_specify", "") or ""))
        with col_inv2:
            vot_status = st.selectbox("Victim of Terrorism (VoT)", ["No", "Yes"], index=0)
            ciac_status = st.selectbox("Child Involved in Armed Conflict (CIAC)", ["No", "Yes"], index=0)
        with col_inv3:
            rank_role = st.text_input("Rank / Role within Group:", value=str(c_data.get("rank_role", "") or ""))
            duration_involvement = st.text_input("Duration of Involvement:", value=str(c_data.get("duration_involvement", "") or ""))

        col_act1, col_act2 = st.columns(2)
        with col_act1:
            locations_activities = st.text_input("Locations Where Activities Took Place:", value=str(c_data.get("locations_activities", "") or ""))
        with col_act2:
            types_activities = st.text_input("Types of Activities Involved:", value=str(c_data.get("types_activities", "") or ""))

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
            purok = st.text_input("Purok/Street/House No.", value=str(c_data.get("purok", "") or ""))
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
            marriage_details = st.selectbox("Marriage Details (if Married)", ["N/A", "Monogamous (isang asawa lang)", "Polygamous (higit isang asawa)"], index=0)
            num_wives = st.number_input("How many wives (if Polygamous)?", min_value=0, max_value=10, value=int(c_data.get("num_wives", 0) or 0))
            wife_order = st.selectbox("For Married Female Combatants:", ["N/A", "First Wife", "Second Wife", "Third Wife", "Fourth Wife and up"], index=0)

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
            education_type = st.selectbox("Education Type:", ["Public", "Private", "Formal", "Non-Formal", "Religious (Madrasa/Seminarian/etc.)", "Informal"], index=0)
            school_name_dates = st.text_input("Name of Educational Institution & Dates:", value=str(c_data.get("school_name_dates", "") or ""))
            education_level = st.selectbox("Educational Level Attained:", ["Primary", "Secondary", "Tertiary", "Post-Graduate", "N/A"], index=0)
            occupation_before = st.text_input("Occupation Before Involvement:", value=str(c_data.get("occupation_before", "") or ""))
            current_occupation = st.text_input("Current Occupation (After Disengagement):", value=str(c_data.get("current_occupation", "") or ""))
        with col_b3:
            motivations_joining = st.text_area("Motivations for Joining:", value=str(c_data.get("motivations_joining", "") or ""))
            reasons_leaving = st.text_area("Events Leading to Disengagement:", value=str(c_data.get("reasons_leaving", "") or ""))
            intentions_motivations = st.text_area("Current Intentions & Motivations:", value=str(c_data.get("intentions_motivations", "") or ""))

        # =========================================================
        # DIALECTS CHECKBOX MATRIX (GIS FORM COMPLIANT)
        # =========================================================
        st.divider()
        st.markdown("##### 🗣️ What dialect are you able to? (Anong diyalekto ang iyong alam gamitin?)")
        
        saved_dialects_str = str(c_data.get("dialects_spoken", "") or "")
        dialect_selections = {}
        grid_col1, grid_col2 = st.columns(2)
        
        with grid_col1:
            st.markdown("**List of Dialects (Group 1)** | **SPEAK** | **READ** | **WRITE**")
            for d_name in DIALECTS_LIST_1:
                dc1, dc2, dc3, dc4 = st.columns([3, 2, 2, 2])
                with dc1:
                    st.write(f"**{d_name}**")
                with dc2:
                    spk = st.checkbox("Speak", value=(f"{d_name}_SPEAK" in saved_dialects_str or f"{d_name}" in saved_dialects_str), key=f"chk_spk_{d_name}")
                with dc3:
                    rd = st.checkbox("Read", value=(f"{d_name}_READ" in saved_dialects_str), key=f"chk_rd_{d_name}")
                with dc4:
                    wrt = st.checkbox("Write", value=(f"{d_name}_WRITE" in saved_dialects_str), key=f"chk_wrt_{d_name}")
                dialect_selections[d_name] = {"speak": spk, "read": rd, "write": wrt}

        with grid_col2:
            st.markdown("**List of Dialects (Group 2)** | **SPEAK** | **READ** | **WRITE**")
            for d_name in DIALECTS_LIST_2:
                dc1, dc2, dc3, dc4 = st.columns([3, 2, 2, 2])
                with dc1:
                    st.write(f"**{d_name}**")
                with dc2:
                    spk = st.checkbox("Speak", value=(f"{d_name}_SPEAK" in saved_dialects_str), key=f"chk_spk_{d_name}")
                with dc3:
                    rd = st.checkbox("Read", value=(f"{d_name}_READ" in saved_dialects_str), key=f"chk_rd_{d_name}")
                with dc4:
                    wrt = st.checkbox("Write", value=(f"{d_name}_WRITE" in saved_dialects_str), key=f"chk_wrt_{d_name}")
                dialect_selections[d_name] = {"speak": spk, "read": rd, "write": wrt}

        st.divider()
        st.markdown("##### 🛡️ Social Protection Certificates & PhilHealth")
        col_sp1, col_sp2, col_sp3 = st.columns(3)
        with col_sp1:
            birth_cert_status = st.selectbox("Birth Certificate Status:", ["Yes", "No"], index=0)
            birth_cert_auth = st.selectbox("Birth Cert Authenticated (PSA)?", ["Yes", "No"], index=0)
            birth_cert_registry = st.text_input("Birth Cert Date & Place of Registry:", value=str(c_data.get("birth_cert_registry", "") or ""))
        with col_sp2:
            marriage_cert_status = st.selectbox("Marriage Certificate Status:", ["Yes", "No", "N/A"], index=0)
            marriage_cert_auth = st.selectbox("Marriage Cert Authenticated?", ["Yes", "No", "N/A"], index=0)
            philhealth_status = st.selectbox("PhilHealth Member Status:", ["Yes (Active)", "Yes (Inactive)", "No"], index=0)
        with col_sp3:
            philhealth_id = st.text_input("PhilHealth Number:", value=str(c_data.get("philhealth_id", "") or ""))
            philhealth_category = st.selectbox("PhilHealth Category:", ["Direct Contributor", "Indirect Contributor", "Formal Economy", "Informal Economy", "OFW", "Domestic Workers", "Lifetime Members", "Sponsored Members", "Senior Citizen", "Indigent", "Group Enrollment", "4Ps Member"], index=0)

        submit_t1 = st.form_submit_button("💾 Save / Update Personal Record", use_container_width=True)
        if submit_t1:
            birthdate_str = bday_picker.strftime('%Y-%m-%d')
            gis_date_str = gis_date_picker.strftime('%m-%d-%Y')
            
            formatted_dialects_list = []
            for d_key, d_vals in dialect_selections.items():
                abilities = []
                if d_vals["speak"]: abilities.append("SPEAK")
                if d_vals["read"]: abilities.append("READ")
                if d_vals["write"]: abilities.append("WRITE")
                if abilities:
                    formatted_dialects_list.append(f"{d_key} ({', '.join(abilities)})")
            
            dialects_spoken = "; ".join(formatted_dialects_list) if formatted_dialects_list else "None"

            if not last_name or not first_name or not control_no_val.strip():
                st.error("⚠️ **REQUIRED FIELDS MISSING:** Palihug sulati ang Household ID No., First Name, ug Last Name!")
            else:
                params_save = {
                    "control_no": control_no_val.strip(), "dc_serial_no": control_no_val.strip(), "gis_date": gis_date_str, "client_id": crn_number,
                    "last_name": last_name.strip(), "first_name": first_name.strip(), "middle_name": middle_name,
                    "ext_name": ext_name, "alias": alias, "phone_no": phone_no, "birthdate": birthdate_str,
                    "age": age, "sex": sex, "civil_status": civil_status, "crn_number": crn_number,
                    "vot_status": vot_status, "ciac_status": ciac_status, "marriage_details": marriage_details,
                    "num_wives": num_wives, "wife_order": wife_order, "affiliated_group": affiliated_group,
                    "fve_specify": fve_specify, "pag_specify": pag_specify, "rank_role": rank_role,
                    "duration_involvement": duration_involvement, "locations_activities": locations_activities, "types_activities": types_activities,
                    "purok": purok, "barangay": barangay, "city_muni": city_muni, "province": province, "region": region, "place_of_birth": place_of_birth,
                    "ethnicity": ethnicity, "place_of_integration": place_of_integration, "physical_disability": physical_disability,
                    "health_conditions_maint": health_conditions_maint, "education_type": education_type, "school_name_dates": school_name_dates,
                    "education_level": education_level, "occupation_before": occupation_before, "current_occupation": current_occupation,
                    "motivations_joining": motivations_joining, "reasons_leaving": reasons_leaving, "intentions_motivations": intentions_motivations,
                    "dialects_spoken": dialects_spoken, "birth_cert_status": birth_cert_status, "birth_cert_registry": birth_cert_registry,
                    "marriage_cert_status": marriage_cert_status, "philhealth_status": philhealth_status, "philhealth_id": philhealth_id,
                    "philhealth_category": philhealth_category, "profile_status": curr_prof_st, "staff_email": user_email, "encoded_by": user_email
                }
                
                try:
                    if selected_option == "-- ADD NEW BENEFICIARY --" and not c_data.get("id"):
                        cols = ", ".join(params_save.keys())
                        vals = ", ".join([f":{k}" for k in params_save.keys()])
                        with engine.begin() as conn:
                            conn.execute(text(f"INSERT INTO cases ({cols}) VALUES ({vals})"), params_save)
                    else:
                        edit_id = c_data.get("id", selected_id)
                        params_save["edit_id"] = edit_id
                        set_clause = ", ".join([f"{k}=:{k}" for k in params_save.keys() if k != "edit_id" and k != "encoded_by"])
                        with engine.begin() as conn:
                            conn.execute(text(f"UPDATE cases SET {set_clause} WHERE id=:edit_id"), params_save)
                    
                    st.toast("✅ Beneficiary record saved successfully to Supabase!", icon="🎉")
                    st.success("✅ Beneficiary record updated successfully!")
                    st.session_state["autofill_data"] = {}
                except Exception as ex:
                    st.error(f"❌ DATABASE ERROR: {ex}")
