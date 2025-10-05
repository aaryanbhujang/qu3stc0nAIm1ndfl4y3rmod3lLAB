from pathlib import Path
import os
import secrets
import tempfile
from datetime import datetime

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

        summary_lines = []
        try:
            model = keras.models.load_model(dest_path, compile=False)
            model.summary(print_fn=lambda x: summary_lines.append(x))
            params = model.count_params()
        except Exception as e:
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
