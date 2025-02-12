def log_message(message, level="INFO"):
    """Logs messages with different severity levels."""
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    
    if level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)

def preprocess_input(user_input):
    """Cleans and preprocesses user input for further processing."""
    import re
    return re.sub(r'\s+', ' ', user_input.strip())

def fetch_external_data(api_url):
    """Fetches data from an external API."""
    import requests
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log_message(f"Error fetching data from {api_url}: {e}", level="ERROR")
        return None

def save_user_preferences(user_id, preferences):
    """Saves user preferences to a local storage or database."""
    import json
    with open(f"user_preferences_{user_id}.json", "w") as f:
        json.dump(preferences, f)

def load_user_preferences(user_id):
    """Loads user preferences from local storage or database."""
    import json
    try:
        with open(f"user_preferences_{user_id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        log_message(f"No preferences found for user {user_id}.", level="WARNING")
        return {}