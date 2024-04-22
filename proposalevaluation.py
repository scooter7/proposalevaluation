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
    for section in sections:
        message = f"As an expert in {expertise}, please evaluate the section '{section['name']}' for its effectiveness, clarity, and accuracy in relation to {expertise} topics: {proposal_text[:2000]}"
        response = chat.send_message(message)
        responses[section['name']] = response.text.strip()
    return responses

def create_pdf(report_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    pdf.cell(200, 10, txt="Proposal Evaluation Report", ln=True, align='C')
    for section, evaluation in report_data.items():
        pdf.cell(200, 10, txt=f"Section: {section}", ln=True)
        pdf.cell(200, 10, txt=f"Evaluation: {evaluation}", ln=True)
    pdf_output = BytesIO()
    pdf.output(pdf_output, 'F')
    pdf_output.seek(0)
    return pdf_output

def display_initial_evaluation(evaluations):
    corrections = {}
    for section, evaluation in evaluations.items():
        corrected_text = st.text_area(f"Review and edit the evaluation for '{section}':", value=evaluation, key=f"feedback_{section}")
        corrections[section] = corrected_text
    return corrections

def main():
    st.title("Proposal Evaluation App")
    expertise = st.text_input("Enter your field of expertise", value="technology")
    num_sections = st.number_input("How many sections does your proposal have?", min_value=1, max_value=10, step=1)
    sections = []
    for i in range(int(num_sections)):
        with st.expander(f"Section {i + 1} Details"):
            section_name = st.text_input(f"Name of section {i + 1}", key=f"name_{i}")
            sections.append({'name': section_name})

    uploaded_file = st.file_uploader("Upload your proposal PDF", type=["pdf"])
    if uploaded_file is not None:
        proposal_text = read_pdf(uploaded_file)
        if st.button("Evaluate Proposal"):
            evaluations = evaluate_with_gemini(proposal_text, sections, expertise)
            corrections = display_initial_evaluation(evaluations)
            if st.button("Submit Corrections"):
                final_evaluations = corrections
                df_scores = pd.DataFrame(list(final_evaluations.items()), columns=['Section', 'Evaluation'])
                st.table(df_scores)
                if st.button("Download Evaluation Report"):
                    pdf_file = create_pdf(final_evaluations)
                    st.download_button(
                        label="Download Evaluation Report",
                        data=pdf_file,
                        file_name="evaluation_report.pdf",
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
