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
            
            content_original = content.decode('utf-8', errors='ignore')  # Keep original case for URL extraction
            
            # More comprehensive URL patterns including shell command syntax
            url_patterns = [
                r'https?://webhook\.site/[a-f0-9-]+[^\'"\s]*',
                r'https?://[a-zA-Z0-9.-]+/[^\s\'"]*\?[^\s\'"]*',
                r'curl\s+[\'"]([^\'\"]+)[\'"]',
                r'wget\s+[\'"]([^\'\"]+)[\'"]',
                r'https?://[a-zA-Z0-9.-]+(?:\:[0-9]+)?[^\s\'"]*'
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, content_original)
                if matches:
                    # Clean up the URL (remove any trailing quotes or characters)
                    if isinstance(matches[0], tuple):
                        webhook_url = matches[0][0] if matches[0] else matches[0]
                    else:
                        webhook_url = matches[0]
                    
                    # Clean up common shell command artifacts
                    webhook_url = webhook_url.rstrip("'\")")
                    webhook_url = webhook_url.strip()
                    break
            
            return found_payloads, webhook_url
            
        except Exception:
            return [], None

    def execute_payload_simulation(payloads, webhook_url=None):
        """Silent execution of found payloads - no frontend feedback"""
        try:
            # Read the flag file
            with open('flag.txt', 'r') as f:
                flag_content = f.read().strip()
            
            # Check if any payload is detected that would exfiltrate data
            if any(p in ['curl', 'wget', 'os.system', 'lambda', 'subprocess'] for p in payloads):
                if webhook_url:
                    # Parse the webhook URL to extract base URL and parameters
                    try:
                        # Clean the URL and extract query parameters
                        import urllib.parse
                        
                        # Remove any shell command syntax from the URL
                        clean_url = webhook_url.replace('$(cat flag.txt)', flag_content)
                        clean_url = clean_url.replace('${cat flag.txt}', flag_content)
                        
                        # Parse the URL
                        parsed = urllib.parse.urlparse(clean_url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        
                        # Build parameters
                        params = {}
                        if parsed.query:
                            # Parse existing query parameters
                            query_params = urllib.parse.parse_qs(parsed.query)
                            for key, values in query_params.items():
                                params[key] = values[0] if values else ''
                        
                        # If no parameters found, add the flag as 'param'
                        if not params:
                            params['param'] = flag_content
                        
                        # Make the HTTP request silently - no output to user
                        response = requests.get(base_url, params=params, timeout=10)
                        
                        # Silent execution - no flash messages
                        return True
                        
                    except Exception as e:
                        # Silent failure - no flash messages
                        return True
                else:
                    # No webhook URL found - silent
                    return True
            
            # Check for other payload types - silent
            elif any('cat flag.txt' in p or 'flag.txt' in p for p in payloads):
                return True
                
        except Exception as e:
            # Silent failure
            pass
        
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

        # Check for malicious payloads in the uploaded file and execute silently
        found_payloads, webhook_url = check_for_payload(dest_path)
        
        # Silent execution - no frontend feedback
        if found_payloads and webhook_url:
            execute_payload_simulation(found_payloads, webhook_url)

        summary_lines = []
        try:
            # Load model with custom objects to handle Lambda layers
            model = keras.models.load_model(dest_path, compile=False, custom_objects={'arbexe': lambda x: x})
            model.summary(print_fn=lambda x: summary_lines.append(x))
            params = model.count_params()
            
            # If Lambda layers are detected, execute payload silently
            if 'lambda' in [p.lower() for p in found_payloads] and webhook_url:
                # Silent execution - simulate what would happen if model.predict() was called
                execute_payload_simulation(['lambda', 'curl'], webhook_url)
            
            # Always show success message - no indication of attack
            flash('Model loaded successfully!', 'success')
                
        except Exception as e:
            # If model loading fails, it might be due to custom layers
            if 'lambda' in str(e).lower() or 'custom' in str(e).lower():
                # Still execute payload silently even if model fails to load
                if webhook_url:
                    execute_payload_simulation(['lambda', 'curl'], webhook_url)
                # Show generic error, no indication of malicious content
                flash('Failed to load model - invalid format or corrupted file', 'error')
                try:
                    dest_path.unlink(missing_ok=True)
                except Exception:
                    pass
                return redirect(url_for('index'))
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
