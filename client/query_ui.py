import tkinter as tk
from tkinter import scrolledtext
import os
import threading
import uuid
from anthropic import Anthropic

from . import db
from . import preprocessor

import json

class ChatSession:
    def __init__(self):
        self.history = []

    def get_messages(self, query, context_str, workflow_str):
        if not self.history:
            system_prompt = f"""
            You are an operational intelligence assistant. You know exactly how this person works. 
            Answer from observed behavioral data only. Never hallucinate processes that aren't in the context.
            
            Context (Structured Summary of Recent Logs):
            {context_str}
            
            Known Workflows:
            {workflow_str}
            """
            self.history.append({"role": "system", "content": system_prompt})
            
        self.history.append({"role": "user", "content": query})
        
        # System role is not supported in the messages array in standard Anthropic API, it's passed separately
        # We will restructure this for the API call
        return self.history

chat_session = ChatSession()

def ask_ai(query):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Please set ANTHROPIC_API_KEY environment variable to use the query interface."
        
    client = Anthropic(api_key=api_key)
    context_dict = preprocessor.build_analysis_context(days=7)
    workflows = db.get_workflows()
    
    context_str = f"Total Work Hours: {context_dict['total_work_hours']}\n"
    context_str += f"Total Sessions: {context_dict['total_sessions']}\n\n"
    context_str += f"Most Used Apps: {', '.join(context_dict['most_used_apps'])}\n\n"
    context_str += "Detected Patterns (App Sequences):\n"
    
    for p in context_dict['detected_patterns']:
        seq = " -> ".join(p['app_sequence'])
        context_str += f"- {seq} (Occurred {p['session_count']} times)\n"
        
    workflow_str = ""
    for w in workflows:
        workflow_str += f"- {w.get('name', 'Unknown')}: {w.get('app_sequence', [])}\n"

    system_prompt = f"""You are an operational intelligence assistant for Nous. 
You have access to this person's actual work behavior data. 
Answer only from the provided context. 
If the data does not support an answer, say so clearly.
Never invent workflows or processes that are not in the context.
Context: {context_str}
Known Workflows: {workflow_str}"""

    chat_session.history.append({"role": "user", "content": query})

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            system=system_prompt,
            max_tokens=800,
            messages=chat_session.history
        )
        answer = response.content[0].text
        chat_session.history.append({"role": "assistant", "content": answer})
        if len(chat_session.history) > 20:
            chat_session.history = chat_session.history[2:]
        return answer
    except Exception as e:
        return f"Error: {str(e)}"

class QueryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MVP Assistant Query")
        self.root.geometry("600x500")
        
        self.history_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.history_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        input_frame = tk.Frame(root)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.entry = tk.Entry(input_frame, font=("Arial", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.send_query)
        
        self.send_btn = tk.Button(input_frame, text="Ask", command=self.send_query)
        self.send_btn.pack(side=tk.RIGHT)

    def append_text(self, text, is_user=False, msg_id=None):
        self.history_area.config(state='normal')
        prefix = "You: " if is_user else "AI: "
        
        start_index = self.history_area.index(tk.INSERT)
        self.history_area.insert(tk.END, prefix + text + "\n\n")
        end_index = self.history_area.index(tk.END)
        
        if msg_id:
            self.history_area.tag_add(msg_id, start_index, end_index)
            
        self.history_area.yview(tk.END)
        self.history_area.config(state='disabled')

    def _threaded_ask_ai(self, query, response_id):
        answer = ask_ai(query)
        self.root.after(0, self._update_answer, answer, response_id)

    def _update_answer(self, answer, response_id):
        self.history_area.config(state='normal')
        
        ranges = self.history_area.tag_ranges(response_id)
        if ranges:
            start_index, end_index = ranges
            self.history_area.delete(start_index, end_index)
            self.history_area.insert(start_index, f"AI: {answer}\n\n", response_id)
            
        self.history_area.config(state='disabled')
        self.history_area.yview(tk.END)
        
        self.entry.config(state='normal')
        self.send_btn.config(state='normal')

    def send_query(self, event=None):
        query = self.entry.get().strip()
        if not query:
            return
            
        self.entry.config(state='disabled')
        self.send_btn.config(state='disabled')
        
        msg_id = str(uuid.uuid4())
        self.append_text(query, is_user=True, msg_id=msg_id)
        
        response_id = str(uuid.uuid4())
        self.append_text("Thinking...", is_user=False, msg_id=response_id)
        
        threading.Thread(target=self._threaded_ask_ai, args=(query, response_id), daemon=True).start()

def launch_ui():
    root = tk.Tk()
    app = QueryApp(root)
    root.mainloop()

if __name__ == "__main__":
    launch_ui()
