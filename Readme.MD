# OpenRouterGUI

OpenRouterGUI is a graphical user interface application built with Python's Tkinter library. It interfaces with the OpenAI API to provide a conversational chat interface with additional functionalities such as file attachments, session cost tracking, and chat archiving.

## Features

- **Chat Interface**: Communicate with the OpenAI models through a user-friendly chat interface.
- **Model Selection**: Choose from a list of available models to interact with.
- **System Prompts**: Customize the system prompt to guide the behavior of the assistant.
- **File Attachments**: Attach images and PDFs to your chat sessions.
- **Token and Cost Tracking**: Keep track of input and output tokens and the associated costs.
- **Session Management**: Start new sessions, archive chats, and view archived chat history.
- **Markdown Rendering**: Display chat messages with markdown rendering for better readability.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Wegatriespython/Ollama_Gui.git
   cd Ollama_Gui
   ```

2. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python OpenRouterGUI.py
   ```

## Usage

1. **Launch the Application**: Run the `OpenRouterGUI.py` script to launch the GUI.
2. **Select a Model**: Choose a model from the dropdown list in the left panel.
3. **Set System Prompt**: Customize the system prompt if needed.
4. **Attach Files**: Use the buttons in the attachments section to attach images or PDFs.
5. **Send Messages**: Type your message in the input area and click "Send" or press `Ctrl+Enter`.
6. **View and Archive Chats**: Archive the current chat session or view previously archived chats.

## Dependencies

- `tkinter`: Python's standard GUI toolkit.
- `openai`: OpenAI API client.
- `Pillow`: Python Imaging Library for image processing.
- `PyPDF2`: Library for reading PDF files.
- `tkhtmlview`: HTML viewer for Tkinter.
- `tiktoken`: Tokenizer for OpenAI models.

## Files

- `OpenRouterGUI.py`: Main application script.
- `Open_router_basics.py`: Contains basic configurations and client initialization for the OpenAI API.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Thanks to OpenAI for providing the API and models used in this application.
- Special thanks to the developers of the libraries used in this project.

## Contact

For any questions or issues, please open an issue on the [GitHub repository](https://github.com/Wegatriespython/Ollama_Gui).

---

This README provides an overview of the OpenRouterGUI application, including its features, installation instructions, usage guidelines, dependencies, and contribution information.
