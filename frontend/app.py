import gradio as gr
import requests
import os

API_URL = "http://localhost:8000"

def upload_file(file):
    if file is None:
        return "Please select a PDF file", None
    
    try:
        with open(file, "rb") as f:
            files = {"file": (os.path.basename(file), f, "application/pdf")}
            response = requests.post(f"{API_URL}/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            return (
                f"✅ Success!\n"
                f"File: {result['filename']}\n"
                f"Pages: {result['pages']}",
                result
            )
        else:
            return f"❌ Error: {response.text}", None
    except Exception as e:
        return f"❌ Connection error: {str(e)}", None

def ask_question(question, history, upload_status):
    """Answer question about the document"""
    # Guard clauses
    if not upload_status:
        return history, "Please upload a PDF first"
    
    if not question or not question.strip():
        return history, ""
    
    # Initialize history as list of dicts with role/content
    if history is None:
        history = []
    
    try:
        # Make API call with timeout
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question.strip()},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract answer and sources
            answer = result.get("answer", "No answer provided")
            sources = result.get("sources", [])
            
            # Format answer with sources
            formatted_answer = answer
            if sources:
                formatted_answer += "\n\n📚 **Sources:**"
                for s in sources:
                    page = s.get('page', '?')
                    text = s.get('text', '')[:100]
                    if text and not text.endswith('...'):
                        text += '...'
                    formatted_answer += f"\n• Page {page}: {text}"
            
            # CRITICAL FIX: Use dictionary format with role/content
            new_history = []
            
            # Copy existing history if it's in the correct format
            if history and isinstance(history, list):
                for item in history:
                    if isinstance(item, dict) and 'role' in item and 'content' in item:
                        new_history.append(item)
            
            # Add new messages
            new_history.append({"role": "user", "content": question})
            new_history.append({"role": "assistant", "content": formatted_answer})
            
            return new_history, ""
            
        else:
            # Handle API error
            error_msg = f"❌ Error: {response.status_code}"
            new_history = []
            if history and isinstance(history, list):
                for item in history:
                    if isinstance(item, dict) and 'role' in item and 'content' in item:
                        new_history.append(item)
            new_history.append({"role": "user", "content": question})
            new_history.append({"role": "assistant", "content": error_msg})
            return new_history, ""
            
    except requests.exceptions.Timeout:
        error_msg = "❌ Request timed out. Please try again."
        new_history = []
        if history and isinstance(history, list):
            for item in history:
                if isinstance(item, dict) and 'role' in item and 'content' in item:
                    new_history.append(item)
        new_history.append({"role": "user", "content": question})
        new_history.append({"role": "assistant", "content": error_msg})
        return new_history, ""
        
    except requests.exceptions.ConnectionError:
        error_msg = "❌ Cannot connect to server. Make sure the backend is running."
        new_history = []
        if history and isinstance(history, list):
            for item in history:
                if isinstance(item, dict) and 'role' in item and 'content' in item:
                    new_history.append(item)
        new_history.append({"role": "user", "content": question})
        new_history.append({"role": "assistant", "content": error_msg})
        return new_history, ""
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        new_history = []
        if history and isinstance(history, list):
            for item in history:
                if isinstance(item, dict) and 'role' in item and 'content' in item:
                    new_history.append(item)
        new_history.append({"role": "user", "content": question})
        new_history.append({"role": "assistant", "content": error_msg})
        return new_history, ""

def get_summary(upload_status):
    if not upload_status:
        return "Please upload a PDF first"
    
    try:
        response = requests.get(f"{API_URL}/summary", timeout=30)
        if response.status_code == 200:
            return response.json()["summary"]
        else:
            return f"Error: {response.text}"
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to server. Make sure the backend is running."
    except Exception as e:
        return f"Connection error: {str(e)}"

def clear_chat():
    """Clear chat history"""
    return [], ""

# Create UI
with gr.Blocks(title="Simple Contract Assistant", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📄 Simple Contract Assistant")
    
    upload_state = gr.State()
    
    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(label="Upload PDF", file_types=[".pdf"])
            upload_btn = gr.Button("📤 Load PDF", variant="primary")
            status = gr.Textbox(label="Status", lines=2, interactive=False)
            
            summary_btn = gr.Button("📋 Summary")
            summary_output = gr.Textbox(label="Summary", lines=5, interactive=False)
        
        with gr.Column(scale=2):
            # Simple Chatbot - no type parameter needed
            chatbot = gr.Chatbot(label="Chat", height=400)
            with gr.Row():
                msg = gr.Textbox(
                    label="Question", 
                    placeholder="Ask about the contract...", 
                    scale=4
                )
                send = gr.Button("Send", variant="primary", scale=1)
            clear = gr.Button("Clear Chat")
    
    # Event handlers
    upload_btn.click(
        upload_file,
        inputs=[file_input],
        outputs=[status, upload_state]
    )
    
    summary_btn.click(
        get_summary,
        inputs=[upload_state],
        outputs=[summary_output]
    )
    
    send.click(
        ask_question,
        inputs=[msg, chatbot, upload_state],
        outputs=[chatbot, msg]
    )
    
    msg.submit(
        ask_question,
        inputs=[msg, chatbot, upload_state],
        outputs=[chatbot, msg]
    )
    
    clear.click(
        clear_chat,
        outputs=[chatbot, msg]
    )
    
    # Add example questions
    gr.Markdown("""
    ### 💡 Example Questions
    - What is this contract about?
    - Who are the parties involved?
    - What are the key terms?
    - When does it take effect?
    - How can it be terminated?
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860, 
        share=False
    )
