def smart_chat_mode():
    st.title("🤖 Smart ChatBot")
    
    # File upload section
    st.sidebar.header("Document Upload")
    file_type = st.sidebar.selectbox(
        "Select Document Type",
        ["None", "PDF", "Word Document", "Excel", "Text File", "XML", "CSV", "JSON", "Image"]
    )
    file_type_extensions = {
        "PDF": [".pdf"],
        "Word Document": [".doc", ".docx"],
        "Excel": [".xls", ".xlsx"],
        "Text File": [".txt"],
        "XML": [".xml"],
        "CSV": [".csv"],
        "JSON": [".json"],
        "Image": [".jpg", ".jpeg", ".png"]
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

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me anything..."):
        with st.chat_message("user"):
            st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            response_placeholder.markdown("Thinking...")

        try:
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
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from PIL import Image
import io
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

# Load environment variables
load_dotenv()

print("Environment variables loaded.")
print(f"GOOGLE_API_KEY from env: {os.environ.get('GOOGLE_API_KEY')}")
print(f"GOOGLE_CSE_ID from env: {os.environ.get('GOOGLE_CSE_ID')}")

# Configuration
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY
print(f"API Key set in openai: {openai.api_key}")

# Initialize Google Search API
def google_search(query, num_results=5):
    try:
        google_api_key = os.environ.get('GOOGLE_API_KEY')
        print(f"GOOGLE_API_KEY inside google_search: {google_api_key}")
        service = build("customsearch", "v1", developerKey=google_api_key)
        result = service.cse().list(q=query, cx=os.environ.get('GOOGLE_CSE_ID'), num=num_results).execute()
        
        search_results = []
        if "items" in result:
            for item in result["items"]:
                search_results.append({
                    "title": item["title"],
                    "snippet": item["snippet"],
                    "link": item["link"]
                })
        return search_results
    except HttpError as e:
        st.error(f"Error performing Google search: {str(e)}")
        return []

def browse_web(url, element_id=None):
    """Browse the web using Selenium and extract information."""
    try:
        options = Options()
        options.add_argument("--headless")  # Run Chrome in headless mode
        options.add_argument("--disable-gpu")  # Disable GPU acceleration
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        if element_id:
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, element_id))
                )
                content = element.get_attribute('textContent')
            except:
                content = driver.page_source
        else:
            content = driver.page_source
        
        driver.quit()
        return content
    except selenium.common.exceptions.WebDriverException as e:
        st.error(f"Selenium WebDriver error: {str(e)}")
        return ""
    except Exception as e:
        st.error(f"Error browsing the web: {type(e).__name__} - {str(e)}")
        return ""

# Streamlit Configuration
st.set_page_config(
    page_title="Smart ChatBot",
    page_icon="download (2).png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Langchain components
embeddings = OpenAIEmbeddings()
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)
llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")

# Mode Selection
mode = st.sidebar.selectbox(
    "Select Mode",
    ["Smart Chat", "Project Generator"]
)

def extract_text_from_pdf(file_bytes):
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
        elif file_extension in ['jpg', 'jpeg', 'png']:
            return process_image(file_bytes)
        else:
            return "Unsupported file format"
    except PyPDF2.errors.PdfReadError as e:
        st.error(f"Error reading PDF file: {str(e)}")
        return f"Error reading PDF file: {str(e)}"
    except docx.opc.exceptions.PackageNotFoundError as e:
        st.error(f"Error opening Word document: {str(e)}")
        return f"Error opening Word document: {str(e)}"
    except Exception as e:
        st.error(f"Error processing file: {type(e).__name__} - {str(e)}")
        return f"Error processing file: {type(e).__name__} - {str(e)}"

def setup_vector_store(documents):
    """Setup ChromaDB vector store with processed documents"""
    texts = text_splitter.split_documents(documents)
    vector_store = Chroma.from_documents(texts, embeddings)
    return vector_store

def analyze_documents(vector_store, query):
    """Analyze documents using Langchain and OpenAI"""
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(),
        return_source_documents=True
    )
    result = qa_chain({"question": query, "chat_history": []})
    return result["answer"]

