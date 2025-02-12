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

print("Environment variables loaded.")

# Configuration
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
print(f"API Key from .env: {OPENAI_API_KEY}")
openai.api_key = OPENAI_API_KEY
print(f"API Key set in openai: {openai.api_key}")

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

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from a PDF file.

    Args:
        file_bytes (bytes): The content of the PDF file as bytes.

    Returns:
        str: The extracted text from the PDF file.
    """
    pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
    text: str = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts text from a Word document (.docx) file.

    Args:
        file_bytes (bytes): The content of the Word document as bytes.

    Returns:
        str: The extracted text from the Word document.
    """
    doc = docx.Document(BytesIO(file_bytes))
    text: str = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_excel(file_bytes: bytes) -> str:
    """
    Extracts text from an Excel file (.xls, .xlsx).

    Args:
        file_bytes (bytes): The content of the Excel file as bytes.

    Returns:
        str: The extracted text from the Excel file.
    """
    df: pd.DataFrame = pd.read_excel(BytesIO(file_bytes))
    return df.to_string()

def extract_text_from_xml(file_bytes: bytes) -> str:
    """
    Extracts text from an XML file.

    Args:
        file_bytes (bytes): The content of the XML file as bytes.

    Returns:
        str: The extracted text from the XML file.
    """
    root: ET.Element = ET.fromstring(file_bytes.decode())
    return ET.tostring(root, encoding='unicode', method='text')

def process_uploaded_file(uploaded_file) -> str | None:
    """
    Processes an uploaded file and extracts its content as text.

    Args:
        uploaded_file (streamlit.UploadedFile): The uploaded file object.

    Returns:
        str: The extracted text from the file, or an error message if processing fails.
    """
    if uploaded_file is None:
        return None

    file_extension: str = uploaded_file.name.split('.')[-1].lower()
    file_bytes: bytes = uploaded_file.getvalue()

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
    except PyPDF2.errors.PdfReadError as e:
        st.error(f"Error reading PDF file: {str(e)}")
        return f"Error reading PDF file: {str(e)}"
    except docx.opc.exceptions.PackageNotFoundError as e:
        st.error(f"Error opening Word document: {str(e)}")
        return f"Error opening Word document: {str(e)}"
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return f"Error processing file: {str(e)}"

# --- Project Generation Functions ---
def get_project_plan(prompt: str) -> str:
    """
    Gets a project plan from OpenAI based on the given prompt.

    Args:
        prompt (str): The project idea or description.

    Returns:
        str: The generated project plan.
    """
    try:
        response: openai.chat.completions.create = openai.chat.completions.create(
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
    except openai.APIError as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

def get_requirements(prompt: str) -> str:
    """
    Gets project requirements from OpenAI based on the given prompt.

    Args:
        prompt (str): The project idea or description.

    Returns:
        str: The extracted project requirements.
    """
    try:
        response: openai.chat.completions.create = openai.chat.completions.create(
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
    except openai.APIError as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

def get_folder_structure(prompt: str) -> str:
    """
    Gets a project folder structure from OpenAI based on the given prompt.

    Args:
        prompt (str): The project idea or description.

    Returns:
        str: The generated folder structure.
    """
    try:
        response: openai.chat.completions.create = openai.chat.completions.create(
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
    except openai.APIError as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

def get_code(prompt: str, file_path: str) -> str:
    """
    Gets code from OpenAI for a specific file based on the given prompt.

    Args:
        prompt (str): The description of the code's functionality.
        file_path (str): The path to the file for which the code is generated.

    Returns:
        str: The generated code.
    """
    try:
        response: openai.chat.completions.create = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a skilled software developer. Write clean, efficient, and well-documented code."
                },
                {"role": "user", "content": f"Write the code for '{file_path}' with this functionality: {prompt}"},
            ],
            max_tokens=4000,
        )
        return response.choices[0].message.content
    except openai.APIError as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

def fix_code_errors(error_message: str, code: str, file_path: str) -> str:
    """
    Fixes code errors using OpenAI.

    Args:
        error_message (str): The error message to be fixed.
        code (str): The code containing the error.
        file_path (str): The path to the file containing the error.

    Returns:
        str: The corrected code.
    """
    try:
        response: openai.chat.completions.create = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a debugging expert. Fix code errors while maintaining functionality."
                },
                {"role": "user", "content": f"Fix this error in '{file_path}':\n{error_message}\n\nCode:\n{code}"},
            ],
            max_tokens=4000,
        )
        return response.choices[0].message.content
    except openai.APIError as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

