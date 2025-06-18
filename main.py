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

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None

# Admin Dashboard

def admin_dashboard():
    st.sidebar.title("Admin Panel")
    option = st.sidebar.radio("Select", ["📃 All Applications", "✅ Approve Loans", "🔍 Fetch User Data"])

    if option == "📃 All Applications":
        st.subheader("All Loan Applications")
        st.dataframe(loans_df)

    elif option == "✅ Approve Loans":
        st.subheader("Auto & Manual Loan Approvals")

        train_df = loans_df[loans_df['status'] != 'pending'][["amount", "income", "status"]].dropna()
        if train_df.empty or len(train_df["status"].unique()) < 2:
            st.warning("Not enough historical data to train model.")
            return

        X = train_df[["amount", "income"]]
        y = (train_df["status"] == "approved").astype(int)
        model = LogisticRegression()
        model.fit(X, y)

        pending_loans = loans_df[loans_df["status"] == "pending"]
        review_required = []

        for idx, row in pending_loans.iterrows():
            X_test = np.array([[row["amount"], row["income"]]])
            prob = model.predict_proba(X_test)[0][1]
            risk_score = round((1 - prob) * 100, 2)
            loan_id = row['loan_id']
            remark = f"Predicted Risk Score: {risk_score}%"

            if risk_score <= 39:
                loans_df.loc[loans_df["loan_id"] == loan_id, "status"] = "approved"
                loans_df.loc[loans_df["loan_id"] == loan_id, "remarks"] = f"Auto-approved. {remark}"
            elif risk_score >= 61:
                loans_df.loc[loans_df["loan_id"] == loan_id, "status"] = "declined"
                loans_df.loc[loans_df["loan_id"] == loan_id, "remarks"] = f"Auto-declined. {remark}"
            else:
                review_required.append((row, risk_score))

        save_csv(loans_df, loans_file)

        if review_required:
            st.warning("⚠️ Loans requiring admin review (Average Risk)")
            for row, risk_score in review_required:
                st.markdown(f"### Loan ID: {row['loan_id']}")
                st.write(row)
                st.info(f"Predicted Risk Score: {risk_score}%")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Approve {row['loan_id']}"):
                        loans_df.loc[loans_df["loan_id"] == row["loan_id"], "status"] = "approved"
                        loans_df.loc[loans_df["loan_id"] == row["loan_id"], "remarks"] = f"Admin-approved. Risk Score: {risk_score}%"
                        save_csv(loans_df, loans_file)
                        st.experimental_rerun()
                with col2:
                    if st.button(f"Decline {row['loan_id']}"):
                        loans_df.loc[loans_df["loan_id"] == row["loan_id"], "status"] = "declined"
                        loans_df.loc[loans_df["loan_id"] == row["loan_id"], "remarks"] = f"Admin-declined. Risk Score: {risk_score}%"
                        save_csv(loans_df, loans_file)
                        st.experimental_rerun()

    elif option == "🔍 Fetch User Data":
        st.subheader("Search User by Username")
        query_username = st.text_input("Enter username to search")

        if st.button("Search"):
            if query_username:
                users_df = load_csv(users_file)
                accounts_df = load_csv(accounts_file)
                merged_df = pd.merge(users_df, accounts_df, on="user_id", how="inner")
                result = merged_df[merged_df["username"] == query_username]
                if not result.empty:
                    st.success("User found:")
                    st.dataframe(result)
                else:
                    st.error("No matching user found")
