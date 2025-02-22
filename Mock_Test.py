import streamlit as st
import random
import subprocess
import json
from langchain_google_genai import GoogleGenerativeAI
import uuid
import re
import sys


# Load the test questions from the JSON file
with open("testkey.json", "r") as file:
    test_questions = json.load(file)

# Function to generate random questions from JSON based on the number of questions
def generate_json_questions(num_questions):
    return random.sample(test_questions, num_questions)

# Function to calculate the score based on user's answers
def calculate_score(answers, selected_answers):
    score = 0
    for i in range(len(answers)):
        if answers[i] == selected_answers[i]:
            score += 1
    return score

def load_keywords():
    file_path = "keywords.json" 
    try:
        with open(file_path, "r") as file:
            keywords_data = json.load(file)
        return keywords_data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON in '{file_path}'.")
        return None





# Function to generate question options using Google Generative AI
def generate_question_options(model, keyword, question_id):
    question_prompt = f"give one {keyword} concept multiple choice question with options and answer question ID: {question_id}?"
    response = model.generate(prompts=[question_prompt], max_tokens=150)
    answer_prompt = f"generate a answer for this multiple choice question {question_prompt}and {question_id}"
    answer = model.generate(prompts=[answer_prompt], max_tokens=150)

    generated_text = response.generations[0][0].text.strip().split("\n")
    answer_text = answer.generations[0][0].text.strip().split("\n")
    question_text = next((item.strip() for item in answer_text if '?' in item), None)

    final_options = [item for item in answer_text[6:-4] if item.strip()]
    print(answer_text)
    if "What is the output of the following" in question_text:
        final_options = answer_text[-5:-1]
    if "**Options:**" and '' in final_options:
        final_options = answer_text[8:13]
    if "**Options:**" or '' in final_options:
        final_options = answer_text[6:-3]
        if len(final_options) == 2:
            final_options = answer_text[4:-2]
        if len(final_options) == 3:
            final_options = answer_text[6:-2]
        if final_options[-1] == '':
            final_options = final_options[:-1]
    if "**Options:**" in final_options:  
        final_options.remove("**Options:**")
    if '' in final_options:
        final_options.remove('')

    return question_text, final_options, answer_text[-1].strip()

# Function to extract skills from text using predefined keywords
def extract_skills(text, keywords_data):
    programming_language_keywords = set(keywords_data["programming_language_keywords"])
    additional_programming_languages = set(keywords_data["additional_programming_languages"])
    programming_tools_keywords = set(keywords_data["programming_tools_keywords"])
    related_technologies = keywords_data["related_technologies"]

    skills_keywords = set(re.findall(r'\b[A-Za-z-]+\b', text.lower()))

    matched_keywords = set()

    for keyword in skills_keywords:
        if keyword.lower() in programming_language_keywords or \
           keyword.lower() in additional_programming_languages or \
           keyword.lower() in programming_tools_keywords or \
           keyword.lower() in related_technologies:
            matched_keywords.add(keyword)

    if "react" in matched_keywords:
        matched_keywords.remove("react")
        matched_keywords.add("reactjs")
    if "node" in matched_keywords:
        matched_keywords.remove("node")
        matched_keywords.add("nodejs")
    if "css" in matched_keywords:
        matched_keywords.remove("css")
        matched_keywords.add("cascading style sheet")

    return list(matched_keywords)

# Streamlit app
def main():
    with open("style_3.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    st.title("Mock Test")
    

        
        

    if "questions_generated" not in st.session_state:
        st.session_state.questions_generated = False

    if not st.session_state.questions_generated:
        num_questions = st.slider("Select the number of questions", min_value=1, max_value=100, value=5)
        st.session_state.num_questions = num_questions

        if st.button("Generate"):
            keywords_data = load_keywords()
            text = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "" else ""
            if keywords_data and text:
                keywords = extract_skills(text, keywords_data)
                model = GoogleGenerativeAI(model="gemini-pro", google_api_key="AIzaSyBsIol3W7uSeFIEBRkKA3Myd48XpJUxs6Y")
                generated_questions = []
                for keyword in keywords[:num_questions]:
                    question_id = str(uuid.uuid4())
                    question, finalops, answer = generate_question_options(model, keyword.lower(), question_id)
                    generated_questions.append({"question": question, "options": finalops, "answer": answer})
                json_questions = generate_json_questions(num_questions - len(generated_questions))
                st.session_state.questions = generated_questions + json_questions
                st.session_state.questions_generated = True
                st.rerun()

    if st.session_state.questions_generated:
        selected_answers = []
        for i, question in enumerate(st.session_state.questions):
            selected_option = None  # Set the default selected option to None
            selected_option = st.radio(question["question"], options=question["options"], key=f"question_{i}", index=None)
            selected_answers.append(selected_option if selected_option is not None else None)

        if st.button("Submit Answers"):
            correct_answers = [question["answer"] for question in st.session_state.questions]
            score = calculate_score(correct_answers, selected_answers)
            if (score > len(selected_answers) / 2):
                st.balloons()
            st.write(f"Your score: **{score}/{st.session_state.num_questions}**", unsafe_allow_html=True)
            with st._main:
                with st.popover("Answers"):
                    for i in range(1, (len(correct_answers)) + 1):
                        st.write(i, correct_answers[i - 1])
    with st._main:
                if st.button("🔃 Re-test"):
                    st.session_state.questions_generated = False
                    print("Refreshing Test")
                    st.rerun()

if __name__ == "__main__":
    main()
