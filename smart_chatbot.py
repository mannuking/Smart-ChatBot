import streamlit as st
import openai
import os
import subprocess
import traceback
import tempfile
import shutil
import json
from dotenv import load_dotenv
import pathlib
from io import BytesIO
import PyPDF2
import docx
import pandas as pd
import xml.etree.ElementTree as ET


# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY

# Streamlit Configuration
st.set_page_config(
    page_title="Smart ChatBot",
    page_icon="download (2).png",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Mode Selection
mode = st.sidebar.selectbox(
    "Select Mode",
    ["Smart Chat", "Project Generator"]
)

def extract_text_from_pdf(file_bytes):
    pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_bytes):
    doc = docx.Document(BytesIO(file_bytes))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_excel(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes))
    return df.to_string()

def extract_text_from_xml(file_bytes):
    root = ET.fromstring(file_bytes.decode())
    return ET.tostring(root, encoding='unicode', method='text')

def process_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return None
    
    file_extension = uploaded_file.name.split('.')[-1].lower()
    file_bytes = uploaded_file.getvalue()
    
    try:
        if file_extension == 'pdf':
            return extract_text_from_pdf(file_bytes)
        elif file_extension in ['doc', 'docx']:
            return extract_text_from_docx(file_bytes)
        elif file_extension in ['xls', 'xlsx']:
            return extract_text_from_excel(file_bytes)
        elif file_extension == 'xml':
            return extract_text_from_xml(file_bytes)
        elif file_extension in ['txt', 'json', 'csv']:
            return file_bytes.decode('utf-8')
        else:
            return "Unsupported file format"
    except Exception as e:
        return f"Error processing file: {str(e)}"

# --- Project Generation Functions ---
def get_project_plan(prompt):
    """Gets project plan from OpenAI."""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a highly skilled project manager with expertise in software development. Create comprehensive project plans with: "
                "1. Project Overview 2. Requirements 3. Project Scope 4. Technology Stack 5. Project Structure "
                "6. Development Phases 7. Testing and Deployment 8. Team Roles 9. Risk Management"
            },
            {"role": "user", "content": f"Create a comprehensive project plan for this idea: {prompt}"},
        ],
        max_tokens=4000,
    )
    return response.choices[0].message.content

def get_requirements(prompt):
    """Gets project requirements from OpenAI."""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an expert software analyst. Extract all functional and non-functional requirements for the project."
            },
            {"role": "user", "content": f"Extract the requirements for this project idea: {prompt}"},
        ],
        max_tokens=2000,
    )
    return response.choices[0].message.content

def get_folder_structure(prompt):
    """Gets project folder structure from OpenAI."""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an experienced software architect. Design a well-organized folder structure following best practices. "
                "IMPORTANT: Respond ONLY with the folder structure, no explanatory text. Use proper indentation with tabs."
            },
            {"role": "user", "content": f"Design the folder structure for this project: {prompt}"},
        ],
        max_tokens=1000,
    )
    return response.choices[0].message.content

def get_code(prompt, file_path):
    """Gets code from OpenAI."""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a skilled software developer. Write clean, efficient, and well-documented code."
            },
            {
                "role": "user",
                "content": f"Write the code for '{file_path}' with this functionality: {prompt}",
            },
        ],
        max_tokens=4000,
    )
    return response.choices[0].message.content

def fix_code_errors(error_message, code, file_path):
    """Fixes code errors using OpenAI."""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a debugging expert. Fix code errors while maintaining functionality."
            },
            {
                "role": "user",
                "content": f"Fix this error in '{file_path}':\n{error_message}\n\nCode:\n{code}",
            },
        ],
        max_tokens=4000,
    )
    return response.choices[0].message.content

def create_project_structure(project_path, folder_structure):
    """Creates the project folder structure."""
    # Clean up the folder structure to remove any explanatory text
    lines = folder_structure.strip().split('\n')
    valid_lines = []
    
    for line in lines:
        # Skip empty lines and lines that look like explanatory text
        if line.strip() and not line.strip().startswith(('Here', 'This', 'The', 'A ', 'An ')):
            valid_lines.append(line)
    
    # Process valid lines
    for line in valid_lines:
        line = line.rstrip()  # Remove trailing whitespace
        if not line:
            continue
            
        # Count leading tabs/spaces for directory level
        level = 0
        for char in line:
            if char in ['\t', ' ']:
                level += 1
            else:
                break
        
        # Get the folder/file name
        folder_name = line.strip()
        if folder_name:
            try:
                # Create the full path
                full_path = os.path.join(project_path, *[''] * level, folder_name)
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                # If it's a file (contains extension), create an empty file
                if '.' in folder_name:
                    open(full_path, 'a').close()
                else:
                    os.makedirs(full_path, exist_ok=True)
            except Exception as e:
                st.error(f"Error creating {folder_name}: {str(e)}")

def generate_code_for_files(project_path, folder_structure, user_input, requirements):
    """Generates code for each file in the project structure."""
    lines = folder_structure.strip().split('\n')
    valid_lines = [line for line in lines if line.strip() and not line.strip().startswith(('Here', 'This', 'The', 'A ', 'An '))]
    
    for line in valid_lines:
        line = line.rstrip()
        if not line or not '.' in line:  # Skip directories
            continue
            
        level = 0
        for char in line:
            if char in ['\t', ' ']:
                level += 1
            else:
                break
        
        file_name = line.strip()
        if file_name:
            try:
                file_path = os.path.join(project_path, *[''] * level, file_name)
                code_prompt = f"Project: {user_input}\nFile: {file_path}\nStructure:\n{folder_structure}\nRequirements:\n{requirements}"
                code = get_code(code_prompt, file_path)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write code to file
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write(code)
                st.code(code, language="python")
            except Exception as e:
                st.error(f"Error generating code for {file_name}: {str(e)}")

