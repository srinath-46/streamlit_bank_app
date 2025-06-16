import streamlit as st
import pandas as pd
import os

# Paths to CSV files
data_path = "data"
users_file = os.path.join(data_path, "users.csv")
accounts_file = os.path.join(data_path, "accounts.csv")
loans_file = os.path.join(data_path, "loan_applications.csv")
loan_status_file = os.path.join(data_path, "loan_status.csv")
transactions_file = os.path.join(data_path, "transactions.csv")

# Load data
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

def save_csv(df, file):
    df.to_csv(file, index=False)

# Load all CSVs
users_df = load_csv(users_file)
accounts_df = load_csv(accounts_file)
loans_df = load_csv(loans_file)
loan_status_df = load_csv(loan_status_file)
transactions_df = load_csv(transactions_file)

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None

# Login Function
def login():
    st.title("\U0001F3E6 Streamlit Bank Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = users_df[(users_df["username"] == username) & (users_df["password"] == password)]
        if not user.empty:
            st.session_state.user = user.iloc[0].to_dict()
            st.success(f"Logged in as {username}")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

# User Dashboard
def user_dashboard():
    st.sidebar.title("User Menu")
    choice = st.sidebar.radio("Go to", ["\U0001F4C8 Account Summary", "\U0001F4DD Apply for Loan", "\U0001F4CA Loan Status", "\U0001F4B5 Transactions"])
    user_id = st.session_state.user["user_id"]

    if choice == "\U0001F4C8 Account Summary":
        acc = accounts_df[accounts_df["user_id"] == user_id]
        st.subheader("Account Summary")
        st.dataframe(acc)

    elif choice == "\U0001F4DD Apply for Loan":
        st.subheader("Loan Application Form")
        amount = st.number_input("Loan Amount", min_value=1000)
        purpose = st.text_input("Purpose")
        income = st.number_input("Monthly Income", min_value=0)
        if st.button("Submit Application"):
            loan_id = f"L{len(loans_df)+1:03d}"
            new_loan = pd.DataFrame([[loan_id, user_id, amount, purpose, income, "pending"]], columns=loans_df.columns)
            loans_df_updated = pd.concat([loans_df, new_loan], ignore_index=True)
            save_csv(loans_df_updated, loans_file)
            st.success("Loan Application Submitted!")

    elif choice == "\U0001F4CA Loan Status":
        st.subheader("Your Loan Applications")
        user_loans = loans_df[loans_df["user_id"] == user_id]
        st.dataframe(user_loans)

    elif choice == "\U0001F4B5 Transactions":
        st.subheader("Transaction History")
        tx = transactions_df[transactions_df["user_id"] == user_id]
        st.dataframe(tx)

# Admin Dashboard
def admin_dashboard():
    st.sidebar.title("Admin Panel")
    option = st.sidebar.radio("Select", ["\U0001F4C3 All Applications", "\u2705 Approve Loans"])

    if option == "\U0001F4C3 All Applications":
        st.subheader("All Loan Applications")
        st.dataframe(loans_df)

    elif option == "\u2705 Approve Loans":
        st.subheader("Approve or Reject Loans")
        for i, row in loans_df.iterrows():
            if row["status"] == "pending":
                st.write(row)
                if st.button(f"Approve {row['loan_id']}"):
                    loans_df.at[i, "status"] = "approved"
                    save_csv(loans_df, loans_file)
                    st.success(f"Loan {row['loan_id']} approved")

# Main Routing
if st.session_state.user:
    st.sidebar.write(f"\U0001F44B Welcome, {st.session_state.user['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()
    if st.session_state.user["role"] == "user":
        user_dashboard()
    elif st.session_state.user["role"] == "admin":
        admin_dashboard()
else:
    login()
