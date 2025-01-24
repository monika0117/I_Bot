import mysql.connector
import streamlit as st
import PyPDF2
import gtts
from io import BytesIO
import os
import subprocess
import sys
import threading
import magic
import requests
import streamlit as st
from docx2pdf import convert
import pygame
import comtypes
import comtypes.client
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_text_splitters import CharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
import win32com.client
from database import authenticate_user, register_user
# Initialize pygame mixer
pygame.mixer.init()

# Initialize comtypes
try:
    word_application = win32com.client.Dispatch("Word.Application")
    print("Word is accessible!")
except Exception as e:
    print("Error:", e)

GOOGLE_API_KEY = "AIzaSyBsIol3W7uSeFIEBRkKA3Myd48XpJUxs6Y"
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)

def convert_docx_to_pdf(docx_file):
    try:
        with open("temp.docx", "wb") as f:
            f.write(docx_file.read())
        
        if os.path.exists("temp.pdf"):
            os.remove("temp.pdf")
        
        convert("temp.docx")
        word_application.Quit()
        
        pdf_bytes = BytesIO()
        with open("temp.pdf", "rb") as f:
            pdf_bytes.write(f.read())
        
        pdf_bytes.seek(0)
        return pdf_bytes
    
    except Exception as e:
        st.error(f"Failed to convert DOCX to PDF: {e}")
        return None

def download_file_from_google_drive(file_id):
    try:
        URL = f"https://drive.google.com/uc?id={file_id}"
        response = requests.get(URL)
        if response.status_code == 200:
            return response.content
        else:
            return None
    except Exception as e:
        print(f"Error downloading file from Google Drive: {str(e)}")
        return None

def extract_text_from_docpdf(pdf_file):
    text = ""
    with pdf_file as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

@st.cache_data
def extract_and_process_text(uploaded_text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    pages = text_splitter.split_text(uploaded_text)
    
    if pages:
        vectordb = FAISS.from_texts(pages, embeddings)
        retriever = vectordb.as_retriever()
        
        template = """
        You are a helpful AI assistant.
        Answer based on the context provided. 
        context: {context}
        input: {input}
        answer:
        """
        prompt = PromptTemplate.from_template(template)
        combine_docs_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
        
        try:
            response = retrieval_chain.invoke({"input": "Tell about myself.Assign you as me and me as interviewer give intro about yourself in 30 to 40 lines"})
            result = response["answer"]
            response = retrieval_chain.invoke({"input": "explain about projects,certification completed ,work experience with details like how many years and role,any volunteering if any .Assign you as me and me as interviewer give about yourself"})
            passing = response["answer"]
            transfer = passing
            return result, transfer
        except Exception as e:
            st.error(f"Model stopped generating: {e}")
            return "", ""

@st.cache_data
def generate_audio(result):
    try:
        if os.path.exists("audio.mp3"):
            stop_and_quit_mixer()
            os.remove("audio.mp3")
        
        t1 = gtts.gTTS(result)
        t1.save("audio.mp3")
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")

def stop_audio():
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            st.success("Audio stopped.")
    except Exception as e:
        st.error(f"Error stopping audio: {str(e)}")

def stop_and_quit_mixer():
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    
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
    st.header(" :scroll: Welcome!")
    
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

        if st.button("Done"):
            if register_user(new_username, new_password):
                st.success("Registration Successful!")
                st.write(f"Welcome, {new_username}!")
                st.session_state.authenticated = True
                st.session_state.setprompt = True



def run_streamlit_app():
        # Logout Button
    with st.sidebar:
        if 'authenticated' in st.session_state and st.session_state.authenticated:
                    current_user = st.session_state.get('username', 'Guest')
                    st.title(f"Welcome, {current_user}!")  # Display the username as the title
        else:
                    st.title("Welcome to the App!")  # Default title for non-authenticated users

        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.choice = None
            st.success(f"{st.session_state.get('username', 'Guest')} has been logged out.")
            # Clear all session state variables
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params = {"param_name": "value"}

    
    if "audio_playing" not in st.session_state:
        st.session_state.audio_playing = False
    
    if "uploaded_text" not in st.session_state:
        st.session_state.uploaded_text = ""
    
    with st.sidebar:
        option = st.radio("Choose Input Type:", ("Upload PDF", "Upload DOCX", "Google Drive Link"))
        
        if option == "Upload PDF":
            uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
            if uploaded_file:
                text = extract_text_from_docpdf(uploaded_file)
                st.session_state.uploaded_text = text
        
        elif option == "Upload DOCX":
            uploaded_file = st.file_uploader("Upload CV (DOCX)", type=["docx"])
            if uploaded_file:
                pdf_file = convert_docx_to_pdf(uploaded_file)
                if pdf_file:
                    text = extract_text_from_docpdf(pdf_file)
                    st.session_state.uploaded_text = text
        
        elif option == "Google Drive Link":
            gdrive_link = st.text_input("Enter Google Drive Link:")
            if gdrive_link:
                file_id = gdrive_link.split('/')[-2]
                file_content = download_file_from_google_drive(file_id)
                if file_content:
                    with open("temp_file", "wb") as f:
                        f.write(file_content)
                    file_type = magic.Magic(mime=True).from_buffer(file_content)
                    
                    if file_type == 'application/pdf':
                        text = extract_text_from_docpdf("temp_file")
                        st.session_state.uploaded_text = text
                    elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                        pdf_file = convert_docx_to_pdf("temp_file")
                        if pdf_file:
                            text = extract_text_from_docpdf(pdf_file)
                            st.session_state.uploaded_text = text
        
        if st.session_state.uploaded_text:
            result,transfer = extract_and_process_text(st.session_state.uploaded_text)
            with st._main:
                question_color = "#1064CE" 
                answer_color = "#000000"
                new_color="#FFFFFF"
                background_color = "#C7E5F9"
                font_weight=900 
                st.markdown(f"<div style='color:{answer_color}; background-color: {background_color}; padding: 10px;border-radius:10px;margin-bottom: 20px;'>{result}</div>",unsafe_allow_html=True,)
        with st._bottom:
            st.markdown("-----")
            c1, c2, c3 = st.columns(3)

            # Column 1: Play/Stop button for audio
        with c1:
            if st.session_state.audio_playing:
                # Show stop button when audio is playing
                toggle_button = st.button("🔊 Play Audio")
                # if toggle_button and st.session_state.audio_playing:
                stop_and_quit_mixer()
                st.session_state.audio_playing = False
            else:
                # Show play button when audio is not playing
                toggle_button = st.button("🔇 Stop Audio")
                # if toggle_button and not st.session_state.audio_playing:
                if st.session_state.uploaded_text:
                        generate_audio(st.session_state.uploaded_text)  # Generate the audio
                        pygame.mixer.music.load("audio.mp3")
                        pygame.mixer.music.play()
                        st.session_state.audio_playing = True

        # Column 3: Additional information
        with c3:
            with st.popover("🔴 To Know"):
                st.text("* After uploading resume only, generating QA will work")
                st.text("* After uploading resume only, generating Apti will work")
    if st.session_state.audio_playing:
        st.write("Audio is playing...")
                    
    st.sidebar.caption("Utilities")
    if st.sidebar.button("Generate interview questions"):
        threading.Thread(target=subprocess.run, args=(["streamlit", "run", "testing2.py", transfer,text],)).start()
    if st.sidebar.button("Generate aptitude test"):
        threading.Thread(target=subprocess.run, args=(["streamlit", "run", "zen.py", text],)).start()

if __name__ == "__main__":
    main()
