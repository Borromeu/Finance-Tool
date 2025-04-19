import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json
import os

st.set_page_config(
    page_title="Simple Finance App",
    page_icon="📊",
    layout="wide"
)
category_file = "categories.json"

if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": [],
    }
    
if os.path.exists(category_file):
    with open(category_file, "r") as f:
        st.session_state.categories = json.load(f)

def save_categories():
    with open("categories.json", "w") as f:
        json.dump(st.session_state.categories, f)

def categorize_transaction(df):
    df["Category"] = "Uncategorized"
    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue
        lower_keywords = [kw.lower().strip() for kw in keywords]
        for idx, row in df.iterrows():
            details = row["Details"].lower().strip()
            if details in lower_keywords:
                df.at[idx, "Category"] = category
                break
    return df
        
def load_transactions(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]
        df['Amount'] = df['Amount'].str.replace(',', '').astype(float)
        df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y')
        
        return categorize_transaction(df)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def add_keyword_to_category(category, keyword):
    if category in st.session_state.categories:
        if keyword not in st.session_state.categories[category]:
            st.session_state.categories[category].append(keyword)
            save_categories()
        else:
            st.warning(f"Keyword '{keyword}' already exists in category '{category}'.")
    else:
        st.error(f"Category '{category}' does not exist.")

def setup_add_keyword(key_category):
    category = st.selectbox("Select Category", options=list(st.session_state.categories.keys()), key=key_category)
    keyword = st.text_input("Keyword to add", key=f"keyword_{key_category}")
    add_button_key = st.button("Add Keyword", key=f"add_button_{key_category}")
    
    if add_button_key:
        if keyword:
            add_keyword_to_category(category, keyword)
            st.rerun()
        else:
            st.warning("Please enter a keyword.")
            
def add_category(key_category):
    new_category = st.text_input("New category name", key=key_category)
    add_button = st.button("Add Category", key=f"add_button_{key_category}")
    
    if add_button and new_category:
        if new_category not in st.session_state.categories:
            st.session_state.categories[new_category] = []
            save_categories()
            st.rerun()
        else:
            st.warning(f"Category '{new_category}' already exists.")
def main():
    st.title("Simple Finance Dashboard")
    
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    
    if uploaded_file is not None:
        df = load_transactions(uploaded_file)
        
        if df is not None:
            debits_df = df[df['Debit/Credit'] == "Debit"].copy()
            credits_df = df[df['Debit/Credit'] == "Credit"].copy()
            
            st.session_state.debits_df = debits_df.copy()
            tab1, tab2 = st.tabs(["Expenses (Debits)", "Payments (Credits)"])
            
            with tab1:
                add_category("debit_category")
                setup_add_keyword("debit_category_keyword")
                
                st.subheader("Expenses (Debits)")
                edited_debits_df = st.data_editor(
                    st.session_state.debits_df[["Date", "Details", "Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
                        "Details": st.column_config.NumberColumn("Amount", format="%.2f AED"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys()),
                        ),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="debits_df_editor"
                )
                
                save_button = st.button("Save Changes", key="save_debits")
                if save_button:
                    for idx, row in edited_debits_df.iterrows():
                        new_category = row["Category"]
                        if new_category == st.session_state.debits_df.at[idx, "Category"]:
                            continue
                        details = row["Details"]
                        st.session_state.debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)
                
                st.subheader("Expenses Summary")
                category_totals = st.session_state.debits_df.groupby("Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values(by="Amount", ascending=False)
                
                st.dataframe(category_totals, 
                             column_config=
                                {   
                                    "Amount": st.column_config.NumberColumn("Amount", format="%.2f AED")
                                }, 
                             use_container_width=True, hide_index=True)
                fig  = px.pie(
                    category_totals,
                    values='Amount',
                    names='Category',
                    title='Expenses by Category'
                )
                
                st.plotly_chart(fig)
                
            with tab2:
                add_category("credit_category")
                setup_add_keyword("credit_category_keyword")
                st.write(credits_df)
                

if __name__ == "__main__":
    main()