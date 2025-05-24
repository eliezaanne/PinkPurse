
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

# Theme customization: Cute and Girly
st.set_page_config(page_title="Personal Finance Manager", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #fff0f6;
    }
    .block-container {
        padding-top: 2rem;
    }
    .css-1d391kg {
        font-family: 'Comic Sans MS', cursive, sans-serif;
    }
    .stButton>button {
        background-color: #ffb6c1;
        color: #4b0033;
        border-radius: 20px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #ff80ab;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

FILE_PATH = "transactions.csv"

# Load or initialize data
if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH, parse_dates=["Date"])
else:
    df = pd.DataFrame(columns=["Date", "Category", "Description", "Amount", "Type"])

# Sidebar: Import/Export only
st.sidebar.title("📂 Data Management")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if uploaded_file:
    import_df = pd.read_csv(uploaded_file, parse_dates=["Date"])
    df = pd.concat([df, import_df], ignore_index=True).drop_duplicates()
    df.to_csv(FILE_PATH, index=False)
    st.sidebar.success("CSV imported successfully!")

st.sidebar.download_button(
    label="Download CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="transactions_export.csv",
    mime="text/csv",
)

# Main UI Tabs
tabs = st.tabs(["💖 Dashboard", "🧶 Add Transaction", "📦 Bill Reminders", "📈 Predictions"])

# 1. Dashboard Tab
with tabs[0]:
    st.header("📊 Transactions Overview")

    if df.empty:
        st.info("No transactions found. Add some transactions.")
    else:
        total_income = df[df["Type"] == "Income"]["Amount"].sum()
        total_expense = abs(df[df["Type"] == "Expense"]["Amount"].sum())
        balance = total_income - total_expense

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"₱{total_income:,.2f}")
        col2.metric("Total Expense", f"₱{total_expense:,.2f}")
        col3.metric("Balance", f"₱{balance:,.2f}")

        st.subheader("🧾 All Transactions")
        st.dataframe(df.sort_values(by="Date", ascending=False))

# 2. Add Transaction Tab
with tabs[1]:
    st.header("➕ Add a New Transaction")

    with st.form("add_transaction_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.today())
        category = st.selectbox("Category", ["Food", "Bills", "Salary", "Shopping", "Other"])
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        t_type = st.radio("Type", ["Income", "Expense"])

        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            new_data = {
                "Date": pd.to_datetime(date),
                "Category": category,
                "Description": description,
                "Amount": amount if t_type == "Income" else -amount,
                "Type": t_type
            }
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            df.to_csv(FILE_PATH, index=False)
            st.success("Transaction added!")

# 3. Bill Reminders Tab
with tabs[2]:
    st.header("⏰ Bill Reminders")

    if "bills" not in st.session_state:
        st.session_state.bills = []

    with st.form("bill_form", clear_on_submit=True):
        bill_name = st.text_input("Bill Name")
        bill_due_date = st.date_input("Due Date")
        bill_amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        add_bill = st.form_submit_button("Add Bill")

    if add_bill:
        st.session_state.bills.append({
            "Name": bill_name,
            "Due Date": bill_due_date,
            "Amount": bill_amount,
            "Paid": False
        })
        st.success("Bill added!")

    if st.session_state.bills:
        bills_df = pd.DataFrame(st.session_state.bills)
        bills_df["Due Soon"] = bills_df["Due Date"].apply(
            lambda d: (d - pd.Timestamp.today().date()).days <= 7
        )
        st.dataframe(bills_df)

        due_soon = bills_df[bills_df["Due Soon"] == True]
        if not due_soon.empty:
            st.warning(f"You have {len(due_soon)} bill(s) due within 7 days!")
    else:
        st.info("No bills added yet.")

# 4. Predictions Tab
with tabs[3]:
    st.header("🔮 Predictions")

    if df.empty:
        st.info("Add transactions first to get predictions.")
    else:
        expense_df = df[df["Type"] == "Expense"].copy()
        income_df = df[df["Type"] == "Income"].copy()

        if len(expense_df) < 2 or len(income_df) < 2:
            st.info("Need at least 2 months of income and expense data to predict.")
        else:
            expense_df["Month"] = expense_df["Date"].dt.to_period("M")
            monthly_expenses = (
                expense_df.groupby("Month")["Amount"].sum().reset_index().sort_values("Month")
            )
            monthly_expenses["MonthIndex"] = range(len(monthly_expenses))

            income_df["Month"] = income_df["Date"].dt.to_period("M")
            monthly_income = (
                income_df.groupby("Month")["Amount"].sum().reset_index().sort_values("Month")
            )
            monthly_income["MonthIndex"] = range(len(monthly_income))

            model_expense = LinearRegression()
            model_expense.fit(monthly_expenses[["MonthIndex"]], monthly_expenses["Amount"])

            model_income = LinearRegression()
            model_income.fit(monthly_income[["MonthIndex"]], monthly_income["Amount"])

            next_month_index = [[max(monthly_expenses["MonthIndex"].max(), monthly_income["MonthIndex"].max()) + 1]]
            predicted_expense = model_expense.predict(next_month_index)[0]
            predicted_income = model_income.predict(next_month_index)[0]
            predicted_savings = predicted_income - predicted_expense

            st.subheader("Predicted Next Month")
            col1, col2, col3 = st.columns(3)
            col1.metric("Expense", f"₱{abs(predicted_expense):,.2f}")
            col2.metric("Income", f"₱{predicted_income:,.2f}")
            col3.metric("Savings", f"₱{predicted_savings:,.2f}")

            savings_data = pd.DataFrame({
                "Month": list(monthly_income["Month"].astype(str)) + ["Next Month"],
                "Income": list(monthly_income["Amount"]) + [predicted_income],
                "Expense": list(monthly_expenses["Amount"]) + [predicted_expense],
            })
            savings_data["Savings"] = savings_data["Income"] - savings_data["Expense"]
            st.line_chart(savings_data.set_index("Month")[["Income", "Expense", "Savings"]])
