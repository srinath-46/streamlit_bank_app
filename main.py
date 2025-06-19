import streamlit as st
import pandas as pd
import os
import random
import hashlib
import numpy as np
from sklearn.linear_model import LogisticRegression

# Paths to CSV files
data_path = "data"
users_file = os.path.join(data_path, "users.csv")
accounts_file = os.path.join(data_path, "accounts.csv")
loans_file = os.path.join(data_path, "loan_applications.csv")
loan_status_file = os.path.join(data_path, "loan_status.csv")
transactions_file = os.path.join(data_path, "transactions.csv")

# Hashing passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

# Load data into session state
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

# Create New User
def create_new_user():
    st.title("Create New User Account")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    role = st.selectbox("Role", ["user"])
    city = st.text_input("City")
    mobile = st.text_input("Mobile Number (e.g., xxxxxxx237)")

    if st.button("Create Account"):
        if username in users_df["username"].values:
            st.error("Username already exists.")
        else:
            user_id = f"U{len(users_df)+1:04d}"
            new_user = pd.DataFrame([{
                "user_id": user_id,
                "username": username,
                "password": hash_password(password),
                "role": role
            }])
            new_account = pd.DataFrame([{
                "user_id": user_id,
                "account_no": f"XXXXXXX{random.randint(100,999)}",
                "address": city,
                "mobile": mobile,
                "balance": 0
            }])
            users_df_updated = pd.concat([users_df, new_user], ignore_index=True)
            accounts_df_updated = pd.concat([accounts_df, new_account], ignore_index=True)
            save_csv(users_df_updated, users_file)
            save_csv(accounts_df_updated, accounts_file)
            st.success("Account created successfully!")
            st.info(f"Username: {username} | Account No: {new_account.iloc[0]['account_no']}")

# Login Page
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
                users_df.loc[users_df["username"] == username, "password"] = hash_password(new_password)
                save_csv(users_df, users_file)
                st.success("✅ Password reset successful!")
        return

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users_df = load_csv(users_file)
        user = users_df[
            (users_df["username"] == username) &
            (users_df["password"] == hash_password(password))
        ]
        if not user.empty:
            st.session_state.user = user.iloc[0].to_dict()
            st.success(f"Logged in as {username}")
            st.rerun()
        else:
            st.error("Invalid username or password.")

# Admin Dashboard
def admin_dashboard():
    st.sidebar.title("Admin Panel")
    option = st.sidebar.radio("Select", ["📃 All Applications", "✅ Approve Loans", "🔍 Fetch User Info"])

    if option == "📃 All Applications":
        st.subheader("All Loan Applications")
        st.dataframe(loans_df)

    elif option == "✅ Approve Loans":
        st.subheader("Auto & Manual Loan Approvals")
        train_df = loans_df[loans_df["status"] != "pending"]
        if train_df.empty or len(train_df["status"].unique()) < 2:
            st.warning("Not enough historical data.")
            return
        train_df = train_df[["amount", "income", "status"]].dropna()
        X = train_df[["amount", "income"]]
        y = (train_df["status"] == "approved").astype(int)
        model = LogisticRegression()
        model.fit(X, y)
        pending_loans = loans_df[loans_df["status"] == "pending"]
        if pending_loans.empty:
            st.info("No pending applications.")
            return
        review_required = []
        for idx, row in pending_loans.iterrows():
            prob = model.predict_proba([[row["amount"], row["income"]]])[0][1]
            risk_score = round((1 - prob) * 100, 2)
            loan_id = row['loan_id']
            if risk_score <= 39:
                loans_df.loc[loans_df["loan_id"] == loan_id, "status"] = "approved"
                loans_df.loc[loans_df["loan_id"] == loan_id, "remarks"] = f"Auto-approved. Risk Score: {risk_score}%"
                st.success(f"✅ Loan {loan_id} auto-approved")
            elif risk_score >= 61:
                loans_df.loc[loans_df["loan_id"] == loan_id, "status"] = "declined"
                loans_df.loc[loans_df["loan_id"] == loan_id, "remarks"] = f"Auto-declined. Risk Score: {risk_score}%"
                st.error(f"❌ Loan {loan_id} auto-declined")
            else:
                review_required.append((row, risk_score))
        save_csv(loans_df, loans_file)
        if review_required:
            st.warning("Loans requiring manual review:")
            for row, risk_score in review_required:
                st.markdown(f"### Loan ID: {row['loan_id']}")
                st.write(row)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Approve {row['loan_id']}"):
                        loans_df.loc[loans_df["loan_id"] == row["loan_id"], "status"] = "approved"
                        save_csv(loans_df, loans_file)
                        st.rerun()
                with col2:
                    if st.button(f"Decline {row['loan_id']}"):
                        loans_df.loc[loans_df["loan_id"] == row["loan_id"], "status"] = "declined"
                        save_csv(loans_df, loans_file)
                        st.rerun()

    elif option == "🔍 Fetch User Info":
        username_input = st.text_input("Enter Username")
        if st.button("Fetch Info"):
            user_info = users_df[users_df["username"] == username_input]
            if user_info.empty:
                st.error("User not found.")
            else:
                user_id = user_info.iloc[0]['user_id']
                st.write("👤 User Info", user_info.drop(columns=['password'], errors='ignore'))
                st.write("🏦 Account Info", accounts_df[accounts_df['user_id'] == user_id])
                st.write("💸 Transactions", transactions_df[transactions_df['user_id'] == user_id])
                st.write("📄 Loans", loans_df[loans_df['user_id'] == user_id])

