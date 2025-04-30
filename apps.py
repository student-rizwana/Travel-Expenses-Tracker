import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
import time
import plotly.express as px

# -------------------- GOOGLE SHEETS SETUP -----------------------
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("Travel Expenses").sheet1
    return sheet

def get_lat_lon(location):
    geolocator = Nominatim(user_agent="expense_tracker")
    loc = geolocator.geocode(location)
    if loc:
        return loc.latitude, loc.longitude
    return None, None

def add_expense(date, category, amount, description, location):
    sheet = get_sheet()
    lat, lon = get_lat_lon(location)
    sheet.append_row([str(date), category, amount, description, location, lat, lon])

def update_expense(row_number, date, category, amount, description, location, justification=""):
    sheet = get_sheet()
    sheet.update(f"A{row_number}:D{row_number}", [[str(date), category, amount, description, justification, location]])


def delete_expense(row_number):
    sheet = get_sheet()
    sheet.delete_rows(row_number)


def analyze_expenses(df, budget=10000):
    total_spent = df["Amount"].sum()
    budget_left = budget - total_spent
    category_spending = df.groupby("Category")["Amount"].sum()
    return total_spent, budget_left, category_spending


def load_data():
    sheet = get_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# -------------------- CUSTOM STYLING -----------------------
with open("assests/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

components.html("""
<script>
    console.log("Streamlit loaded with custom JS");
</script>
""")

# -------------------- STREAMLIT UI -----------------------
st.markdown('<div class="title">Travel Expense Tracker</div>', unsafe_allow_html=True)

# -------------------- ADD NEW EXPENSE -----------------------
st.subheader("➕ Add New Expense")

with st.form("entry_form"):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date")
        category = st.selectbox("Category", ["Flight", "Hotel", "Food", "Transport", "Shopping", "Other"])
    with col2:
        amount = st.number_input("Amount", min_value=0.0)
        description = st.text_input("Description")

    # NEW LOCATION INPUT
    location = st.text_input("Location (City or Place Name)")
    submitted = st.form_submit_button("Add Expense")

    if submitted:
        add_expense(date, category, amount, description, location)
        st.success("Expense added successfully!")


# Load data from Google Sheet
df = load_data()


# ----------- Budget Analysis -----------
if not df.empty:
    st.subheader("💸 Budget Analysis")
    total_spent, budget_left, category_spending = analyze_expenses(df)

    col1, col2 = st.columns(2)
    col1.metric("Total Spent (₹)", f"{total_spent:.2f}")
    col2.metric("Budget Left (₹)", f"{budget_left:.2f}")

    st.subheader("📊 Category-wise Breakdown")
    st.bar_chart(df.groupby("Category")["Amount"].sum())
   
   
# Pie chart by category
category_group = df.groupby("Category")["Amount"].sum().reset_index()
fig = px.pie(category_group, values="Amount", names="Category", title="Expenses by Category")
st.plotly_chart(fig)


# DISPLAY EXPENSE DATA
st.subheader("📋 All Expenses")
df = load_data()
df.index.name = 'Index'
df.reset_index(inplace=True)
st.dataframe(df)

# ADD Update/Delete Section (Paste step 2 code here)
st.subheader("✏️ Update or Delete Expense")

selected_index = st.selectbox("Select the row index to update/delete", df["Index"])
selected_row = df[df["Index"] == selected_index].iloc[0]

updated_date = st.date_input("Date", pd.to_datetime(selected_row["Date"]))
updated_category = st.selectbox("Category", ["Flight", "Hotel", "Food", "Transport", "Shopping", "Other"], index=["Flight", "Hotel", "Food", "Transport", "Shopping", "Other"].index(selected_row["Category"]))
updated_amount = st.number_input("Amount", value=float(selected_row["Amount"]), min_value=0.0)
updated_description = st.text_input("Description", value=selected_row["Description"])

if st.button("Update Expense"):
    sheet = get_sheet()
    sheet.update_cell(selected_index + 2, 1, str(updated_date))       # Row + header offset
    sheet.update_cell(selected_index + 2, 2, updated_category)
    sheet.update_cell(selected_index + 2, 3, updated_amount)
    sheet.update_cell(selected_index + 2, 4, updated_description)
    st.success("Expense updated successfully!")

if st.button("Delete Expense"):
    sheet = get_sheet()
    sheet.delete_rows(selected_index + 2)   # Header offset
    st.success("Expense deleted successfully!")
else:
    st.info("No expenses found. Add a new one above!")



 
