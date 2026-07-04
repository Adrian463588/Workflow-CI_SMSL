"""
modelling.py (MLProject Entry Point)
=====================================
Script pelatihan model Credit Risk untuk MLflow Project runner.
Mendukung parameter via command-line arguments.

Digunakan oleh:
    mlflow run MLProject/ -P n_estimators=200 -P max_depth=20

Atau oleh GitHub Actions CI pipeline.
"""

import argparse
import logging
import os
import shutil
import sys

import dagshub
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

TARGET_COL      = "loan_status"
EXPERIMENT_NAME = "credit-risk-workflow-ci"
DAGSHUB_OWNER   = "Adrian463588"
DAGSHUB_REPO    = "CreditRiskPrediction"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments dari MLflow Project runner."""
    parser = argparse.ArgumentParser(description="Credit Risk MLProject Training")
    parser.add_argument("--n-estimators",      type=int,   default=200)
    parser.add_argument("--max-depth",         type=int,   default=12)
    parser.add_argument("--min-samples-split", type=int,   default=10)
    parser.add_argument("--min-samples-leaf",  type=int,   default=4)
    parser.add_argument("--max-features",      type=str,   default="sqrt")
    parser.add_argument("--data-dir",          type=str,   default="credit_risk_preprocessing")
    return parser.parse_args()


def load_data(data_dir: str):
    """Memuat dataset train dan test dari direktori."""
    train_path = os.path.join(data_dir, "credit_risk_train.csv")
    test_path  = os.path.join(data_dir, "credit_risk_test.csv")

    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Dataset tidak ditemukan: {train_path}")

    train = pd.read_csv(train_path)
    test  = pd.read_csv(test_path)

    X_train = train.drop(columns=[TARGET_COL])
    y_train = train[TARGET_COL]
    X_test  = test.drop(columns=[TARGET_COL])
    y_test  = test[TARGET_COL]

    logger.info("Data: train=%s | test=%s", X_train.shape, X_test.shape)
    return X_train, X_test, y_train, y_test


def plot_roc_auc(y_test, y_prob, path: str) -> None:
    """Buat dan simpan ROC-AUC Curve."""
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    auc = roc_auc_score(y_test, y_prob)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(fpr, tpr, lw=2.5, color="#2ECC71", label=f"AUC = {auc:.4f}")
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC-AUC Curve — Credit Risk Model")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_feature_importance(model, features, path: str, top_n: int = 15) -> None:
    """Buat dan simpan Feature Importance Plot."""
    importances = model.feature_importances_
    indices     = np.argsort(importances)[::-1][:top_n]
    top_feat    = [features[i] for i in indices]
    top_vals    = importances[indices]

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(range(top_n), top_vals[::-1], color="#3498DB", edgecolor="black", alpha=0.8)
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(top_feat[::-1], fontsize=9)
    ax.set_xlabel("Importance Score")
    ax.set_title(f"Top {top_n} Feature Importances")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def train(args: argparse.Namespace) -> None:
    """Menjalankan training dan logging ke DagsHub MLflow."""
    if "DAGSHUB_TOKEN" in os.environ and "DAGSHUB_USER_TOKEN" not in os.environ:
        os.environ["DAGSHUB_USER_TOKEN"] = os.environ["DAGSHUB_TOKEN"]
    dagshub.init(repo_owner=DAGSHUB_OWNER, repo_name=DAGSHUB_REPO, mlflow=True)
    mlflow.set_experiment(EXPERIMENT_NAME)

    X_train, X_test, y_train, y_test = load_data(args.data_dir)
    feature_names = list(X_train.columns)

    os.makedirs("artifacts", exist_ok=True)

    with mlflow.start_run(run_name="rf-mlproject-ci") as run:
        # ── Parameters ──
        params = {
            "n_estimators":      args.n_estimators,
            "max_depth":         args.max_depth,
            "min_samples_split": args.min_samples_split,
            "min_samples_leaf":  args.min_samples_leaf,
            "max_features":      args.max_features,
        }
        mlflow.log_params(params)

        # ── Training ──
        model = RandomForestClassifier(**params, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        # ── Metrics ──
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy":  round(accuracy_score(y_test, y_pred), 4),
            "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
            "recall":    round(recall_score(y_test, y_pred, zero_division=0), 4),
            "f1_score":  round(f1_score(y_test, y_pred, zero_division=0), 4),
            "roc_auc":   round(roc_auc_score(y_test, y_prob), 4),
        }
        mlflow.log_metrics(metrics)

        for k, v in metrics.items():
            logger.info("   %s: %.4f", k, v)

        # ── Artifacts ──
        roc_path = "artifacts/roc_auc_curve.png"
        fi_path  = "artifacts/feature_importance.png"
        plot_roc_auc(y_test, y_prob, roc_path)
        plot_feature_importance(model, feature_names, fi_path)
        mlflow.log_artifact(roc_path, artifact_path="plots")
        mlflow.log_artifact(fi_path,  artifact_path="plots")

        # ── Model ──
        mlflow.sklearn.log_model(model, artifact_path="credit-risk-model")

        # Save model locally for Docker build reliability
        local_model_path = "artifacts/credit-risk-model"
        if os.path.exists(local_model_path):
            shutil.rmtree(local_model_path)
        mlflow.sklearn.save_model(model, local_model_path)
        logger.info("✅ Model disimpan secara lokal di: %s", local_model_path)

        logger.info("✅ Run selesai | ID: %s", run.info.run_id)


if __name__ == "__main__":
    args = parse_args()
    try:
        train(args)
    except Exception as exc:
        logger.error("Training gagal: %s", exc)
        sys.exit(1)
