import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk
import threading
import ollama
from PyPDF2 import PdfReader
import textwrap
import time

def create_interface():
    root = tk.Tk()
    root.title("Ollama Chat Interface")
    root.geometry("2560x1440")

    # Chat history display
    chat_history = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    chat_history.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    chat_history.configure(state='disabled')

    # PDF attachment section
    attachment_frame = tk.Frame(root)
    attachment_frame.pack(padx=10, pady=5, fill=tk.X)

    attach_button = tk.Button(attachment_frame, text="Attach PDF", command=attach_pdf)
    attach_button.pack(side=tk.LEFT)

    pdf_listbox = tk.Listbox(attachment_frame, selectmode=tk.SINGLE, width=50)
    pdf_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

    remove_button = tk.Button(attachment_frame, text="Remove", command=remove_pdf)
    remove_button.pack(side=tk.RIGHT)

    # Add control buttons
    control_frame = tk.Frame(root)
    control_frame.pack(padx=10, pady=5, fill=tk.X)
    
    clear_button = tk.Button(control_frame, text="New Session", command=clear_session)
    clear_button.pack(side=tk.RIGHT, padx=(10, 0))

    # User input section
    input_frame = tk.Frame(root)
    input_frame.pack(padx=10, pady=10, fill=tk.X)

    input_field = tk.Entry(input_frame)
    input_field.pack(side=tk.LEFT, fill=tk.X, expand=True)
    input_field.bind("<Return>", lambda event: send_message())

    send_button = tk.Button(input_frame, text="Send", command=send_message)
    send_button.pack(side=tk.RIGHT, padx=(10, 0))

    # Status indicator
    status_label = tk.Label(root, text="Ready", anchor=tk.W)
    status_label.pack(side=tk.BOTTOM, fill=tk.X)

    # Add progress bar
    progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, mode='determinate')
    progress.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    return {
        'root': root,
        'chat_history': chat_history,
        'input_field': input_field,
        'status_label': status_label,
        'pdf_listbox': pdf_listbox,
        'attached_pdfs': [],
        'progress': progress,
        'current_context': "",
        'response_buffer': '',
        'last_update': 0
    }

def attach_pdf():
    file_path = filedialog.askopenfilename(
        title="Select PDF",
        filetypes=[("PDF Files", "*.pdf")]
    )
    if file_path:
        app_state['attached_pdfs'].append(file_path)
        app_state['pdf_listbox'].insert(tk.END, file_path.split('/')[-1])

def remove_pdf():
    selection = app_state['pdf_listbox'].curselection()
    if selection:
        index = selection[0]
        app_state['pdf_listbox'].delete(index)
        del app_state['attached_pdfs'][index]

def extract_pdf_text(file_path, update_progress):
    try:
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        extracted_text = []
        
        for i, page in enumerate(reader.pages):
            extracted_text.append(page.extract_text())
            update_progress((i + 1) / total_pages * 100)
            
        return " ".join(extracted_text)
    except Exception as e:
        return f"PDF Error: {str(e)}"

def prepare_context(state):
    state['current_context'] = ""
    total_pdfs = len(state['attached_pdfs'])
    
    if not total_pdfs:
        return ""

    # Create progress window
    progress_window = tk.Toplevel(state['root'])
    progress_window.title("Processing PDFs")
    progress_bar = ttk.Progressbar(progress_window, length=300, mode='determinate')
    progress_bar.pack(padx=20, pady=20)
    progress_window.grab_set()

    def update_pdf_progress(percentage):
        progress_bar['value'] = percentage
        if percentage >= 100:
            progress_window.destroy()

    context_parts = []
    for idx, pdf_path in enumerate(state['attached_pdfs']):
        progress_window.title(f"Processing PDF {idx+1}/{total_pdfs}")
        pdf_text = extract_pdf_text(pdf_path, update_pdf_progress)
        context_parts.append(f"PDF CONTEXT [{pdf_path.split('/')[-1]}]:\n{textwrap.shorten(pdf_text, width=4000, placeholder='...')}")

    state['current_context'] = "\n\n".join(context_parts)
    return state['current_context']

def update_chat(history_widget, message, is_user=True):
    history_widget.configure(state='normal')
    tag = 'user' if is_user else 'bot'
    history_widget.insert(tk.END, f"{'You' if is_user else 'Assistant'}: {message}\n", tag)
    history_widget.configure(state='disabled')
    history_widget.see(tk.END)

def clear_session():
    app_state['chat_history'].configure(state='normal')
    app_state['chat_history'].delete(1.0, tk.END)
    app_state['chat_history'].configure(state='disabled')
    app_state['pdf_listbox'].delete(0, tk.END)
    app_state['attached_pdfs'].clear()
    app_state['current_context'] = ""
    app_state['status_label'].config(text="Session Cleared")
    app_state['progress']['value'] = 0
    app_state['response_buffer'] = ''
    app_state['last_update'] = 0

def flush_response(state, force=False):
    current_time = time.time()
    if force or (current_time - state['last_update'] >= 0.5 and state['response_buffer']):
        wrapped = textwrap.fill(state['response_buffer'], width=100) + '\n'
        update_chat(state['chat_history'], wrapped, False)
        state['response_buffer'] = ''
        state['last_update'] = current_time

def handle_response(state):
    try:
        user_input = state['input_field'].get()
        state['input_field'].delete(0, tk.END)
        update_chat(state['chat_history'], user_input, is_user=True)
        
        state['status_label'].config(text="Processing...")
        state['progress']['value'] = 0
        
        context = prepare_context(state)
        full_prompt = f"CONTEXT:\n{context}\n\nQUERY: {user_input}" if context else user_input
        
        state['root'].after(0, lambda: update_chat(
            state['chat_history'], 
            f"System: Sending query with context:\n{full_prompt}\n\n--- Generating Response ---\n",
            False
        ))
        
        # Create streaming response
        response = ollama.generate(
            model='deepseek-r1:14b',
            prompt=full_prompt,
            options={'num_ctx': 4096},
            stream=True
        )
        
        # Process stream chunks
        state['response_buffer'] = ''
        state['last_update'] = time.time()
        
        for chunk in response:
            if 'response' in chunk:
                state['response_buffer'] += chunk['response']
                
                # Check for natural break points
                if len(state['response_buffer']) > 80 or any(c in '.!?,;:' for c in chunk['response']):
                    state['root'].after(0, flush_response, state, False)
        
        # Final flush
        state['root'].after(0, flush_response, state, True)
        
        state['progress']['value'] = 100
        state['status_label'].config(text="Ready")
        
    except Exception as e:
        state['status_label'].config(text=f"Error: {str(e)}")
        state['progress']['value'] = 0

def send_message():
    state = app_state
    threading.Thread(target=handle_response, args=(state,)).start()

# Application setup
app_state = create_interface()
app_state['chat_history'].tag_config('user', foreground='blue')
app_state['chat_history'].tag_config('bot', foreground='green')
app_state['root'].mainloop()
