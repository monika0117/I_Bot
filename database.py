import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("./config.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
#firebase useed
# Authentication functions
def authenticate_user(username, password):
    """Authenticate user and fetch their data from Firestore."""
    try:
        users_ref = db.collection('users')
        query = users_ref.where('username', '==', username).where('password', '==', password).get()

        if query:
            user_data = query[0].to_dict()  # Fetch the first matched user
            print(f"Authenticated User Data: {user_data}")  # Debug print
            st.session_state.authenticated = True
            st.session_state.username = user_data.get('username', 'Guest')  # Save username in session
            return True
        else:
            st.error("Invalid username or password")
            st.session_state.authenticated = False
            return False
    except Exception as e:
        st.error(f"Error authenticating user: {e}")
        return False


def register_user(username, password):
    """Register a new user in the Firestore database."""
    user_ref = db.collection("users").document(username)
    if user_ref.get().exists:
        return False  # User already exists
    
    user_ref.set({"username": username, "password": password})
    return True
# Example Streamlit App
def main():
    st.title("Firebase User Authentication")

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        option = st.radio("Choose an option", ("Login", "Register"))

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if option == "Login":
            if st.button("Login"):
                if authenticate_user(username, password):
                    st.success("Login successful!")
                else:
                    st.error("Invalid username or password.")
        elif option == "Register":
            if st.button("Register"):
                if register_user(username, password):
                    st.success("Registration successful! Please log in.")
    else:
        st.success("You are logged in!")

if __name__ == "__main__":
    main()
