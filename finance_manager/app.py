import streamlit as st  
import pandas as pd
import os
import json
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Pink Purse 💖", layout="centered")

# CSS styling
st.markdown("""
    <style>
    .main {
        background-color: #fff0f6;
        font-family: 'Segoe UI', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    .mobile-frame {
        max-width: 390px;
        margin: auto;
        border: none;
        border-radius: 0;
        padding: 0 1rem 1rem 1rem;
        box-shadow: none;
        background: transparent;
        transition: all 0.3s ease-in-out;
    }
    .mobile-frame-full {
        max-width: 100%;
        border-radius: 0;
    }
    .stButton>button {
        background-color: #ffb6c1;
        color: #4b0033;
        border-radius: 20px;
        border: none;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #ff80ab;
        color: white;
        box-shadow: 0 0 10px #ffb6c1;
        transform: scale(1.05);
    }
    .progress-bar {
        height: 18px;
        background-color: #ffb6c1;
        border-radius: 9px;
    }
    </style>
""", unsafe_allow_html=True)

FILE_PATH = "transactions.csv"
BILLS_PATH = "bills.json"
BUDGETS_PATH = "budgets.json"
SAVINGS_GOALS_PATH = "savings_goals.json"
JOURNAL_PATH = "journal.json"

emoji_map = {
    "Food": "🍔 Food",
    "Bills": "🧾 Bills",
    "Salary": "💼 Salary",
    "Shopping": "🛍️ Shopping",
    "Other": "📁 Other",
}

def category_with_emoji(cat):
    return emoji_map.get(cat, cat)

# Load or initialize dataframes and lists in session state
if "df" not in st.session_state:
    if os.path.exists(FILE_PATH):
        st.session_state.df = pd.read_csv(FILE_PATH, parse_dates=["Date"])
    else:
        st.session_state.df = pd.DataFrame(columns=["Date", "Category", "Description", "Amount", "Type"])
df = st.session_state.df

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

if "bills" not in st.session_state:
    st.session_state.bills = load_json(BILLS_PATH, [])
if "budgets" not in st.session_state:
    st.session_state.budgets = load_json(BUDGETS_PATH, {})
if "savings_goals" not in st.session_state:
    st.session_state.savings_goals = load_json(SAVINGS_GOALS_PATH, [])
if "journal" not in st.session_state:
    st.session_state.journal = load_json(JOURNAL_PATH, [])

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, default=str)