def create_project_structure(project_path: str, folder_structure: str) -> None:
    """
    Creates the project folder structure based on the given structure.

    Args:
        project_path (str): The base path for the project.
        folder_structure (str): The folder structure to create.
    """
    # Clean up the folder structure to remove any explanatory text
    lines: list[str] = folder_structure.strip().split('\n')
    valid_lines: list[str] = []

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
        level: int = 0
        for char in line:
            if char in ['\t', ' ']:
                level += 1
            else:
                break

        # Get the folder/file name
        folder_name: str = line.strip()
        if folder_name:
            try:
                # Create the full path
                full_path: str = os.path.join(project_path, *[''] * level, folder_name)
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                # If it's a file (contains extension), create an empty file
                if '.' in folder_name:
                    open(full_path, 'a').close()
                else:
                    os.makedirs(full_path, exist_ok=True)
            except OSError as e:
                st.error(f"Error creating {folder_name}: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

def generate_code_for_files(project_path: str, folder_structure: str, user_input: str, requirements: str) -> None:
    """
    Generates code for each file in the project structure.

    Args:
        project_path (str): The base path for the project.
        folder_structure (str): The folder structure.
        user_input (str): The user's project idea.
        requirements (str): The project requirements.
    """
    lines: list[str] = folder_structure.strip().split('\n')
    valid_lines: list[str] = [line for line in lines if line.strip() and not line.strip().startswith(('Here', 'This', 'The', 'A ', 'An '))]

    for line in valid_lines:
        line = line.rstrip()
        if not line or not '.' in line:  # Skip directories
            continue

        level: int = 0
        for char in line:
            if char in ['\t', ' ']:
                level += 1
            else:
                break

        file_name: str = line.strip()
        if file_name:
            try:
                file_path: str = os.path.join(project_path, *[''] * level, file_name)
                code_prompt: str = f"Project: {user_input}\nFile: {file_path}\nStructure:\n{folder_structure}\nRequirements:\n{requirements}"
                code: str = get_code(code_prompt, file_path)

                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Write code to file
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write(code)
                st.code(code, language="python")
            except OSError as e:
                st.error(f"Error generating code for {file_name}: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

def execute_code(project_path: str) -> None:
    """
    Executes the project code and handles errors.

    Args:
        project_path (str): The path to the project directory.
    """
    try:
        process: subprocess.CompletedProcess = subprocess.run(
            f"cd {project_path} && python main.py",
            capture_output=True,
            text=True,
            shell=True
        )
        if process.stderr:
            st.error(f"Error:\n{process.stderr}")
            st.warning("Attempting to fix errors...")
            for file_name in [f for f in os.listdir(project_path) if f.endswith(".py")]:
                file_path: str = os.path.join(project_path, file_name)
                with open(file_path, "r") as f:
                    original_code: str = f.read()
                fixed_code: str = fix_code_errors(process.stderr, original_code, file_path)
                if fixed_code != original_code:
                    with open(file_path, "w") as f:
                        f.write(fixed_code)
                    execute_code(project_path)
                    break
        else:
            st.success("Code executed successfully!")
            st.write(process.stdout)
    except subprocess.CalledProcessError as e:
        st.error(f"Error executing code: {str(e)}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {traceback.format_exc()}")

def get_chat_response(prompt: str, context: list = [], document_context: str | None = None) -> str:
    """
    Gets a chat response from OpenAI.

    Args:
        prompt (str): The user's prompt.
        context (list, optional): A list of previous messages for context. Defaults to [].
        document_context (str, optional): Context from an uploaded document. Defaults to None.

    Returns:
        str: The generated chat response.
    """
    messages: list[dict] = [
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

    try:
        response: openai.chat.completions.create = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except openai.APIError as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

def smart_chat_mode():
    """
    Handles the Smart Chat mode of the application.

    This function sets up the UI for the Smart Chat mode, including the file upload section,
    chat history display, and chat input box. It also handles the interaction with the OpenAI API
    to generate responses to user prompts.
    """
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


def project_generator_mode():
    """
    Handles the Project Generator mode of the application.

    This function sets up the UI for the Project Generator mode, including the project idea input,
    project generation button, and the display of generated project plan, requirements,
    folder structure, and code. It also handles the creation of the project directory,
    code generation, code execution, and project download.
    """
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


# --- Main Application Logic ---
if mode == "Smart Chat":
    smart_chat_mode()
elif mode == "Project Generator":
    project_generator_mode()
