import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk, font, messagebox
import threading
import openai
import io
import base64
from PIL import Image, ImageTk
import re
import os
from PyPDF2 import PdfReader
import textwrap
import markdown
import tkhtmlview
import tiktoken
import mimetypes   # <-- Added for MIME type guessing
import json
from datetime import datetime

import Open_router_basics

# Initialize OpenRouter client
client = Open_router_basics.client

# Available models
MODEL_LIST = Open_router_basics.Model_list

# Model pricing information ($/million tokens)
MODEL_PRICING = Open_router_basics.Model_cost

class OpenRouterGUI:
    def __init__(self, root):
        # Initialize token counters and session cost tracking before any UI setup calls
        self.total_input_tokens = 0  # Initialize input tokens to 0
        self.total_output_tokens = 0  # Initialize output tokens to 0
        self.total_cost = 0.0         # Initialize session cost to 0.0

        self.root = root
        self.root.title("OpenRouter Chat Interface")
        self.root.geometry("1920x1080")
        
        # Set up the main frame with a nice background
        self.main_frame = tk.Frame(root, bg="#f5f5f5")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a paned window for resizable sections
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for settings and attachments
        self.left_panel = tk.Frame(self.paned_window, bg="#e0e0e0", width=300)
        
        # Right panel for chat
        self.right_panel = tk.Frame(self.paned_window, bg="#f5f5f5")
        
        self.paned_window.add(self.left_panel, weight=1)
        self.paned_window.add(self.right_panel, weight=3)
        
        # Initialize UI components
        self.setup_left_panel()
        self.setup_right_panel()
        
        # Initialize state variables
        self.attached_files = []
        self.conversation_history = []
        self.is_processing = False
        
        # Apply styling
        self.apply_styling()
    
    def apply_styling(self):
        # Configure tags for the chat display
        custom_font = font.Font(family="Helvetica", size=11)
        self.chat_display.tag_configure("user", foreground="#0066cc", font=custom_font)
        self.chat_display.tag_configure("assistant", foreground="#006633", font=custom_font)
        italic_font = font.Font(family="Helvetica", size=11, slant="italic")
        self.chat_display.tag_configure("system", foreground="#666666", font=italic_font)
        
        # Style buttons
        button_style = {"bg": "#4a86e8", "fg": "white", "padx": 10, "pady": 5, 
                        "font": ("Helvetica", 10), "relief": tk.RAISED}
        
        for btn in [self.send_button, self.attach_image_btn, self.attach_pdf_btn, 
                    self.clear_button, self.remove_file_btn]:
            for key, value in button_style.items():
                btn.config(**{key: value})
    
    def setup_left_panel(self):
        # Model selection section
        model_frame = tk.LabelFrame(self.left_panel, text="Model Selection", bg="#e0e0e0", padx=10, pady=10)
        model_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.model_var = tk.StringVar(value=MODEL_LIST[0])
        model_dropdown = ttk.Combobox(model_frame, textvariable=self.model_var, values=MODEL_LIST, state="readonly", width=25)
        model_dropdown.pack(fill=tk.X)
        model_dropdown.bind("<<ComboboxSelected>>", self.update_cost_display)
        
        # System prompt section
        system_frame = tk.LabelFrame(self.left_panel, text="System Prompt", bg="#e0e0e0", padx=10, pady=10)
        system_frame.pack(fill=tk.X, padx=10, pady=10, expand=False)
        
        self.system_prompt = scrolledtext.ScrolledText(system_frame, height=6, wrap=tk.WORD)
        self.system_prompt.pack(fill=tk.X)
        self.system_prompt.insert(tk.END, "You are a helpful assistant.")
        
        # File attachments section
        attachments_frame = tk.LabelFrame(self.left_panel, text="Attachments", bg="#e0e0e0", padx=10, pady=10)
        attachments_frame.pack(fill=tk.X, padx=10, pady=10)
        
        button_frame = tk.Frame(attachments_frame, bg="#e0e0e0")
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.attach_image_btn = tk.Button(button_frame, text="Attach Image", command=self.attach_image)
        self.attach_image_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.attach_pdf_btn = tk.Button(button_frame, text="Attach PDF", command=self.attach_pdf)
        self.attach_pdf_btn.pack(side=tk.LEFT)
        
        self.remove_file_btn = tk.Button(button_frame, text="Remove", command=self.remove_file)
        self.remove_file_btn.pack(side=tk.RIGHT)
        
        self.file_listbox = tk.Listbox(attachments_frame, selectmode=tk.SINGLE, height=5)
        self.file_listbox.pack(fill=tk.X)
        
        # Cost tracking section
        cost_frame = tk.LabelFrame(self.left_panel, text="Session Cost Tracker", bg="#e0e0e0", padx=10, pady=10)
        cost_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Model pricing info
        pricing_frame = tk.Frame(cost_frame, bg="#e0e0e0")
        pricing_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(pricing_frame, text="Current Model Pricing ($/M tokens):", bg="#e0e0e0", anchor=tk.W).pack(fill=tk.X)
        
        price_info_frame = tk.Frame(pricing_frame, bg="#e0e0e0")
        price_info_frame.pack(fill=tk.X)
        
        tk.Label(price_info_frame, text="Input:", bg="#e0e0e0", width=10, anchor=tk.W).grid(row=0, column=0, sticky=tk.W)
        self.input_price_label = tk.Label(price_info_frame, text="$0.15", bg="#e0e0e0", anchor=tk.W)
        self.input_price_label.grid(row=0, column=1, sticky=tk.W)
        
        tk.Label(price_info_frame, text="Output:", bg="#e0e0e0", width=10, anchor=tk.W).grid(row=1, column=0, sticky=tk.W)
        self.output_price_label = tk.Label(price_info_frame, text="$0.60", bg="#e0e0e0", anchor=tk.W)
        self.output_price_label.grid(row=1, column=1, sticky=tk.W)
        
        # Token usage
        token_frame = tk.Frame(cost_frame, bg="#e0e0e0")
        token_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(token_frame, text="Token Usage:", bg="#e0e0e0", anchor=tk.W).pack(fill=tk.X)
        
        token_info_frame = tk.Frame(token_frame, bg="#e0e0e0")
        token_info_frame.pack(fill=tk.X)
        
        tk.Label(token_info_frame, text="Input:", bg="#e0e0e0", width=10, anchor=tk.W).grid(row=0, column=0, sticky=tk.W)
        self.input_tokens_label = tk.Label(token_info_frame, text="0", bg="#e0e0e0", anchor=tk.W)
        self.input_tokens_label.grid(row=0, column=1, sticky=tk.W)
        
        tk.Label(token_info_frame, text="Output:", bg="#e0e0e0", width=10, anchor=tk.W).grid(row=1, column=0, sticky=tk.W)
        self.output_tokens_label = tk.Label(token_info_frame, text="0", bg="#e0e0e0", anchor=tk.W)
        self.output_tokens_label.grid(row=1, column=1, sticky=tk.W)
        
        # Total cost
        cost_total_frame = tk.Frame(cost_frame, bg="#e0e0e0")
        cost_total_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(cost_total_frame, text="Total Cost:", bg="#e0e0e0", font=("Helvetica", 10, "bold"), anchor=tk.W).grid(row=0, column=0, sticky=tk.W)
        self.total_cost_label = tk.Label(cost_total_frame, text="$0.00", bg="#e0e0e0", font=("Helvetica", 10, "bold"), anchor=tk.W)
        self.total_cost_label.grid(row=0, column=1, sticky=tk.W)
        
        # Session control
        control_frame = tk.Frame(self.left_panel, bg="#e0e0e0", padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.clear_button = tk.Button(control_frame, text="New Session", command=self.clear_session)
        self.clear_button.pack(fill=tk.X)
        
        # New buttons for archiving and viewing chat history
        self.archive_button = tk.Button(control_frame, text="Archive Chat", command=self.archive_chat)
        self.archive_button.pack(fill=tk.X, pady=(5, 0))
        
        self.view_history_button = tk.Button(control_frame, text="View History", command=self.view_history)
        self.view_history_button.pack(fill=tk.X, pady=(5, 0))
        
        # Status indicator
        self.status_label = tk.Label(self.left_panel, text="Ready", bg="#e0e0e0", anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.progress = ttk.Progressbar(self.left_panel, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Initialize cost display
        self.update_cost_display()
    
    def setup_right_panel(self):
        # Chat display area
        chat_frame = tk.Frame(self.right_panel, bg="#f5f5f5")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Use HTML viewer for markdown rendering
        self.chat_display = tkhtmlview.HTMLScrolledText(chat_frame, html="<html><body></body></html>")
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # User input area
        input_frame = tk.Frame(self.right_panel, bg="#f5f5f5")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.user_input = scrolledtext.ScrolledText(input_frame, height=5, wrap=tk.WORD)
        self.user_input.pack(fill=tk.X, pady=(0, 5))
        self.user_input.bind("<Control-Return>", self.send_message_event)
        
        self.send_button = tk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)
    
    def attach_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            self.attached_files.append({"type": "image", "path": file_path})
            self.file_listbox.insert(tk.END, f"Image: {os.path.basename(file_path)}")
    
    def attach_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Select PDF",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if file_path:
            self.attached_files.append({"type": "pdf", "path": file_path})
            self.file_listbox.insert(tk.END, f"PDF: {os.path.basename(file_path)}")
    
    def remove_file(self):
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            self.file_listbox.delete(index)
            del self.attached_files[index]
    
    def clear_session(self):
        self.conversation_history = []
        self.chat_display.set_html("<html><body></body></html>")
        self.status_label.config(text="Session Cleared")
        self.progress['value'] = 0
        
        # Reset token and cost tracking
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.update_cost_display()
    
    def extract_pdf_text(self, file_path):
        try:
            reader = PdfReader(file_path)
            extracted_text = []
            
            for page in reader.pages:
                extracted_text.append(page.extract_text())
                
            return " ".join(extracted_text)
        except Exception as e:
            return f"PDF Error: {str(e)}"
    
    def encode_image(self, image_path):
        # Open and encode the image with a data URI prefix based on its MIME type.
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "image/jpeg"  # default MIME type if unknown
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    
    def prepare_messages(self, user_input):
        messages = []

        # Add system message if provided
        system_content = self.system_prompt.get("1.0", tk.END).strip()
        if system_content:
            messages.append({"role": "system", "content": system_content})

        # Add conversation history
        for msg in self.conversation_history:
            messages.append(msg)

        # Build the user message as a single plain text string.
        message_content = user_input

        # Process file attachments:
        for file in self.attached_files:
            if file["type"] == "image":
                try:
                    # (Optionally, you could include image data here if supported.)
                    # For now, simply add a marker to inform the user and model.
                    message_content += f"\n[Image Attached: {os.path.basename(file['path'])}]"
                except Exception as e:
                    self.update_status(f"Error processing image: {str(e)}")
            
            elif file["type"] == "pdf":
                try:
                    # Instead of appending the full PDF text, add a marker.
                    message_content += f"\n[PDF Attached: {os.path.basename(file['path'])}]"
                except Exception as e:
                    self.update_status(f"Error processing PDF: {str(e)}")

        # Append the plain-text user message.
        messages.append({"role": "user", "content": message_content})
        return messages
    
    def update_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()
    
    def get_rendered_chat_html(self):
        # Generate HTML content based on conversation history
        html_content = "<html><body style='font-family: Helvetica, Arial, sans-serif;'>"
        for msg in self.conversation_history:
            if msg["role"] == "user":
                html_content += (
                    "<div style='margin: 10px 0; padding: 10px; "
                    "background-color: #e6f2ff; border-radius: 10px;'>"
                )
                html_content += "<strong>You:</strong><br/>"
                content_to_display = msg.get("display", msg.get("content", ""))
                text_with_br = content_to_display.replace('\n', '<br/>')
                html_content += text_with_br
                html_content += "</div>"
            elif msg["role"] == "assistant":
                html_content += (
                    "<div style='margin: 10px 0; padding: 10px; "
                    "background-color: #f0f0f0; border-radius: 10px;'>"
                )
                html_content += "<strong>Assistant:</strong><br/>"
                md_content = msg["content"]
                html_from_md = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
                html_content += html_from_md
                html_content += "</div>"
            elif msg["role"] == "system":
                html_content += (
                    "<div style='margin: 10px 0; padding: 10px; "
                    "color: #666; font-style: italic;'>"
                )
                content_with_br = msg['content'].replace('\n', '<br/>')
                html_content += f"System: {content_with_br}"
                html_content += "</div>"
        html_content += "</body></html>"
        return html_content

    def update_chat_display(self):
        html_content = self.get_rendered_chat_html()
        self.chat_display.set_html(html_content)
    
    def send_message_event(self, event):
        self.send_message()
    
    def send_message(self):
        if self.is_processing:
            return
        
        user_input = self.user_input.get("1.0", tk.END).strip()
        if not user_input:
            return
        
        self.user_input.delete("1.0", tk.END)
        self.is_processing = True
        self.update_status("Processing...")
        self.progress['value'] = 10
        
        # Build separate display and API versions of the user message.
        display_message = user_input
        api_message_parts = []
        
        # Add the text part if present.
        if user_input:
            api_message_parts.append({"type": "text", "text": user_input})
        
        # Process file attachments:
        for file in self.attached_files:
            if file["type"] == "image":
                display_message += f"\n[Image Attached: {os.path.basename(file['path'])}]"
                try:
                    encoded_image = self.encode_image(file["path"])
                    api_message_parts.append({
                        "type": "image_url",
                        "image_url": {"url": encoded_image}
                    })
                except Exception as e:
                    self.update_status(f"Error processing image: {str(e)}")
            elif file["type"] == "pdf":
                display_message += f"\n[PDF Attached: {os.path.basename(file['path'])}]"
                try:
                    pdf_text = self.extract_pdf_text(file["path"])
                    api_message_parts.append({
                        "type": "text",
                        "text": f"PDF CONTENT ({os.path.basename(file['path'])}):\n{pdf_text}"
                    })
                except Exception as e:
                    self.update_status(f"Error processing PDF: {str(e)}")
        
        # Store the user message with separate display and API multi-part content.
        user_message = {"role": "user", "display": display_message, "content": api_message_parts}
        self.conversation_history.append(user_message)
        self.update_chat_display()
        
        # Begin processing in a separate thread.
        threading.Thread(target=self.process_message).start()
    
    def process_message(self):
        try:
            # Build messages for the API call.
            system_content = self.system_prompt.get("1.0", tk.END).strip()
            messages = []
            if system_content:
                messages.append({"role": "system", "content": system_content})
            for msg in self.conversation_history:
                if msg["role"] == "user" and "api_content" in msg:
                    messages.append({"role": "user", "content": msg["api_content"]})
                else:
                    messages.append({"role": msg["role"], "content": msg.get("content", "")})

            selected_model = self.model_var.get()
            
            # Estimate input tokens
            input_tokens = self.estimate_tokens(messages)
            self.total_input_tokens += input_tokens
            
            self.progress['value'] = 30
            self.update_status(f"Sending request to {selected_model}...")
            
            response = client.chat.completions.create(
                model=selected_model,
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            )
            
            self.progress['value'] = 90
            
            assistant_response = response.choices[0].message.content.strip()
            
            # Estimate output tokens
            output_tokens = self.estimate_tokens([{"role": "assistant", "content": assistant_response}])
            self.total_output_tokens += output_tokens
            
            # Calculate cost
            self.calculate_session_cost()
            
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            self.root.after(0, self.update_chat_display)
            self.root.after(0, self.update_cost_display)
            self.root.after(0, lambda: self.update_status("Ready"))
            self.root.after(0, lambda: setattr(self.progress, 'value', 100))
            self.root.after(0, self.clear_attachments)
            
        except Exception as e:
            error_message = f"Error: {str(e)}"
            self.root.after(0, lambda: self.update_status(error_message))
            print(error_message)
        finally:
            self.is_processing = False
    
    def estimate_tokens(self, messages):
        """Estimate token count for a list of messages"""
        try:
            # Try to use tiktoken for OpenAI models
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            token_count = 0
            
            for message in messages:
                # Add tokens for message role
                token_count += 4  # Approximate tokens for role
                
                content = message.get("content", "")
                if isinstance(content, list):
                    # Process each part in multi-part messages
                    for part in content:
                        if part.get("type") == "text":
                            text = part.get("text", "")
                            token_count += len(encoding.encode(text))
                        elif part.get("type") == "image_url":
                            # Use a constant token count for image parts
                            token_count += 3
                else:
                    # Fallback to string content estimation
                    token_count += len(encoding.encode(content))
            
            # Add a few tokens for message formatting
            token_count += 2
            
            return token_count
        except:
            # Fallback to character-based estimation (very rough)
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            # Rough estimate: 1 token ≈ 4 characters for English text
            return total_chars // 4
    
    def calculate_session_cost(self):
        """Calculate the total cost of the session based on token usage"""
        selected_model = self.model_var.get()
        
        if selected_model in MODEL_PRICING:
            pricing = MODEL_PRICING[selected_model]
            input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
            output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]
            self.total_cost = input_cost + output_cost
    
    def update_cost_display(self, event=None):
        """Update the cost display UI elements"""
        selected_model = self.model_var.get()
        
        if selected_model in MODEL_PRICING:
            pricing = MODEL_PRICING[selected_model]
            self.input_price_label.config(text=f"${pricing['input']:.2f}")
            self.output_price_label.config(text=f"${pricing['output']:.2f}")
        
        self.input_tokens_label.config(text=f"{self.total_input_tokens:,}")
        self.output_tokens_label.config(text=f"{self.total_output_tokens:,}")
        self.total_cost_label.config(text=f"${self.total_cost:.6f}")
    
    def clear_attachments(self):
        self.attached_files = []
        self.file_listbox.delete(0, tk.END)

    def get_conversation_markdown(self):
        """Generate a markdown summary from the conversation history."""
        md_text = ""
        for msg in self.conversation_history:
            if msg["role"] == "user":
                text = msg.get("display", msg.get("content", ""))
                md_text += f"**You:** {text}\n\n"
            elif msg["role"] == "assistant":
                md_text += f"**Assistant:** {msg.get('content', '')}\n\n"
            elif msg["role"] == "system":
                md_text += f"**System:** {msg.get('content', '')}\n\n"
        return md_text

    def archive_chat(self):
        # Archive the current chat state if there is conversation history.
        if not self.conversation_history:
            self.update_status("No chat to archive")
            return
        try:
            # Generate markdown context from the conversation history
            conversation_md = self.get_conversation_markdown()
            # Ping the naming model with markdown context for a short descriptive name
            response = client.chat.completions.create(
                model="google/gemini-2.0-flash-001",
                messages=[
                    {"role": "system", "content": "Describe the conversation in maximum 5 words. Use the markdown below as context:"},
                    {"role": "user", "content": conversation_md}
                ],
            )
            chat_name = response.choices[0].message.content.strip()
            chat_name = " ".join(chat_name.split()[:5])  # Only take the first 5 words
        except Exception as e:
            chat_name = "Archived Chat"
            self.update_status(f"Archiving name error: {str(e)}")
        
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rendered_content = self.get_rendered_chat_html()
        attachments = self.attached_files.copy()  # capture current attachments list
        
        archive_entry = {
            "name": chat_name,
            "date": current_date,
            "conversation_history": self.conversation_history,
            "rendered_content": rendered_content,
            "attachments": attachments,
        }
        
        archive_file = "chat_archives.json"
        archives = []
        if os.path.exists(archive_file):
            try:
                with open(archive_file, "r", encoding="utf-8") as f:
                    archives = json.load(f)
            except:
                archives = []
        archives.append(archive_entry)
        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(archives, f, indent=4)
        self.update_status(f"Chat archived as: {chat_name}")

    def view_history(self):
        archive_file = "chat_archives.json"
        if not os.path.exists(archive_file):
            self.update_status("No archived chats found.")
            return
        try:
            with open(archive_file, "r", encoding="utf-8") as f:
                archives = json.load(f)
        except Exception as e:
            self.update_status(f"Error loading archives: {str(e)}")
            return
        
        history_win = tk.Toplevel(self.root)
        history_win.title("Archived Chats")
        history_win.geometry("400x300")
        # Reminder for deletion action
        info_label = tk.Label(history_win, text="(Hint: Ctrl+Left-click on an entry to delete it)", fg="red")
        info_label.pack(pady=(5, 0))
        
        listbox = tk.Listbox(history_win)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for idx, entry in enumerate(archives):
            listbox.insert(tk.END, f"{entry['date']} - {entry['name']}")
        
        def on_view():
            # Archive the current chat if there's content
            if self.conversation_history:
                self.archive_chat()
            selection = listbox.curselection()
            if not selection:
                return
            index = selection[0]
            selected_archive = archives[index]

            # Load the selected archive as the current chat
            self.conversation_history = selected_archive.get("conversation_history", [])
            self.attached_files = selected_archive.get("attachments", [])
            self.update_chat_display()
            self.update_status(f"Loaded archived chat: {selected_archive.get('name')}")
        
        view_btn = tk.Button(history_win, text="View Chat", command=on_view)
        view_btn.pack(pady=5)

        def on_ctrl_click(event):
            # Determine which archive entry was clicked
            index = listbox.nearest(event.y)
            if index < 0 or index >= len(archives):
                return
            # Confirm deletion using a message box
            if messagebox.askyesno("Delete Chat", "Are you sure you want to delete this archived chat?"):
                archives.pop(index)
                with open(archive_file, "w", encoding="utf-8") as f:
                    json.dump(archives, f, indent=4)
                # Refresh the listbox with updated archives
                listbox.delete(0, tk.END)
                for idx, entry in enumerate(archives):
                    listbox.insert(tk.END, f"{entry['date']} - {entry['name']}")
                self.update_status("Deleted archived chat.")

        listbox.bind("<Control-Button-1>", on_ctrl_click)

def main():
    root = tk.Tk()
    app = OpenRouterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 