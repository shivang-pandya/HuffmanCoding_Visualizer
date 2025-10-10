"""
Flask Application for Huffman Coding Visualizer and File Compressor
"""

import os
import json
import zipfile
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from huffman import HuffmanCoding, compress_file_content, process_compressed_zip

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
            flash('No file part', 'error')
            return redirect(request.url)

        files = request.files.getlist('files[]')
        if not files or all(f.filename == '' for f in files):
            flash('No files selected', 'error')
            return redirect(request.url)

        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files.append((filepath, filename))  # Store both path and original filename
            else:
                flash(f'File type not allowed for {file.filename}', 'warning')

        if not uploaded_files:
            flash('No valid files to compress', 'error')
            return redirect(request.url)

        # Create a zip file to store compressed files
        zip_filename = 'compressed_files.zip'
        zip_filepath = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

        try:
            with zipfile.ZipFile(zip_filepath, 'w') as zipf:
                for filepath, original_filename in uploaded_files:
                    with open(filepath, 'rb') as f:
                        content = f.read()
                    
                    # Pass the original filename to preserve extension
                    compressed_content, metadata = compress_file_content(content, original_filename)
                    
                    # Write compressed data and metadata to the zip
                    base_filename = os.path.basename(filepath)
                    zipf.writestr(f'{base_filename}.huf', compressed_content)
                    zipf.writestr(f'{base_filename}.meta', json.dumps(metadata))

            # Clean up original uploaded files
            for filepath, _ in uploaded_files:
                if os.path.exists(filepath):
                    os.remove(filepath)

            return send_file(zip_filepath, as_attachment=True, download_name=zip_filename)

        except Exception as e:
            flash(f'An error occurred during compression: {str(e)}', 'error')
            # Clean up in case of error
            if os.path.exists(zip_filepath):
                os.remove(zip_filepath)
            for filepath, _ in uploaded_files:
                if os.path.exists(filepath):
                    os.remove(filepath)
            return redirect(request.url)

    return render_template('compressor.html')


@app.route('/decompressor', methods=['GET', 'POST'])
def decompressor():
    """Handle file decompression requests."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if not file.filename.endswith('.zip'):
            flash('Please upload a valid .zip file', 'error')
            return redirect(request.url)

        try:
            # Save the uploaded zip file
            zip_filename = secure_filename(file.filename)
            zip_filepath = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
            file.save(zip_filepath)

            # Process the zip file
            decompressed_files = process_compressed_zip(zip_filepath, app.config['UPLOAD_FOLDER'])
            
            if not decompressed_files:
                flash('No valid compressed files found in the archive', 'error')
                return redirect(request.url)

            # Create a zip file for the decompressed files
            output_zip_filename = 'decompressed_files.zip'
            output_zip_path = os.path.join(app.config['UPLOAD_FOLDER'], output_zip_filename)

            with zipfile.ZipFile(output_zip_path, 'w') as zipf:
                for item in decompressed_files:
                    # Reconstruct the original filename with extension if available
                    ext = f".{item['original_extension']}" if item['original_extension'] else ''
                    filename = f"{item['filename']}{ext}"
                    
                    # Write the decompressed content to the zip
                    if item['is_binary'] and isinstance(item['content'], bytes):
                        zipf.writestr(filename, item['content'])
                    else:
                        # For text files, ensure we're writing strings
                        content = item['content'] if isinstance(item['content'], str) else str(item['content'])
                        zipf.writestr(filename, content)

            # Clean up the uploaded zip file
            if os.path.exists(zip_filepath):
                os.remove(zip_filepath)

            return send_file(
                output_zip_path,
                as_attachment=True,
                download_name=output_zip_filename,
                mimetype='application/zip'
            )

        except Exception as e:
            flash(f'An error occurred during decompression: {str(e)}', 'error')
            # Clean up any created files
            if 'zip_filepath' in locals() and os.path.exists(zip_filepath):
                os.remove(zip_filepath)
            if 'output_zip_path' in locals() and os.path.exists(output_zip_path):
                os.remove(output_zip_path)
            return redirect(request.url)

    return render_template('decompressor.html')


if __name__ == '__main__':
    app.run(debug=True)
