import os
import json
from embedchain import App
import streamlit as st
from googleapiclient.discovery import build
from dotenv import load_dotenv
from functools import lru_cache
import re

# Import additional loaders as needed
from embedchain.loaders.directory_loader import DirectoryLoader
from embedchain.loaders.github import GithubLoader
from embedchain.loaders.notion import NotionLoader
from embedchain.loaders.sitemap import SitemapLoader

load_dotenv()

# --- Backend Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# --- Streamlit UI Configuration ---
st.set_page_config(
    page_title="Web-Powered Chatbot",
    page_icon="download (2).png",  # Replace with the actual path to your icon image
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌐 Web-Powered Chatbot 🔎")
st.markdown("**Ask me anything! I'll search the web and provide insightful answers.**")

# --- Data Source Selection ---
data_source_type = st.sidebar.selectbox(
    "Select Data Source Type",
    [
        "File Types",
        "Website/Platforms",
        "Database",
        "Other"
    ],
)

# --- Data Source Options based on Type ---
data_source_options = {
    "File Types": [
        "PDF file",
        "CSV file",
        "JSON file",
        "Text",
        "Text File",
        "MDX file",
        "DOCX file",
        "XML file",
        "Image",
        "Audio"
    ],
    "Website/Platforms": [
        "Web page",
        "Youtube Channel",
        "Youtube Video",
        "Docs website",
        "Notion",
        "Substack",
        "Beehiiv",
        "Google Drive",
        "GitHub",
        "Slack",
        "Discord",
        "Dropbox"
    ],
    "Database": ["PostgreSQL", "MySQL"],
    "Other": [
        "Directory",
        "Sitemap",
        "Q&A pair",
        "OpenAPI",
        "Gmail",
        "Discourse",
        "Custom"
    ]
}

data_source = st.sidebar.selectbox(
    "Select Data Source",
    data_source_options[data_source_type]
)

# --- Chat History and Feedback Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """
            Hi! I'm a web-powered chatbot. Ask me anything, and I'll do my best to find the information you need!
            """,
        }
    ]

if "feedback" not in st.session_state:
    st.session_state.feedback = []

# --- Display Chat Messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Google Search Function with Caching ---
@lru_cache(maxsize=128)
def google_search(query, num_results=3):
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        res = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=num_results).execute()
        return [{"link": item['link'], "snippet": item.get('snippet', '')} for item in res.get('items', [])]
    except Exception as e:
        st.error(f"Error during Google Search: {e}")
        return []

# --- Helper function to extract video ID from YouTube URL ---
def extract_video_id_from_url(url):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(?:embed\/)?([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None

# --- User Input and Processing ---
if prompt := st.chat_input("Enter your query here..."):
    # --- Embedchain Configuration ---
    config = {
        'llm': {
            'provider': 'openai',
            'config': {
                'model': 'gpt-3.5-turbo',
            }
        },
        'embedder': {
            'provider': 'openai',
        }
    }

    app = App.from_config(config=config)

    # --- Chat Interaction and Response Generation ---
    with st.chat_message("user"):
        st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        msg_placeholder = st.empty()
        msg_placeholder.markdown("Thinking...")

        full_response = ""

        try:
            # --- Data Source Handling ---
            if data_source_type == "Website/Platforms":
                if data_source == "Web page":
                    search_results = google_search(prompt, num_results=3)
                    for result in search_results:
                        app.add(result["link"])

                    msg_placeholder.markdown("Analyzing search results...")

                    for response in app.chat(prompt):
                        msg_placeholder.empty()
                        full_response += response

                    # st.markdown("**Search Results:**")
                    # for result in search_results:
                    #     st.write(f"- [{result['link']}]({result['link']}) - {result['snippet']}")

                elif data_source in ["Youtube Video", "Youtube Channel", "Docs website"]:
                    app.add(prompt, data_type=data_source.replace(" ", "_").lower())
                    msg_placeholder.markdown(f"Analyzing {data_source}...")
                    for response in app.chat(prompt):
                        msg_placeholder.empty()
                        full_response += response

                elif data_source == "Notion":
                    # You'll likely need to handle Notion authentication here
                    notion_loader = NotionLoader()  # Add Notion integration details if needed
                    app.add(prompt, data_type='notion', loader=notion_loader)
                    msg_placeholder.markdown("Analyzing Notion page...")
                    for response in app.chat(prompt):
                        msg_placeholder.empty()
                        full_response += response
                # ... Add handling for other Website/Platforms as needed

            elif data_source_type == "File Types":
                data_type_mapping = {
                    "PDF file": "pdf_file",
                    "CSV file": "csv",
                    "JSON file": "json",
                    "Text": "text",
                    "Text File": "text_file",
                    "MDX file": "mdx",
                    "DOCX file": "docx",
                    "XML file": "xml",  # Auto-detected, but specifying for clarity
                    # Add other file types here
                }
                data_type = data_type_mapping.get(data_source, data_source.lower())
                app.add(prompt, data_type=data_type)
                msg_placeholder.markdown(f"Analyzing {data_source}...")
                for response in app.chat(prompt):
                    msg_placeholder.empty()
                    full_response += response

            elif data_source_type == "Database":
                # ... Add handling for Database types 
                pass  # Implement database handling later

            elif data_source_type == "Other":
                if data_source == "Directory":
                    dir_config = {
                        "recursive": True,
                        "extensions": [".txt"]  # Customize as needed
                    }
                    loader = DirectoryLoader(config=dir_config)
                    app.add(prompt, loader=loader, data_type="directory")
                    msg_placeholder.markdown("Analyzing directory...")
                    for response in app.chat(prompt):
                        msg_placeholder.empty()
                        full_response += response
                elif data_source == "Sitemap":
                    loader = SitemapLoader()
                    app.add(prompt, data_type='sitemap', loader=loader)
                    msg_placeholder.markdown("Analyzing sitemap...")
                    for response in app.chat(prompt):
                        msg_placeholder.empty()
                        full_response += response
                elif data_source == "Q&A pair":
                    # Assuming the prompt contains both question and answer
                    question, answer = prompt.split(" | ")  # Split using a delimiter
                    app.add((question, answer), data_type='qna_pair')
                    msg_placeholder.markdown("Analyzing Q&A pair...")
                    for response in app.chat(prompt):
                        msg_placeholder.empty()
                        full_response += response
                elif data_source == "OpenAPI":
                    app.add(prompt, data_type='openapi')
                    msg_placeholder.markdown("Analyzing OpenAPI spec...")
                    for response in app.chat(prompt):
                        msg_placeholder.empty()
                        full_response += response
                # ... Add handling for other "Other" data sources as needed

        except Exception as e:
            st.error(f"Error processing data: {e}")
            full_response = "Could not process the data source."

        msg_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # --- Feedback Buttons ---
        feedback_option = st.radio(
            "Was this response helpful?",
            options=["Yes", "No"],
            key=f"feedback_{len(st.session_state.messages) - 1}"
        )

        if st.button("Submit Feedback"):
            # Save feedback
            feedback = {
                "query": prompt,
                "response": full_response,
                "feedback": feedback_option
            }
            st.session_state.feedback.append(feedback)

            # Optionally, save feedback to a file
            with open("feedback.json", "a") as f:
                json.dump(feedback, f)
                f.write("\n")

            st.success("Thank you for your feedback!")
