import streamlit as st
from cryptography.fernet import Fernet
from tinydb import TinyDB, Query
import os

# Generate encryption key (store securely, not in the code in production)
def get_fernet_key():
    if not os.path.exists("fernet_key.key"):
        key = Fernet.generate_key()
        with open("fernet_key.key", "wb") as key_file:
            key_file.write(key)
    else:
        with open("fernet_key.key", "rb") as key_file:
            key = key_file.read()
    return key

fernet = Fernet(get_fernet_key())

# Initialize TinyDB
db = TinyDB("api_keys.json")
api_table = db.table("keys")

# Encrypt API key before saving to TinyDB
def save_key(service_name, api_key):
    encrypted_key = fernet.encrypt(api_key.encode()).decode()
    api_table.insert({"service": service_name, "key": encrypted_key})

# Decrypt API key for display or copying
def get_decrypted_key(encrypted_key):
    return fernet.decrypt(encrypted_key.encode()).decode()

# Delete API key from TinyDB
def delete_key(service_name):
    query = Query()
    api_table.remove(query.service == service_name)

# Fetch all keys
def fetch_keys():
    return api_table.all()

# Dark mode toggle
st.set_page_config(page_title="API Key Manager", layout="centered", initial_sidebar_state="expanded")
st.title("🔑 API Key Manager")
st.sidebar.title("Settings")
dark_mode = st.sidebar.checkbox("Enable Dark Mode", value=False)

if dark_mode:
    st.markdown(
        """
        <style>
        body {
            background-color: #2C2F33;
            color: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Tabbed UI
tab1, tab2 = st.tabs(["Manage API Keys", "Add New Key"])

# Core functionalities
with tab1:
    st.header("Stored API Keys")
    
    stored_keys = fetch_keys()
    if stored_keys:
        search = st.text_input("Search keys", key="search_input")
        filtered_keys = [
            key for key in stored_keys if search.lower() in key["service"].lower()
        ]

        for key in filtered_keys:
            service = key["service"]
            api_key = key["key"]
            decrypted_key = get_decrypted_key(api_key)

            col1, col2, col3 = st.columns([3, 1, 1])
            col1.text(service)
            col2.button(
                "Copy", 
                key=f"copy_{service}", 
                on_click=lambda key=decrypted_key: st.experimental_set_query_params(key=key)
            )
            if col3.button("Delete", key=f"delete_{service}"):
                delete_key(service)
                st.experimental_rerun()

        if not filtered_keys:
            st.info("No matching keys found.")
    else:
        st.info("No API keys stored. Add a new key using the tab above.")

with tab2:
    st.header("Add a New API Key")

    with st.form("add_key_form"):
        service_name = st.text_input("Service Name", placeholder="Enter service name")
        api_key = st.text_input("API Key", placeholder="Enter API key", type="password")
        submitted = st.form_submit_button("Add Key")

        if submitted:
            if not service_name or not api_key:
                st.error("Both fields are required.")
            elif any(key["service"] == service_name for key in fetch_keys()):
                st.warning("Service name already exists.")
            else:
                save_key(service_name, api_key)
                st.success("API key added successfully.")
                st.experimental_rerun()

# Copy API Key to clipboard
if st.experimental_get_query_params().get("key"):
    st.write(
        """
        <script>
        navigator.clipboard.writeText("{key}");
        </script>
        """.format(key=st.experimental_get_query_params()["key"][0]),
        unsafe_allow_html=True,
    )
    st.success("API Key copied to clipboard!")
