# Huffman Coding Visualizer & File Compressor

A Flask-based web application for visualizing Huffman coding algorithm and compressing multiple files using Huffman encoding.

## Features

- **Huffman Coding Visualizer**: Input characters and frequencies to visualize the Huffman tree and encoding
- **File Compressor**: Compress multiple files (.pdf, .docx, .csv, .jpg, .png, .txt, etc.) into a zip archive using Huffman coding
- Beautiful UI with Tailwind CSS
- Modular template structure

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to `http://localhost:5000`

## Usage

### Visualizer
- Navigate to the Visualizer page
- Enter characters and their frequencies
- View the generated Huffman tree and encoding table

### File Compressor
- Navigate to the File Compressor page
- Upload multiple files (supports .pdf, .docx, .csv, .jpg, .png, .txt, etc.)
- Download the compressed zip file
```
