# filepath: /innovative-chatbot/innovative-chatbot/src/smart_chatbot.py

import streamlit as st
from advanced_ai import AdvancedAI
from utils import load_user_data, save_user_data, log_interaction

class InnovativeChatbot:
    def __init__(self):
        self.ai_model = AdvancedAI()
        self.user_data = load_user_data()
        self.initialize_chat()

    def initialize_chat(self):
        st.title("🤖 Innovative ChatBot")
        st.sidebar.header("User Preferences")
        self.setup_user_preferences()

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            st.write(message)

        if prompt := st.chat_input("How can I assist you today?"):
            self.handle_user_input(prompt)

    def setup_user_preferences(self):
        self.user_name = st.sidebar.text_input("Enter your name", value=self.user_data.get("name", ""))
        self.user_interests = st.sidebar.multiselect("Select your interests", options=["Technology", "Health", "Finance", "Travel"], default=self.user_data.get("interests", []))
        if st.sidebar.button("Save Preferences"):
            self.save_user_preferences()

    def save_user_preferences(self):
        self.user_data["name"] = self.user_name
        self.user_data["interests"] = self.user_interests
        save_user_data(self.user_data)
        st.success("Preferences saved!")

    def handle_user_input(self, prompt):
        response = self.ai_model.generate_response(prompt, self.user_data)
        st.session_state.messages.append(f"You: {prompt}")
        st.session_state.messages.append(f"Bot: {response}")
        log_interaction(prompt, response)

if __name__ == "__main__":
    InnovativeChatbot()