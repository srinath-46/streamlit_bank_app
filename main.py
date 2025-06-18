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

# Load and save data
def load_csv(file): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()
def save_csv(df, file): df.to_csv(file, index=False)

# Load all CSVs
users_df = load_csv(users_file)
accounts_df = load_csv(accounts_file)
loans_df = load_csv(loans_file)
loan_status_df = load_csv(loan_status_file)
transactions_df = load_csv(transactions_file)

# Initialize columns if missing
if 'status' not in loans_df.columns: loans_df['status'] = 'pending'
if 'remarks' not in loans_df.columns: loans_df['remarks'] = ''
for col in ['account_no', 'address', 'balance']:
    if col not in accounts_df.columns:
        accounts_df[col] = '' if col != 'balance' else 0

# Session state
if "user" not in st.session_state: st.session_state.user = None

# ✅ Create New User
def create_new_user():
    st.title("Create New User Account")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    role = st.selectbox("Role", ["user", "admin"])
    city = st.text_input("City")
    mobile = st.text_input("Mobile Number (e.g., xxxxxxx237)")

    if st.button("Create Account"):
        if username in users_df["username"].values:
            st.error("Username already exists.")
        else:
            user_id = f"U{len(users_df)+1:04d}"
            new_user = pd.DataFrame([{"user_id": user_id, "username": username, "password": password, "role": role}])
            new_account = pd.DataFrame([{
                "user_id": user_id, "account_no": f"XXXXXXX{random.randint(100,999)}",
                "address": city, "mobile": mobile, "balance": 0
            }])
            save_csv(pd.concat([users_df, new_user], ignore_index=True), users_file)
            save_csv(pd.concat([accounts_df, new_account], ignore_index=True), accounts_file)
            st.success("Account created successfully!")

# ✅ Login Page
def login():
    st.title("Lavudhu Bank 69")
    menu = st.radio("Select", ["Login", "Create Account", "Forgot Password?"])

    if menu == "Create Account":
        create_new_user()
        return

    if menu == "Forgot Password?":
        st.subheader("Reset Password")
        username = st.text_input("Enter username")
        mobile = st.text_input("Enter registered mobile number")
        new_password = st.text_input("Enter new password", type="password")
        if st.button("Reset Password"):
            user_row = users_df[users_df["username"] == username]
            if user_row.empty:
                st.error("❌ Username not found.")
                return
            user_id = user_row.iloc[0]["user_id"]
            acc_row = accounts_df[(accounts_df["user_id"] == user_id) & (accounts_df["mobile"] == mobile)]
            if acc_row.empty:
                st.error("❌ Mobile number mismatch.")
            else:
                users_df.loc[users_df["username"] == username, "password"] = new_password
                save_csv(users_df, users_file)
                st.success("✅ Password reset successful!")
        return

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = users_df[(users_df["username"] == username) & (users_df["password"] == password)]
        if not user.empty:
            st.session_state.user = user.iloc[0].to_dict()
            st.success(f"Welcome {username}")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# ✅ User Dashboard
def user_dashboard():
    st.sidebar.title("User Menu")
    choice = st.sidebar.radio("Go to", ["📈 Account Summary", "📝 Apply for Loan", "📊 Loan Status", "💵 Transactions"])
    user_id = st.session_state.user["user_id"]

    if choice == "📈 Account Summary":
        acc = accounts_df[accounts_df["user_id"] == user_id][["account_no", "address", "balance"]]
        st.subheader("Account Summary")
        st.dataframe(acc)

    elif choice == "📝 Apply for Loan":
        st.subheader("Loan Application")
        amount = st.number_input("Loan Amount", min_value=1000)
        purpose = st.text_input("Purpose")
        income = st.number_input("Monthly Income", min_value=0)
        if st.button("Submit Application"):
            loan_id = f"L{len(loans_df)+1:03d}"
            new_loan = {
                "loan_id": loan_id, "user_id": user_id, "amount": amount,
                "purpose": purpose, "income": income,
                "status": "pending", "application_date": pd.Timestamp.today().strftime('%Y-%m-%d'),
                "remarks": "Awaiting review"
            }
            save_csv(pd.concat([loans_df, pd.DataFrame([new_loan])], ignore_index=True), loans_file)
            st.success("Loan Application Submitted!")

    elif choice == "📊 Loan Status":
        st.subheader("Your Loan Applications")
        user_loans = loans_df[loans_df["user_id"] == user_id]
        st.dataframe(user_loans)

    elif choice == "💵 Transactions":
        st.subheader("Transaction History")
        st.dataframe(transactions_df[transactions_df["user_id"] == user_id])

# ✅ Admin Dashboard
def admin_dashboard():
    st.sidebar.title("Admin Panel")
    option = st.sidebar.radio("Select", ["📃 All Applications", "✅ Approve Loans", "🔍 Fetch User Data"])

    if option == "📃 All Applications":
        st.subheader("All Loan Applications")
        st.dataframe(loans_df)

    elif option == "✅ Approve Loans":
        st.subheader("Auto & Manual Loan Approval")
        train_df = loans_df[loans_df["status"] != "pending"]
        if train_df.empty or len(train_df["status"].unique()) < 2:
            st.warning("Not enough data to train model.")
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
            X_test = np.array([[row["amount"], row["income"]]])
            prob = model.predict_proba(X_test)[0][1]
            risk_score = round((1 - prob) * 100, 2)
            remark = f"Risk Score: {risk_score}%"
            if risk_score <= 39:
                loans_df.loc[loans_df["loan_id"] == row["loan_id"], ["status", "remarks"]] = ["approved", f"Auto-approved. {remark}"]
                st.success(f"✅ Loan {row['loan_id']} auto-approved (Low Risk)")
            elif risk_score >= 61:
                loans_df.loc[loans_df["loan_id"] == row["loan_id"], ["status", "remarks"]] = ["declined", f"Auto-declined. {remark}"]
                st.error(f"❌ Loan {row['loan_id']} auto-declined (High Risk)")
            else:
                review_required.append((row, risk_score))

        save_csv(loans_df, loans_file)

        if review_required:
            st.warning("⚠️ Admin Review Required")
            for row, risk_score in review_required:
                st.markdown(f"### Loan ID: {row['loan_id']}")
                st.write(row)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Approve {row['loan_id']}"):
                        loans_df.loc[loans_df["loan_id"] == row["loan_id"], ["status", "remarks"]] = ["approved", f"Admin-approved. Risk Score: {risk_score}%"]
                        save_csv(loans_df, loans_file)
                        st.success(f"Loan {row['loan_id']} approved")
                        st.experimental_rerun()
                with col2:
                    if st.button(f"Decline {row['loan_id']}"):
                        loans_df.loc[loans_df["loan_id"] == row["loan_id"], ["status", "remarks"]] = ["declined", f"Admin-declined. Risk Score: {risk_score}%"]
                        save_csv(loans_df, loans_file)
                        st.error(f"Loan {row['loan_id']} declined")
                        st.experimental_rerun()

    elif option == "🔍 Fetch User Data":
        st.subheader("Search User and Account Info")
        search_id = st.text_input("Enter Username or User ID")
        if st.button("Search"):
            merged = pd.merge(users_df, accounts_df, on="user_id", how="outer")
            results = merged[
                (merged["username"].str.lower() == search_id.lower()) |
                (merged["user_id"].str.lower() == search_id.lower())
            ]
            if not results.empty:
                st.write(results)
            else:
                st.warning("User not found.")

# ✅ Routing Logic
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
