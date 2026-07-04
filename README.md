# Credit Risk Model Training & Workflow CI 🏗️🐳
> **Fase Continuous Integration, Pelatihan MLflow Project, & Dockerization (Kriteria 3 Advanced)**

[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![MLflow](https://img.shields.io/badge/MLflow-v2.19.0-blue?logo=mlflow&logoColor=white)](https://mlflow.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker&logoColor=white)](https://www.docker.com/)
[![DagsHub](https://img.shields.io/badge/DagsHub-MLflow%20Remote-orange?logo=git&logoColor=white)](https://dagshub.com/)
[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-brightgreen?logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![DevSecOps](https://img.shields.io/badge/DevSecOps-Husky%20Hook-red?logo=git&logoColor=white)](https://git-scm.com/)

Repositori ini memuat tahap ketiga dari siklus MLOps Proyek Kelayakan Kredit. Repositori ini bertanggung jawab atas standardisasi pelatihan model Machine Learning dengan spesifikasi MLflow Project, mengotomatiskan pelatihan ulang (re-training) model melalui GitHub Actions CI Pipeline, mengintegrasikan tracking parameter & metrik secara online ke **DagsHub**, serta merakit dan mengunggah model serving Docker image yang teroptimasi ke **Docker Hub**.

---

## 📁 Struktur Repositori

```text
Workflow-CI/
├── .github/
│   └── workflows/
│       └── ci_pipeline.yml               # GitHub Actions CI workflow (Train + Docker build & push)
│
├── .husky/
│   └── pre-commit                        # Git hook lokal untuk perlindungan commit
│
├── MLProject/
│   ├── MLProject                         # Manifes MLflow Project (definisi entrypoint parameter)
│   ├── conda.yaml                        # Manifes conda environment untuk replikasi lingkungan
│   ├── Dockerfile                        # Dockerfile serving (Multi-stage optimized, python:3.10-slim)
│   ├── modelling.py                      # Skrip latih otomatis untuk runner CI
│   ├── docker_hub_reference.txt          # File referensi alamat Docker Hub image hasil build
│   └── credit_risk_preprocessing/        # Dataset bersih input training
│       ├── credit_risk_train.csv         # Data train bersih
│       └── credit_risk_test.csv          # Data test bersih
│
├── detect_secrets.py                     # Skrip pemindai kebocoran kredensial lokal & CI
├── package.json                          # Konfigurasi npm package untuk Husky
└── package-lock.json
```

---

## ⚡ Pelatihan Model & Integrasi DagsHub

* **MLProject**: Alur eksekusi dikontrol secara ketat menggunakan berkas manifest [**`MLProject/MLProject`**](file:///d:/Dicoding/MembangunSistemMachineLearning/ProyekAkhir/Workflow-CI_Repo/MLProject/MLProject) dan [**`MLProject/conda.yaml`**](file:///d:/Dicoding/MembangunSistemMachineLearning/ProyekAkhir/Workflow-CI_Repo/MLProject/conda.yaml). Ini memungkinkan model dilatih ulang secara modular dengan hyperparameter masukan (`n_estimators` dan `max_depth`) yang fleksibel.
* **Online Tracking (DagsHub)**: Selama pipeline CI berjalan, metrik evaluasi model (Akurasi, ROC-AUC, F1-Score, Precision, Recall) serta plot visual kurva ROC-AUC dan Feature Importance dikirimkan secara langsung ke repositori remote DagsHub MLflow Server Anda menggunakan kredensial rahasia yang aman.

---

## 🐳 Optimasi Containerization (Docker)

* **Slim Multi-stage Build**: Alih-alih menggunakan default MLflow build-docker (yang mengunduh paket grafis/mesa/xterm sebesar ~3 GB dan memakan waktu build >30 menit), kami menggunakan custom multi-stage [**`MLProject/Dockerfile`**](file:///d:/Dicoding/MembangunSistemMachineLearning/ProyekAkhir/Workflow-CI_Repo/MLProject/Dockerfile) berbasis `python:3.10-slim`.
* **Hasil Optimasi**:
  * Ukuran image dipangkas menjadi **~500 MB** (hemat 83%).
  * Durasi build pada Actions runner dipangkas menjadi **~3 menit** (cepat 90%).
  * Standardisasi keamanan DevSecOps terpenuhi: kontainer dijalankan dengan non-root user (`mluser:1000`) dan menyematkan HEALTHCHECK otomatis ke endpoint `/ping`.

---

## 🛡️ Standar DevSecOps

* **Husky Pre-commit Hook**: Mencegah kebocoran token DagsHub, password Docker Hub, atau token rahasia lainnya saat developer melakukan commit lokal.
* **CI Secrets Protection**: Seluruh kredensial sensitif dalam file [**`ci_pipeline.yml`**](file:///d:/Dicoding/MembangunSistemMachineLearning/ProyekAkhir/Workflow-CI_Repo/.github/workflows/ci_pipeline.yml) dilewatkan secara aman menggunakan enkripsi **GitHub Secrets** (`secrets.DOCKERHUB_TOKEN`, `secrets.DAGSHUB_TOKEN`).

---

## 🚀 Panduan Menjalankan Latih Ulang Secara Lokal

### Prasyarat
* Anaconda / Miniconda terinstal.
* Docker Desktop terinstal.

### Langkah-Langkah:
1. **Kloning Repositori**:
   ```bash
   git clone https://github.com/Adrian463588/Workflow-CI_SMSL.git
   cd Workflow-CI_SMSL
   ```
2. **Jalankan MLflow Project**:
   ```bash
   cd MLProject
   mlflow run . --experiment-name "credit-risk-local-run" -P n_estimators=200 -P max_depth=12
   ```
3. **Membangun Docker Image secara Manual**:
   ```bash
   docker build --file Dockerfile -t credit-risk-model:latest .
   ```
4. **Menjalankan Docker Container Model**:
   ```bash
   docker run -d -p 8080:8080 credit-risk-model:latest
   ```
   *Layanan model serving akan menyala di pelabuhan `http://localhost:8080` dan siap menerima request prediksi.*
