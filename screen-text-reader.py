
# Written by Marco Ghislanzoni in 2025 with some help from Anthropic's Claude

import tkinter as tk
from PIL import ImageGrab
import pytesseract
import pyttsx4
import keyboard
import threading
import re
import queue

class ScreenReader:
    def __init__(self):
        # Core variables
        self.is_speaking = False
        self.selection_rect = None
        self.speech_queue = queue.Queue()
        self.current_segment = None
        
        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("Screen Text Reader")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Initialize TTS
        try:
            self.engine = pyttsx4.init()  # Updated initialization
            print("TTS engine initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")
            return
        
        self.engine.setProperty('rate', 150)
        
        # Setup UI
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        control_frame = tk.Frame(main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Left side controls
        left_controls = tk.Frame(control_frame)
        left_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_label = tk.Label(left_controls, text="Press Alt+S to capture")
        self.status_label.pack(side=tk.LEFT)

        self.capture_button = tk.Button(left_controls, text="Capture Screen", command=self.capture_and_read)
        self.capture_button.pack(side=tk.LEFT, padx=10)
        
        # Right side controls
        right_controls = tk.Frame(control_frame)
        right_controls.pack(side=tk.RIGHT)
        
        # Voice selection and control
        voice_frame = tk.Frame(right_controls)
        voice_frame.pack(side=tk.RIGHT, padx=10)
        tk.Label(voice_frame, text="Voice:").pack(side=tk.LEFT)
        voices = self.engine.getProperty('voices')
        voice_names = [v.id.split('\\')[-1].split('/')[-1] for v in voices]
        self.voice_map = dict(zip(voice_names, [v.id for v in voices]))
        self.voice_var = tk.StringVar(value=voice_names[0])
        voice_menu = tk.OptionMenu(voice_frame, self.voice_var, 
                                 *voice_names,
                                 command=self.change_voice)
        voice_menu.config(width=20)
        voice_menu.pack(side=tk.LEFT)
        
        # Speed control
        speed_frame = tk.Frame(right_controls)
        speed_frame.pack(side=tk.RIGHT, padx=10)
        tk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_scale = tk.Scale(speed_frame, from_=50, to=300,
                                  orient=tk.HORIZONTAL, length=150,
                                  command=lambda x: self.root.after(100, self.change_speed, x))
        self.speed_scale.set(150)
        self.speed_scale.pack(side=tk.LEFT)
        
        # Highlight toggle
        self.highlight_var = tk.BooleanVar(value=True)
        self.highlight_check = tk.Checkbutton(right_controls, text="Highlight text", 
                                            variable=self.highlight_var)
        self.highlight_check.pack(side=tk.RIGHT, padx=10)
        
        self.last_text = tk.Text(main_frame)
        scrollbar = tk.Scrollbar(main_frame, command=self.last_text.yview)
        self.last_text.configure(yscrollcommand=scrollbar.set)
        
        self.last_text.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")
        
        self.last_text.tag_configure("highlight", background="yellow")
        
        # Register hotkey
        keyboard.unhook_all()
        keyboard.add_hotkey('alt+s', self.capture_and_read, suppress=True)
    
    def capture_and_read(self):
        if self.is_speaking:
            self.engine.stop()
            self.is_speaking = False
            self.last_text.tag_remove("highlight", "1.0", tk.END)
            # Reinitialize the TTS engine to ensure it's in a clean state
            self.engine = pyttsx4.init()
            self.engine.setProperty('rate', self.speed_scale.get())
            self.engine.setProperty('voice', self.voice_map[self.voice_var.get()])
        
        self.status_label.config(text="Click and drag to select area")
        self.root.iconify()
        
        selection = tk.Toplevel(self.root)
        selection.attributes('-fullscreen', True, '-alpha', 0.3)
        selection.configure(background='grey')
        
        canvas = tk.Canvas(selection, highlightthickness=0, cursor="crosshair")
        canvas.pack(fill='both', expand=True)
        
        start_x = tk.IntVar()
        start_y = tk.IntVar()
        
        def on_click(event):
            start_x.set(event.x_root)
            start_y.set(event.y_root)
            
        def on_drag(event):
            if self.selection_rect:
                canvas.delete(self.selection_rect)
            self.selection_rect = canvas.create_rectangle(
                start_x.get() - selection.winfo_x(), 
                start_y.get() - selection.winfo_y(),
                event.x, event.y,
                outline='red', width=2
            )
            
        def on_release(event):
            selection.destroy()
            self.root.deiconify()
            self.process_screenshot(start_x.get(), start_y.get(), 
                                event.x_root, event.y_root)
        
        selection.bind('<Button-1>', on_click)
        selection.bind('<B1-Motion>', on_drag)
        selection.bind('<ButtonRelease-1>', on_release)
        
    def process_screenshot(self, x1, y1, x2, y2):
        screenshot = ImageGrab.grab(bbox=(min(x1, x2), min(y1, y2), 
                                       max(x1, x2), max(y1, y2)))
        
        ocr_data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
        
        # First pass: collect words and their positions
        lines = []
        current_line = []
        
        for i in range(len(ocr_data['text'])):
            if ocr_data['conf'][i] > 0:
                word = ocr_data['text'][i].strip()
                if word:
                    current_line.append({
                        'word': word,
                        'left': ocr_data['left'][i],
                        'top': ocr_data['top'][i],
                        'height': ocr_data['height'][i]
                    })
                    
            # New line detected
            if (i + 1 >= len(ocr_data['text']) or 
                ocr_data['top'][i + 1] > ocr_data['top'][i] + ocr_data['height'][i]):
                if current_line:
                    lines.append(sorted(current_line, key=lambda x: x['left']))
                    current_line = []
        
        # Second pass: join hyphenated words while preserving line heights
        processed_lines = []
        line_heights = []
        i = 0
        while i < len(lines):
            current_line = lines[i]
            current_words = [word['word'] for word in current_line]
            max_height = sum(word['height'] for word in current_line) / len(current_line)
            
            # Look ahead for hyphenated continuations
            next_i = i + 1
            while next_i < len(lines):
                if not current_words[-1].endswith('-') and not current_words[-1].endswith('- '):
                    break
                    
                # Join with next line
                clean_last_word = current_words.pop().rstrip('- ')
                next_line = lines[next_i]
                next_words = [word['word'] for word in next_line]
                next_height = sum(word['height'] for word in next_line) / len(next_line)
                max_height = max(max_height, next_height)
                
                # Join the split word
                current_words.append(clean_last_word + next_words[0])
                current_words.extend(next_words[1:])
                next_i += 1
            
            processed_lines.append(' '.join(current_words))
            line_heights.append(max_height)
            i = next_i if next_i > i + 1 else i + 1
        
        # Clean up any remaining hyphenations
        processed_text = ' '.join(processed_lines)
        processed_text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', processed_text)
        processed_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', processed_text)
        
        # Detect headers using baseline height
        baseline_height = sorted(line_heights)[len(line_heights)//2]
        print(f"\nBaseline height: {baseline_height:.2f}")
        text_segments = []
        
        for i, line in enumerate(processed_lines):
            current_height = line_heights[i]
            is_header = (current_height > baseline_height * 1.2 and 
                       not line.strip().endswith('.'))
            text_segments.append((line.strip(), is_header))
            print(f"Line {i}: Height={current_height:.2f}, Ratio={current_height/baseline_height:.2f}, " +
                  f"Is Header={is_header}, Text='{line.strip()[:50]}...'") if len(line.strip()) > 50 else \
                  print(f"Line {i}: Height={current_height:.2f}, Ratio={current_height/baseline_height:.2f}, " +
                  f"Is Header={is_header}, Text='{line.strip()}')")
        
        display_text = ""
        speech_text = ""
        speech_segments = []

        # Process headers to make them stand out and add a short pause after them        
        for text, is_header in text_segments:
            if is_header:
                display_text += f"\n\n{text}\n\n"
                speech_text += text + ". . . "
            else:
                display_text += f"{text} "
                speech_text += text + " "
              
        # Create segments for highlighting
        start = 0
        for segment in re.split(r'([.!?]+\s+)', display_text):
            if segment.strip():
                end = start + len(segment)
                speech_segments.append((segment, start, end))
                start = end
        
        self.last_text.delete(1.0, tk.END)
        self.last_text.insert(tk.END, display_text)
        
        threading.Thread(target=self.speak_text_with_highlight, 
                       args=(speech_segments,), daemon=True).start()
        self.status_label.config(text="Press Alt+S to capture")
    
    def speak_text_with_highlight(self, speech_segments):
        self.is_speaking = True

        self.engine.setProperty('rate', self.speed_scale.get())
        self.engine.setProperty('voice', self.voice_map[self.voice_var.get()])
        
        if self.highlight_var.get() and speech_segments:
            start_pos = self.last_text.index(f"1.0 + {speech_segments[0][1]} chars")
            end_pos = self.last_text.index(f"1.0 + {speech_segments[0][2]} chars")
            self.last_text.tag_add("highlight", start_pos, end_pos)
            self.last_text.see(start_pos)
        
        try:
            for idx, segment in enumerate(speech_segments):
                if not self.is_speaking:
                    break
                
                self.current_segment = segment
                text, start, end = segment
                    
                if self.highlight_var.get():
                    self.engine.say(text)
                    self.engine.runAndWait()
                    
                    if idx < len(speech_segments) - 1:
                        next_start = speech_segments[idx + 1][1]
                        next_end = speech_segments[idx + 1][2]
                        next_start_pos = self.last_text.index(f"1.0 + {next_start} chars")
                        next_end_pos = self.last_text.index(f"1.0 + {next_end} chars")
                        self.last_text.tag_remove("highlight", "1.0", tk.END)
                        self.last_text.tag_add("highlight", next_start_pos, next_end_pos)
                        self.last_text.see(next_start_pos)
                else:
                    self.engine.say(text)
                    self.engine.runAndWait()
        except:
            pass
        finally:
            self.is_speaking = False
            self.current_segment = None
            self.last_text.tag_remove("highlight", "1.0", tk.END)
    
    def change_voice(self, voice_name):
        self.engine.setProperty('voice', self.voice_map[voice_name])
    
    def change_speed(self, speed):
        try:
            self.engine.setProperty('rate', int(speed))
        except:
            pass
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenReader()
    app.run()