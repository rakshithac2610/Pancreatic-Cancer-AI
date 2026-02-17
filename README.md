# 🧠 Prediction and Detection of Pancreatic Cancer using Explainable Multimodal AI

## 📌 Overview
This project presents an AI-powered clinical decision support system for pancreatic cancer detection and prognosis estimation using a multimodal approach.

The system integrates:
- CT scan imaging
- Laboratory biomarkers
- Radiology report text

It provides not only predictions but also explainable outputs to support clinical interpretation.

---

## 🚀 Key Features

### 🖼 Imaging Analysis
- Tumor detection and segmentation using nnU-Net
- Automatic tumor localization
- Overlay visualization on CT scan

### 📊 Quantitative Analysis
- Tumor volume calculation (mm³)
- Tumor dimensions (x, y, z in mm)
- Maximum tumor diameter estimation

### 🧪 Lab-based Prediction
- Stage prediction using clinical biomarkers:
  - CA19-9
  - Total Bilirubin
  - ALP
  - Albumin
  - NLR
  - Age

### 📈 Prognosis Estimation
- Personalized survival prediction based on risk score

### 🤖 Explainable AI (XAI)
- Heatmaps for tumor attention
- Highlighted radiology report phrases
- Structured clinical summary using LLM

---

## 🏗 System Architecture

1. Upload CT scan (NIfTI format)
2. nnU-Net performs segmentation
3. Tumor metrics are computed
4. Lab values are analyzed using ML model
5. Gemini API processes radiology text
6. Results are displayed in a clinician-friendly dashboard

---

## 📂 Project Structure
