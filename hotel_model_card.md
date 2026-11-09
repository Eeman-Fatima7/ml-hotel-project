# Model Card — Hotel Guest Segmentation

## Dataset
Three synthetic source workbooks: guest profiles, hotel operations (Reservations and ServiceCharges sheets), and room inventory/rate guide. The SQLite master table contains 24 guest-level rows. Names, email addresses, and direct identifiers are excluded from model features.

## Intended task and use
Explore groups of hotel guests with similar historical booking, stay, and service-spending patterns. K-Means assignments are used as pseudo-labels to train a supervised model that reproduces the discovered segmentation for a new guest profile.

## Methods and algorithms
- SQL JOINs: GuestProfiles, Reservations, ServiceCharges, RoomInventory, and RateGuide. Service charges are first aggregated by booking to avoid duplicate booking rows.
- Preprocessing: median imputation and standard scaling for numeric fields; most-frequent imputation and one-hot encoding for categorical fields.
- K-Means: selected k=2; silhouette score=0.297; cluster sizes={1: 19, 0: 5}.
- DBSCAN: eps=4.120, min_samples=2; non-noise silhouette=0.424; noise rate=12.5%; label counts={0: 19, -1: 3, 1: 2}.
- Classifiers compared: Logistic Regression and Random Forest. Selected family: Logistic Regression. Tuned parameters: {'classifier__C': 0.01}.

## Held-out classification results
- Accuracy: 1.000
- Macro Precision: 1.000
- Macro Recall: 1.000
- Macro F1-score: 1.000

## Validation and saved artifact
Stratified train/test split (25% test), stratified cross-validation for model selection, GridSearchCV for tuning, confusion matrix, and reload-equivalence assertion. The fitted preprocessing + classifier pipeline is saved in `hotel_guest_cluster_classifier.joblib` with its input schema.

## Limitations
- The dataset is small, synthetic, and contains only 24 guests and 52 reservations.
- K-Means results depend on features, scaling, k, and initialization.
- DBSCAN is sensitive to eps and min_samples. A small min_samples value may create small clusters; noise points are labelled -1.
- Classification predicts K-Means pseudo-labels, not booking likelihood, revenue, guest satisfaction, or churn. Metrics are not an independent measure of business prediction.
- Results are educational and should not be generalized to real hotel guests without larger, representative and time-aware validation.

## Risks and responsible use
Do not use these segments to deny service, set discriminatory prices, or make other high-impact decisions. Avoid interpreting loyalty tier or country as measures of guest worth. Use the output only for exploratory service planning, review clusters with hotel staff, and follow privacy and consent requirements for real guest data.
