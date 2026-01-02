import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ==================== PAGE CONFIG & STUNNING THEME ====================
st.set_page_config(
    page_title="SMS Pro - School Management",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Beautiful Gradient Theme
st.markdown("""
<style>
    .main {
        background: linear-gradient(to bottom, #667eea, #764ba2);
    }
    h1, h2, h3 {
        color: white !important;
        text-align: center;
        text-shadow: 2px 2px 6px rgba(0,0,0,0.4);
    }
    .stButton > button {
        border-radius: 12px;
        height: 3.8em;
        font-weight: bold;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    .search-btn {background-color: #6c757d !important; color: white !important;}
    .search-btn:hover {background-color: #5a6268 !important;}
    .add-btn {background-color: #28a745 !important; color: white !important;}
    .add-btn:hover {background-color: #218838 !important;}
    .update-btn {background-color: #007bff !important; color: white !important;}
    .update-btn:hover {background-color: #0056b3 !important;}
    .delete-btn {background-color: #dc3545 !important; color: white !important;}
    .delete-btn:hover {background-color: #c82333 !important;}
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        text-align: center;
    }
    .sidebar .sidebar-content {background-color: #2c3e50;}
</style>
""", unsafe_allow_html=True)

# Database
conn = sqlite3.connect("school.db", check_same_thread=False)
c = conn.cursor()

# Create Tables (same as before)
# ... (keep all table creations from previous code)

conn.commit()

# ==================== SIDEBAR ====================
st.sidebar.markdown("<h1 style='color:white;text-align:center;'>🏫 SMS Pro</h1>", unsafe_allow_html=True)

page = st.sidebar.radio("**Navigation**", [
    "🏠 Dashboard",
    "👨‍🎓 Students",
    "👩‍🏫 Teachers",
    "📅 Attendance",
    "💰 Fees Management",
    "📊 Exams",
    "📚 Library Books",
    "🗓️ Timetable"
])

# ==================== UNIVERSAL CRUD + SEARCH FUNCTION ====================
def crud_search_module(icon_title, table, fields, display_cols, search_fields):
    st.markdown(f"<h1>{icon_title}</h1>", unsafe_allow_html=True)

    # Search Bar
    st.markdown("### 🔍 Search Records")
    search_term = st.text_input("Enter search term", "")
    query = f"SELECT * FROM {table}"
    params = ()
    if search_term:
        conditions = " OR ".join([f"{field} LIKE ?" for field in search_fields])
        query += f" WHERE {conditions}"
        params = tuple(f"%{search_term}%" for _ in search_fields)

    df = pd.read_sql_query(query, conn, params=params) if search_term else pd.read_sql_query(f"SELECT * FROM {table}", conn)

    tab_add, tab_manage = st.tabs(["➕ Add New", "📋 View & Manage"])

    with tab_add:
        with st.form("add_form"):
            st.subheader("Add New Record")
            inputs = {}
            cols = st.columns(2)
            for idx, (field, label) in enumerate(fields.items()):
                with cols[idx % 2]:
                    if "amount" in field or "copies" in field or "marks" in field or "period" in field or "age" in field:
                        inputs[field] = st.number_input(label, min_value=0 if "amount" in field else 1)
                    elif "date" in field:
                        inputs[field] = str(st.date_input(label, date.today()))
                    else:
                        inputs[field] = st.text_input(label)
            if st.form_submit_button("➕ Add Record", use_container_width=True):
                try:
                    cols_str = ", ".join(inputs.keys())
                    placeholders = ", ".join(["?"] * len(inputs))
                    c.execute(f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})", tuple(inputs.values()))
                    conn.commit()
                    st.success("✅ Added!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ Duplicate entry!")

    with tab_manage:
        if not df.empty:
            st.dataframe(df[display_cols], use_container_width=True)

            st.markdown("### ✏️ Update | 🗑️ Delete")
            record_id = st.number_input("Enter Record ID", min_value=1, step=1)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Load for Update", use_container_width=True):
                    if record_id in df["id"].values:
                        row = df[df["id"] == record_id].iloc[0]
                        for col in df.columns:
                            st.session_state[f"{table}_{col}"] = row[col]
                        st.session_state[f"{table}_edit_id"] = record_id
                        st.success("Loaded for update!")
                    else:
                        st.error("ID not found!")

            with col2:
                if st.button("🗑️ Delete Record", use_container_width=True):
                    if record_id in df["id"].values and st.checkbox("Confirm delete"):
                        c.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))
                        conn.commit()
                        st.success("Deleted!")
                        st.rerun()

            if f"{table}_edit_id" in st.session_state:
                st.markdown("### ✏️ Edit Record")
                with st.form("update_form"):
                    updated = {}
                    cols = st.columns(2)
                    for idx, (field, label) in enumerate(fields.items()):
                        default = st.session_state.get(f"{table}_{field}", "")
                        with cols[idx % 2]:
                            if "amount" in field or "copies" in field:
                                updated[field] = st.number_input(label, value=float(default) if default else 0.0)
                            elif "date" in field:
                                updated[field] = str(st.date_input(label, value=date.fromisoformat(default) if default else date.today()))
                            else:
                                updated[field] = st.text_input(label, value=default)
                    if st.form_submit_button("💾 Save Changes"):
                        set_clause = ", ".join([f"{k}=?" for k in updated])
                        values = list(updated.values()) + [st.session_state[f"{table}_edit_id"]]
                        c.execute(f"UPDATE {table} SET {set_clause} WHERE id=?", values)
                        conn.commit()
                        st.success("Updated!")
                        st.rerun()
        else:
            st.info("No records found.")

# ==================== MODULES WITH SEARCH + CRUD ====================

if page == "🏠 Dashboard":
    st.markdown("<h1>Welcome to SMS Pro</h1>", unsafe_allow_html=True)
    # Dashboard metrics as before

elif page == "👨‍🎓 Students":
    crud_search_module("👨‍🎓 Student Management", "students",
                       {"name": "Name *", "roll_no": "Roll No *", "class": "Class", "section": "Section", "age": "Age", "phone": "Phone"},
                       ["id", "name", "roll_no", "class", "section", "age", "phone"],
                       ["name", "roll_no", "phone"])

elif page == "👩‍🏫 Teachers":
    crud_search_module("👩‍🏫 Teacher Management", "teachers",
                       {"name": "Name *", "teacher_id": "ID *", "subject": "Subject", "phone": "Phone", "email": "Email"},
                       ["id", "name", "teacher_id", "subject", "phone", "email"],
                       ["name", "teacher_id", "email"])

# Apply the same for other modules: Attendance, Fees, Exams, Library, Timetable
# (Use appropriate search_fields like "student_id", "exam_name", "title", etc.)

conn.close()
