
import streamlit as st
import pandas as pd
import os
import random
from sklearn.linear_model import LogisticRegression
import numpy as np

# File paths
data_path = "data"
users_file = os.path.join(data_path, "users.csv")
accounts_file = os.path.join(data_path, "accounts.csv")
loans_file = os.path.join(data_path, "loan_applications.csv")
loan_status_file = os.path.join(data_path, "loan_status.csv")
transactions_file = os.path.join(data_path, "transactions.csv")

# Load CSV safely
def load_csv(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

def save_csv(df, file):
    df.to_csv(file, index=False)

# Load data
users_df = load_csv(users_file)
accounts_df = load_csv(accounts_file)
loans_df = load_csv(loans_file)
transactions_df = load_csv(transactions_file)

# Add missing columns if needed
if 'status' not in loans_df.columns:
    loans_df['status'] = 'pending'

for col in ['account_no', 'address', 'balance']:
    if col not in accounts_df.columns:
        accounts_df[col] = ''

if 'mobile' not in accounts_df.columns:
    accounts_df['mobile'] = ''

# Session initialization
if "user" not in st.session_state:
    st.session_state.user = None

# Account creation
def create_new_user():
    st.title("Create New User Account")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    role = st.selectbox("Role", ["user", "admin"])
    city = st.text_input("City")
    mobile = st.text_input("Mobile Number")

    if st.button("Create Account"):
        if username in users_df["username"].values:
            st.error("Username already exists.")
        else:
            user_id = f"U{len(users_df)+1:04d}"
            account_no = f"XXXXXXX{random.randint(100,999)}"
            new_user = pd.DataFrame([{
                "user_id": user_id, "username": username, "password": password, "role": role
            }])
            new_account = pd.DataFrame([{
                "user_id": user_id, "account_no": account_no, "address": city, "mobile": mobile, "balance": 0
            }])
            save_csv(pd.concat([users_df, new_user], ignore_index=True), users_file)
            save_csv(pd.concat([accounts_df, new_account], ignore_index=True), accounts_file)
            st.success("Account created successfully!")

# Login
def login():
    st.title("SKS Bank ")
    action = st.radio("Choose an action", ["Login", "Create Account"])

    if action == "Create Account":
        create_new_user()
        return

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = users_df[(users_df["username"] == username) & (users_df["password"] == password)]
        if not user.empty:
            st.session_state.user = user.iloc[0].to_dict()
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

# User Dashboard
def user_dashboard():
    user_id = st.session_state.user["user_id"]
    st.sidebar.title("User Menu")
    menu = st.sidebar.radio("Navigate", ["Account Summary", "Apply for Loan", "Loan Status", "Transactions"])

    if menu == "Account Summary":
        st.subheader("Account Summary")
        acc = accounts_df[accounts_df["user_id"] == user_id][["account_no", "address", "balance", "mobile"]]
        st.dataframe(acc)

    elif menu == "Apply for Loan":
        st.subheader("Apply for a New Loan")
        amount = st.number_input("Loan Amount", min_value=1000)
        purpose = st.text_input("Purpose")
        income = st.number_input("Monthly Income", min_value=0)
        if st.button("Submit Application"):
            loan_id = f"L{len(loans_df)+1:04d}"
            loan = pd.DataFrame([{
                "loan_id": loan_id,
                "user_id": user_id,
                "amount": amount,
                "purpose": purpose,
                "income": income,
                "status": "pending",
                "application_date": pd.Timestamp.today().strftime('%Y-%m-%d'),
                "remarks": "Awaiting review"
            }])
            save_csv(pd.concat([loans_df, loan], ignore_index=True), loans_file)
            st.success("Loan application submitted!")

    elif menu == "Loan Status":
        st.subheader("Your Loan Applications")
        st.dataframe(loans_df[loans_df["user_id"] == user_id])

    elif menu == "Transactions":
        st.subheader("Transaction History")
        st.dataframe(transactions_df[transactions_df["user_id"] == user_id])

# Admin Dashboard
def admin_dashboard():
    st.sidebar.title("Admin Panel")
    option = st.sidebar.radio("Choose Action", ["All Applications", "Approve Loans"])

    if option == "All Applications":
        st.subheader("All Loan Applications")
        st.dataframe(loans_df)

    elif option == "Approve Loans":
        st.subheader("Loan Approval Panel")
        pending = loans_df[loans_df["status"] == "pending"]

        if pending.empty:
            st.info("No pending loans.")
        else:
            train_df = loans_df[loans_df["status"] != "pending"]
            if not train_df.empty:
                model = LogisticRegression()
                X = train_df[["amount", "income"]]
                y = (train_df["status"] == "approved").astype(int)
                model.fit(X, y)

                for idx, row in pending.iterrows():
                    X_test = np.array([[row["amount"], row["income"]]])
                    prob = model.predict_proba(X_test)[0][1]
                    risk_score = round(prob * 100, 2)

                    with st.expander(f"Loan ID: {row['loan_id']} - {row['user_id']}"):
                        st.write(f"Amount: ₹{row['amount']}, Income: ₹{row['income']}")
                        st.info(f"Predicted Approval Probability: {risk_score}%")

                        col1, col2 = st.columns(2)
                        if col1.button(f"Approve {row['loan_id']}", key=f"a{idx}"):
                            loans_df.at[idx, "status"] = "approved"
                            loans_df.at[idx, "remarks"] = f"Approved with risk {risk_score}%"
                            save_csv(loans_df, loans_file)
                            st.success("Approved")
                            st.experimental_rerun()

                        if col2.button(f"Decline {row['loan_id']}", key=f"d{idx}"):
                            loans_df.at[idx, "status"] = "declined"
                            loans_df.at[idx, "remarks"] = f"Declined with risk {risk_score}%"
                            save_csv(loans_df, loans_file)
                            st.error("Declined")
                            st.experimental_rerun()

# App Router
if st.session_state.user:
    st.sidebar.write(f"👤 Logged in as: {st.session_state.user['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()
    if st.session_state.user["role"] == "user":
        user_dashboard()
    else:
        admin_dashboard()
else:
    login()
