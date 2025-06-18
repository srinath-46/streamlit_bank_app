import streamlit as st
import pandas as pd
import os
import random
from sklearn.linear_model import LogisticRegression
import numpy as np

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

# Ensure required columns exist
if 'status' not in loans_df.columns:
    loans_df['status'] = 'pending'
if 'remarks' not in loans_df.columns:
    loans_df['remarks'] = ''

for col in ['account_no', 'address', 'balance']:
    if col not in accounts_df.columns:
        accounts_df[col] = '' if col != 'balance' else 0

if 'username' not in users_df.columns:
    users_df['username'] = ''
if 'user_id' not in users_df.columns:
    users_df['user_id'] = ''

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None

# Create New User
def create_new_user():
    st.title("Create New User Account")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    role = st.selectbox("Role", ["user", "admin"])
    city = st.text_input("City")
    mobile = st.text_input("Mobile Number (e.g., xxxxxxx237)")

    if st.button("Create Account"):
        if username in users_df["username"].values:
            st.error("Username already exists. Please choose another.")
        else:
            user_id = f"U{len(users_df)+1:04d}"
            new_user = pd.DataFrame([{"user_id": user_id, "username": username, "password": password, "role": role}])
            new_account = pd.DataFrame([{"user_id": user_id, "account_no": f"XXXXXXX{random.randint(100,999)}", "address": city, "mobile": mobile, "balance": 0}])

            updated_users = pd.concat([users_df, new_user], ignore_index=True)
            updated_accounts = pd.concat([accounts_df, new_account], ignore_index=True)

            save_csv(updated_users, users_file)
            save_csv(updated_accounts, accounts_file)

            st.success("Account created successfully!")
            st.info(f"Username: {username}\nAccount Number: {new_account.iloc[0]['account_no']}\nCity: {city}")

# Login Function
def login():
    st.title("lavudhu Bank 69")
    menu = st.radio("Select an option", ["Login", "Create Account", "Forgot Password?"])

    if menu == "Create Account":
        create_new_user()
        return

    if menu == "Forgot Password?":
        st.subheader("Reset Your Password with Mobile Verification")

        username = st.text_input("Enter your username")
        mobile = st.text_input("Enter your registered mobile number")
        new_password = st.text_input("Enter your new password", type="password")

        if st.button("Reset Password"):
            users_df = load_csv(users_file)
            accounts_df = load_csv(accounts_file)

            user_row = users_df[users_df["username"] == username]
            if user_row.empty:
                st.error("❌ Username not found.")
                return

            user_id = user_row.iloc[0]["user_id"]
            acc_row = accounts_df[(accounts_df["user_id"] == user_id) & (accounts_df["mobile"] == mobile)]

            if acc_row.empty:
                st.error("❌ Mobile number does not match our records.")
            else:
                users_df.loc[users_df["username"] == username, "password"] = new_password
                save_csv(users_df, users_file)
                st.success("✅ Password reset successful! You may now log in.")
        return

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users_df = load_csv(users_file)

        required_cols = {"username", "password", "role", "user_id"}
        if not required_cols.issubset(set(users_df.columns)):
            st.error("Error: 'users.csv' is missing required columns.")
            st.stop()

        user = users_df[
            (users_df["username"] == username) & 
            (users_df["password"] == password)
        ]

        if not user.empty:
            st.session_state.user = user.iloc[0].to_dict()
            st.success(f"Logged in as {username}")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# User Dashboard
def user_dashboard():
   st.sidebar.title("User Menu")
    choice = st.sidebar.radio("Go to", ["📈 Account Summary", "📝 Apply for Loan", "📊 Loan Status", "💵 Transactions"])
    user_id = st.session_state.user["user_id"]

    if choice == "📈 Account Summary":
        if all(col in accounts_df.columns for col in ["user_id", "account_no", "address", "balance"]):
            acc = accounts_df[accounts_df["user_id"] == user_id][["account_no", "address", "balance"]]
            st.subheader("Account Summary")
            st.dataframe(acc)
        else:
            st.error("Account data is missing some required columns.")

    elif choice == "📝 Apply for Loan":
        st.subheader("Loan Application Form")
        amount = st.number_input("Loan Amount", min_value=1000)
        purpose = st.text_input("Purpose")
        income = st.number_input("Monthly Income", min_value=0)
        if st.button("Submit Application"):
            loan_id = f"L{len(loans_df)+1:03d}"
            new_loan_data = {
                "loan_id": loan_id,
                "user_id": user_id,
                "amount": amount,
                "purpose": purpose,
                "income": income,
                "status": "pending",
                "application_date": pd.Timestamp.today().strftime('%Y-%m-%d'),
                "remarks": "Awaiting review"
            }
            new_loan = pd.DataFrame([new_loan_data])
            loans_df_updated = pd.concat([loans_df, new_loan], ignore_index=True)
            save_csv(loans_df_updated, loans_file)
            st.success("Loan Application Submitted!")

    elif choice == "📊 Loan Status":
        st.subheader("Your Loan Applications")
        user_loans = loans_df[loans_df["user_id"] == user_id]
        st.dataframe(user_loans)

    elif choice == "💵 Transactions":
        st.subheader("Transaction History")
        tx = transactions_df[transactions_df["user_id"] == user_id]
        st.dataframe(tx)


# Admin Dashboard
def admin_dashboard():
    st.sidebar.title("Admin Panel")
    option = st.sidebar.radio("Select", ["📃 All Applications", "✅ Approve Loans", "🔍 Fetch User Data"])

    if option == "🔍 Fetch User Data":
        st.subheader("Search User and Account Info")
        search_id = st.text_input("Enter Username or User ID")
        if st.button("Search"):
            users_df_reloaded = load_csv(users_file)
            accounts_df_reloaded = load_csv(accounts_file)

            user_results = users_df_reloaded[(users_df_reloaded["username"].str.lower() == search_id.lower()) |
                                             (users_df_reloaded["user_id"].str.lower() == search_id.lower())]

            account_results = accounts_df_reloaded[(accounts_df_reloaded["user_id"].isin(user_results["user_id"]))]

            if not user_results.empty:
                st.subheader("User Details")
                st.dataframe(user_results)
                st.subheader("Account Details")
                st.dataframe(account_results)
            else:
                st.warning("❌ No matching user or ID found.")

# Main Routing
if st.session_state.user:
    st.sidebar.write(f"👋 Welcome, {st.session_state.user['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()
    if st.session_state.user["role"] == "user":
        user_dashboard()
    elif st.session_state.user["role"] == "admin":
        admin_dashboard()
else:
    login()
