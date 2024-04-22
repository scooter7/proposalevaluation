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
    responses = {}
    for section_name, section_details in sections.items():
        prompt = (
            f"As an expert on {expertise}, evaluate the section '{section_name}'. "
            f"Focus your evaluation on:\n"
            "- Prose: Assess the clarity and precision of the language.\n"
            "- Structure: Review the logical flow and coherence.\n"
            "- Format: Evaluate the professional formatting of the document."
        )
        evaluation = st.text_area(prompt)
        score = calculate_score(evaluation, section_details['max_points'])
        responses[section_name] = {'evaluation': evaluation, 'score': score, 'max_points': section_details['max_points']}
    return responses

def calculate_score(evaluation_text, max_points):
    # Evaluate the quality of the evaluation text based on qualitative criteria related to the area of expertise
    # Adjust the scoring based on the overall quality
    evaluation_quality = evaluate_quality(evaluation_text)
    score = 0
    if evaluation_quality == "excellent":
        score = int(0.9 * max_points)
    elif evaluation_quality == "good":
        score = int(0.8 * max_points)
    elif evaluation_quality == "average":
        score = int(0.7 * max_points)
    elif evaluation_quality == "poor":
        score = int(0.6 * max_points)
    elif evaluation_quality == "very poor":
        score = int(0.5 * max_points)
    return score

def evaluate_quality(evaluation_text):
    # Perform a qualitative analysis of the evaluation text based on the defined area of expertise
    # Determine the overall quality of the evaluation text
    # This function should be replaced with actual evaluation logic based on the area of expertise
    # For demonstration purposes, we'll use a placeholder evaluation criterion
    # You should replace this with the appropriate evaluation criteria based on the area of expertise
    # Example criteria: relevance, depth of analysis, clarity of explanation, etc.
    if "relevant" in evaluation_text.lower() and "well-analyzed" in evaluation_text.lower():
        return "excellent"
    elif "relevant" in evaluation_text.lower():
        return "good"
    elif "clear" in evaluation_text.lower():
        return "average"
    elif "unclear" in evaluation_text.lower():
        return "poor"
    else:
        return "very poor"

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
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

def display_initial_evaluations(evaluations):
    for section, data in evaluations.items():
        st.write(f"### {section}")
        st.text_area(f"Evaluation for '{section}'", value=data['evaluation'], key=f"eval_{section}_view")
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
    expertise = st.text_input("Enter your field of expertise", value="")

    st.write(f"You're an {expertise} expert, known for decades of meticulous study, review, and evaluation of projects and proposals.")
    num_sections = st.number_input("How many sections does your proposal have?", min_value=1, max_value=10, step=1)
    sections = {}

    for i in range(int(num_sections)):
        section_name = st.text_input(f"Name of section {i + 1}")
        max_points = st.text_input(f"Max points for '{section_name}'", key=f"max_points_{i}")
        sections[section_name] = {'max_points': max_points}

    uploaded_file = st.file_uploader("Upload your proposal PDF", type=["pdf"])
    if uploaded_file is not None:
        proposal_text = read_pdf(uploaded_file)
        if st.button("Evaluate Proposal"):
            evaluations = evaluate_with_gemini(proposal_text, sections, expertise)  # Pass expertise argument
            st.session_state.evaluations = evaluations  # Save evaluations in session state
            display_initial_evaluations(evaluations)

    if "evaluations" in st.session_state:
        if st.button("Review and Edit Evaluations"):
            display_revision_interface(st.session_state.evaluations)
            if st.button("Save Edited Evaluations"):
                st.session_state.evaluations = {}  # Clear previous evaluations
                # Retrieve edited evaluations and update session state
                for i, section_name in enumerate(sections.keys()):
                    evaluation = st.text_area(f"Edit evaluation for '{section_name}'", value="")
                    max_points_key = f"max_points_{i}"
                    max_points = st.text_input(f"Max points for '{section_name}'", key=max_points_key)
                    st.session_state.evaluations[section_name] = {'evaluation': evaluation, 'max_points': max_points}
                st.experimental_rerun()  # Rerun the app to reflect the changes

    if st.button("Finalize and Download Report"):
        pdf_file = create_pdf(st.session_state.evaluations)
        st.download_button(
            label="Download Evaluation Report",
            data=pdf_file.getvalue(),
            file_name="evaluation_report.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
