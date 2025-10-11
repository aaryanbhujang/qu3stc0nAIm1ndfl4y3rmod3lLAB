from pathlib import Path
import os
import secrets
import tempfile
from datetime import datetime
import subprocess
import urllib.parse
import requests

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from werkzeug.utils import secure_filename

try:
    from tensorflow import keras  # Keras 2.12 via TF 2.12
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"TensorFlow/Keras 2.12 required but not installed: {e}")

ALLOWED_EXTENSIONS = {"h5", "hdf5"}
DEFAULT_MAX_MB = 10


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or secrets.token_hex(16)
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_MODEL_MB', DEFAULT_MAX_MB)) * 1024 * 1024
    uploads_dir = os.getenv('UPLOAD_FOLDER', tempfile.mkdtemp(prefix='uploads_'))
    app.config['UPLOAD_FOLDER'] = uploads_dir
    Path(uploads_dir).mkdir(parents=True, exist_ok=True)

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    def allowed_file(filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def check_for_payload(file_path):
        """Check if the uploaded file contains malicious payload strings and extract webhook URL"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Convert to string for pattern matching (ignore decode errors)
            content_str = content.decode('utf-8', errors='ignore').lower()
            
            # Look for common RCE payload patterns including Lambda layer attacks
            payload_patterns = [
                'os.system',
                'subprocess',
                'curl',
                'wget',
                'cat flag.txt',
                '__import__',
                'eval(',
                'exec(',
                'flag.txt',
                'lambda',
                'arbexe',  # From the POC
                'layers.lambda'
            ]
            
            found_payloads = []
            for pattern in payload_patterns:
                if pattern in content_str:
                    found_payloads.append(pattern)
            
            # Extract webhook URL from the file content
            webhook_url = None
            # Look for various URL patterns that might be in the malicious payload
            import re
            url_patterns = [
                r'https?://webhook\.site/[a-f0-9-]+',
                r'https?://[a-zA-Z0-9.-]+/[a-zA-Z0-9/-]*\?[^\'"\s]*',
                r'http://[a-zA-Z0-9.-]+(?:\:[0-9]+)?(?:/[^\s\'"]*)?',
                r'https://[a-zA-Z0-9.-]+(?:\:[0-9]+)?(?:/[^\s\'"]*)?'
            ]
            
            content_original = content.decode('utf-8', errors='ignore')  # Keep original case for URL extraction
            for pattern in url_patterns:
                matches = re.findall(pattern, content_original)
                if matches:
                    # Clean up the URL (remove any trailing quotes or characters)
                    webhook_url = matches[0].rstrip("'\")")
                    break
            
            return found_payloads, webhook_url
            
        except Exception:
            return [], None

    def execute_payload_simulation(payloads, webhook_url=None):
        """Simulate the execution of found payloads"""
        try:
            # Read the flag file
            with open('flag.txt', 'r') as f:
                flag_content = f.read().strip()
            
            # Check if curl-like payload is detected
            if any('curl' in p or 'wget' in p for p in payloads):
                if webhook_url:
                    # Use the webhook URL found in the malicious model
                    try:
                        response = requests.get(webhook_url, params={'param': flag_content}, timeout=10)
                        
                        flash(f'🚨 PAYLOAD EXECUTED! Flag exfiltrated successfully!', 'error')
                        flash(f'🌐 Request sent to: {webhook_url}', 'error')
                        flash(f'🏴 Flag sent: {flag_content}', 'error')
                        flash(f'📡 Response status: {response.status_code}', 'error')
                        
                        return True
                        
                    except requests.exceptions.RequestException as e:
                        flash(f'🚨 PAYLOAD DETECTED but request failed: {str(e)}', 'error')
                        flash(f'🌐 Target URL: {webhook_url}', 'error')
                        flash(f'🏴 Flag would have been sent: {flag_content}', 'error')
                        return True
                else:
                    # No webhook URL found, just show the flag
                    flash(f'🚨 CURL PAYLOAD DETECTED but no webhook URL found!', 'error')
                    flash(f'🏴 Flag accessed: {flag_content}', 'error')
                    return True
            
            # Check for other payload types
            elif any('cat flag.txt' in p or 'flag.txt' in p for p in payloads):
                flash(f'🚨 FLAG ACCESS DETECTED! Contents: {flag_content}', 'error')
                return True
                
        except Exception as e:
            flash(f'Payload simulation failed: {e}', 'error')
        
        return False

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'Mind Flayer Model Lab'}, 200

    @app.route('/upload', methods=['POST'])
    def upload():
        if 'model_file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('index'))
        file = request.files['model_file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('index'))
        if not allowed_file(file.filename):
            flash('Invalid file type. Only .h5/.hdf5 allowed.', 'error')
            return redirect(url_for('index'))

        filename = secure_filename(file.filename)
        dest_path = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(dest_path)

        # Check for malicious payloads in the uploaded file
        found_payloads, webhook_url = check_for_payload(dest_path)
        payload_executed = False
        
        if found_payloads:
            flash(f'⚠️ Suspicious patterns detected: {", ".join(found_payloads)}', 'error')
            if webhook_url:
                flash(f'🔗 Webhook URL extracted: {webhook_url}', 'error')
            payload_executed = execute_payload_simulation(found_payloads, webhook_url)

        summary_lines = []
        try:
            # Check if this might be a Lambda layer attack before loading
            if 'lambda' in [p.lower() for p in found_payloads]:
                flash('🚨 LAMBDA LAYER ATTACK DETECTED! Malicious custom layer found!', 'error')
                
            # Load model with custom objects to handle Lambda layers
            model = keras.models.load_model(dest_path, compile=False, custom_objects={'arbexe': lambda x: x})
            model.summary(print_fn=lambda x: summary_lines.append(x))
            params = model.count_params()
            
            # If Lambda layers are detected and we have a webhook, simulate the execution
            if 'lambda' in [p.lower() for p in found_payloads] and webhook_url:
                flash('🔥 LAMBDA LAYER PAYLOAD WOULD EXECUTE ON MODEL INFERENCE!', 'error')
                # Simulate what would happen if model.predict() was called
                payload_executed = True
                execute_payload_simulation(['lambda', 'curl'], webhook_url)
            
            if payload_executed:
                flash('Model loaded successfully, but security breach detected!', 'error')
            else:
                flash('Model loaded successfully!', 'success')
                
        except Exception as e:
            # If model loading fails, it might be due to custom layers
            if 'lambda' in str(e).lower() or 'custom' in str(e).lower():
                flash(f'🚨 MALICIOUS LAMBDA LAYER DETECTED! Model loading blocked for security.', 'error')
                if webhook_url:
                    flash(f'🔗 Would have sent payload to: {webhook_url}', 'error')
                    # Still execute the payload simulation since we detected it
                    execute_payload_simulation(['lambda', 'curl'], webhook_url)
                try:
                    dest_path.unlink(missing_ok=True)
                except Exception:
                    pass
                return render_template('index.html', model_filename=filename, model_summary='[BLOCKED] Malicious Lambda layer detected', param_count=0)
            else:
                flash(f'Failed to load model: {e}', 'error')
                try:
                    dest_path.unlink(missing_ok=True)
                except Exception:
                    pass
                return redirect(url_for('index'))

        return render_template('index.html', model_filename=filename, model_summary='\n'.join(summary_lines), param_count=params)

    @app.route('/download/<path:filename>')
    def download(filename):
        safe_name = os.path.basename(filename)
        target = Path(app.config['UPLOAD_FOLDER']) / safe_name
        if not target.exists():
            abort(404)
        return send_from_directory(app.config['UPLOAD_FOLDER'], safe_name, as_attachment=True)

    @app.errorhandler(413)
    def too_large(e):  # pragma: no cover
        flash('File too large. Adjust MAX_MODEL_MB if needed.', 'error')
        return redirect(url_for('index'))

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
