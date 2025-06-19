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

# Load and Save CSV
def load_csv(file, expected_columns=None):
    try:
        if os.path.exists(file):
            df = pd.read_csv(file)
            if expected_columns:
                for col in expected_columns:
                    if col not in df.columns:
                        df[col] = np.nan
            return df
        else:
            return pd.DataFrame(columns=expected_columns if expected_columns else [])
    except Exception as e:
        st.error(f"Error loading {file}: {e}")
        return pd.DataFrame(columns=expected_columns if expected_columns else [])

def save_csv(df, file):
    try:
        df.to_csv(file, index=False)
    except Exception as e:
        st.error(f"Error saving {file}: {e}")

# Load data into session state
def load_data_to_session():
    st.session_state.users_df = load_csv(users_file, ["user_id", "username", "password", "role"])
    st.session_state.accounts_df = load_csv(accounts_file, ["user_id", "account_no", "address", "mobile", "balance"])
    st.session_state.loans_df = load_csv(loans_file, ["loan_id", "user_id", "amount", "purpose", "income", "status", "application_date", "remarks"])
    st.session_state.loan_status_df = load_csv(loan_status_file, ["loan_id", "user_id", "amount", "purpose", "income", "status", "application_date", "remarks"])
    st.session_state.transactions_df = load_csv(transactions_file, ["user_id", "loan_id", "amount", "method", "date"])

load_data_to_session()

users_df = st.session_state.users_df
accounts_df = st.session_state.accounts_df
loans_df = st.session_state.loans_df
loan_status_df = st.session_state.loan_status_df
transactions_df = st.session_state.transactions_df

if "user" not in st.session_state:
    st.session_state.user = None

# Registration and Login
def create_new_user():
    st.title("Create New User Account")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    role = st.selectbox("Role", ["user"])
    city = st.text_input("City")
    mobile = st.text_input("Mobile Number (e.g., xxxxxxx237)")

    if st.button("Create Account"):
        if username in users_df["username"].values:
            st.error("Username already exists. Please choose another.")
        else:
            user_id = f"U{len(users_df)+1:04d}"
            new_user = pd.DataFrame([{"user_id": user_id, "username": username, "password": password, "role": role}])
            new_account = pd.DataFrame([{"user_id": user_id, "account_no": f"XXXXXXX{random.randint(100,999)}", "address": city, "mobile": mobile, "balance": 0}])
            users_df_updated = pd.concat([users_df, new_user], ignore_index=True)
            accounts_df_updated = pd.concat([accounts_df, new_account], ignore_index=True)
            save_csv(users_df_updated, users_file)
            save_csv(accounts_df_updated, accounts_file)
            st.success("Account created successfully!")

def login():
    st.title("Indian Bank")
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
        user = users_df[
            (users_df["username"] == username) &
            (users_df["password"] == password)
        ]
        if not user.empty:
            st.session_state.user = user.iloc[0].to_dict()
            st.success(f"Logged in as {username}")
            st.rerun()
        else:
            st.error("Invalid username or password")

