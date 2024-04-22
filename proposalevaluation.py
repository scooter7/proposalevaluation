import streamlit as st
import fitz
import pandas as pd
from fpdf import FPDF
import google.generativeai as genai

genai.configure(api_key=st.secrets["google_gen_ai"]["api_key"])

def read_pdf(uploaded_file):
    file_stream = uploaded_file.read()
    doc = fitz.open("pdf", file_stream)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def evaluate_with_gemini(proposal_text, sections, expertise):
    model = genai.GenerativeModel("gemini-pro")
    chat = model.start_chat(history=[])
    responses = {}
    for section in sections:
        message = f"As an expert in {expertise}, please evaluate the section '{section['name']}' for its effectiveness, clarity, and accuracy in relation to {expertise}: {proposal_text[:2000]}"
        response = chat.send_message(message)
        evaluation = response.text.strip()
        word_count = len(evaluation.split())
        max_possible_score = section['points']
        score = min(word_count * (max_possible_score / 100), max_possible_score) if word_count < 100 else max_possible_score * 0.8
        responses[section['name']] = {
            'evaluation': evaluation,
            'score': score,
            'max_points': max_possible_score
        }
    return responses

def create_pdf(report_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    pdf.cell(200, 10, txt="Proposal Evaluation Report", ln=True, align='C')
    for section, data in report_data.items():
        pdf.cell(200, 10, txt=f"Section: {section}", ln=True)
        pdf.cell(200, 10, txt=f"Evaluation: {data['evaluation']}", ln=True)
        pdf.cell(200, 10, txt=f"Score: {data['score']}/{data['max_points']}", ln=True)
    pdf_file_path = "evaluation_report.pdf"
    pdf.output(pdf_file_path)
    return pdf_file_path

def main():
    st.title("Proposal Evaluation App")
    expertise = st.text_input("Enter your field of expertise", value="technology")
    num_sections = st.number_input("How many sections does your proposal have?", min_value=1, max_value=10, step=1)
    sections = []
    for i in range(int(num_sections)):
        with st.expander(f"Section {i + 1} Details"):
            section_name = st.text_input(f"Name of section {i + 1}", key=f"name_{i}")
            section_points = st.number_input(f"Points for section {i + 1}", min_value=1, max_value=100, step=1, key=f"points_{i}")
            sections.append({'name': section_name, 'points': section_points})

    uploaded_file = st.file_uploader("Upload your proposal PDF", type=["pdf"])
    if uploaded_file is not None:
        proposal_text = read_pdf(uploaded_file)
        if st.button("Evaluate Proposal"):
            evaluations = evaluate_with_gemini(proposal_text, sections, expertise)
            df_scores = pd.DataFrame.from_dict(evaluations, orient='index', columns=['evaluation', 'score', 'max_points'])
            st.table(df_scores)
            if st.button("Download Evaluation Report"):
                pdf_file_path = create_pdf(evaluations)
                with open(pdf_file_path, "rb") as file:
                    st.download_button(
                        label="Download Evaluation Report",
                        data=file,
                        file_name="evaluation_report.pdf",
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
