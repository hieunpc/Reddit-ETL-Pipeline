# Reddit ETL Pipeline

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)

A scalable ETL pipeline for extracting Reddit data, transforming it, and loading it for analytics.

## 📌 Overview

This repository currently provides a baseline ETL flow:
1. Extract posts/comments from Reddit API.
2. Transform and clean raw payloads.
3. Load cleaned data to storage/database targets.
4. Visualize core KPIs in a dashboard.

## 🛠️ Current Architecture

```mermaid
graph TD
    A[Reddit API] -->|Extract| B[Raw JSON Data]
    B -->|Transform| C[Cleaned Data CSV/JSON]
    C -->|Load| D[(PostgreSQL/B2)]
    C -->|Serve| E[Flask Dashboard]
```

## 📊 Dashboard

Dashboard path: `src/dashboard/app.py`

Main metrics:
- Total posts/comments
- Average post score
- Comment per post ratio
- Daily trend of posts and comments
- Top posts by score

Run dashboard locally:

```bash
python src/dashboard/app.py
```

Then open: `http://localhost:8501`

> Note: run ETL first to generate `data/processed/posts.csv` and `data/processed/comments.csv`.

## 🚀 Upgrade Plan (Data Engineer Portfolio + Dashboard)

Detailed roadmap: `docs/PROJECT_UPGRADE_PLAN.md`

## ▶️ Run ETL

```bash
pip install -r requirements.txt
python src/main.py
```
