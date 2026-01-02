import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Page Config
st.set_page_config(page_title="SMS Pro", page_icon="🏫", layout="wide", initial_sidebar_state="expanded")

# Beautiful Theme with Icons & Buttons
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
        height: 3.5em;
        font-weight: bold;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        transition: all 0.3s;
    }
    .add-btn {background-color: #28a745 !important; color: white !important;}
    .add-btn:hover {background-color: #218838 !important; transform: translateY(-3px);}
    .update-btn {background-color: #007bff !important; color: white !important;}
    .update-btn:hover {background-color: #0056b3 !important; transform: translateY(-3px);}
    .delete-btn {background-color: #dc3545 !important; color: white !important;}
    .delete-btn:hover {background-color: #c82333 !important; transform: translateY(-3px);}
    .search-bar {border-radius: 10px; padding: 10px;}
</style>
""", unsafe_allow_html=True)

# Database Connection
conn = sqlite3.connect("school.db", check_same_thread=False)
c = conn.cursor()

# Create Tables
tables = [
    '''CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, roll_no TEXT NOT NULL UNIQUE, class TEXT, section TEXT, age INTEGER, phone TEXT)''',
    '''CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, teacher_id TEXT NOT NULL UNIQUE, subject TEXT, phone TEXT, email TEXT)''',
    '''CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, date TEXT, status TEXT)''',
    '''CREATE TABLE IF NOT EXISTS fees (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount REAL, payment_date TEXT, status TEXT)''',
    '''CREATE TABLE IF NOT EXISTS exams (id INTEGER PRIMARY KEY AUTOINCREMENT, exam_name TEXT, class TEXT, subject TEXT, max_marks INTEGER, date TEXT)''',
    '''CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author TEXT, isbn TEXT UNIQUE, total_copies INTEGER DEFAULT 1)''',
    '''CREATE TABLE IF NOT EXISTS timetable (id INTEGER PRIMARY KEY AUTOINCREMENT, class TEXT, day TEXT, period INTEGER, subject TEXT, teacher TEXT)'''
]
for table in tables:
    c.execute(table)
conn.commit()

# Sidebar with Icons
st.sidebar.markdown("<h1 style='color:white;text-align:center;'>🏫 SMS Pro</h1>", unsafe_allow_html=True)
page = st.sidebar.radio("**Navigation**", [
    "🏠 Dashboard",
    "👨‍🎓 Students",
    "👩‍🏫 Teachers",
    "📅 Attendance",
    "💰 Fees",
    "📊 Exams",
    "📚 Library",
    "🗓️ Timetable"
])

# Universal Module Function with Icons & Buttons
def module_with_icons(title, table, fields, display_cols, search_cols):
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)

    # 🔍 Search Bar
    st.markdown("### 🔍 Search Records")
    search = st.text_input("", placeholder="Type to search...", key=f"search_{table}")

    # Load Data with Search
    if search:
        conditions = " OR ".join([f"{col} LIKE ?" for col in search_cols])
        df = pd.read_sql_query(f"SELECT * FROM {table} WHERE {conditions}", conn, params=[f"%{search}%"] * len(search_cols))
    else:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)

    tab1, tab2 = st.tabs(["➕ Add New", "📋 Manage"])

    with tab1:
        with st.form("add_form"):
            st.subheader("Add New Record")
            inputs = {}
            cols = st.columns(2)
            for i, (field, label) in enumerate(fields.items()):
                with cols[i % 2]:
                    if "age" in field or "copies" in field or "marks" in field or "period" in field:
                        inputs[field] = st.number_input(label, min_value=1)
                    elif "amount" in field:
                        inputs[field] = st.number_input(label, min_value=0.0, format="%.2f")
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
                    st.success("✅ Added successfully!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ Duplicate entry!")

    with tab2:
        if not df.empty:
            st.dataframe(df[display_cols], use_container_width=True)

            st.markdown("### ✏️ Update | 🗑️ Delete")
            record_id = st.number_input("Enter ID", min_value=1, step=1, key=f"id_{table}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Load for Update", use_container_width=True, key=f"load_{table}"):
                    row = df[df["id"] == record_id]
                    if not row.empty:
                        data = row.iloc[0].to_dict()
                        st.session_state[f"edit_{table}"] = data
                        st.success("Loaded! Edit below.")
                    else:
                        st.error("ID not found!")

            with col2:
                if st.button("🗑️ Delete Record", use_container_width=True, key=f"delete_{table}"):
                    if st.checkbox("Confirm delete"):
                        c.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
                        conn.commit()
                        st.success("Deleted!")
                        st.rerun()

            # Update Form
            if f"edit_{table}" in st.session_state:
                edit_data = st.session_state[f"edit_{table}"]
                with st.form("update_form"):
                    updated = {}
                    cols = st.columns(2)
                    for i, (field, label) in enumerate(fields.items()):
                        default = edit_data.get(field, "")
                        with cols[i % 2]:
                            if "age" in field or "copies" in field or "marks" in field or "period" in field:
                                updated[field] = st.number_input(label, value=int(default) if default else 1)
                            elif "amount" in field:
                                updated[field] = st.number_input(label, value=float(default) if default else 0.0)
                            elif "date" in field:
                                updated[field] = str(st.date_input(label, value=date.fromisoformat(default) if default else date.today()))
                            else:
                                updated[field] = st.text_input(label, value=default)
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        set_clause = ", ".join([f"{k}=?" for k in updated])
                        values = list(updated.values()) + [edit_data["id"]]
                        c.execute(f"UPDATE {table} SET {set_clause} WHERE id=?", values)
                        conn.commit()
                        st.success("Updated successfully!")
                        del st.session_state[f"edit_{table}"]
                        st.rerun()
        else:
            st.info("No records found.")

# Dashboard
if page == "🏠 Dashboard":
    st.markdown("<h1>Welcome to SMS Pro</h1>", unsafe_allow_html=True)
    st.markdown("<h3>School Management System</h3>", unsafe_allow_html=True)

# Modules with Icons & Buttons
if page == "👨‍🎓 Students":
    module_with_icons("👨‍🎓 Student Management", "students",
                      {"name": "Name *", "roll_no": "Roll No *", "class": "Class", "section": "Section", "age": "Age", "phone": "Phone"},
                      ["id", "name", "roll_no", "class", "section", "age", "phone"],
                      ["name", "roll_no", "phone"])

elif page == "👩‍🏫 Teachers":
    module_with_icons("👩‍🏫 Teacher Management", "teachers",
                      {"name": "Name *", "teacher_id": "ID *", "subject": "Subject", "phone": "Phone", "email": "Email"},
                      ["id", "name", "teacher_id", "subject", "phone", "email"],
                      ["name", "teacher_id", "email"])

elif page == "📅 Attendance":
    module_with_icons("📅 Attendance", "attendance",
                      {"student_id": "Student ID *", "date": "Date", "status": "Status (Present/Absent)"},
                      ["id", "student_id", "date", "status"],
                      ["student_id", "status"])

elif page == "💰 Fees":
    module_with_icons("💰 Fees Management", "fees",
                      {"student_id": "Student ID *", "amount": "Amount", "payment_date": "Date", "status": "Status"},
                      ["id", "student_id", "amount", "payment_date", "status"],
                      ["student_id", "status"])

elif page == "📊 Exams":
    module_with_icons("📊 Exams", "exams",
                      {"exam_name": "Exam Name *", "class": "Class", "subject": "Subject", "max_marks": "Max Marks", "date": "Date"},
                      ["id", "exam_name", "class", "subject", "max_marks", "date"],
                      ["exam_name", "subject"])

elif page == "📚 Library":
    module_with_icons("📚 Library Books", "books",
                      {"title": "Title *", "author": "Author", "isbn": "ISBN", "total_copies": "Copies"},
                      ["id", "title", "author", "isbn", "total_copies"],
                      ["title", "author", "isbn"])

elif page == "🗓️ Timetable":
    module_with_icons("🗓️ Timetable", "timetable",
                      {"class": "Class *", "day": "Day", "period": "Period", "subject": "Subject", "teacher": "Teacher"},
                      ["id", "class", "day", "period", "subject", "teacher"],
                      ["class", "subject", "teacher"])

conn.close()
