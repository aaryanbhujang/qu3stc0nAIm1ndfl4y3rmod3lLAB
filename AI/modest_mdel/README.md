# modest_mdel (Keras 2.12 Model Inspector CTF)

Moved into subfolder as requested. Upload a `.h5` / `.hdf5` model and view `model.summary()`.
See original README content (condensed) below.

## Quick Start
```powershell
cd modest_mdel
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
python app.py
```

## Docker
```powershell
cd modest_mdel
docker build -t modest_mdel .
docker run --rm -p 8000:8000 --env-file .env modest_mdel
```

Or compose:
```powershell
cd modest_mdel
docker compose up --build
```

## Notes
- Intentional minimal restructure for repository cleanliness.
- Adjust challenge components as desired.