def execute_code(project_path):
    """Executes the project code and handles errors."""
    try:
        process = subprocess.run(
            f"cd {project_path} && python main.py",
            capture_output=True,
            text=True,
            shell=True
        )
        if process.stderr:
            st.error(f"Error:\n{process.stderr}")
            st.warning("Attempting to fix errors...")
            for file_name in [f for f in os.listdir(project_path) if f.endswith(".py")]:
                file_path = os.path.join(project_path, file_name)
                with open(file_path, "r") as f:
                    original_code = f.read()
                fixed_code = fix_code_errors(process.stderr, original_code, file_path)
                if fixed_code != original_code:
                    with open(file_path, "w") as f:
                        f.write(fixed_code)
                    execute_code(project_path)
                    break
        else:
            st.success("Code executed successfully!")
            st.write(process.stdout)
    except Exception as e:
        st.error(f"Error:\n{traceback.format_exc()}")

def get_chat_response(prompt, context=[], document_context=None):
    """Gets chat response from OpenAI."""
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant that can both chat and help with project generation. "
            "You can provide information, answer questions, and help users with their projects."
        }
    ]
    
    # Add document context if available
    if document_context:
        messages.append({
            "role": "system",
            "content": f"Context from uploaded document:\n{document_context}"
        })
    
    # Add context from previous messages
    messages.extend(context)
    
    # Add user's prompt
    messages.append({"role": "user", "content": prompt})
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=2000,
    )
    return response.choices[0].message.content

# --- Main Application Logic ---
if mode == "Smart Chat":
    st.title("🤖 Smart ChatBot")
    
    # File upload section
    st.sidebar.header("Document Upload")
    file_type = st.sidebar.selectbox(
        "Select Document Type",
        ["None", "PDF", "Word Document", "Excel", "Text File", "XML", "CSV", "JSON"]
    )
    
    file_type_extensions = {
        "PDF": [".pdf"],
        "Word Document": [".doc", ".docx"],
        "Excel": [".xls", ".xlsx"],
        "Text File": [".txt"],
        "XML": [".xml"],
        "CSV": [".csv"],
        "JSON": [".json"]
    }
    
    uploaded_file = None
    document_context = None
    
    if file_type != "None":
        uploaded_file = st.sidebar.file_uploader(
            "Upload Document",
            type=file_type_extensions.get(file_type, []),
            key="document_uploader"
        )
        
        if uploaded_file:
            document_context = process_uploaded_file(uploaded_file)
            st.sidebar.success(f"Successfully processed {uploaded_file.name}")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm a smart chatbot that can help with both general questions and project generation. You can also upload documents to chat about their contents. How can I assist you today?"
            }
        ]

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            response_placeholder.markdown("Thinking...")
            
            try:
                # Check if prompt is asking for project generation
                if any(keyword in prompt.lower() for keyword in ["create project", "generate project", "build project"]):
                    response_placeholder.markdown("Switching to Project Generator mode...")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "I'll help you generate a project. Switching to Project Generator mode..."
                    })
                    st.experimental_rerun()
                
                # Get chat response
                context = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
                response = get_chat_response(prompt, context, document_context)
                
                response_placeholder.markdown(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                error_response = "I encountered an error processing your request."
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_response
                })

elif mode == "Project Generator":
    st.title("🚀 Project Generator")
    
    user_input = st.text_area("Enter your project idea:")
    run_code = st.checkbox("Run the generated code")
    
    if st.button("Generate Project"):
        if user_input:
            st.write("Generating project...")
            
            # Generate project plan
            project_plan = get_project_plan(user_input)
            st.header("Project Plan:")
            st.write(project_plan)
            
            # Generate requirements
            requirements = get_requirements(user_input)
            st.header("Requirements:")
            st.code(requirements)
            
            # Generate folder structure
            folder_structure = get_folder_structure(user_input)
            st.header("Folder Structure:")
            st.code(folder_structure)
            
            # Setup project directory
            project_name = "generated_project"
            user_home_dir = pathlib.Path.home()
            projects_dir = user_home_dir / "Downloads" / "projects"
            projects_dir.mkdir(parents=True, exist_ok=True)
            project_path = projects_dir / project_name
            
            try:
                # Create project structure
                create_project_structure(project_path, folder_structure)
                
                # Generate code
                st.header("Generated Code:")
                generate_code_for_files(project_path, folder_structure, user_input, requirements)
                
                # Execute code if requested
                if run_code:
                    execute_code(project_path)
                
                # Create download button
                shutil.make_archive("project", "zip", project_path)
                with open("project.zip", "rb") as f:
                    st.download_button(
                        "Download Project",
                        f,
                        "project.zip",
                        "application/zip"
                    )
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            finally:
                # Cleanup
                shutil.rmtree(project_path, ignore_errors=True)
                if os.path.exists("project.zip"):
                    os.remove("project.zip")
