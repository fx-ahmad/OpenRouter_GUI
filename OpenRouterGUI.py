import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk, font
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

import Open_router_basics

# Initialize OpenRouter client
client = Open_router_basics.client

# Available models
MODEL_LIST = [
    "openai/o3-mini-high",
    "anthropic/claude-3-7-sonnet",
    "anthropic/claude-3.7-sonnet:thinking",
    "openai/gpt-4.5-preview",
    "google/gemini-2.0-flash-001",
    "anthropic/claude-3.5-sonnet",
    "perplexity/r1-1776"
]

class OpenRouterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenRouter Chat Interface")
        self.root.geometry("1200x800")
        
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
        
        # System prompt section
        system_frame = tk.LabelFrame(self.left_panel, text="System Prompt", bg="#e0e0e0", padx=10, pady=10)
        system_frame.pack(fill=tk.X, padx=10, pady=10, expand=False)
        
        self.system_prompt = scrolledtext.ScrolledText(system_frame, height=6, wrap=tk.WORD)
        self.system_prompt.pack(fill=tk.X)
        self.system_prompt.insert(tk.END, "You are a helpful assistant.")
        
        # File attachments section
        attachments_frame = tk.LabelFrame(self.left_panel, text="Attachments", bg="#e0e0e0", padx=10, pady=10)
        attachments_frame.pack(fill=tk.BOTH, padx=10, pady=10, expand=True)
        
        button_frame = tk.Frame(attachments_frame, bg="#e0e0e0")
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.attach_image_btn = tk.Button(button_frame, text="Attach Image", command=self.attach_image)
        self.attach_image_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.attach_pdf_btn = tk.Button(button_frame, text="Attach PDF", command=self.attach_pdf)
        self.attach_pdf_btn.pack(side=tk.LEFT)
        
        self.remove_file_btn = tk.Button(button_frame, text="Remove", command=self.remove_file)
        self.remove_file_btn.pack(side=tk.RIGHT)
        
        self.file_listbox = tk.Listbox(attachments_frame, selectmode=tk.SINGLE, height=10)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Session control
        control_frame = tk.Frame(self.left_panel, bg="#e0e0e0", padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.clear_button = tk.Button(control_frame, text="New Session", command=self.clear_session)
        self.clear_button.pack(fill=tk.X)
        
        # Status indicator
        self.status_label = tk.Label(self.left_panel, text="Ready", bg="#e0e0e0", anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.progress = ttk.Progressbar(self.left_panel, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 10))
    
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
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def prepare_messages(self, user_input):
        messages = []
        
        # Add system message if provided
        system_content = self.system_prompt.get("1.0", tk.END).strip()
        if system_content:
            messages.append({"role": "system", "content": system_content})
        
        # Add conversation history
        for msg in self.conversation_history:
            messages.append(msg)
        
        # Prepare the current message with any attachments
        content = []
        
        # Add text content
        content.append({"type": "text", "text": user_input})
        
        # Add file attachments
        for file in self.attached_files:
            if file["type"] == "image":
                try:
                    base64_image = self.encode_image(file["path"])
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })
                except Exception as e:
                    self.update_status(f"Error processing image: {str(e)}")
            
            elif file["type"] == "pdf":
                try:
                    pdf_text = self.extract_pdf_text(file["path"])
                    content.append({
                        "type": "text", 
                        "text": f"\nPDF CONTENT ({os.path.basename(file['path'])}):\n{textwrap.shorten(pdf_text, width=8000, placeholder='...')}"
                    })
                except Exception as e:
                    self.update_status(f"Error processing PDF: {str(e)}")
        
        messages.append({"role": "user", "content": content})
        return messages
    
    def update_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()
    
    def update_chat_display(self):
        html_content = "<html><body style='font-family: Helvetica, Arial, sans-serif;'>"
        
        for msg in self.conversation_history:
            if msg["role"] == "user":
                html_content += f"<div style='margin: 10px 0; padding: 10px; background-color: #e6f2ff; border-radius: 10px;'>"
                html_content += f"<strong>You:</strong><br/>"
                
                if isinstance(msg["content"], list):
                    for item in msg["content"]:
                        if item.get("type") == "text":
                            text_with_br = item['text'].replace('\n', '<br/>')
                            html_content += text_with_br
                        elif item.get("type") == "image_url":
                            html_content += f"<em>[Image attached]</em><br/>"
                else:
                    text_with_br = msg['content'].replace('\n', '<br/>')
                    html_content += text_with_br
                
                html_content += "</div>"
            
            elif msg["role"] == "assistant":
                html_content += f"<div style='margin: 10px 0; padding: 10px; background-color: #f0f0f0; border-radius: 10px;'>"
                html_content += f"<strong>Assistant:</strong><br/>"
                
                # Convert markdown to HTML
                md_content = msg["content"]
                html_from_md = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
                html_content += html_from_md
                
                html_content += "</div>"
            
            elif msg["role"] == "system":
                html_content += f"<div style='margin: 10px 0; padding: 10px; color: #666; font-style: italic;'>"
                # Fix the backslash issue by using a temporary variable
                content_with_br = msg['content'].replace('\n', '<br/>')
                html_content += f"System: {content_with_br}"
                html_content += "</div>"
        
        html_content += "</body></html>"
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
        
        # Store user message
        if len(self.attached_files) > 0:
            user_message = {"role": "user", "content": self.prepare_messages(user_input)[-1]["content"]}
        else:
            user_message = {"role": "user", "content": user_input}
        
        self.conversation_history.append(user_message)
        self.update_chat_display()
        
        # Start processing in a separate thread
        threading.Thread(target=self.process_message, args=(user_input,)).start()
    
    def process_message(self, user_input):
        try:
            messages = self.prepare_messages(user_input)
            selected_model = self.model_var.get()
            
            self.progress['value'] = 30
            self.update_status(f"Sending request to {selected_model}...")
            
            response = client.chat.completions.create(
                model=selected_model,
                messages=[{
                    "role": msg["role"],
                    "content": msg["content"]
                } for msg in messages],
            )
            
            self.progress['value'] = 90
            
            # Get the response content
            assistant_response = response.choices[0].message.content.strip()
            
            # Store assistant message
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            # Update the chat display
            self.root.after(0, self.update_chat_display)
            self.root.after(0, lambda: self.update_status("Ready"))
            self.root.after(0, lambda: setattr(self.progress, 'value', 100))
            
            # Clear attachments after successful message
            self.root.after(0, self.clear_attachments)
            
        except Exception as e:
            error_message = f"Error: {str(e)}"
            self.root.after(0, lambda: self.update_status(error_message))
            print(error_message)  # Print to console for debugging
        finally:
            self.is_processing = False
    
    def clear_attachments(self):
        self.attached_files = []
        self.file_listbox.delete(0, tk.END)

def main():
    root = tk.Tk()
    app = OpenRouterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
