# Ollama GUI

A graphical user interface for interacting with Ollama models, featuring PDF context support and real-time response streaming.

## Prerequisites

- Python 3.8 or higher
- Ollama installed and running on your system
  - [Install Ollama](https://ollama.ai/download)

## Installation

1. Install required Python packages:
bash
pip install tkinter ollama PyPDF2 pyinstaller

2. Clone or download this repository:
bash
git clone <https://github.com/Wegatriespython/Ollama_Gui>
cd ollama-gui
3. Run directly with Python:
bash
python ollama_gui.py

Or build as standalone application:
bash
python -m PyInstaller ollama_gui.spec
The executable will be created in `dist/Ollama GUI/`.

## Features

- Real-time chat interface with Ollama models
- PDF document context support
- Model selection dropdown
- Response streaming with stop capability
- Session management
- Progress indicators for long operations

## Usage

1. Launch the application
2. Select your preferred Ollama model from the dropdown
   - Use "Refresh" button to update available models
3. (Optional) Attach PDF documents for context
   - Click "Attach PDF" to select documents
   - Use "Remove" to remove selected documents
4. Type your message and press Enter or click "Send"
5. Use "Stop" to halt generation
6. "New Session" clears the current chat and removes attached PDFs

## Troubleshooting

- Ensure Ollama is running before launching the GUI
- Check that required models are downloaded in Ollama
- For PDF issues, ensure files are not corrupted or password-protected

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
