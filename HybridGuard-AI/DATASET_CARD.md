# Dataset Card: WELFake Benchmark Dataset

## Dataset Summary
- **Dataset Name**: WELFake (Word Embedding-based Linear Fake News Detection Dataset)
- **Primary Source**: HuggingFace (`davanstrien/WELFake`) / IEEE / Kaggle
- **Original Authors**: P. K. Verma, P. Agrawal, I. Amorim, R. Prodan (IEEE Transactions / Data in Brief 2021)
- **Total Instances in Source**: 72,134 news articles
- **Class Balance**: 35,028 Real (48.56%), 37,106 Fake (51.44%)
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)

## Schema & Attributes
| Field | Type | Description |
|---|---|---|
| `Unnamed: 0` / `index` | Integer | Original record index |
| `title` | String | Headline of the news article |
| `text` | String | Full body text of the article |
| `label` | Integer / Binary | Ground truth label: `0` = Real, `1` = Fake |

## Label Normalization
- Raw label `0` maps to class name `Real` (reliable reporting).
- Raw label `1` maps to class name `Fake` (unsubstantiated, manipulated, or fabricated news).
- Target variable `y`: `1` for Fake News (positive class), `0` for Real News (negative class).

## Data Quality & Leakage Prevention
1. **Missing & Empty Records**: Articles with empty or null body text and title are identified and pruned.
2. **Title & Body Concat**: Feature input combines `title` + `" "` + `text` to ensure headline clickbait patterns and body substance are both evaluated.
3. **Deduplication**: Duplicate text bodies and headline collisions are filtered to prevent identical articles from appearing in multiple splits.
4. **Partitioning**:
   - Training Set: 70% (used strictly for vectorizer fitting, baseline model training, and out-of-fold stacking meta-learner).
   - Validation Set: 15% (used for hyperparameter tuning and probability calibration).
   - Test Set: 15% (sealed, untouched test set used solely for final unbiased metric calculation).
5. **No Synthetic Data in Production**: All reported metrics are derived strictly from genuine benchmark samples.

## Known Limitations
- The dataset reflects online English news articles predominantly from political, international, and social domains.
- Language evolution, emerging slang, or modern AI-generated synthetic articles post-2022 may exhibit distributional shift requiring continuous model calibration and evidence retrieval.

