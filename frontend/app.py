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
    if not upload_status:
        return history, "Please upload a PDF first"
    
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question}
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result["answer"]
            
            if result["sources"]:
                answer += "\n\n📚 **Sources:**\n"
                for s in result["sources"]:
                    answer += f"• Page {s['page']}: {s['text']}\n"
            
            history = history or []
            history.append((question, answer))
            return history, ""
        else:
            history.append((question, f"❌ Error: {response.text}"))
            return history, ""
    except Exception as e:
        history.append((question, f"❌ Connection error: {str(e)}"))
        return history, ""

def get_summary(upload_status):
    if not upload_status:
        return "Please upload a PDF first"
    
    try:
        response = requests.get(f"{API_URL}/summary")
        if response.status_code == 200:
            return response.json()["summary"]
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return f"Connection error: {str(e)}"

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
            chatbot = gr.Chatbot(label="Chat", height=400)
            with gr.Row():
                msg = gr.Textbox(label="Question", placeholder="Ask about the contract...", scale=4)
                send = gr.Button("Send", variant="primary", scale=1)
            clear = gr.Button("Clear Chat")
    
    upload_btn.click(upload_file, inputs=[file_input], outputs=[status, upload_state])
    summary_btn.click(get_summary, inputs=[upload_state], outputs=[summary_output])
    send.click(ask_question, inputs=[msg, chatbot, upload_state], outputs=[chatbot, msg])
    msg.submit(ask_question, inputs=[msg, chatbot, upload_state], outputs=[chatbot, msg])
    clear.click(lambda: (None, ""), outputs=[chatbot, msg])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
