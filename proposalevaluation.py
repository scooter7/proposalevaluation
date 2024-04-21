import streamlit as st
import fitz  # PyMuPDF for handling PDFs
import pandas as pd
from fpdf import FPDF
import google.generativeai as genai

# Initialize Google Gemini with API Key from Streamlit Secrets
genai.configure(api_key=st.secrets["google_gen_ai"]["api_key"])

def read_pdf(uploaded_file):
    file_stream = uploaded_file.read()
    doc = fitz.open("pdf", file_stream)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def evaluate_with_gemini(proposal_text, sections):
    model = genai.GenerativeModel("gemini-pro")
    chat = model.start_chat(history=[])
    responses = {}
    total_possible_points = sum(section['points'] for section in sections)
    total_scored_points = 0

    for section in sections:
        message = f"Please provide a detailed evaluation and suggestions for improvement for the section '{section['name']}': {proposal_text[:2000]}"
        response = chat.send_message(message)
        evaluation = response.text.strip()
        # Example scoring logic, replace with your specific criteria
        score = len(evaluation) / 100  # Placeholder for demonstration
        score = min(score, section['points'])
        total_scored_points += score
        responses[section['name']] = {
            'evaluation': evaluation,
            'score': score,
            'max_points': section['points']
        }

    responses['total_score'] = total_scored_points
    responses['total_possible'] = total_possible_points
    return responses

def create_pdf(report_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    pdf.cell(200, 10, txt = "Proposal Evaluation Report", ln = True, align = 'C')

    for section, data in report_data.items():
        if section not in ['total_score', 'total_possible']:
            pdf.cell(200, 10, txt = f"Section: {section}", ln = True)
            pdf.cell(200, 10, txt = f"Evaluation: {data['evaluation']}", ln = True)
            pdf.cell(200, 10, txt = f"Score: {data['score']}/{data['max_points']}", ln = True)

    pdf.cell(200, 10, txt = f"Total Score: {report_data['total_score']}/{report_data['total_possible']}", ln = True)
    pdf.output("evaluation_report.pdf")

def main():
    st.title("Proposal Evaluation App")
    expertise = st.text_input("Enter your field of expertise", value="technology")
    st.write(f"You're a {expertise} expert, known for two decades of meticulous study, review, and evaluation of {expertise} projects and proposals.")
    num_sections = st.number_input("How many sections does your proposal have?", min_value=0, max_value=10, step=1)
    sections = []
    for i in range(int(num_sections)):
        with st.expander(f"Section {i + 1} Details"):
            section_name = st.text_input(f"Name of section {i + 1}", key=f"name_{i}")
            section_points = st.number_input(f"Points for section {i + 1}", min_value=0, max_value=100, step=1, key=f"points_{i}")
            sections.append({'name': section_name, 'points': section_points})
    uploaded_file = st.file_uploader("Upload your proposal PDF", type=["pdf"])
    if uploaded_file is not None:
        proposal_text = read_pdf(uploaded_file)
        if st.button("Evaluate Proposal"):
            scores = evaluate_with_gemini(proposal_text, sections)
            df_scores = pd.DataFrame.from_dict(scores, orient='index', columns=['evaluation', 'score', 'max_points']).drop(['total_score', 'total_possible'], errors='ignore')
            st.table(df_scores)
            create_pdf(scores)
            st.subheader("Detailed Feedback and Suggestions")
            for section, data in scores.items():
                if section not in ['total_score', 'total_possible']:
                    st.markdown(f"### {section}")
                    st.write("Evaluation:", data['evaluation'])
                    st.write("Score:", f"{data['score']}/{data['max_points']}")
            st.markdown(f"### Total Score")
            st.write("Score:", f"{scores['total_score']}/{scores['total_possible']}")

            with open("evaluation_report.pdf", "rb") as file:
                btn = st.download_button(
                    label="Download Evaluation Report",
                    data=file,
                    file_name="evaluation_report.pdf",
                    mime="application/octet-stream"
                )

if __name__ == "__main__":
    main()
