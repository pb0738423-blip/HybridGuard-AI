# HybridGuard AI — Fake News Detection & Fact-Checking

A full-stack academic project that combines a TF-IDF-based hybrid machine-learning classifier with explainable predictions and an evidence-oriented fact-checking workflow. The interface is built with React and Vite; the API uses FastAPI.

> **Important:** A model prediction is an automated estimate, not proof that an article is true or false. Check original sources and treat uncertain results as requiring human review.

## Features

- Fake/real news text classification using Logistic Regression, calibrated Linear SVM, Multinomial Naive Bayes and a stacking ensemble.
- Confidence, uncertainty and model-agreement information.
- Explainable word-level feature attribution.
- Claim extraction and evidence lookup with source links where available.
- YouTube transcript/video analysis with manual-transcript fallback.
- Live speech transcript analysis in supported browsers.
- React dashboard, model metrics and methodology views.

## Technology stack

- **Frontend:** React 18, Vite, Tailwind CSS, Recharts
- **Backend:** Python, FastAPI, Pydantic
- **Machine learning:** scikit-learn, TF-IDF, Logistic Regression, Linear SVM, Multinomial Naive Bayes, stacking
- **Data:** WELFake dataset (see `DATASET_CARD.md`)

## Project structure

```text
├── data/
│   └── samples/                 # Small demo inputs
├── models/
│   ├── artifacts/               # Pre-trained model and vectorizer files
│   └── evaluation/              # Evaluation report and comparison
├── src/
│   ├── api/                     # FastAPI app and routes
│   ├── ml/                      # Training, prediction and explainability
│   ├── fact_check/              # Claim extraction and evidence evaluation
│   ├── video/                   # Video transcript analysis
│   └── speech/                  # Speech session handling
├── frontend/                    # React + Vite application
├── tests/                       # Pytest suite
├── docs/                        # Technical documentation
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.11 or newer
- Node.js 18 or newer and npm
- Windows PowerShell, macOS Terminal or Linux shell

The pre-trained model artifacts are included, so you do **not** need to train the model just to run the application. The large WELFake parquet dataset files are intentionally not included in this Git repository; see `DATASET_CARD.md` and the training instructions if you want to reproduce training.

## Run locally (Windows PowerShell)

Open a terminal in the project root (the folder containing `requirements.txt`).

### 1. Create a Python environment and install dependencies

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks environment activation, run the commands below from Command Prompt instead, or use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for the current PowerShell session.

### 2. Start the backend

From the project root:

```powershell
uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000
```

Backend health check: `http://127.0.0.1:8000/health`  
Interactive API docs: `http://127.0.0.1:8000/docs`

### 3. Start the frontend

Open a **second terminal**, move to the frontend directory and install its dependencies:

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`). The Vite development server proxies `/api` and `/health` requests to the backend on port 8000.

### 4. Optional: build and serve the production frontend

```powershell
cd frontend
npm ci
npm run build
cd ..
uvicorn src.api.app:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`.

## Tests

From the project root, with the Python environment activated:

```powershell
python -m pytest tests/ -v
```

The supplied project test suite currently passes **29 tests** in the validation environment. Model files were serialized with scikit-learn 1.9.1, so the requirements pin that version to reduce model-loading compatibility issues.

## Re-training the model (optional)

Training requires the WELFake dataset and the processed train/validation/test parquet files. These large files are not committed to GitHub. Follow the dataset and methodology documentation to obtain and prepare the data, then use the training module:

```powershell
python -m src.ml.train --subsample 25000 --cv 5
```

Do not run this step for a normal demo; the saved model artifacts are already provided.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Methodology](docs/METHODOLOGY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Viva questions](docs/VIVA_QUESTIONS.md)
- [Dataset card](DATASET_CARD.md)
- [Experiment log](EXPERIMENT_LOG.md)
- [Implementation plan](IMPLEMENTATION_PLAN.md)

## GitHub upload

Create an empty repository on GitHub (do not initialize it with a README if you already have this project README). Then run these commands from the project root, replacing the URL with your repository URL:

```powershell
git init
git add .
git status
git commit -m "Initial commit: HybridGuard AI fake news checker"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Review `git status` before committing. Do not commit `.env`, API keys, virtual environments, `node_modules`, or large dataset files.

## Limitations

- The classifier learns patterns from its training dataset; its label is not an independent verification of every factual statement.
- Evidence retrieval depends on external services and network availability. A lack of evidence is not proof that a claim is false.
- Transcript availability and browser speech-recognition support vary.
- Treat results as decision support and verify important claims using reliable primary sources.
