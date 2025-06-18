import streamlit as st
import pandas as pd
import os
import random
import hashlib
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression

# Paths to CSV files
data_path = "data"
users_file = os.path.join(data_path, "users.csv")
accounts_file = os.path.join(data_path, "accounts.csv")
loans_file = os.path.join(data_path, "loan_applications.csv")
loan_status_file = os.path.join(data_path, "loan_status.csv")
transactions_file = os.path.join(data_path, "transactions.csv")
model_file = os.path.join(data_path, "loan_model.pkl")

# Hashing function
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# Load and Save CSV
def load_csv(file):
    try:
        return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading {file}: {e}")
        return pd.DataFrame()

def save_csv(df, file):
    try:
        df.to_csv(file, index=False)
    except Exception as e:
        st.error(f"Error saving {file}: {e}")

# Load data into session state if not already loaded
def load_data_to_session():
    for name, file in [
        ("users_df", users_file),
        ("accounts_df", accounts_file),
        ("loans_df", loans_file),
        ("loan_status_df", loan_status_file),
        ("transactions_df", transactions_file),
    ]:
        if name not in st.session_state:
            st.session_state[name] = load_csv(file)

load_data_to_session()

users_df = st.session_state.users_df
accounts_df = st.session_state.accounts_df
loans_df = st.session_state.loans_df
loan_status_df = st.session_state.loan_status_df
transactions_df = st.session_state.transactions_df

# Ensure required columns exist
def ensure_columns():
    global users_df, accounts_df, loans_df

    if 'status' not in loans_df.columns:
        loans_df['status'] = 'pending'
    if 'remarks' not in loans_df.columns:
        loans_df['remarks'] = ''
    for col in ['account_no', 'address', 'balance', 'mobile']:
        if col not in accounts_df.columns:
            accounts_df[col] = '' if col != 'balance' else 0
    for col in ['username', 'user_id', 'password', 'role']:
        if col not in users_df.columns:
            users_df[col] = ''

ensure_columns()

if "user" not in st.session_state:
    st.session_state.user = None

# User Registration
def create_new_user():
    st.title("Create New User Account")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    role = st.selectbox("Role", ["user", "admin"])
    city = st.text_input("City")
    mobile = st.text_input("Mobile Number (10 digits)")

    if st.button("Create Account"):
        if not mobile.isdigit() or len(mobile) != 10:
            st.error("Enter a valid 10-digit mobile number.")
            return

        if username in st.session_state.users_df["username"].values:
            st.error("Username already exists.")
        else:
            user_id = f"U{len(st.session_state.users_df)+1:04d}"
            hashed_pw = hash_password(password)
            new_user = pd.DataFrame([{ "user_id": user_id, "username": username, "password": hashed_pw, "role": role }])
            new_account = pd.DataFrame([{ "user_id": user_id, "account_no": f"XXXXXXX{random.randint(100,999)}", "address": city, "mobile": mobile, "balance": 0 }])
            st.session_state.users_df = pd.concat([st.session_state.users_df, new_user], ignore_index=True)
            st.session_state.accounts_df = pd.concat([st.session_state.accounts_df, new_account], ignore_index=True)
            save_csv(st.session_state.users_df, users_file)
            save_csv(st.session_state.accounts_df, accounts_file)
            st.success("Account created successfully!")

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

def admin_dashboard():
    st.sidebar.title("Admin Panel")
    option = st.sidebar.radio("Select", ["📃 All Applications", "✅ Approve Loans", "🔍 Fetch User Info"])
    if option == "📃 All Applications":
        st.subheader("All Loan Applications")
        st.dataframe(loans_df.drop(columns=["user_id"], errors="ignore"))

    elif option == "✅ Approve Loans":
        st.subheader("Auto & Manual Loan Approvals")
        model = load_model()
        if model is None:
            st.warning("Not enough data to train model.")
            return

        pending_loans = loans_df[loans_df["status"] == "pending"]
        if pending_loans.empty:
            st.info("No pending loan applications.")
            return

        for idx, row in pending_loans.iterrows():
            X_test = np.array([[row["amount"], row["income"]]])
            prob = model.predict_proba(X_test)[0][1]
            risk_score = round((1 - prob) * 100, 2)
            loan_id = row['loan_id']
            remark = f"Risk Score: {risk_score}%"
            if risk_score <= 39:
                loans_df.at[idx, "status"] = "approved"
                loans_df.at[idx, "remarks"] = f"Auto-approved. {remark}"
            elif risk_score >= 61:
                loans_df.at[idx, "status"] = "declined"
                loans_df.at[idx, "remarks"] = f"Auto-declined. {remark}"
            else:
                st.warning(f"Review Required - Loan ID: {loan_id}")
                st.write(row)
                if st.button(f"Approve {loan_id}"):
                    loans_df.at[idx, "status"] = "approved"
                    loans_df.at[idx, "remarks"] = f"Admin-approved. {remark}"
                    st.experimental_rerun()
                if st.button(f"Decline {loan_id}"):
                    loans_df.at[idx, "status"] = "declined"
                    loans_df.at[idx, "remarks"] = f"Admin-declined. {remark}"
                    st.experimental_rerun()
        save_csv(loans_df, loans_file)

    elif option == "🔍 Fetch User Info":
        st.subheader("Fetch User Details")
        username_input = st.text_input("Enter Username")
        if st.button("Fetch Info"):
            user_info = users_df[users_df["username"] == username_input]
            if user_info.empty:
                st.error("User not found.")
            else:
                user_id = user_info.iloc[0]['user_id']
                account_info = accounts_df[accounts_df['user_id'] == user_id]
                transaction_info = transactions_df[transactions_df['user_id'] == user_id]
                loan_info = loans_df[loans_df['user_id'] == user_id]
                st.write("👤 User Info", user_info.drop(columns=['password'], errors='ignore'))
                st.write("🏦 Account Info", account_info)
                st.write("💸 Transaction History", transaction_info)
                st.write("📄 Loan History", loan_info)

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
          
if st.session_state.user:
    st.sidebar.write(f"👋 Welcome, {st.session_state.user['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()
    if st.session_state.user.get("role") == "admin":
        admin_dashboard()
    else:
        user_dashboard()
else:
    login()
