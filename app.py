import sklearn
import hashlib
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import streamlit as st

# Locate trained model in the same folder as app.py
MODEL_PATH = Path(__file__).resolve().parent / "hotel_guest_cluster_classifier.joblib"

st.set_page_config(
    page_title="Hotel Guest Segmentation",
    page_icon="🏨",
    layout="wide"
)

st.subheader("Deployment Diagnostics")

st.write("Scikit-learn version:", sklearn.__version__)
st.write("Joblib version:", joblib.__version__)
st.write("Model path:", str(MODEL_PATH))
st.write("Model exists:", MODEL_PATH.exists())

if MODEL_PATH.exists():
    st.write("Model size:", MODEL_PATH.stat().st_size, "bytes")

    model_hash = hashlib.sha256(
        MODEL_PATH.read_bytes()
    ).hexdigest()

    st.write("Model SHA256:", model_hash)
@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


def validate_input(data, schema):
    required = schema["required_features"]

    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    clean = data[required].copy()

    # Validate numeric columns
    for col in schema["numeric_features"]:
        original = clean[col]
        clean[col] = pd.to_numeric(original, errors="coerce")

        if (original.notna() & clean[col].isna()).any():
            raise ValueError(f"{col} must contain numeric values.")

        if (clean[col].dropna() < 0).any():
            raise ValueError(f"{col} cannot be negative.")

    # Validate categorical values
    for col in schema["categorical_features"]:
        allowed = schema["allowed_values"].get(col, [])
        invalid = set(clean[col].dropna().astype(str)) - set(allowed)

        if invalid:
            raise ValueError(
                f"Invalid values for {col}: {invalid}. "
                f"Allowed values: {allowed}"
            )

    return clean


def predict_guests(data, bundle):
    schema = bundle["input_schema"]
    clean_data = validate_input(data, schema)

    predictions = bundle["pipeline"].predict(clean_data)

    result = data.copy()
    result["predicted_guest_cluster"] = predictions.astype(int)

    return result


# Application title
st.title("Hotel Guest Segmentation")
st.write(
    "Predict hotel guest segments using your trained "
    "K-Means classification model."
)

# Load model
if not MODEL_PATH.exists():
    st.error("Trained model not found. Upload the .joblib file beside app.py.")
    st.stop()

try:
    bundle = load_model()
except Exception as e:
    st.error(f"Could not load model: {e}")
    st.stop()

schema = bundle["input_schema"]

numeric_features = schema["numeric_features"]
categorical_features = schema["categorical_features"]
required_features = schema["required_features"]

# Sidebar
with st.sidebar:
    st.header("Model Information")
    st.write("Project: Hotel Guest Segmentation")
    st.write(f"K-Means Clusters: {bundle.get('selected_kmeans_k', 'N/A')}")
    st.write("Algorithm: K-Means + Classification")

# Tabs
tab1, tab2, tab3 = st.tabs([
    "Single Guest Prediction",
    "Batch CSV Prediction",
    "Input Schema"
])

# SINGLE GUEST PREDICTION
with tab1:
    st.subheader("Enter Guest Information")

    with st.form("guest_form"):
        record = {}
        columns = st.columns(3)

        count_features = {
            "total_bookings", "completed_bookings",
            "cancelled_bookings", "no_show_bookings",
            "completed_nights", "breakfast_stays",
            "room_type_variety"
        }

        for i, col in enumerate(numeric_features):
            with columns[i % 3]:
                step = 1.0 if col in count_features else 0.5

                record[col] = st.number_input(
                    col.replace("_", " ").title(),
                    min_value=0.0,
                    value=0.0,
                    step=step
                )

        for col in categorical_features:
            allowed = schema["allowed_values"].get(col, [])

            with columns[0]:
                record[col] = st.selectbox(
                    col.replace("_", " ").title(),
                    allowed
                )

        submitted = st.form_submit_button(
            "Predict Guest Cluster",
            type="primary"
        )

    if submitted:
        try:
            guest = pd.DataFrame(
                [record],
                columns=required_features
            )

            result = predict_guests(guest, bundle)

            cluster = result["predicted_guest_cluster"].iloc[0]

            st.success(f"Predicted Guest Cluster: {cluster}")

            st.dataframe(
                result,
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Prediction Error: {e}")


# BATCH CSV PREDICTION
with tab2:
    st.subheader("Upload Multiple Guest Records")

    uploaded_file = st.file_uploader(
        "Upload guest data CSV",
        type=["csv"]
    )

    if uploaded_file:
        try:
            data = pd.read_csv(uploaded_file)

            st.write("Uploaded Data Preview")
            st.dataframe(data.head())

            if st.button("Predict All Guests"):
                results = predict_guests(data, bundle)

                st.success(
                    f"Predictions generated for {len(results)} guests."
                )

                st.dataframe(
                    results,
                    use_container_width=True
                )

                csv = results.to_csv(index=False).encode("utf-8")

                st.download_button(
                    "Download Predictions",
                    data=csv,
                    file_name="hotel_guest_predictions.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"CSV Processing Error: {e}")


# INPUT SCHEMA
with tab3:
    st.subheader("Required Input Features")

    schema_data = []

    for col in numeric_features:
        schema_data.append({
            "Feature": col,
            "Type": "Numeric",
            "Allowed Values": "Non-negative numbers"
        })

    for col in categorical_features:
        schema_data.append({
            "Feature": col,
            "Type": "Categorical",
            "Allowed Values": ", ".join(
                schema["allowed_values"].get(col, [])
            )
        })

    st.dataframe(
        pd.DataFrame(schema_data),
        use_container_width=True,
        hide_index=True
    )


st.divider()
st.caption(
    "Hotel Guest Segmentation | Machine Learning Final Project"
)
