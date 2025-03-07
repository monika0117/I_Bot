import sys
import json
import re
import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAI

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

def load_keywords():
    file_path = "keywords.json"
    try:
        with open(file_path, "r") as file:
            keywords_data = json.load(file)
        # Convert keyword sets to lowercase
        keywords_data = {key: set(map(str.lower, value)) for key, value in keywords_data.items()}
        return keywords_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: File '{file_path}' not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Error: Unable to decode JSON in '{file_path}'.")

def extract_skills(text, keywords_data):
    # Extract keyword sets
    programming_language_keywords = keywords_data["programming_language_keywords"]
    additional_programming_languages = keywords_data["additional_programming_languages"]
    programming_tools_keywords = keywords_data["programming_tools_keywords"]
    related_technologies = keywords_data["related_technologies"]

    # Find keywords in the text
    skills_keywords = set(re.findall(r'\b[A-Za-z-]+\b', text.lower()))

    # Declare set to store the words
    matched_keywords = set()

    # Match keywords
    for keyword_set in (programming_language_keywords, additional_programming_languages, programming_tools_keywords, related_technologies):
        matched_keywords |= skills_keywords.intersection(keyword_set)

    # Replace specific keywords
    replacements = {"react": "reactjs", "node": "nodejs", "css": "cascading style sheet"}
    matched_keywords = {replacements.get(keyword, keyword) for keyword in matched_keywords}

    return list(matched_keywords)

def extract_lines(dialogues):
    resume_keywords = ["work experience", "certification", "project", "volunteer","projects","certification"]
    extracted_lines = {}
    for dialogue in dialogues:
        for keyword in resume_keywords:
            if keyword.lower() in dialogue.lower():
                lines = [line.strip() for line in dialogue.split('\n')]
                extracted_lines[keyword.lower()] = lines
    return extracted_lines

def generate_interview_questions_and_answers(model, keywords, total_questions=20):
    if not keywords:
        raise ValueError("No keywords found. Unable to generate questions.")

    qa_pairs = []
    num_questions = total_questions // len(keywords)

    # Generate questions for matched keywords
    for keyword in keywords:
        unique_questions = set()
        for _ in range(num_questions):
            question_prompt = f"{keyword}"
            # Generate a question to redue the que length decrease max length
            question_response = model.generate(prompts=[question_prompt], max_length=50, temperature=0.3)

            question = question_response.generations[0][0].text.removeprefix("**Question:**").strip()

            if question not in unique_questions:
                unique_questions.add(question)

                answer_prompt = f"Provide simple response to the following question: {question} with 75 words"
                answer_response = model.generate(prompts=[answer_prompt], max_length=50, temperature=0.3)
                answer = answer_response.generations[0][0].text.strip()

                qa_pairs.append((question, answer))

    return qa_pairs

def generate_interview_resume(keywords, total_question):
    if not google_api_key:
        print("Error: Google API key is missing.")
        return []
    
    if not keywords:
        print("No keywords found. Unable to generate questions.")
        return []

    # Configure API
    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    qa_pairs = []
    num_questions_per_keyword = max(1, total_question // len(keywords))  # Ensure at least 1 question per keyword

    for keyword in keywords:
        unique_questions = set()

        for _ in range(num_questions_per_keyword):
            # Generate a question for the keyword
            question_prompt = f"Generate an interview question related to: {keyword}"
            question_response = model.generate_content(question_prompt)

            if question_response and hasattr(question_response, "candidates") and question_response.candidates:
                question = question_response.candidates[0].content.parts[0].text.strip()

                if question and question not in unique_questions:
                    unique_questions.add(question)

                    # Generate an answer
                    answer_prompt = f"Provide an answer to the following question: {question} with 75 words"
                    answer_response = model.generate_content(answer_prompt)

                    if answer_response and hasattr(answer_response, "candidates") and answer_response.candidates:
                        answer = answer_response.candidates[0].content.parts[0].text.strip()
                        
                        if answer:
                            qa_pairs.append((question, answer))

                        # Stop generating if we reach total_question
                        if len(qa_pairs) >= total_question:
                            return qa_pairs

    return qa_pairs



def main():
    
    with open("style_2.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)    
        st.title("Question and Answer Generation")
       

    if len(sys.argv) > 2:
        text = sys.argv[1]
        passage = sys.argv[2]

        me_dialogues = re.split(r'Interviewer:', text)
        me_only = ''.join([dialogue.split('Me:')[1].strip() for dialogue in me_dialogues if 'Me:' in dialogue])
        keywords_data = load_keywords()

        if keywords_data:
            keywords = extract_skills(passage, keywords_data)
            resume_keywords = extract_lines(me_dialogues)
            resume_keywords_list = list(resume_keywords.values())

            model = GoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=google_api_key)

            qa_pairs = generate_interview_questions_and_answers(model, keywords)
            render_qa_pairs(qa_pairs)

            resume_qa_pairs = generate_interview_resume(resume_keywords_list, len(resume_keywords_list))
            render_qa_pairs(resume_qa_pairs)
        else:
            st.error("Failed to load keywords.")
    else:
        st.error("No text provided.")

def render_qa_pairs(qa_pairs):
    question_color = "#1064CE"
    answer_color = "#000000"
    background_color = "#C7E5F9"
    font_weight = 900

    for question, answer in qa_pairs:
        st.markdown(
            f"<div style='font-weight: {font_weight}; color:#fff; padding: 10px; background:#735DA5;border-radius:10px;'>"
            f"{question}</div>", unsafe_allow_html=True)

        st.markdown(
            f"<div style='color:{answer_color}; ; padding: 10px;border-radius:10px;margin: 10px;font-weight: 500;text-align:left;'>Answer: {answer}</div>",
            unsafe_allow_html=True)

if __name__ == "__main__":
    main()