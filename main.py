import os
import json
import datetime
import re
import tkinter as tk
import customtkinter as ctk
import requests
import markdown
from dotenv import load_dotenv
from PIL import Image, ImageTk
from tkhtmlview import HTMLScrolledText, HTMLLabel

# Load environment variables from .env file
load_dotenv()

def markdown_to_html(md_text):
    """Convert markdown to HTML"""
    try:
        # Convert markdown to HTML using the markdown library
        html = markdown.markdown(
            md_text,
            extensions=['extra', 'codehilite', 'tables', 'nl2br']
        )
        
        # Add inline CSS styles directly to elements instead of using a style tag
        # Replace common elements with styled versions
        html = html.replace('<h1>', '<h1 style="font-size: 1.8em; color: #333;">')
        html = html.replace('<h2>', '<h2 style="font-size: 1.5em; color: #333;">')
        html = html.replace('<h3>', '<h3 style="font-size: 1.3em; color: #333;">')
        html = html.replace('<code>', '<code style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: monospace;">')
        html = html.replace('<pre>', '<pre style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto;">')
        html = html.replace('<blockquote>', '<blockquote style="border-left: 4px solid #ccc; margin-left: 0; padding-left: 16px; color: #555;">')
        html = html.replace('<table>', '<table style="border-collapse: collapse; width: 100%;">')
        html = html.replace('<th>', '<th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;">')
        html = html.replace('<td>', '<td style="border: 1px solid #ddd; padding: 8px; text-align: left;">')
        
        # Add a base style for the whole content
        styled_html = f'<div style="font-family: Arial, sans-serif; margin: 0; padding: 0;">{html}</div>'
        
        return styled_html
    except Exception as e:
        print(f"Error converting markdown to HTML: {e}")
        return f"<p>Error rendering markdown: {str(e)}</p><pre>{md_text}</pre>"

