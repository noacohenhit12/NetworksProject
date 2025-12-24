import tkinter as tk
from tkinter import ttk, messagebox
from client import ChatClient
import datetime
import threading

class ChatGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Network Chat Client")
        self.root.geometry("720x500")
        self.root.minsize(650, 450)

        self.client: ChatClient | None = None

        self._build_style()
        self._build_layout()

    # ---------- UI BUILD ----------

    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Header.TLabel",
            font=("Segoe UI", 14, "bold")
        )

        style.configure(
            "Status.TLabel",
            font=("Segoe UI", 9)
        )

        style.configure(
            "Send.TButton",
            font=("Segoe UI", 10, "bold")
        )

    def _build_layout(self):
        # Header
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="TCP Network Chat",
            style="Header.TLabel"
        ).pack(side="left")

        self.status_label = ttk.Label(
            header,
            text="Disconnected",
            style="Status.TLabel",
            foreground="red"
        )
        self.status_label.pack(side="right")

        # Chat area
        chat_frame = ttk.Frame(self.root, padding=(10, 5))
        chat_frame.pack(fill="both", expand=True)

        self.chat_box = tk.Text(
            chat_frame,
            state="disabled",
            wrap="word",
            font=("Segoe UI", 10),
            bg="#f9f9f9"
        )
        self.chat_box.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(chat_frame, command=self.chat_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.chat_box.config(yscrollcommand=scrollbar.set)

        # Input area
        input_frame = ttk.Frame(self.root, padding=10)
        input_frame.pack(fill="x")

        self.message_entry = ttk.Entry(
            input_frame,
            font=("Segoe UI", 10)
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.message_entry.bind("<Return>", self._send_message_event)

        self.send_button = ttk.Button(
            input_frame,
            text="Send",
            style="Send.TButton",
            command=self.send_message,
            state="disabled"
        )
        self.send_button.pack(side="right")

        # Username prompt
        self._prompt_username()

    # ---------- CONNECTION ----------

    def _prompt_username(self):
        popup = tk.Toplevel(self.root)
        popup.title("Connect")
        popup.geometry("300x140")
        popup.resizable(False, False)
        popup.grab_set()

        ttk.Label(
            popup,
            text="Enter your username:",
            padding=10
        ).pack()

        username_entry = ttk.Entry(popup)
        username_entry.pack(padx=10, fill="x")
        username_entry.focus()

        def connect():
            username = username_entry.get().strip()
            if not username:
                messagebox.showerror("Error", "Username cannot be empty")
                return

            popup.destroy()
            self._connect_client(username)

        ttk.Button(
            popup,
            text="Connect",
            command=connect
        ).pack(pady=10)

        popup.bind("<Return>", lambda _: connect())

    def _connect_client(self, username: str):
        self.client = ChatClient(
            username=username,
            on_message=self._on_message,
            on_status=self._on_status
        )

        threading.Thread(
            target=self._connect_background,
            daemon=True
        ).start()

    def _connect_background(self):
        success = self.client.connect()
        if success:
            self.client.start_listening()
            self.root.after(0, self._enable_input)

    # ---------- UI CALLBACKS ----------

    def _on_message(self, message: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.root.after(
            0,
            lambda: self._append_message(f"[{timestamp}] {message}")
        )

    def _on_status(self, status: str):
        self.root.after(0, lambda: self._update_status(status))

    def _append_message(self, message: str):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", message + "\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def _update_status(self, status: str):
        self.status_label.config(text=status)
        if status.lower().startswith("connected"):
            self.status_label.config(foreground="green")
        else:
            self.status_label.config(foreground="red")

    def _enable_input(self):
        self.send_button.config(state="normal")

    # ---------- SEND ----------

    def _send_message_event(self, _):
        self.send_message()

    def send_message(self):
        if not self.client or not self.client.is_connected:
            return

        message = self.message_entry.get().strip()
        if not message:
            return

        self.client.send_message(message)
        self.message_entry.delete(0, "end")

    # ---------- CLEANUP ----------

    def on_close(self):
        if self.client:
            self.client.disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ChatGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
