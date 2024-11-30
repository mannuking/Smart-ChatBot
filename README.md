# Smart ChatBot

## Project Overview

Smart ChatBot is an interactive web application powered by Streamlit and OpenAI's GPT-3.5 Turbo model. It offers two main functionalities:
1. **Smart Chat Mode**: A conversational assistant that provides answers, interacts with uploaded documents, and assists with various queries.
2. **Project Generator Mode**: A tool to create comprehensive project plans, requirements, folder structures, and code templates.

## Features

### Smart Chat Mode
- Chat with an intelligent assistant.
- Upload and analyze documents in formats such as PDF, Word, Excel, JSON, and more.
- Extract and display content from uploaded files.

### Project Generator Mode
- Generate detailed project plans, including:
  - Project scope and requirements.
  - Folder structure adhering to best practices.
  - Code templates based on user input.
- Automatically debug and execute generated code.
- Download complete projects as a zip file.

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key (saved in a `.env` file)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/mannuking/Smart-ChatBot
   cd https://github.com/mannuking/Smart-ChatBot
   ```
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file:
     ```
     OPENAI_API_KEY=your_openai_api_key
     ```
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

### Smart Chat Mode
1. Upload supported documents through the sidebar.
2. Interact with the chatbot to analyze document content or answer queries.

### Project Generator Mode
1. Enter a project idea in the text area.
2. Generate project outputs:
   - Comprehensive project plan.
   - Folder structure.
   - Requirements and code templates.
3. Download the entire project for use.

## Supported File Types
- **PDF**: Extracted using `PyPDF2`.
- **Word Documents**: Processed with `python-docx`.
- **Excel**: Data extracted using `pandas`.
- **XML**: Extracted as plain text.
- **JSON, CSV, TXT**: Read as plain text.

## Example Project Structure

```
project/
├── src/
│   ├── main.py
│   ├── utils/
│   │   └── helper_functions.py
│   └── models/
│       └── example_model.py
├── tests/
│   └── test_main.py
├── docs/
│   └── README.md
└── requirements.txt
```

## Dependencies
- `streamlit`
- `openai`
- `python-dotenv`
- `PyPDF2`
- `python-docx`
- `pandas`
- Other dependencies in `requirements.txt`.

## Known Issues
- Limited support for complex Excel and XML files.
- Requires a stable internet connection for OpenAI API requests.

## Contributing
Contributions are welcome. Submit pull requests or report issues for improvement.

## License
Licensed under the MIT License. See the `LICENSE` file for details.

## Contact
For queries, reach out at jk422331@gmail.com.