# User Dashboard
def user_dashboard():
    st.sidebar.title("User Menu")
    choice = st.sidebar.radio("Go to", ["📈 Account Summary", "📝 Apply for Loan", "📊 Loan Status", "💵 Transactions", "💳 Pay Loan Dues"])
    user_id = st.session_state.user["user_id"]

    if choice == "📈 Account Summary":
        st.subheader("Account Summary")
        st.dataframe(accounts_df[accounts_df["user_id"] == user_id])

    elif choice == "📝 Apply for Loan":
        st.subheader("Loan Application")
        amount = st.number_input("Loan Amount", min_value=1000)
        purpose = st.selectbox("Purpose", ["Education", "Medical", "Home Renovation", "Vehicle", "Business", "Personal"])
        income = st.number_input("Monthly Income", min_value=0)
        if st.button("Submit Application"):
            loan_id = f"L{len(loans_df)+1:03d}"
            new_loan = pd.DataFrame([{
                "loan_id": loan_id,
                "user_id": user_id,
                "amount": amount,
                "purpose": purpose,
                "income": income,
                "status": "pending",
                "application_date": pd.Timestamp.today().strftime('%Y-%m-%d'),
                "remarks": "Awaiting review"
            }])
            loans_df_updated = pd.concat([loans_df, new_loan], ignore_index=True)
            save_csv(loans_df_updated, loans_file)
            save_csv(loans_df_updated, loan_status_file)
            st.session_state.loans_df = loans_df_updated
            st.session_state.loan_status_df = loans_df_updated
            st.success("Loan application submitted!")

    elif choice == "📊 Loan Status":
        st.subheader("Your Loan Applications")
        user_loans = loan_status_df[loan_status_df["user_id"] == user_id]
        st.dataframe(user_loans)

    elif choice == "💵 Transactions":
        st.subheader("Your Transactions")
        tx = transactions_df[transactions_df["user_id"] == user_id]
        st.dataframe(tx)

    elif choice == "💳 Pay Loan Dues":
        st.subheader("Pay Loan Dues")
        user_loans = loans_df[(loans_df["user_id"] == user_id) & (loans_df["status"] == "approved")]
        if user_loans.empty:
            st.info("No loans due.")
            return
        selected_loan = st.selectbox("Select Loan ID", user_loans["loan_id"])
        due_amount = user_loans[user_loans["loan_id"] == selected_loan]["amount"].values[0]
        st.write(f"Due Amount: ₹{due_amount}")
        method = st.radio("Payment Method", ["UPI", "Online Banking"])
        if st.button("Pay Now"):
            new_tx = pd.DataFrame([{
                "user_id": user_id,
                "loan_id": selected_loan,
                "amount": due_amount,
                "method": method,
                "date": pd.Timestamp.today().strftime('%Y-%m-%d')
            }])
            updated_tx = pd.concat([transactions_df, new_tx], ignore_index=True)
            save_csv(updated_tx, transactions_file)
            st.session_state.transactions_df = updated_tx
            st.success(f"Paid ₹{due_amount} via {method}")

# Run app
if st.session_state.user:
    st.sidebar.write(f"👋 Welcome, {st.session_state.user['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()
    if st.session_state.user["role"] == "admin":
        admin_dashboard()
    else:
        user_dashboard()
else:
    login()