def get_chat_response(prompt, context=[], document_context=None):
    """Gets chat response from OpenAI with web search and Selenium integration."""
    
    # Load previous interactions
    try:
        with open("interactions.txt", "r", encoding="utf-8") as f:
            all_interactions = f.read().strip().split("\n\n")
            last_interactions = all_interactions[-5:]  # Get last 5 interactions
            
            # Format interactions for context
            interaction_context = ""
            for interaction in last_interactions:
                interaction_context += f"{interaction}\n\n"
    except FileNotFoundError:
        interaction_context = ""
    except Exception as e:
        st.error(f"Error loading interactions: {str(e)}")
        interaction_context = ""
    
    # Check if the prompt contains a URL
    if "http://" in prompt or "https://" in prompt:
        # Extract the URL from the prompt
        urls = re.findall(r'(https?://\S+)', prompt)
        
        # Browse the web and extract information
        web_context = ""
        for url in urls:
            web_context += f"Content from {url}:\n{browse_web(url)}\n\n"
    else:
        # Perform web search
        search_results = google_search(prompt)
        web_context = ""
        if search_results:
            web_context = "Current web search results:\n"
            for i, result in enumerate(search_results, 1):
                web_context += f"{i}. {result['title']}\n{result['snippet']}\nSource: {result['link']}\n\n"
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant that can both chat and help with project generation. "
            f"You have the following context from previous interactions:\n{interaction_context}"
            "You can provide information, answer questions, and help users with their projects. "
            "Use the provided web search results or content from browsed websites to give current and accurate information."
        }
    ]
    
    if web_context:
        messages.append({
            "role": "system",
            "content": web_context
        })
    
    if document_context:
        messages.append({
            "role": "system",
            "content": f"Context from uploaded document:\n{document_context}"
        })
    
    messages.extend(context)
    messages.append({"role": "user", "content": prompt})
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=2000,
    )
    
    # Save interaction
    save_interaction(prompt, response.choices[0].message.content)
    
    return response.choices[0].message.content

def save_interaction(prompt, response):
    """Saves the user's prompt and the chatbot's response to a file."""
    try:
        with open("interactions.txt", "a", encoding="utf-8") as f:
            f.write(f"User: {prompt}\nChatBot: {response}\n\n")
    except IOError as e:
        st.error(f"IOError saving interaction: {str(e)}")
    except Exception as e:
        st.error(f"Error saving interaction: {type(e).__name__} - {str(e)}")

def get_user_context():
    """Placeholder function to get user context data."""
    # TODO: Implement actual data access (calendar, email, etc.)
    return {
        "current_time": "2025-02-09 22:30:00",
        "upcoming_events": [],
        "recent_emails": [],
    }

def proactive_suggestions(user_context):
    """Placeholder function to generate proactive suggestions."""
    # TODO: Implement logic to generate suggestions based on user context
    suggestions = []
    if not user_context["upcoming_events"]:
        suggestions.append("You have no upcoming events. Would you like to schedule one?")
    if user_context["recent_emails"]:
        suggestions.append("You have unread emails. Would you like to read them?")
    return suggestions

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
        if line.strip() and not line.strip().startswith(('Here', 'This', 'The', 'A ', 'An ')):
            valid_lines.append(line)
    
    # Process valid lines
    for line in valid_lines:
        line = line.rstrip()
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
                if '.' in folder_name:
                    open(full_path, 'a').close()
                else:
                    os.makedirs(full_path, exist_ok=True)
            except OSError as e:
                st.error(f"Error creating {folder_name}: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {type(e).__name__} - {str(e)}")

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
        if not line or not '.' in line:
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
                file_path = os.path.join(project_path, *[''] * level, file_name)
                code_prompt = f"Project: {user_input}\nFile: {file_path}\nStructure:\n{folder_structure}\nRequirements:\n{requirements}"
                code = get_code(code_prompt, file_path)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Write code to file
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write(code)
                st.code(code, language="python")
            except OSError as e:
                st.error(f"Error generating code for {file_name}: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {type(e).__name__} - {str(e)}")

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


# --- Main Application Logic ---
if mode == "Smart Chat":
    smart_chat_mode()
elif mode == "Project Generator":
    project_generator_mode()
