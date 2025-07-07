# PDF Research Method Extractor (Display Version)

This project is a Python-based tool designed for extracting research methods from academic PDF documents using local LLMs (e.g., Deepseek via Ollama). It is intended for demonstration purposes only.

## 🚀 Features

- Extracts text from the **first three pages** of each PDF
- Calls a **local Ollama model** (e.g., Deepseek) to analyze research methods
- Outputs structured summaries and classifies research type
- Automatically cleans model output to extract keywords such as:
  - Quantitative Research
  - Qualitative Research
  - Theoretical Research
  - Policy Research
  - Literature Review

## 🛠️ Technologies

- Python 3.8+
- pdfplumber
- requests
- Ollama + Deepseek (locally running models)


