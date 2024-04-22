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
    # Mapping quality indicators to score thresholds
    score_thresholds = {
        'excellent': 0.9,
        'good': 0.8,
        'average': 0.7,
        'poor': 0.6,
        'very poor': 0.5
    }
    # Extracting quality indicators from evaluation text
    for indicator, threshold in score_thresholds.items():
        if indicator in evaluation_text.lower():
            return int(threshold * max_points)
    return int(0.5 * max_points)  # Default to 50% of max points

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
            eval_key = f"eval_{section}_edit"
            data['evaluation'] = st.text_area(f"Edit evaluation for '{section}':", value=data['evaluation'], key=eval_key)
            max_points_key = f"max_points_{section}_edit"
            data['max_points'] = st.text_input(f"Max points for '{section}':", value=data['max_points'], key=max_points_key)

def main():
    st.title("Proposal Evaluation App")
    expertise = st.text_input("Enter your field of expertise", value="environmental science")
    num_sections = st.number_input("How many sections does your proposal have?", min_value=1, max_value=10, step=1)
    sections = []
    for i in range(int(num_sections)):
        with st.expander(f"Section {i + 1} Details"):
            section_name = st.text_input(f"Name of section {i + 1}")
            section_points = st.text_input(f"Max points for '{section_name}'", value="5")
            sections.append({'name': section_name, 'points': int(section_points)})

    uploaded_file = st.file_uploader("Upload your proposal PDF", type=["pdf"])
    if uploaded_file is not None:
        proposal_text = read_pdf(uploaded_file)
        evaluations = evaluate_with_gemini(proposal_text, sections, expertise)
        st.session_state.evaluations = evaluations  # Initialize or update the session state with evaluations
        display_initial_evaluations(evaluations)

        if st.button("Review and Edit Evaluations"):
            display_revision_interface(st.session_state.evaluations)
            if st.button("Save Edited Evaluations"):
                st.session_state.evaluations = {section: {'evaluation': st.session_state.evaluations[section]['evaluation'], 
                                                          'score': calculate_score(st.session_state.evaluations[section]['evaluation'], 
                                                                                   st.session_state.evaluations[section]['max_points']),
                                                          'max_points': st.session_state.evaluations[section]['max_points']}
                                                 for section in st.session_state.evaluations}
                st.experimental_rerun()  # Rerun the app to reflect the updated evaluations

        if st.button("Finalize and Download Report"):
            evaluations = st.session_state.evaluations
            pdf_file = create_pdf(evaluations)
            st.download_button(
                label="Download Evaluation Report",
                data=pdf_file,
                file_name="evaluation_report.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()