class DeepSeekAPI:
    """Class to handle DeepSeek R1 API interactions"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"  # Default model
        
        if not self.api_key:
            print("Warning: No DeepSeek API key found. Please set it in the .env file or provide it directly.")
    
    def set_api_key(self, api_key):
        """Set or update the API key"""
        self.api_key = api_key
        
    def set_model(self, model):
        """Set or update the model"""
        self.model = model
    
    def generate_response(self, messages):
        """Generate a response from DeepSeek API"""
        if not self.api_key:
            return {"error": "No API key provided. Please set your API key."}
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}


class ConversationManager:
    """Class to manage conversation history"""
    
    def __init__(self, save_dir="conversations"):
        self.save_dir = save_dir
        self.current_conversation = []
        
        # Create save directory if it doesn't exist
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
    def add_message(self, role, content):
        """Add a message to the current conversation"""
        message = {"role": role, "content": content}
        self.current_conversation.append(message)
        return message
    
    def get_conversation(self):
        """Get the current conversation"""
        return self.current_conversation
    
    def clear_conversation(self):
        """Clear the current conversation"""
        self.current_conversation = []
    
    def save_conversation(self, filename=None):
        """Save the current conversation to a file"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        filepath = os.path.join(self.save_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.current_conversation, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_conversation(self, filepath):
        """Load a conversation from a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_conversation = json.load(f)
                
            # Clear current conversation first
            self.current_conversation = []
            
            # Add each message to the conversation
            for message in loaded_conversation:
                if isinstance(message, dict) and 'role' in message and 'content' in message:
                    self.current_conversation.append(message)
            
            print(f"Loaded {len(self.current_conversation)} messages from {filepath}")
            return True
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading conversation: {str(e)}")
            return False
    
    def list_saved_conversations(self):
        """List all saved conversations"""
        if not os.path.exists(self.save_dir):
            return []
        
        return [f for f in os.listdir(self.save_dir) if f.endswith('.json')]


class ChatApp(ctk.CTk):
    """Main chat application UI"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize API and conversation manager
        self.api = DeepSeekAPI()
        self.conversation_manager = ConversationManager()
        
        # Configure window
        self.title("DeepSeek R1 Chat")
        self.geometry("900x700")
        self.minsize(600, 400)
        
        # Set appearance mode and color theme
        ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"
        
        # Create UI elements
        self.create_widgets()
        
        # Bind events
        self.bind("<Configure>", self.on_resize)
    
    def create_widgets(self):
        """Create and arrange UI widgets"""
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create top frame for settings
        self.top_frame = ctk.CTkFrame(self.main_frame)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # API Key entry
        self.api_key_label = ctk.CTkLabel(self.top_frame, text="API Key:")
        self.api_key_label.pack(side=tk.LEFT, padx=5)
        
        self.api_key_var = tk.StringVar(value=os.getenv("DEEPSEEK_API_KEY", ""))
        self.api_key_entry = ctk.CTkEntry(self.top_frame, width=300, show="*", textvariable=self.api_key_var)
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        
        self.toggle_api_key_btn = ctk.CTkButton(self.top_frame, text="👁️", width=30, command=self.toggle_api_key_visibility)
        self.toggle_api_key_btn.pack(side=tk.LEFT, padx=2)
        
        self.save_api_key_btn = ctk.CTkButton(self.top_frame, text="Save Key", command=self.save_api_key)
        self.save_api_key_btn.pack(side=tk.LEFT, padx=5)
        
        # Conversation management buttons
        self.new_chat_btn = ctk.CTkButton(self.top_frame, text="New Chat", command=self.new_chat)
        self.new_chat_btn.pack(side=tk.RIGHT, padx=5)
        
        self.save_chat_btn = ctk.CTkButton(self.top_frame, text="Save Chat", command=self.save_chat)
        self.save_chat_btn.pack(side=tk.RIGHT, padx=5)
        
        # Create content frame (contains sidebar and chat area)
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create sidebar for conversation history
        self.sidebar_frame = ctk.CTkFrame(self.content_frame, width=200)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.sidebar_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Sidebar header
        self.sidebar_header = ctk.CTkLabel(self.sidebar_frame, text="Conversation History", font=("Arial", 14, "bold"))
        self.sidebar_header.pack(pady=10)
        
        # Sidebar listbox frame
        self.sidebar_listbox_frame = ctk.CTkFrame(self.sidebar_frame)
        self.sidebar_listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Get colors based on appearance mode
        if ctk.get_appearance_mode() == "Dark":
            listbox_bg = "#2b2b2b"
            listbox_fg = "white"
            chat_bg = "#2b2b2b"
            chat_fg = "#DCE4EE"
        else:
            listbox_bg = "#F9F9FA"
            listbox_fg = "black"
            chat_bg = "#F9F9FA"
            chat_fg = "#1A1A1A"
        
        # Sidebar listbox with scrollbar
        self.sidebar_scrollbar = ctk.CTkScrollbar(self.sidebar_listbox_frame)
        self.sidebar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.conversation_listbox = tk.Listbox(
            self.sidebar_listbox_frame,
            bg=listbox_bg,
            fg=listbox_fg,
            selectbackground="#1f538d",
            font=("Arial", 11),
            relief="flat",
            highlightthickness=0
        )
        self.conversation_listbox.pack(fill=tk.BOTH, expand=True)
        self.conversation_listbox.bind("<<ListboxSelect>>", self.on_conversation_select)
        
        self.sidebar_scrollbar.configure(command=self.conversation_listbox.yview)
        self.conversation_listbox.configure(yscrollcommand=self.sidebar_scrollbar.set)
        
        # Refresh button for conversation history
        self.refresh_btn = ctk.CTkButton(self.sidebar_frame, text="Refresh", command=self.refresh_conversation_list)
        self.refresh_btn.pack(pady=10, padx=5, fill=tk.X)
        
        # Create chat area frame
        self.chat_area_frame = ctk.CTkFrame(self.content_frame)
        self.chat_area_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Chat display with scrollbar - using a simpler approach
        self.chat_frame = ctk.CTkScrollableFrame(
            self.chat_area_frame,
            fg_color=chat_bg,
            corner_radius=0
        )
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create bottom frame for input
        self.bottom_frame = ctk.CTkFrame(self.chat_area_frame)
        self.bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # User input
        self.user_input = ctk.CTkTextbox(self.bottom_frame, height=80, wrap=tk.WORD)
        self.user_input.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=5, pady=5)
        self.user_input.bind("<Return>", self.on_enter_key)
        self.user_input.bind("<Shift-Return>", self.on_shift_enter)
        
        # Send button
        self.send_btn = ctk.CTkButton(self.bottom_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Status bar
        self.status_bar = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status_bar.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Load conversation history
        self.refresh_conversation_list()
    
    def on_resize(self, event):
        """Handle window resize events"""
        # This method can be used to adjust UI elements on resize if needed
        pass
        
    # Removed the canvas configuration methods as they're no longer needed
    
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_entry.cget("show") == "*":
            self.api_key_entry.configure(show="")
            self.toggle_api_key_btn.configure(text="🔒")
        else:
            self.api_key_entry.configure(show="*")
            self.toggle_api_key_btn.configure(text="👁️")
    
    def save_api_key(self):
        """Save API key and update the API instance"""
        api_key = self.api_key_var.get().strip()
        if api_key:
            self.api.set_api_key(api_key)
            self.status_bar.configure(text="API key saved")
        else:
            self.status_bar.configure(text="API key cannot be empty")
    
    def new_chat(self):
        """Start a new chat conversation"""
        self.conversation_manager.clear_conversation()
        
        # Clear all existing messages
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
            
        self.status_bar.configure(text="New conversation started")
        
        # Clear selection in the conversation listbox
        self.conversation_listbox.selection_clear(0, tk.END)
    
    def save_chat(self):
        """Save the current chat conversation"""
        if not self.conversation_manager.get_conversation():
            self.status_bar.configure(text="No conversation to save")
            return
        
        filepath = self.conversation_manager.save_conversation()
        self.status_bar.configure(text=f"Conversation saved to {filepath}")
        
        # Refresh the conversation list to show the newly saved conversation
        self.refresh_conversation_list()
    
    def refresh_conversation_list(self):
        """Refresh the conversation history list"""
        # Clear the listbox
        self.conversation_listbox.delete(0, tk.END)
        
        # Get all saved conversations
        conversations = self.conversation_manager.list_saved_conversations()
        
        # Sort conversations by date (newest first)
        conversations.sort(reverse=True)
        
        # Add conversations to the listbox
        for conv in conversations:
            # Format the filename for display (remove .json extension and format timestamp)
            display_name = conv
            if conv.startswith("conversation_") and conv.endswith(".json"):
                # Extract timestamp from filename (format: conversation_YYYYMMDD_HHMMSS.json)
                timestamp_str = conv[13:-5]  # Remove "conversation_" prefix and ".json" suffix
                try:
                    # Parse timestamp
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    # Format as readable date/time
                    display_name = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # If timestamp parsing fails, just use the filename
                    pass
            
            self.conversation_listbox.insert(tk.END, display_name)
            
        # Store the actual filenames for later use
        self.conversation_files = conversations
    
    def on_conversation_select(self, event):
        """Handle conversation selection from the listbox"""
        selection = self.conversation_listbox.curselection()
        if not selection:
            return
        
        # Get the selected conversation file
        selected_index = selection[0]
        if selected_index >= len(self.conversation_files):
            return
            
        selected_file = self.conversation_files[selected_index]
        filepath = os.path.join(self.conversation_manager.save_dir, selected_file)
        
        # Clear current conversation first
        self.conversation_manager.clear_conversation()
        
        # Load the conversation
        if self.conversation_manager.load_conversation(filepath):
            # Print debug info
            print(f"Loaded conversation from {selected_file}")
            print(f"Conversation has {len(self.conversation_manager.get_conversation())} messages")
            
            # Display the conversation
            self.display_conversation()
            self.status_bar.configure(text=f"Loaded conversation from {selected_file}")
        else:
            self.status_bar.configure(text=f"Failed to load conversation from {selected_file}")
    
    def load_chat(self):
        """Load a saved chat conversation (legacy method, kept for the button)"""
        # This functionality is now handled by the sidebar
        # Just refresh the conversation list
        self.refresh_conversation_list()
    
    def display_conversation(self):
        """Display the current conversation in the chat display"""
        # Clear all existing messages
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        
        # Get colors based on appearance mode
        if ctk.get_appearance_mode() == "Dark":
            user_bg = "#1f1f1f"
            assistant_bg = "#2d2d2d"
            text_color = "#DCE4EE"
        else:
            user_bg = "#e6e6e6"
            assistant_bg = "#f0f0f0"
            text_color = "#1A1A1A"
        
        # Get all messages from the conversation
        all_messages = self.conversation_manager.get_conversation()
        print(f"Displaying {len(all_messages)} messages from conversation")
        
        # Display each message
        for i, message in enumerate(all_messages):
            role = message["role"]
            content = message["content"]
            
            # Skip system messages
            if role == "system":
                continue
                
            # Print debug info
            print(f"Processing message {i+1}: role={role}, content length={len(content)}")
            
            if role == "user":
                # Create a frame for the user message
                msg_frame = ctk.CTkFrame(self.chat_frame, fg_color=user_bg, corner_radius=10)
                msg_frame.pack(fill=tk.X, padx=10, pady=5, anchor="e")
                
                # Add user label
                label = ctk.CTkLabel(msg_frame, text="You:", text_color="#4a9eff", font=("Arial", 12, "bold"))
                label.pack(anchor="w", padx=10, pady=(5, 0))
                
                # Add user message content
                content_label = ctk.CTkLabel(
                    msg_frame,
                    text=content,
                    text_color=text_color,
                    font=("Arial", 12),
                    wraplength=500,
                    justify="left"
                )
                content_label.pack(anchor="w", padx=10, pady=(0, 5), fill=tk.X)
                
            elif role == "assistant":
                # Create a frame for the assistant message
                msg_frame = ctk.CTkFrame(self.chat_frame, fg_color=assistant_bg, corner_radius=10)
                msg_frame.pack(fill=tk.X, padx=10, pady=5, anchor="w")
                
                # Add assistant label
                label = ctk.CTkLabel(msg_frame, text="DeepSeek:", text_color="#ff6b6b", font=("Arial", 12, "bold"))
                label.pack(anchor="w", padx=10, pady=(5, 0))
                
                # Add assistant message content as HTML
                html_content = markdown_to_html(content)
                
                # Create HTML widget with proper configuration
                html_widget = HTMLScrolledText(
                    msg_frame,
                    width=500,
                    html=html_content,
                    background=assistant_bg,
                    padx=10,
                    pady=5,
                    borderwidth=0,
                    highlightthickness=0
                )
                
                # Calculate appropriate height based on content
                # This helps avoid excessive blank space
                content_lines = content.count('\n') + 1
                height = min(max(content_lines * 20, 50), 400)  # Min 50px, max 400px
                html_widget.configure(height=height)
                
                html_widget.pack(anchor="w", padx=10, pady=(0, 5), fill=tk.X, expand=True)
            
            # Force update after each message to ensure proper rendering
            self.update_idletasks()
    
    def on_enter_key(self, event):
        """Handle Enter key press"""
        if not event.state & 0x1:  # Check if Shift is not pressed
            self.send_message()
            return "break"  # Prevent default behavior (newline)
        return None  # Allow default behavior
    
    def on_shift_enter(self, event):
        """Handle Shift+Enter key press"""
        # Allow default behavior (newline)
        return None
    
    def send_message(self):
        """Send user message and get AI response"""
        user_message = self.user_input.get("1.0", tk.END).strip()
        
        if not user_message:
            return
        
        # Clear input field
        self.user_input.delete("1.0", tk.END)
        
        # Add user message to conversation
        self.conversation_manager.add_message("user", user_message)
        
        # Get colors based on appearance mode
        if ctk.get_appearance_mode() == "Dark":
            user_bg = "#1f1f1f"
            text_color = "#DCE4EE"
        else:
            user_bg = "#e6e6e6"
            text_color = "#1A1A1A"
        
        # Create a frame for the user message
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color=user_bg, corner_radius=10)
        msg_frame.pack(fill=tk.X, padx=10, pady=5, anchor="e")
        
        # Add user label
        label = ctk.CTkLabel(msg_frame, text="You:", text_color="#4a9eff", font=("Arial", 12, "bold"))
        label.pack(anchor="w", padx=10, pady=(5, 0))
        
        # Add user message content
        content_label = ctk.CTkLabel(
            msg_frame,
            text=user_message,
            text_color=text_color,
            font=("Arial", 12),
            wraplength=500,
            justify="left"
        )
        content_label.pack(anchor="w", padx=10, pady=(0, 5), fill=tk.X)
        
        # Force update to ensure proper rendering
        self.update_idletasks()
        
        # Update status
        self.status_bar.configure(text="Waiting for response...")
        self.update_idletasks()
        
        # Get AI response
        self.get_ai_response()
    
    def get_ai_response(self):
        """Get response from DeepSeek API"""
        try:
            # Get current conversation
            messages = self.conversation_manager.get_conversation()
            
            # Call API
            response = self.api.generate_response(messages)
            
            # Get colors based on appearance mode
            if ctk.get_appearance_mode() == "Dark":
                assistant_bg = "#2d2d2d"
                text_color = "#DCE4EE"
            else:
                assistant_bg = "#f0f0f0"
                text_color = "#1A1A1A"
            
            if "error" in response:
                error_message = response["error"]
                
                # Create a frame for the error message
                msg_frame = ctk.CTkFrame(self.chat_frame, fg_color=assistant_bg, corner_radius=10)
                msg_frame.pack(fill=tk.X, padx=10, pady=5, anchor="w")
                
                # Add error label
                label = ctk.CTkLabel(msg_frame, text="Error:", text_color="#ff0000", font=("Arial", 12, "bold"))
                label.pack(anchor="w", padx=10, pady=(5, 0))
                
                # Add error message content
                content_label = ctk.CTkLabel(
                    msg_frame,
                    text=error_message,
                    text_color="#ff0000",
                    font=("Arial", 12),
                    wraplength=500,
                    justify="left"
                )
                content_label.pack(anchor="w", padx=10, pady=(0, 5), fill=tk.X)
                
                # Force update to ensure proper rendering
                self.update_idletasks()
                
                self.status_bar.configure(text="Error getting response")
                return
            
            # Extract assistant message
            assistant_message = response["choices"][0]["message"]["content"]
            
            # Add assistant message to conversation
            self.conversation_manager.add_message("assistant", assistant_message)
            
            # Create a frame for the assistant message
            msg_frame = ctk.CTkFrame(self.chat_frame, fg_color=assistant_bg, corner_radius=10)
            msg_frame.pack(fill=tk.X, padx=10, pady=5, anchor="w")
            
            # Add assistant label
            label = ctk.CTkLabel(msg_frame, text="DeepSeek:", text_color="#ff6b6b", font=("Arial", 12, "bold"))
            label.pack(anchor="w", padx=10, pady=(5, 0))
            
            # Add assistant message content as HTML
            html_content = markdown_to_html(assistant_message)
            
            # Create HTML widget with proper configuration
            html_widget = HTMLScrolledText(
                msg_frame,
                width=500,
                html=html_content,
                background=assistant_bg,
                padx=10,
                pady=5,
                borderwidth=0,
                highlightthickness=0
            )
            
            # Calculate appropriate height based on content
            content_lines = assistant_message.count('\n') + 1
            height = min(max(content_lines * 20, 50), 400)  # Min 50px, max 400px
            html_widget.configure(height=height)
            
            html_widget.pack(anchor="w", padx=10, pady=(0, 5), fill=tk.X, expand=True)
            
            # Force update to ensure proper rendering
            self.update_idletasks()
            
            # Update status
            self.status_bar.configure(text="Ready")
            
        except Exception as e:
            # Handle any exceptions
            # Create a frame for the error message
            if ctk.get_appearance_mode() == "Dark":
                assistant_bg = "#2d2d2d"
            else:
                assistant_bg = "#f0f0f0"
                
            msg_frame = ctk.CTkFrame(self.chat_frame, fg_color=assistant_bg, corner_radius=10)
            msg_frame.pack(fill=tk.X, padx=10, pady=5, anchor="w")
            
            # Add error label
            label = ctk.CTkLabel(msg_frame, text="Error:", text_color="#ff0000", font=("Arial", 12, "bold"))
            label.pack(anchor="w", padx=10, pady=(5, 0))
            
            # Add error message content
            content_label = ctk.CTkLabel(
                msg_frame,
                text=f"An error occurred: {str(e)}",
                text_color="#ff0000",
                font=("Arial", 12),
                wraplength=500,
                justify="left"
            )
            content_label.pack(anchor="w", padx=10, pady=(0, 5), fill=tk.X)
            
            # Force update to ensure proper rendering
            self.update_idletasks()
            
            self.status_bar.configure(text="Error getting response")


def main():
    """Main function to run the application"""
    app = ChatApp()
    app.mainloop()


if __name__ == "__main__":
    main()