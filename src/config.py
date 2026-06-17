import os
from dotenv import load_dotenv

load_dotenv()


def get_secret(key):
    """Reads an API key from Streamlit Cloud's secrets manager when deployed,
    falling back to the local .env file during local development. st.secrets
    isn't available (or raises) outside a Streamlit run context, hence the try/except.
    """
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)
