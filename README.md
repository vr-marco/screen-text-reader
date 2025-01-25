# Screen Text Reader

A Python application that captures text from your screen and reads it aloud using text-to-speech. Features text highlighting, adjustable reading speed, and voice selection.

## Features
- Screen area selection for text capture
- OCR (Optical Character Recognition) for text extraction
- Text-to-speech with multiple voice options
- Adjustable reading speed
- Text highlighting during reading
- Smart handling of hyphenated words and headers
- Keyboard shortcut (Alt+S) for quick capture

## Prerequisites
- Python 3.11
- Tesseract OCR (must be installed separately)
- Python packages:
  ```
  pip install pillow pytesseract pyttsx4 keyboard
  ```

## Installation
1. Install Tesseract OCR:
   - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the program:
   ```bash
   python screen-text-reader.py
   ```
2. Press Alt+S or click "Capture Screen"
3. Click and drag to select the screen area containing text
4. The text will be extracted and read aloud
5. Use the controls to:
   - Change voice
   - Adjust reading speed
   - Toggle text highlighting
   - Stop/restart reading (Alt+S)

## License
MIT

## Author
Marco Ghislanzoni (2025)
