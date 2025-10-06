"""
Flask Application for Huffman Coding Visualizer and File Compressor
"""

import os
import json
import zipfile
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from huffman import HuffmanCoding, compress_file_content

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/visualizer', methods=['GET', 'POST'])
def visualizer():
    """Handle Huffman visualization requests."""
    if request.method == 'POST':
        try:
            char_freq_str = request.form.get('char_freq', '{}')
            char_freq = json.loads(char_freq_str)

            if not isinstance(char_freq, dict) or not all(isinstance(k, str) and isinstance(v, int) for k, v in char_freq.items()):
                raise ValueError("Invalid input format.")

            text = "".join([char * freq for char, freq in char_freq.items()])

            huffman = HuffmanCoding()
            encoded_text, codes, root = huffman.compress(text)
            tree_json = huffman.get_tree_json()

            return jsonify({
                'tree': tree_json,
                'codes': codes
            })
        except (json.JSONDecodeError, ValueError) as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'An unexpected error occurred.'}), 500

    return render_template('visualizer.html')

@app.route('/compressor', methods=['GET', 'POST'])
def compressor():
    """Handle file compression requests."""
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        if not files or all(f.filename == '' for f in files):
            flash('No selected files')
            return redirect(request.url)

        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files.append(filepath)
            else:
                flash(f'File type not allowed for {file.filename}')

        if not uploaded_files:
            return redirect(request.url)

        # Create a zip file to store compressed files
        zip_filename = 'compressed_files.zip'
        zip_filepath = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

        try:
            with zipfile.ZipFile(zip_filepath, 'w') as zipf:
                for filepath in uploaded_files:
                    with open(filepath, 'rb') as f:
                        content = f.read()
                    
                    compressed_content, metadata = compress_file_content(content)
                    
                    # Write compressed data and metadata to the zip
                    base_filename = os.path.basename(filepath)
                    zipf.writestr(f'{base_filename}.huf', compressed_content)
                    zipf.writestr(f'{base_filename}.meta', json.dumps(metadata))

            # Clean up original uploaded files
            for filepath in uploaded_files:
                os.remove(filepath)

            return send_file(zip_filepath, as_attachment=True, download_name=zip_filename)

        except Exception as e:
            flash(f'An error occurred during compression: {e}')
            # Clean up in case of error
            if os.path.exists(zip_filepath):
                os.remove(zip_filepath)
            for filepath in uploaded_files:
                if os.path.exists(filepath):
                    os.remove(filepath)
            return redirect(request.url)

    return render_template('compressor.html')


if __name__ == '__main__':
    app.run(debug=True)
