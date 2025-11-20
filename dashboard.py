import streamlit as st
import pandas as pd
import requests 
from datetime import datetime

# --- Configuration ---
# Point this to your running FastAPI instance
FASTAPI_BASE_URL = "http://localhost:8000"

# Set the page configuration
st.set_page_config(
    page_title="Lease Lightning Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FastAPI API Call Functions ---
# Use Streamlit's cache to reduce unnecessary calls to the API
@st.cache_data(ttl=3) 
def fetch_applicants():
    """Fetches the list of all applicants from the FastAPI backend."""
    try:
        # FastAPI endpoint defined in backend/api.py
        response = requests.get(f"{FASTAPI_BASE_URL}/applicants/")
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to FastAPI backend. Ensure Uvicorn is running on port 8000.")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return []

def send_action_to_api(endpoint, payload=None):
    """Sends action requests (CRUD/Approve) to the backend."""
    try:
        # Ensure payload is sent as JSON
        if payload:
            response = requests.post(f"{FASTAPI_BASE_URL}{endpoint}", json=payload)
        else:
            response = requests.post(f"{FASTAPI_BASE_URL}{endpoint}")
            
        response.raise_for_status()
        st.success(response.json().get("message", "Action successful."))
        st.cache_data.clear() # Clear cache to force a refresh
        time.sleep(1) # Wait slightly for the message to be seen before rerunning
        st.rerun()
    except requests.exceptions.RequestException as e:
        error_detail = e.response.json().get("detail", "Unknown error") if e.response is not None else str(e)
        st.error(f"API Error: {error_detail}")

# --- Streamlit Wrapper Functions (calling API) ---

def add_applicant(name, unit):
    send_action_to_api("/applicants/add", payload={"name": name, "unit": unit})

def update_applicant(app_id, new_status, new_risk):
    send_action_to_api(f"/applicants/update/{app_id}", payload={"status": new_status, "risk": new_risk})

def delete_applicant(app_id):
    send_action_to_api(f"/applicants/delete/{app_id}")

def approve_applicant(app_id):
    send_action_to_api(f"/applicants/approve/{app_id}")


# --- Sidebar Navigation and Metrics ---
with st.sidebar:
    st.title("⚡ Lease Lightning")
    st.markdown("---")
    
    # Navigation state
    view = st.radio("Current View", ["Applicant Pipeline", "Manage Applicants (CRUD)", "Lease Renewal Tracker", "Audit Log"], index=0)
    
    st.markdown("---")
    st.header("Quick Metrics")
    
    applicants = fetch_applicants() # Fetches data from FastAPI

    # Calculate derived metrics
    total_applications = len(applicants)
    ready_for_review = sum(1 for app in applicants if app['status'] == 'Decision Ready')
    denied = sum(1 for app in applicants if app['status'] in ['Denied', 'Denied/Overridden'])
    
    st.metric(label="Total Applications", value=total_applications)
    st.metric(label="Ready for Approval (GenAI Reviewed)", value=ready_for_review)
    st.metric(label="Vacancy Loss Reduction (Mo.)", value="$4,500", delta="+$500 Mo.")
    
# --- Main Dashboard Content Rendering ---

if view == "Applicant Pipeline":
    st.header("Property Manager Dashboard: Applicant Pipeline")
    st.markdown("Track applicants in real-time through the multi-agent screening workflow.")

    # Create columns for high-level status count
    col1, col2, col3, col4 = st.columns(4)
    col1.info(f"**{ready_for_review}** Ready for Approval")
    col2.warning(f"**{sum(1 for app in applicants if app['status'] == 'Verification Agent')}** In Verification")
    col3.success(f"**{sum(1 for app in applicants if app['status'] == 'Document Agent')}** Lease Generated (E-Sign)")
    col4.error(f"**{denied}** Denied")

    st.markdown("---")
    st.subheader("Applicant Flow Table")

    # Display the main pipeline table
    df = pd.DataFrame(applicants)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Human-in-the-Loop Approval Gate (Key MVP Functionality) ---

    st.markdown("---")
    st.subheader("Mandatory Human Approval Gate")

    # Filter for applicants ready for approval (Decision Ready)
    approval_candidates = [app for app in applicants if app['status'] == 'Decision Ready']

    if approval_candidates:
        ready_applicant = approval_candidates[0] # Focus on the first applicant ready for review
        
        st.markdown(f"**Applicant Ready for Review:** **{ready_applicant['name']}** (Unit {ready_applicant['unit']})")

        # Display key Decision Engine outputs
        st.markdown("##### 🧠 AI Decision Engine Report Summary:")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("AI Risk Score", f"**{ready_applicant['risk']}**", "Objective/Standardized")
        col_b.metric("Verified Income Match", ready_applicant['income_match'], "Verification Agent Output")
        col_c.metric("Lease Error Rate", ready_applicant['error_rate'], "Document Agent Target")

        # Mock the Lease Preview and Approval Buttons
        st.text_area("Lease Document Preview (Mock Output):", 
                     "This is a placeholder for the dynamically generated lease with customized clauses and zero data entry errors, ready for E-Signature. The AI has confirmed all local compliance requirements.", 
                     height=100)

        # Human-in-the-Loop buttons
        col_btn1, col_btn2 = st.columns([1, 4])
        if col_btn1.button("✅ Final Approve & Send Lease", key="approve_btn", type="primary"):
            approve_applicant(ready_applicant['id'])
            st.balloons()
        
        if col_btn2.button("🚫 Override Deny & Log Reason", key="deny_btn"):
            update_applicant(ready_applicant['id'], 'Denied/Overridden', ready_applicant['risk'])


    else:
        st.info("No applications currently in the 'Decision Ready' stage. The AI Agents are processing other applications.")


# --- New CRUD Management Page ---

elif view == "Manage Applicants (CRUD)":
    st.header("🛠️ Applicant Data Management")
    st.warning("Manual editing of records is intended for testing, compliance audits, or data correction only.")
    
    # 1. ADD NEW APPLICANT
    st.subheader("➕ Add New Applicant (Manual Entry)")
    with st.form("add_form", clear_on_submit=True):
        col_add1, col_add2 = st.columns(2)
        new_name = col_add1.text_input("Applicant Name")
        new_unit = col_add2.text_input("Unit Applied For")
        submitted = st.form_submit_button("Add Applicant")
        
        if submitted and new_name and new_unit:
            add_applicant(new_name, new_unit)

    st.markdown("---")

    # 2. UPDATE APPLICANT STATUS/RISK
    st.subheader("✏️ Update Applicant Status")
    with st.form("update_form"):
        col_up1, col_up2, col_up3 = st.columns(3)
        
        app_ids = [app['id'] for app in applicants]
        
        if not app_ids:
            st.info("No applicants to update.")
            # Use st.stop() to prevent errors if no applicants exist
            
        update_id = col_up1.selectbox("Select Applicant ID to Update", app_ids) if app_ids else None
        
        # Ensure we only try to look up current_app if update_id is not None
        current_app = next((app for app in applicants if app['id'] == update_id), {}) if update_id else {}
        
        # Helper list for status select box
        status_options = ["Submitted/Manual", "Verification Agent", "Decision Ready", "Document Agent", "Approved/Leased", "Denied", "Denied/Overridden"]
        current_status_index = status_options.index(current_app.get('status', "Submitted/Manual"))
        new_status = col_up2.selectbox("New Status", status_options, index=current_status_index)
        
        # Helper list for risk select box
        risk_options = ["Pending", "Low", "Medium", "High"]
        current_risk_index = risk_options.index(current_app.get('risk', "Pending"))
        new_risk = col_up3.selectbox("New Risk Score", risk_options, index=current_risk_index)
        
        update_submitted = st.form_submit_button("Update Record")
        
        if update_submitted and update_id:
            update_applicant(update_id, new_status, new_risk)

    st.markdown("---")

    # 3. DELETE APPLICANT
    st.subheader("🗑️ Delete Applicant")
    with st.form("delete_form"):
        col_del1, col_del2 = st.columns([2, 1])
        delete_id = col_del1.selectbox("Select Applicant ID to Delete", app_ids, key="delete_select") if app_ids else None
        
        st.warning(f"Are you sure you want to permanently delete record for ID: {delete_id}?")
        
        delete_submitted = col_del2.form_submit_button("Confirm Delete", type="primary")
        
        if delete_submitted and delete_id:
            delete_applicant(delete_id)

    st.markdown("---")
    st.subheader("Current Data Table")
    st.dataframe(pd.DataFrame(applicants), use_container_width=True, hide_index=True)


# --- Other Views (Placeholders) ---
elif view == "Lease Renewal Tracker":
    st.header("📅 Lease Renewal Tracker (Future Feature)")
    st.info("This agent will proactively track leases expiring in the next 90 days and initiate renewal outreach.")
    st.code("Query database for leases expiring between (today) and (today + 90 days) ORDER BY expiration_date", language="sql")
    
elif view == "Audit Log":
    st.header("🔒 Compliance Audit Log (Future Feature)")
    st.info("This view provides an immutable log of all AI decisions and human overrides for fair housing compliance.")
    st.table(pd.DataFrame({"Timestamp": [datetime.now()], "Event": ["AI Decision: Approved ID 1001"], "Reason": ["Income >= 3x rent"]}))


st.markdown("---")
st.caption("Powered by Lease Lightning Multi-Agent GenAI Pipeline. System Uptime: 99.99%")