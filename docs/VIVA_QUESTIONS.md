# HybridGuard AI — Academic Defense & Viva Voce Questions

This guide provides concise, rigorous answers to technical defense questions regarding machine learning design, evaluation metrics, calibration, and architectural decisions.

---

### Q1: Why did you choose an out-of-fold stacking ensemble instead of a simple voting classifier or an end-to-end deep neural network?
**Answer:**
A simple voting classifier weights all models equally regardless of which classifier is most calibrated or accurate. Deep neural networks (e.g., multi-gigabyte BERT/RoBERTa transformers) require substantial GPU acceleration and memory, which hinders low-latency CPU deployment and interpretability.
Our **5-fold out-of-fold Stacking Ensemble** learns an optimal meta-weight vector (`[Linear SVM: 6.996, Logistic Regression: 3.349, Multinomial NB: -0.859]`) using out-of-sample predictions. This strictly avoids in-sample leakage and delivers high test accuracy (96.91%) and ultra-low latency (~20 ms on standard CPU) without heavy dependencies.

---

### Q2: Why is the ensemble accuracy (96.91%) slightly lower than Linear SVM alone (96.96%)?
**Answer:**
This is an empirical reality documented in our evaluation report: an ensemble is not mathematically guaranteed to strictly exceed its best constituent classifier on every slice. Linear SVM with Platt calibration formed an exceptionally sharp hyperplane ($F_1 = 0.9664$, $\text{ECE} = 0.0082$).
The stacking ensemble, however, incorporates consensus verification across three distinct learning paradigms (margin optimization, maximum likelihood logistic sigmoid, and probabilistic Bayes). When base models disagree, the ensemble provides uncertainty quantification rather than overconfident margin reliance.

---

### Q3: How did you ensure zero data leakage between your training, validation, and test splits?
**Answer:**
1. **Sanitization & Deduplication:** Before splitting, duplicate text articles (8,452 records) and conflicting labels were removed to prevent identical texts from residing across splits.
2. **Stratified Split Prior to Transformation:** The clean dataset was partitioned into 70% Train, 15% Validation, and 15% Test sets using stratified random sampling (`random_state=42`).
3. **Training-Only Feature Fitting:** The TF-IDF vectorizer was fitted strictly on the training set. The validation and test sets were transformed out-of-sample using the pre-fitted vocabulary.
4. **Out-of-Fold Meta Training:** The stacking meta-learner was trained solely on out-of-fold probability vectors produced via 5-fold cross-validation on the training set.

---

### Q4: What is Expected Calibration Error (ECE) and why is it critical in fake news detection?
**Answer:**
Expected Calibration Error (ECE) measures the difference between a model's predicted confidence and its actual empirical accuracy:
$$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
In fake news verification, an uncalibrated model that outputs 99% confidence on an ambiguous text could mislead human fact-checkers. By using Platt Sigmoid calibration, HybridGuard AI achieves an ECE of **0.82%** (0.0082), ensuring that when the model reports 80% confidence, it is historically accurate 80% of the time.

---

### Q5: Why separate the ML fake news detector from the evidence-based fact-checking engine?
**Answer:**
Because style does not equal truth. A machine learning text classifier evaluates lexical features, sensationalism, and emotional tone. A fabricated story written in calm, objective AP/Reuters journalistic style will fool a stylistic ML classifier.
Conversely, an empirical fact (e.g., *"The lunar module landed on July 20, 1969"*) can only be confirmed by cross-referencing external reference knowledge. HybridGuard AI decouples these two tasks: Engine 1 identifies stylistic and rhetorical deception, while Engine 2 queries external reference knowledge (Wikipedia REST APIs, web reporting) to verify empirical propositions with authentic citations.

---

### Q6: How does the system prevent hallucinated citations?
**Answer:**
The fact-checking pipeline does not generate URLs through an LLM. It queries live search endpoints (Wikipedia REST API and DuckDuckGo), retrieves verified URLs, page summaries, and publication timestamps directly from API response payloads, and checks token overlap against the claim. If no relevant evidence is found, it returns `Insufficient Evidence` with a transparent explanation rather than inventing a citation.

---

### Q7: How does YouTube Shorts analysis work given platform caption restrictions?
**Answer:**
The system accepts both standard YouTube URLs (`watch?v=...`) and Shorts (`/shorts/aUyVATJqEoQ`), extracts the 11-character video ID, and attempts to fetch official or auto-generated English captions via `youtube-transcript-api`. If a creator has explicitly disabled captions, the system provides a seamless **Manual Transcript Fallback** where the user can paste transcript text with timestamps (`[01:23]`). The system chunks the transcript, extracts checkable claims, associates them with timestamps, and allows users to click any timestamp to seek the embedded video player.

