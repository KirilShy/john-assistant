# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import queue
from src.john.core import (
    ask_llm, say, get_system_prompt, get_model,
    record_audio, transcribe_audio,
    reload_config, set_speak, get_speak
)

class ModernButton(tk.Button):
    """Custom styled button with hover effects"""
    def __init__(self, master, **kwargs):
        # Store original colors for hover effects
        self.original_bg = kwargs.get('bg', '#f0f0f0')
        self.original_fg = kwargs.get('fg', 'black')
        
        super().__init__(master, **kwargs)
        self.config(
            relief=tk.FLAT,
            borderwidth=0,
            font=("Segoe UI", 10),
            cursor="hand2",
            padx=15,
            pady=8
        )
        self._bind_events()
    
    def _bind_events(self):
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        # Create a slightly lighter version of the original color for hover
        if self.original_bg.startswith('#'):
            # Convert hex to RGB, lighten, then back to hex
            r = int(self.original_bg[1:3], 16)
            g = int(self.original_bg[3:5], 16)
            b = int(self.original_bg[5:7], 16)
            # Lighten by 20%
            r = min(255, int(r * 1.2))
            g = min(255, int(g * 1.2))
            b = min(255, int(b * 1.2))
            hover_color = f"#{r:02x}{g:02x}{b:02x}"
        else:
            hover_color = "#e1e5e9"  # fallback
        self.config(bg=hover_color)
    
    def _on_leave(self, event):
        self.config(bg=self.original_bg)

class JohnGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"John AI Assistant - {get_model()}")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors
        self.colors = {
            'bg': '#f8f9fa',
            'chat_bg': '#ffffff',
            'border': '#e1e5e9',
            'primary': '#007bff',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'text': '#212529',
            'text_secondary': '#6c757d'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Create main container
        self.main_frame = tk.Frame(root, bg=self.colors['bg'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self._create_header()
        
        # Chat area
        self._create_chat_area()
        
        # Control panel
        self._create_control_panel()
        
        # Status bar
        self._create_status_bar()
        
        # Initialize state
        self.q = queue.Queue()
        self.busy = False
        self.messages = [{"role": "system", "content": get_system_prompt()}]
        self.recording = False
        
        # Start polling
        self.root.after(100, self._poll_queue)
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()

    def _create_header(self):
        """Create the header section with title and controls"""
        header_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="John AI Assistant",
            font=("Segoe UI", 24, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['bg']
        )
        title_label.pack(side=tk.LEFT)
        
        # Model info
        model_label = tk.Label(
            header_frame,
            text=f"Model: {get_model()}",
            font=("Segoe UI", 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg']
        )
        model_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Settings button
        settings_btn = ModernButton(
            header_frame,
            text="⚙️ Settings",
            command=self._show_settings,
            bg="#f8f9fa"
        )
        settings_btn.pack(side=tk.RIGHT)

    def _create_chat_area(self):
        """Create the main chat display area"""
        chat_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Chat area with better styling
        self.chat_area = ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            state='disabled',
            font=("Segoe UI", 11),
            bg=self.colors['chat_bg'],
            fg=self.colors['text'],
            relief=tk.FLAT,
            borderwidth=1,
            selectbackground=self.colors['primary'],
            selectforeground='white'
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for different message types
        self.chat_area.tag_config("you", foreground="#007bff", font=("Segoe UI", 11, "bold"))
        self.chat_area.tag_config("john", foreground="#28a745", font=("Segoe UI", 11))
        self.chat_area.tag_config("system", foreground="#6c757d", font=("Segoe UI", 10, "italic"))
        self.chat_area.tag_config("error", foreground="#dc3545", font=("Segoe UI", 10, "bold"))
        self.chat_area.tag_config("meta", foreground="#6c757d", font=("Segoe UI", 9, "italic"))

    def _create_control_panel(self):
        """Create the input and control panel"""
        control_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Input area
        input_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Text input with placeholder
        self.entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 11),
            relief=tk.FLAT,
            borderwidth=1,
            bg=self.colors['chat_bg'],
            fg=self.colors['text']
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.send_message)
        self.entry.bind("<KeyRelease>", self._on_input_change)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        
        # Placeholder text
        self.placeholder_text = "Type your message here..."
        self.entry.insert(0, self.placeholder_text)
        self.entry.config(fg=self.colors['text_secondary'])
        self._show_placeholder()
        
        # Button frame
        button_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X)
        
        # Send button
        self.send_btn = ModernButton(
            button_frame,
            text="📤 Send",
            command=self.send_message,
            bg=self.colors['primary'],
            fg='white'
        )
        self.send_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Voice button
        self.talk_btn = ModernButton(
            button_frame,
            text="🎤 Voice",
            command=self.send_voice,
            bg=self.colors['success'],
            fg='white'
        )
        self.talk_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_btn = ModernButton(
            button_frame,
            text="🗑️ Clear",
            command=self._clear_chat,
            bg=self.colors['warning'],
            fg='white'
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Toggle speech button
        self.speech_btn = ModernButton(
            button_frame,
            text="🔊 Speech: ON" if get_speak() else "🔇 Speech: OFF",
            command=self._toggle_speech,
            bg=self.colors['success'] if get_speak() else self.colors['text_secondary'],
            fg='white'
        )
        self.speech_btn.pack(side=tk.RIGHT)

    def _create_status_bar(self):
        """Create the status bar at the bottom"""
        status_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        status_frame.pack(fill=tk.X)
        
        # Status label
        self.status_lbl = tk.Label(
            status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg']
        )
        self.status_lbl.pack(side=tk.LEFT)
        
        # Character count
        self.char_count_lbl = tk.Label(
            status_frame,
            text="0 chars",
            font=("Segoe UI", 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg']
        )
        self.char_count_lbl.pack(side=tk.RIGHT)

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind("<Control-Return>", self.send_message)
        self.root.bind("<Control-v>", self.send_voice)
        self.root.bind("<Control-l>", self._clear_chat)
        self.root.bind("<Control-s>", self._toggle_speech)

    def _show_placeholder(self):
        """Show placeholder text in input field"""
        if self.entry.get() == "":
            self.entry.insert(0, self.placeholder_text)
            self.entry.config(fg=self.colors['text_secondary'])

    def _hide_placeholder(self):
        """Hide placeholder text"""
        if self.entry.get() == self.placeholder_text:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.colors['text'])
    
    def _on_focus_in(self, event):
        """Handle when input field gains focus"""
        if self.entry.get() == self.placeholder_text:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.colors['text'])
    
    def _on_focus_out(self, event):
        """Handle when input field loses focus"""
        if self.entry.get().strip() == "":
            self._show_placeholder()

    def _on_input_change(self, event=None):
        """Handle input field changes"""
        current_text = self.entry.get()
        if current_text == self.placeholder_text:
            return
        
        # Update character count
        char_count = len(current_text)
        self.char_count_lbl.config(text=f"{char_count} chars")
        
        # Enable/disable send button based on content
        if char_count > 0 and current_text != self.placeholder_text:
            self.send_btn.config(state=tk.NORMAL)
        else:
            self.send_btn.config(state=tk.DISABLED)

    def _show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.colors['bg'])
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings content
        tk.Label(settings_window, text="Settings", font=("Segoe UI", 16, "bold"), 
                bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=20)
        
        # Reload config button
        reload_btn = ModernButton(
            settings_window,
            text="🔄 Reload Config",
            command=lambda: self._reload_config(settings_window),
            bg=self.colors['primary'],
            fg='white'
        )
        reload_btn.pack(pady=10)
        
        # Current settings display
        settings_text = f"Model: {get_model()}\nSpeech: {'ON' if get_speak() else 'OFF'}"
        tk.Label(settings_window, text=settings_text, font=("Segoe UI", 10),
                bg=self.colors['bg'], fg=self.colors['text']).pack(pady=20)

    def _reload_config(self, window):
        """Reload configuration"""
        try:
            config = reload_config()
            messagebox.showinfo("Success", f"Config reloaded!\nModel: {config['model']}\nSpeech: {'ON' if config['speak'] else 'OFF'}")
            window.destroy()
            # Update UI elements
            self.root.title(f"John AI Assistant - {get_model()}")
            self.speech_btn.config(
                text="🔊 Speech: ON" if get_speak() else "🔇 Speech: OFF",
                bg=self.colors['success'] if get_speak() else self.colors['text_secondary']
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload config: {str(e)}")

    def _clear_chat(self):
        """Clear the chat area"""
        if messagebox.askyesno("Clear Chat", "Are you sure you want to clear the chat history?"):
            self.chat_area.config(state='normal')
            self.chat_area.delete(1.0, tk.END)
            self.chat_area.config(state='disabled')
            self.messages = [{"role": "system", "content": get_system_prompt()}]
            self._append_chat("System", "Chat history cleared", tag="system")

    def _toggle_speech(self):
        """Toggle speech on/off"""
        current = get_speak()
        set_speak(not current)
        self.speech_btn.config(
            text="🔊 Speech: ON" if not current else "🔇 Speech: OFF",
            bg=self.colors['success'] if not current else self.colors['text_secondary']
        )

    def send_voice(self):
        """Handle voice input"""
        if self.busy or self.recording:
            return
        
        self.recording = True
        self._append_chat("System", "🎤 Recording for 5 seconds...", tag="meta")
        self._set_busy(True, "Recording...")
        self.talk_btn.config(text="⏹️ Stop", bg=self.colors['danger'])
        
        threading.Thread(target=self._worker_voice, daemon=True).start()

    def _worker_voice(self):
        """Background worker for voice processing"""
        try:
            wav = record_audio(duration=5)
            text = transcribe_audio(wav)
            self.q.put(("voice_ok", text))
        except Exception as e:
            self.q.put(("err", str(e)))

    def send_message(self, event=None):
        """Handle text message sending"""
        if self.busy:
            return

        user_text = self.entry.get().strip()
        if not user_text or user_text == self.placeholder_text:
            return
        
        self.entry.delete(0, tk.END)
        self._show_placeholder()
        self.char_count_lbl.config(text="0 chars")
        self.send_btn.config(state=tk.DISABLED)

        # Show user message
        self._append_chat("You", user_text, tag="you")
        self.messages.append({"role": "user", "content": user_text})
        
        # Trim message history
        if len(self.messages) > 16:
            self.messages = [self.messages[0]] + self.messages[-14:]

        # Process in background
        snapshot = list(self.messages)
        self._set_busy(True, "Thinking...")
        threading.Thread(target=self._worker_llm, args=(snapshot,), daemon=True).start()

    def _worker_llm(self, messages_snapshot):
        """Background worker for LLM processing"""
        try:
            reply = ask_llm(messages_snapshot)
            self.q.put(("ok", reply))
        except Exception as e:
            self.q.put(("err", str(e)))

    def _poll_queue(self):
        """Poll the message queue for results"""
        try:
            kind, payload = self.q.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_queue)
            return

        if kind == "ok":
            reply = payload
            self.messages.append({"role": "assistant", "content": reply})
            self._append_chat("John", reply, tag="john")
            
            # Speak the reply if enabled
            if get_speak():
                threading.Thread(target=say, args=(reply,), daemon=True).start()
                
        elif kind == "voice_ok":
            user_text = payload
            self._append_chat("You", user_text, tag="you")
            self.messages.append({"role": "user", "content": user_text})
            
            if len(self.messages) > 16:
                self.messages = [self.messages[0]] + self.messages[-14:]

            # Process voice input
            snapshot = list(self.messages)
            self._set_busy(True, "Thinking...")
            threading.Thread(target=self._worker_llm, args=(snapshot,), daemon=True).start()
            
        elif kind == "err":
            self._append_chat("System", f"Error: {payload}", tag="error")

        # Reset UI state
        self._set_busy(False)
        self.recording = False
        self.talk_btn.config(text="🎤 Voice", bg=self.colors['success'])
        
        self.root.after(100, self._poll_queue)

    def _set_busy(self, busy: bool, text: str = ""):
        """Set the busy state of the UI"""
        self.busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        
        self.entry.config(state=state)
        self.send_btn.config(state=state)
        self.talk_btn.config(state=state)
        
        if not busy:
            self.entry.config(state=tk.NORMAL)
            self._show_placeholder()
        
        self.status_lbl.config(text=text if text else "Ready")

    def _append_chat(self, speaker, text, tag=None):
        """Append a message to the chat area"""
        self.chat_area.config(state='normal')
        
        # Add timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        
        if tag:
            self.chat_area.insert(tk.END, f"[{timestamp}] {speaker}: {text}\n", tag)
        else:
            self.chat_area.insert(tk.END, f"[{timestamp}] {speaker}: {text}\n")
        
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = JohnGUI(root)
    root.mainloop()
