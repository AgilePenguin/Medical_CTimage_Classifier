# Medical_CTimage_Classifier
An automated ETL tool for classifying clinical pelvic CT images by anatomical plane, streamlining the data-collection process for machine learning models on fracture risk factors.

# Medical_CTimage_Classifier

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data_Manipulation-150458)
![Pydicom](https://img.shields.io/badge/pydicom-Medical_Imaging-red)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-green)

## 📌 Overview
An automated ETL tool for classifying clinical pelvic CT images by anatomical plane, streamlining the data-collection process for machine learning models on fracture risk factors.

In medical imaging research, researchers spend a significant amount of time manually extracting, renaming, and sorting raw DICOM files from hospital PACS systems. This Python-based pipeline automates the tedious data wrangling process, parses complex DICOM metadata, and structures the data into a machine-learning-ready format.

## 🚀 Version History (Changelog)
This project has been iteratively developed to handle real-world clinical data anomalies:

- **Version 1 (Basic ETL):** Implemented core classification based on patient information and section details (`SeriesDescription`). Added chronological slice numbering using DICOM `InstanceNumber` to preserve 3D spatial sequences.
- **Version 2 (Advanced Parsing for Contrast Phases):** Upgraded the parsing logic to evaluate `StudyDescription` as a secondary condition. This accounts for variations in contrast agent administration (e.g., pre/post/arterial phases) and allows manual overriding/annotations in the PACS system to correctly classify difficult cases (e.g., labeling 'abdomen' as 'ax').
- **Version 3.1 (Automated QA & Verification):** Introduced an actionable Verification module (`Verify`) to cross-check empty patient folders (`no CT`) or missing anatomical planes. Automatically exports a diagnostic Excel dashboard (`Y/N/need to check`) to ensure 100% data integrity before feeding it into the ML models.

## ⚠️ Note on PHI (Protected Health Information)
> **HIPAA Compliance:** To strictly adhere to medical data privacy regulations, **no real patient data or PHI is included in this repository.** The codebase is designed to run locally within a secure hospital network. Any provided sample files in the `data/` directory are completely anonymized dummy data used solely to demonstrate the algorithm's functionality.

## 🛠️ Key Features
- **Robust Metadata Parsing:** Extracts metadata directly from DICOM headers using `pydicom`, bypassing messy and arbitrary manual filenames.
- **Automated Data Routing:** Automatically creates a hierarchical folder structure (`Target / P_no / StudyDate / View`) based on a provided Excel mapping table.
- **Actionable Verification Dashboard (QA/QC):** Recursively traverses complex directory structures using `os.walk` to audit the integrity of the transformed dataset, flagging missing planes or empty folders instantly.

## 💻 Pipeline Architecture
The application provides a user-friendly Tkinter GUI (`DICOM_classifier_v3.1`) divided into two main modules:
1. **[Step 1] Sorter:** Maps raw DICOMs to the structured directory and standardizes filenames.
2. **[Step 2] Verifier:** Scans the structured directory and outputs the actionable QA Excel report.

## ⚙️ How to Run
You can run this tool either via the Python script or the standalone executable.

### 1. Using the Python Script
1. Clone this repository:
   ```bash
   git clone [https://github.com/yourusername/Medical_CTimage_Classifier.git](https://github.com/yourusername/Medical_CTimage_Classifier.git)
   cd Medical_CTimage_Classifier
