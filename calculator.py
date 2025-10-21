import customtkinter
import threading
import queue
import json
import os

LANGUAGES = {
    "ru": {
        "title": "Калькулятор",
        "settings_title": "Настройки",
        "history_title": "История",
        "history_button": "Показать историю",
        "history_empty": "История пуста.",
        "error_div_zero": "Ошибка: деление на 0",
        "error_generic": "Ошибка",
        "calculating": "Вычисление...",
        "theme_switch_light": "Переключить на светлую ✨",
        "theme_switch_dark": "Переключить на темную ⚫",
        "lang_switch_en": "English",
        "lang_switch_ru": "404"
    },
    "en": {
        "title": "Calculator",
        "settings_title": "Settings",
        "history_title": "History",
        "history_button": "Show History",
        "history_empty": "History is empty.",
        "error_div_zero": "Error: division by 0",
        "error_generic": "Error",
        "calculating": "Calculating...",
        "theme_switch_light": "Switch to Light ✨",
        "theme_switch_dark": "Switch to Dark ⚫",
        "lang_switch_en": "English",
        "lang_switch_ru": "404"
    }
}

SETTINGS_FILE = "settings.json"

class SettingsWindow(customtkinter.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master
        self.transient(master)
        self.attributes("-topmost", True)
        self.geometry("300x150")
        self.resizable(False, False)

        self.theme_button = customtkinter.CTkButton(self, font=("Arial", 16), command=self.toggle_theme)
        self.theme_button.pack(pady=10, padx=20, fill="x")
        self.lang_button = customtkinter.CTkButton(self, font=("Arial", 16), command=self.toggle_language)
        self.lang_button.pack(pady=10, padx=20, fill="x")
        
        self.update_texts()

    def toggle_theme(self):
        self.master_app.theme = "light" if self.master_app.theme == "dark" else "dark"
        customtkinter.set_appearance_mode(self.master_app.theme)
        self.master_app.save_settings()
        self.update_texts()

    def toggle_language(self):
        self.master_app.lang = "en" if self.master_app.lang == "ru" else "ru"
        self.master_app.save_settings()
        self.master_app.update_language()
        self.update_texts()

    def update_texts(self):
        lang = self.master_app.lang
        self.title(LANGUAGES[lang]["settings_title"])
        theme_text = LANGUAGES[lang]["theme_switch_light"] if self.master_app.theme == "dark" else LANGUAGES[lang]["theme_switch_dark"]
        self.theme_button.configure(text=theme_text)
        lang_text = LANGUAGES[lang]["lang_switch_en"] if lang == "ru" else LANGUAGES[lang]["lang_switch_ru"]
        self.lang_button.configure(text=lang_text)


class Calculator(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.load_settings()
        customtkinter.set_appearance_mode(self.theme)
        
        self.geometry("400x550")
        self.resizable(False, False)

        self.expression = ""
        self.history = []
        self.queue = queue.Queue()
        
        self.entry = customtkinter.CTkEntry(self, font=("Arial", 40), justify="right")
        self.entry.grid(row=0, column=0, columnspan=4, padx=10, pady=20, sticky="nsew")

        buttons = ['7', '8', '9', '/', '4', '5', '6', '*', '1', '2', '3', '-', '0', '.', 'C', '+', '=']
        row, col = 1, 0
        for btn_text in buttons:
            btn = customtkinter.CTkButton(self, text=btn_text, font=("Arial", 24), fg_color="#3a4d70")
            if btn_text == '=':
                btn.configure(command=self.calculate)
                btn.grid(row=row, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
            else:
                btn.configure(command=lambda b=btn_text: self.on_button_click(b))
                btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            col += 1
            if col > 3: col, row = 0, row + 1
        
        self.history_button = customtkinter.CTkButton(self, font=("Arial", 20), fg_color="#3a4d70", command=self.show_history)
        self.history_button.grid(row=row + 1, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

        for i in range(4): self.grid_columnconfigure(i, weight=1)
        for i in range(1, 7): self.grid_rowconfigure(i, weight=1)
        
        self.update_language()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self.theme = settings.get("theme", "dark")
                    self.lang = settings.get("lang", "ru")
            except (json.JSONDecodeError, IOError):
                self.theme = "dark"
                self.lang = "ru"
        else:
            self.theme = "dark"
            self.lang = "ru"

    def save_settings(self):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({"theme": self.theme, "lang": self.lang}, f)

    def update_language(self):
        lang_dict = LANGUAGES[self.lang]
        self.title(lang_dict["title"])
        self.history_button.configure(text=lang_dict["history_button"])

    def show_history(self):
        history_window = customtkinter.CTkToplevel(self)
        history_window.title(LANGUAGES[self.lang]["history_title"])
        history_window.geometry("300x400")
        history_text = "\n".join(self.history) if self.history else LANGUAGES[self.lang]["history_empty"]
        history_textbox = customtkinter.CTkTextbox(history_window, font=("Arial", 16))
        history_textbox.pack(expand=True, fill="both", padx=10, pady=10)
        history_textbox.insert("0.0", history_text)
        history_textbox.configure(state="disabled")

    def on_button_click(self, char):
        if char == 'C': self.expression = ""
        else: self.expression += str(char)
        self.entry.delete(0, "end")
        self.entry.insert("end", self.expression)

    def calculate(self):
        if not self.expression: return
        self.entry.delete(0, "end")
        self.entry.insert("end", LANGUAGES[self.lang]["calculating"])
        threading.Thread(target=self.calculation_thread, daemon=True).start()
        self.after(100, self.check_queue)

    def calculation_thread(self):
        try:
            result = str(eval(self.expression.replace('^', '**')))
            self.queue.put(("result", result, self.expression))
        except ZeroDivisionError:
            self.queue.put(("error", LANGUAGES[self.lang]["error_div_zero"]))
        except Exception:
            self.queue.put(("error", LANGUAGES[self.lang]["error_generic"]))

    def check_queue(self):
        try:
            msg_type, data, *orig_expr = self.queue.get_nowait()
            self.entry.delete(0, "end")
            if msg_type == "result":
                self.history.append(f"{orig_expr[0]} = {data}")
                self.entry.insert("end", data)
                self.expression = data
            else:
                self.entry.insert("end", data)
                self.expression = ""
        except queue.Empty:
            self.after(100, self.check_queue)

if __name__ == "__main__":
    app = Calculator()
    settings_window = SettingsWindow(app)
    app.mainloop()