# Sidebar: Upload CSV and Manage Data
st.sidebar.title("📂 Manage Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if uploaded_file:
    import_df = pd.read_csv(uploaded_file, parse_dates=["Date"])
    def clean_cat(x):
        for em in emoji_map.values():
            x = x.replace(em, "").strip()
        return x
    import_df["Category"] = import_df["Category"].apply(clean_cat)
    df = pd.concat([df, import_df], ignore_index=True).drop_duplicates()
    df["Date"] = pd.to_datetime(df["Date"])
    st.session_state.df = df
    df.to_csv(FILE_PATH, index=False)
    st.sidebar.success("CSV imported successfully!")

st.sidebar.download_button(
    label="Download CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="transactions_export.csv",
    mime="text/csv",
)

if st.sidebar.button("Save Bills, Budgets, Savings Goals & Journal"):
    save_json(st.session_state.bills, BILLS_PATH)
    save_json(st.session_state.budgets, BUDGETS_PATH)
    save_json(st.session_state.savings_goals, SAVINGS_GOALS_PATH)
    save_json(st.session_state.journal, JOURNAL_PATH)
    st.sidebar.success("Data saved!")

# Clear All Transactions button below Save button
if st.sidebar.button("🗑️ Clear All Transactions"):
    st.session_state.df = pd.DataFrame(columns=["Date", "Category", "Description", "Amount", "Type"])
    st.session_state.df.to_csv(FILE_PATH, index=False)
    st.sidebar.success("All transactions have been cleared!")

# Tabs
tabs = st.tabs(["🏠 Home", "➕ Add", "📦 Bills", "📈 Predict", "🧮 Budget", "🎯 Savings Goal", "📊 Expense Pie Chart", "📓 Journal"])

with st.container():
    st.markdown('<div class="mobile-frame">', unsafe_allow_html=True)

    # Home Tab
    with tabs[0]:
        st.markdown("## 👛 Hello, Elieza!")
        st.markdown("Your personal finance space 💖")

        if df.empty:
            st.info("No transactions found. Add some transactions.")
        else:
            st.subheader("Filter Transactions")
            categories = ["All"] + list(emoji_map.keys())
            filter_cat = st.selectbox("Category", categories)
            start_date = st.date_input("Start Date", value=df["Date"].min())
            end_date = st.date_input("End Date", value=df["Date"].max())

            filtered_df = df[
                (df["Date"] >= pd.to_datetime(start_date)) &
                (df["Date"] <= pd.to_datetime(end_date))
            ]
            if filter_cat != "All":
                filtered_df = filtered_df[filtered_df["Category"] == filter_cat]

            with st.spinner("Crunching numbers 💖..."):
                total_income = filtered_df[filtered_df["Type"] == "Income"]["Amount"].sum()
                total_expense = abs(filtered_df[filtered_df["Type"] == "Expense"]["Amount"].sum())
                balance = total_income - total_expense

                col1, col2, col3 = st.columns(3)
                col1.metric("Income 💼", f"₱{total_income:,.2f}")
                col2.metric("Expense 🛍️", f"₱{total_expense:,.2f}")
                col3.metric("Balance 💰", f"₱{balance:,.2f}")

                st.subheader("📋 All Transactions")
                display_df = filtered_df.copy()
                display_df["Category"] = display_df["Category"].apply(category_with_emoji)
                st.dataframe(display_df.sort_values(by="Date", ascending=False))

    # Add Transaction Tab
    with tabs[1]:
        st.header("➕ Add a Transaction")

        with st.form("add_transaction_form", clear_on_submit=True):
            date = st.date_input("Date", datetime.today())
            category = st.selectbox("Category", list(emoji_map.values()))
            description = st.text_input("Description", placeholder="E.g. Grocery, Netflix subscription")
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            t_type = st.radio("Type", ["Income", "Expense"])
            submitted = st.form_submit_button("Add")

            if submitted:
                if not description.strip():
                    st.error("Please enter a description.")
                elif amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    cat_clean = [k for k, v in emoji_map.items() if v == category]
                    cat_clean = cat_clean[0] if cat_clean else category

                    new_data = {
                        "Date": pd.to_datetime(date),
                        "Category": cat_clean,
                        "Description": description.strip(),
                        "Amount": amount if t_type == "Income" else -amount,
                        "Type": t_type
                    }
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    st.session_state.df = df
                    df.to_csv(FILE_PATH, index=False)
                    st.success("Transaction added! 💖")

    # Bills Tab
    with tabs[2]:
        st.header("📦 Bills")

        bills = st.session_state.bills

        if bills:
            for bill in bills:
                st.write(f"- **{bill['name']}**: ₱{bill['amount']:.2f} due on {bill['due_date']}")
        else:
            st.info("No bills added yet.")

        with st.form("add_bill_form", clear_on_submit=True):
            name = st.text_input("Bill Name")
            amount = st.number_input("Amount (₱)", min_value=0.0, format="%.2f")
            due_date = st.date_input("Due Date")
            submitted = st.form_submit_button("Add Bill")

            if submitted:
                if not name.strip():
                    st.error("Please enter a bill name.")
                elif amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    new_bill = {"name": name.strip(), "amount": amount, "due_date": str(due_date)}
                    bills.append(new_bill)
                    st.session_state.bills = bills
                    save_json(bills, BILLS_PATH)
                    st.success(f"Bill '{name}' added!")

    # Predict Tab
    with tabs[3]:
        st.header("📈 Predict Future Expenses")

        if df.empty:
            st.info("No transaction data available for prediction.")
        else:
            df_exp = df[df["Type"] == "Expense"].copy()
            df_exp['Month'] = df_exp['Date'].dt.to_period('M')
            monthly_expense = df_exp.groupby('Month')['Amount'].sum().abs().reset_index()
            monthly_expense['Month'] = monthly_expense['Month'].dt.to_timestamp()

            if len(monthly_expense) < 3:
                st.info("Need at least 3 months of expense data to make predictions.")
            else:
                X = np.arange(len(monthly_expense)).reshape(-1,1)
                y = monthly_expense['Amount'].values

                model = LinearRegression()
                model.fit(X, y)

                future_months = 3
                X_future = np.arange(len(monthly_expense), len(monthly_expense) + future_months).reshape(-1,1)
                preds = model.predict(X_future)

                future_dates = pd.Series([monthly_expense['Month'].iloc[-1] + pd.DateOffset(months=i) for i in range(1, future_months+1)])
                all_dates = pd.concat([monthly_expense['Month'], future_dates])

                fig = px.line(
                    x=all_dates,
                    y=np.concatenate([y, preds]),
                    labels={"x": "Month", "y": "Expense (₱)"},
                    title="Monthly Expense with 3-Month Prediction"
                )

                st.plotly_chart(fig, use_container_width=True)

    # Budget Tab
    with tabs[4]:
        st.header("🧮 Budget Management")

        budgets = st.session_state.budgets

        if budgets:
            st.subheader("Your Budgets")
            for category, amount in budgets.items():
                st.write(f"- **{category}**: ₱{amount:.2f}")
        else:
            st.info("No budgets set yet.")

        with st.form("budget_form", clear_on_submit=True):
            category = st.selectbox("Category", list(emoji_map.keys()))
            amount = st.number_input("Budget Amount (₱)", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Set Budget")

            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    budgets[category] = amount
                    st.session_state.budgets = budgets
                    save_json(budgets, BUDGETS_PATH)
                    st.success(f"Budget for {category} set to ₱{amount:.2f}")

    # Savings Goal Tab
    with tabs[5]:
        st.header("🎯 Savings Goals")

        goals = st.session_state.savings_goals

        if goals:
            for g in goals:
                st.write(f"- **{g['goal']}**: ₱{g['amount']:.2f}, Target Date: {g['target_date']}")
        else:
            st.info("No savings goals set.")

        with st.form("savings_form", clear_on_submit=True):
            goal = st.text_input("Goal Name")
            amount = st.number_input("Target Amount (₱)", min_value=0.0, format="%.2f")
            target_date = st.date_input("Target Date")
            submitted = st.form_submit_button("Add Savings Goal")

            if submitted:
                if not goal.strip():
                    st.error("Please enter a goal name.")
                elif amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    new_goal = {"goal": goal.strip(), "amount": amount, "target_date": str(target_date)}
                    goals.append(new_goal)
                    st.session_state.savings_goals = goals
                    save_json(goals, SAVINGS_GOALS_PATH)
                    st.success(f"Savings goal '{goal}' added!")

    # Expense Pie Chart Tab
    with tabs[6]:
        st.header("📊 Expense Pie Chart")

        exp_df = df[df["Type"] == "Expense"]
        if exp_df.empty:
            st.info("No expenses to display.")
        else:
            pie_data = exp_df.groupby("Category")["Amount"].sum().abs()
            fig = px.pie(
                values=pie_data.values,
                names=[category_with_emoji(cat) for cat in pie_data.index],
                title="Expenses by Category",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Journal Tab
    with tabs[7]:
        st.header("📓 Journal")

        journal = st.session_state.journal

        if journal:
            for entry in reversed(journal):
                st.markdown(f"**{entry['date']}** - {entry['title']}")
                st.write(entry['content'])
                st.markdown("---")
        else:
            st.info("No journal entries yet.")

        with st.form("journal_form", clear_on_submit=True):
            title = st.text_input("Entry Title")
            content = st.text_area("Content")
            submitted = st.form_submit_button("Add Journal Entry")

            if submitted:
                if not title.strip() or not content.strip():
                    st.error("Title and content cannot be empty.")
                else:
                    new_entry = {"date": str(datetime.today().date()), "title": title.strip(), "content": content.strip()}
                    journal.append(new_entry)
                    st.session_state.journal = journal
                    save_json(journal, JOURNAL_PATH)
                    st.success("Journal entry added!")

    st.markdown("</div>", unsafe_allow_html=True)