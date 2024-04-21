import streamlit as st
import fitz  # PyMuPDF for handling PDFs
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
    for section in sections:
        message = f"Please provide a detailed evaluation and suggestions for improvement for the section '{section['name']}': {proposal_text[:2000]}"
        response = chat.send_message(message)
        responses[section['name']] = {
            'evaluation': response.text.strip(),
            'max_points': section['points']
        }
    return responses

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
            df_scores = pd.DataFrame.from_dict(scores, orient='index', columns=['evaluation', 'max_points'])
            st.table(df_scores)
            st.subheader("Detailed Feedback and Suggestions")
            for section, data in scores.items():
                st.markdown(f"### {section}")
                st.write("Evaluation:", data['evaluation'])
                st.write("Maximum Points:", data['max_points'])

if __name__ == "__main__":
    main()
