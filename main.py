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
    st.title("lavudhu Bank 69 ")
    menu = st.radio("Select an option", ["Login", "Create Account"])

    if menu == "Create Account":
        create_new_user()
        return

    username = st.text_input("gopamavan ")
    password = st.text_input("irumbu kol ᵍⁱᵛᵉ ᵐᵉ ʸᵒᵘʳ ᵖᵘˢˢʸ", type="password")

    if st.button("oombu ᶠᶸᶜᵏMe𓀐𓂸"):
        users_df = pd.read_csv("data/users.csv")

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
    choice = st.sidebar.radio("Go to", ["\U0001F4C8 Account Summary", "\U0001F4DD Apply for Loan", "\U0001F4CA Loan Status", "\U0001F4B5 Transactions"])
    user_id = st.session_state.user["user_id"]

    if choice == "\U0001F4C8 Account Summary":
        acc = accounts_df[accounts_df["user_id"] == user_id][["account_no", "address", "balance"]]
        st.subheader("Account Summary")
        st.dataframe(acc)

    elif choice == "\U0001F4DD Apply for Loan":
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
    option = st.sidebar.radio("Select", ["\U0001F4C3 All Applications", "✅ Approve Loans"])

    if option == "\U0001F4C3 All Applications":
        st.subheader("All Loan Applications")
        st.dataframe(loans_df)

    elif option == "✅ Approve Loans":
        st.subheader("Approve or Reject Loans")

        # Simple risk model (dummy training)
        if len(loans_df) > 0:
            X = loans_df[(loans_df['status'] != 'pending')][["amount", "income"]]
            y = (loans_df[(loans_df['status'] != 'pending')]["status"] == "approved").astype(int)

            if len(X) > 0:
                model = LogisticRegression()
                model.fit(X, y)

                for i, row in loans_df.iterrows():
                    if row["status"] == "pending":
                        X_test = np.array([[row["amount"], row["income"]]])
                        prob = model.predict_proba(X_test)[0][1]
                        risk_score = round(prob * 100, 2)

                        st.markdown(f"### Loan ID: {row['loan_id']}")
                        st.write(row)
                        st.info(f"Predicted Approval Probability: {risk_score}%")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Accept {row['loan_id']}"):
                                loans_df.at[i, "status"] = "approved"
                                loans_df.at[i, "remarks"] = f"Auto-approved. Risk Score: {risk_score}%"
                                save_csv(loans_df, loans_file)
                                st.success(f"Loan {row['loan_id']} approved")
                        with col2:
                            if st.button(f"Decline {row['loan_id']}"):
                                loans_df.at[i, "status"] = "declined"
                                loans_df.at[i, "remarks"] = f"Declined by admin. Risk Score: {risk_score}%"
                                save_csv(loans_df, loans_file)
                                st.error(f"Loan {row['loan_id']} declined")

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
