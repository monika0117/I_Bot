import streamlit as st
from PIL import Image
from database import authenticate_user, register_user
from i_bot import run_streamlit_app
#Database    
def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'setprompt' not in st.session_state:
        st.session_state.setprompt = True

    if st.session_state.authenticated:
        run_streamlit_app()
    else:
        authenticate_and_register()


def authenticate_and_register():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    image = Image.open("./logo/mainlogo.png")
    resized_image = image.resize((640, 360))
    col1, col2, col3 = st.columns([1, 2, 1])
    st.markdown(
            """
            <style>
            div.block-container {
                margin-top: -80px;
            }
            </style>
            """,
            unsafe_allow_html=True,
    )

    # Layout to center the image
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(resized_image)

    
    if 'choice' not in st.session_state:
        st.session_state.choice = None

    with st.sidebar:
        st.sidebar.header("Authentication")
        if st.sidebar.button("Login"):
            st.session_state.choice = "Login"
        if st.sidebar.button("Signup"):
            st.session_state.choice = "Register"

    if st.session_state.choice == "Login":
        st.header("Login Page")
        username = st.text_input("Username:")
        password = st.text_input("Password:", type="password")
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        login_button = st.button("Done", key="login_button")

        if login_button:
                # Disable the button after click to prevent double clicks
                st.session_state.login_button_disabled = True
                
                # Authenticate the user
                user = authenticate_user(username, password)
                if user:
                    st.success("Login Successful! Redirecting...")
                    st.session_state.authenticated = True
                    st.session_state.username = username  # Store username in session state
                    # Set query params to indicate the user is logged in
                    st.query_params = {"logged_in": "true"}
                    st.rerun()  # Trigger rerun to show logged-in state
                else:
                    st.error("Invalid username or password. Please try again.")

           


    elif st.session_state.choice == "Register":
        st.header("Register Page")
        new_username = st.text_input("New Username:")
        new_password = st.text_input("New Password:", type="password")
        
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

        if st.button("Done"):
            if register_user(new_username, new_password):
                st.success("Registration Successful!")
                st.write(f"Welcome, {new_username}!")
                st.session_state.authenticated = True
                st.session_state.setprompt = True

if __name__ == "__main__":    
    main()