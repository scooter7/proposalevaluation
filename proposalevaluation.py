import streamlit as st
import fitz  # PyMuPDF
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
        prompt = (
            f"As an expert on {expertise}, evaluate the section '{section['name']}' in the context of {expertise} projects and proposals. "
            f"Focus your evaluation on:\n"
            f"- Prose: Assess the clarity and precision of the language.\n"
            f"- Structure: Review the logical flow and coherence.\n"
            f"- Format: Evaluate how the formatting enhances readability.\n"
            f"Provide detailed commentary and suggestions for improvement."
        )
        response = chat.send_message(prompt)
        evaluation = response.text.strip()
        responses[section['name']] = {
            'evaluation': evaluation,
            'score': calculate_score(evaluation, section['points']),
            'max_points': section['points']
        }
    return responses

def calculate_score(evaluation_text, max_points):
    quality_indicators = ['excellent', 'good', 'adequate', 'poor']
    score_multiplier = {'excellent': 0.9, 'good': 0.75, 'adequate': 0.5, 'poor': 0.25, 'default': 0.1}
    for indicator in quality_indicators:
        if indicator in evaluation_text.lower():
            return max_points * score_multiplier[indicator]
    return max_points * score_multiplier['default']

def create_pdf(report_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Proposal Evaluation Report", ln=True, align='C')
    for section, data in report_data.items():
        pdf.cell(200, 10, txt=f"Section: {section}", ln=True)
        pdf.cell(200, 10, txt=f"Evaluation: {data['evaluation']}", ln=True)
        pdf.cell(200, 10, txt=f"Score: {data['score']}/{data['max_points']}", ln=True)
    pdf_output = BytesIO()
    pdf.output(pdf_output, 'F')
    pdf_output.seek(0)
    return pdf_output

def display_initial_evaluations(evaluations):
    for section, data in evaluations.items():
        st.write(f"### {section}")
        st.text_area("Evaluation", value=data['evaluation'], key=f"eval_{section}_view")
        st.write("Score:", data['score'], "/", data['max_points'])

def display_revision_interface(evaluations):
    for section, data in evaluations.items():
        with st.container():
            data['evaluation'] = st.text_area(f"Edit evaluation for '{section}':", value=data['evaluation'])
            data['score'] = st.slider(f"Adjust score for '{section}':", 0, data['max_points'], value=int(data['score']))

def main():
    st.title("Proposal Evaluation App")
    expertise = st.text_input("Enter your field of expertise", value="environmental science")
    num_sections = st.number_input("How many sections does your proposal have?", min_value=1, max_value=10, step=1)
    sections = []
    for i in range(int(num_sections)):
        with st.expander(f"Section {i + 1} Details"):
            section_name = st.text_input(f"Name of section {i + 1}")
            section_points = st.number_input(f"Maximum Points for section {i + 1}", min_value=1, max_value=100)
            sections.append({'name': section_name, 'points': section_points})

    uploaded_file = st.file_uploader("Upload your proposal PDF", type=["pdf"])
    if uploaded_file is not None:
        proposal_text = read_pdf(uploaded_file)
        evaluations = evaluate_with_gemini(proposal_text, sections, expertise)
        st.session_state.evaluations = evaluations  # Initialize or update the session state with evaluations
        display_initial_evaluations(evaluations)

        if st.button("Review and Edit Evaluations"):
            display_revision_interface(st.session_state.evaluations)
            if st.button("Finalize and Download Report"):
                pdf_file = create_pdf(st.session_state.evaluations)
                st.download_button(
                    label="Download Evaluation Report",
                    data=pdf_file,
                    file_name="evaluation_report.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