# User Dashboard
def user_dashboard():
    st.sidebar.title("User Menu")
    choice = st.sidebar.radio("Go to", [
        "📈 Account Summary",
        "📝 Apply for Loan",
        "📊 Loan Status",
        "💵 Transactions",
        "💳 Pay Loan Dues",
        "📚 Loan Repayment History",
        "🧮 EMI Calculator"
    ])
    user_id = st.session_state.user["user_id"]

    if choice == "📈 Account Summary":
        st.subheader("Account Summary")
        acc = accounts_df[accounts_df["user_id"] == user_id]
        st.dataframe(acc)

    elif choice == "📝 Apply for Loan":
        st.subheader("Loan Application Form")
        amount = st.number_input("Loan Amount", min_value=1000)
        purpose = st.selectbox("Purpose", ["Education", "Medical", "Home Renovation", "Vehicle", "Business", "Personal"])
        income = st.number_input("Monthly Income", min_value=0)
        if st.button("Submit Application"):
            loan_id = f"L{len(loans_df)+1:03d}"
            new_loan = {
                "loan_id": loan_id,
                "user_id": user_id,
                "amount": amount,
                "purpose": purpose,
                "income": income,
                "status": "pending",
                "application_date": pd.Timestamp.today().strftime('%Y-%m-%d'),
                "remarks": "Awaiting review"
            }
            loans_df_updated = pd.concat([loans_df, pd.DataFrame([new_loan])], ignore_index=True)
            st.session_state.loans_df = loans_df_updated
            st.session_state.loan_status_df = loans_df_updated
            save_csv(loans_df_updated, loans_file)
            save_csv(loans_df_updated, loan_status_file)
            st.success("Loan Application Submitted!")

    elif choice == "📊 Loan Status":
        st.subheader("Your Loan Applications")
        user_loans = loans_df[loans_df["user_id"] == user_id]
        st.dataframe(user_loans)

    elif choice == "💵 Transactions":
        st.subheader("Transaction History")
        tx = transactions_df[transactions_df["user_id"] == user_id]
        st.dataframe(tx)

    elif choice == "💳 Pay Loan Dues":
        st.subheader("Pay Loan Dues")
        user_loans = loans_df[(loans_df["user_id"] == user_id) & (loans_df["status"] == "approved")]
        if user_loans.empty:
            st.info("No approved loans with dues found.")
            return
        selected_loan = st.selectbox("Select Loan ID", user_loans["loan_id"].values)
        due_amount = user_loans[user_loans["loan_id"] == selected_loan]["amount"].values[0]
        st.write(f"Total Due Amount: ₹{due_amount}")
        payment_method = st.radio("Choose Payment Method", ["UPI", "Online Banking"])
        if st.button("Pay Now"):
            new_tx = {
                "user_id": user_id,
                "loan_id": selected_loan,
                "amount": due_amount,
                "method": payment_method,
                "date": pd.Timestamp.today().strftime('%Y-%m-%d')
            }
            transactions_df.loc[len(transactions_df.index)] = new_tx
            save_csv(transactions_df, transactions_file)
            st.success(f"Payment of ₹{due_amount} via {payment_method} successful!")

    elif choice == "📚 Loan Repayment History":
        st.subheader("Loan Repayment History")
        user_tx = transactions_df[transactions_df["user_id"] == user_id]

        required_cols = {"loan_id", "amount"}
        if not required_cols.issubset(user_tx.columns):
            st.warning("⚠️ Transactions data is missing 'loan_id' or 'amount' columns.")
            return

        if user_tx.empty:
            st.info("No repayments made yet.")
        else:
            st.dataframe(user_tx)
            summary = user_tx.groupby("loan_id")["amount"].sum().reset_index().rename(columns={"amount": "Total Paid"})
            st.write("### Summary of Paid Amount by Loan")
            st.dataframe(summary)

    elif choice == "🧮 EMI Calculator":
        st.subheader("Monthly EMI Calculator")
        loan_amount = st.number_input("Enter Loan Amount", min_value=1000)
        interest_rate = st.number_input("Annual Interest Rate (in %)", min_value=0.0)
        tenure = st.number_input("Loan Tenure (in months)", min_value=1)
        if st.button("Calculate EMI"):
            monthly_rate = interest_rate / (12 * 100)
            emi = (loan_amount * monthly_rate * (1 + monthly_rate)**tenure) / ((1 + monthly_rate)**tenure - 1)
            st.success(f"Your Monthly EMI is ₹{emi:.2f}")

# Main App Logic
if st.session_state.user:
    st.sidebar.write(f"👋 Welcome, {st.session_state.user['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()
    if st.session_state.user.get("role") == "admin":
        admin_dashboard()  # Assume you have defined this already above
    else:
        user_dashboard()
else:
    login()
