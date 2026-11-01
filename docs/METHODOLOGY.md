# HybridGuard AI — Methodology & Theoretical Formulation

## 1. Machine Learning Methodology

### 1.1 Problem Formulation
We formulate stylistic fake news detection as a supervised binary classification task. Given a news document $D$ composed of headline $T$ and body $B$, we construct text string $S = T \oplus \text{"\n\n"} \oplus B$.

The document is mapped to a sparse feature vector $\mathbf{x} \in \mathbb{R}^V$ using TF-IDF (Term Frequency - Inverse Document Frequency) across unigrams and bigrams:
$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \left(1 + \ln \frac{1 + |D|}{1 + \text{DF}(t, D)}\right)$$
With sublinear scaling applied: $\text{TF}(t, d) = 1 + \ln(\text{count}(t, d))$.

### 1.2 Model Ensembling (Out-of-Fold Stacking)
To prevent in-sample overfitting, the stacking meta-learner is trained strictly on out-of-fold probability vectors generated via 5-fold stratified cross-validation.
For each fold $k \in \{1, \dots, 5\}$:
1. Base classifiers (Logistic Regression, Calibrated Linear SVM, Multinomial Naive Bayes) are fitted on training indices $I_{-k}$.
2. Predictions $\hat{P}_m(y=1 \mid \mathbf{x}_i)$ are generated for validation instances $i \in I_k$.
3. The meta-estimator $\mathcal{M}$ (Logistic Regression with L2 regularization) is fitted on the stacked matrix:
   $$\mathbf{Z} = [\hat{\mathbf{p}}_{\text{lr}}, \hat{\mathbf{p}}_{\text{svm}}, \hat{\mathbf{p}}_{\text{nb}}] \in \mathbb{R}^{N \times 3}$$

### 1.3 Probability Calibration & Expected Calibration Error (ECE)
Platt Sigmoid scaling maps raw linear decision margins $f(\mathbf{x})$ into calibrated posterior probabilities:
$$P(y=1 \mid f(\mathbf{x})) = \frac{1}{1 + \exp(A f(\mathbf{x}) + B)}$$
Expected Calibration Error partitions the interval $[0, 1]$ into $M=10$ equal-width bins $B_1, \dots, B_{10}$:
$$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
Where $\text{acc}(B_m) = \frac{1}{|B_m|} \sum_{i \in B_m} \mathbf{1}(y_i = \hat{y}_i)$ and $\text{conf}(B_m) = \frac{1}{|B_m|} \sum_{i \in B_m} \hat{p}_i$.

### 1.4 Uncertainty Metric & "Needs Review"
We quantify predictive uncertainty using Shannon entropy normalized to $[0, 1]$:
$$H(p) = - \left( p \log_2 p + (1-p) \log_2 (1-p) \right)$$
If the maximum class probability falls below the confidence threshold ($< 0.65$) or within the boundary margin ($|p - 0.50| < 0.15$), the system triggers a **"Needs Review"** alert.

---

## 2. Evidence-Based Fact-Checking Methodology

### 2.1 Distinction Between Factual Statements and Opinions
A proposition $P$ is deemed checkable if it:
1. Asserts a concrete state of affairs regarding named entities, quantities, dates, or verifiable actions.
2. Does not rely predominantly on subjective evaluation predicates (*"beautiful"*, *"better"*, *"in my view"*).
3. Is not a forward-looking future forecast or rhetorical question.

### 2.2 Stance Determination Algorithm
Retrieved document excerpts $E = \{e_1, \dots, e_K\}$ are matched against claim $C$:
- Token overlap Jaccard index: $J(C, e_k) = \frac{|\text{Tokens}(C) \cap \text{Tokens}(e_k)|}{|\text{Tokens}(C) \cup \text{Tokens}(e_k)|}$
- Refutation marker presence: $\text{Pattern}_{\text{contradiction}} \in e_k \implies \text{Contradiction Weight} \uparrow$
- Corroboration marker presence: $\text{Pattern}_{\text{support}} \in e_k \implies \text{Support Weight} \uparrow$

### 2.3 Verdict Taxonomy
- **Supported**: Multiple authoritative sources affirm the core proposition.
- **Contradicted**: Evidence explicitly debunks or refutes the claim.
- **Partially Supported / Misleading**: Elements are accurate, but critical context or quantification is distorted.
- **Insufficient Evidence**: Search returns null or tangential results. The system refuses to hallucinate a verdict.
- **Not a Checkable Factual Claim**: Statement is subjective or speculative.

