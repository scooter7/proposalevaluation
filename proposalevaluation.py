import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
from fpdf import FPDF
from io import BytesIO
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
    total_points_possible = sum(section['max_points'] for section in sections)
    for section in sections:
        message = f"As an expert in {expertise}, evaluate how well the section '{section['name']}' addresses {expertise} in terms of prose, structure, format, and demonstration of expertise: {proposal_text[:2000]}"
        response = chat.send_message(message)
        evaluation = response.text.strip()
        score = calculate_score(evaluation, section['max_points'])
        responses[section['name']] = {
            'evaluation': evaluation,
            'score': score,
            'max_points': section['max_points']
        }
    return responses, total_points_possible

def calculate_score(evaluation, max_points):
    # Simulated qualitative scoring based on relevance and completeness
    relevance = sum(1 for word in evaluation.lower().split() if len(word) > 4)  # count longer words as a proxy for content depth
    completeness = min(relevance / 10, 1)  # assuming 10 relevant terms as fully complete
    score = min(completeness * max_points, max_points)
    return score

def create_pdf(report_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    pdf.cell(200, 10, txt="Proposal Evaluation Report", ln=True, align='C')
    for section, data in report_data.items():
        pdf.cell(200, 10, txt=f"Section: {section}", ln=True)
        pdf.cell(200, 10, txt=f"Evaluation: {data['evaluation']}", ln=True)
        pdf.cell(200, 10, txt=f"Score: {data['score']}/{data['max_points']}", ln=True)
    pdf_output = BytesIO()
    pdf.output(pdf_output, 'F')
    pdf_output.seek(0)
    return pdf_output

def main():
    st.title("Proposal Evaluation App")
    expertise = st.text_input("Enter your field of expertise", value="technology")
    num_sections = st.number_input("How many sections does your proposal have?", min_value=1, max_value=10, step=1)
    sections = []
    for i in range(int(num_sections)):
        with st.expander(f"Section {i + 1} Details"):
            section_name = st.text_input(f"Name of section {i + 1}", key=f"name_{i}")
            max_points = st.number_input(f"Max points for section {i + 1}", min_value=1, max_value=100, step=1, key=f"max_points_{i}")
            sections.append({'name': section_name, 'max_points': max_points})

    uploaded_file = st.file_uploader("Upload your proposal PDF", type=["pdf"])
    if uploaded_file is not None:
        proposal_text = read_pdf(uploaded_file)
        if st.button("Evaluate Proposal"):
            evaluations, total_points_possible = evaluate_with_gemini(proposal_text, sections, expertise)
            df_scores = pd.DataFrame([{**{'Section': k}, **v} for k, v in evaluations.items()])
            st.table(df_scores)
            if st.button("Download Evaluation Report"):
                pdf_file = create_pdf(evaluations)
                st.download_button(
                    label="Download Evaluation Report",
                    data=pdf_file,
                    file_name="evaluation_report.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
