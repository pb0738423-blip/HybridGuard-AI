# HybridGuard AI — False-positive handling updates

## What changed
1. The prediction API now reads `best_model_by_f1` from `models/artifacts/metadata.json` and uses that saved baseline model for the main prediction. In the supplied evaluation report this is `linear_svm`.
2. The API now flags inputs shorter than 80 words for human review. The supplied WELFake training pipeline uses `title + article body`, so headline-only predictions are out-of-distribution and must not be treated as fact-checks.
3. Prediction responses include `selected_model`, `input_word_count`, and `input_warning`.
4. The News Detector UI explains that the score is a model pattern score, not proof of truth. Headline-only input gets an explicit insufficient-context warning.
5. Word explanations now use the selected Linear SVM coefficients when Linear SVM is the chosen prediction model.
6. Batch prediction uses the same selected-model and review logic.
7. Added API regression tests for short-headline warnings and full-article scope notices.

## Verification
- `python -m pytest tests/ -q`
- Result in the supplied environment: 31 passed.

## Important limitation
This change does not prove the Karnataka claim is true or force the model to label it Real. It prevents a short headline from being presented as a confident factual verdict and uses the best model in the project's saved benchmark report. For real-world verification, use the Fact Checker with independent, current sources and inspect the evidence.

## Apply the update
Replace the corresponding files in your local project with this ZIP, install backend requirements, then restart the FastAPI server. For the React frontend, run `npm ci` inside `frontend` and `npm run dev` (or `npm run build` for production).
