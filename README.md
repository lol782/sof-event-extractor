<div align="center">

# ⚓ SoF EVENT EXTRACTOR

</div>

<div align="center">
  <p><em>An intelligent maritime document processing platform that transforms unstructured Statement of Facts into actionable timeline data using advanced AI.</em></p>

  <p>
    <img src="https://img.shields.io/badge/React-black?style=for-the-badge&logo=react&logoColor=white&color=61DAFB" alt="React" />
    <img src="https://img.shields.io/badge/Python-black?style=for-the-badge&logo=python&logoColor=white&color=3776AB" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-black?style=for-the-badge&logo=fastapi&logoColor=white&color=009688" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Google%20Gemini-black?style=for-the-badge&logo=google&logoColor=white&color=4285F4" alt="Google Gemini" />
  </p>

  <a href="https://tbi-x-ime-hackathon-frontend.onrender.com/" target="_blank">
    <img src="https://img.shields.io/badge/Live_Site-SoF_Extractor-28a745?style=for-the-badge&logo=vercel&logoColor=white" alt="Live Site" />
  </a>
  <br /><br />
  <a href="https://youtu.be/FjC9vwCJo_E">
    <img src="./images/landing.png" alt="SoF Event Extractor Demo" width="800" />
  </a>
  <br /><br />
  <a href="https://youtu.be/FjC9vwCJo_E" target="_blank">
    <img src="https://img.shields.io/badge/Watch_Demo_Video-YouTube-red?style=for-the-badge&logo=youtube&logoColor=white" alt="Watch Demo Video" />
  </a>
</div>

---

## Overview

**SoF Event Extractor** is an AI-powered maritime platform that:

* Processes unstructured Statement of Facts documents
* Extracts maritime events with 95%+ accuracy using the Google Gemini API
* Generates interactive timelines and visualizations automatically
* Provides results through a modern web interface and RESTful APIs

This solution transforms hours of manual document processing into seconds of automated intelligence.

---

## Core Features

| Feature                  | Description                                                 |
| ------------------------ | ----------------------------------------------------------- |
| **AI Processing**        | Google Gemini integration for document understanding        |
| **Multi-Format Support** | Handles PDF, DOCX and images with OCR                      |
| **Timeline Generation**  | Automatic chronological visualization of events             |
| **Enterprise API**       | RESTful endpoints with JWT authentication and documentation |

---

## Technology Stack

| Component       | Technology           | Badge                                                                                                    |
| --------------- | -------------------- | -------------------------------------------------------------------------------------------------------- |
| Backend     | Python, FastAPI | ![Python](https://img.shields.io/badge/Python-black?style=flat\&logo=python&logoColor=white&color=3776AB) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat\&logo=fastapi\&logoColor=white)        |
| Frontend        | React, Tailwind | ![React](https://img.shields.io/badge/React-61DAFB?style=flat\&logo=react\&logoColor=black)   ![Tailwind](https://img.shields.io/badge/Tailwind-4F46E5?style=flat\&logo=tailwind-css\&logoColor=white)           |
| Authentication  | JWT         | ![JWT](https://img.shields.io/badge/JWT-000000?style=flat\&logo=json-web-tokens\&logoColor=white)        |
| AI Processing   | Google Gemini API    | ![Google](https://img.shields.io/badge/Google_Gemini-4285F4?style=flat\&logo=google\&logoColor=white)    |
| OCR             | Tesseract            | ![OCR](https://img.shields.io/badge/Tesseract-OCR-blue)                                                  |
| PDF Processing  | PyMuPDF, pdfplumber  | ![PDF](https://img.shields.io/badge/PDF-Processing-red)                                                  |
| Deployment      | Render.com           | ![Render](https://img.shields.io/badge/Render-46E3B7?style=flat\&logo=render\&logoColor=white)           |

---

## Architecture

1. **Document Upload** → FastAPI backend
2. **Text Extraction** → Tesseract/PyMuPDF extract raw text from SoF documents
2. **AI Processing** → Google Gemini API interprets extracted text and identifies maritime events
3. **Data Structuring** → Events organized into structured timelines
4. **Frontend** → React interface for visualization and interaction

---

## Showcase

<div align="center">
  <img src="./images/doc-upload.png" alt="Document Upload Interface" width="700" />
  <p><em>Drag-and-drop interface for document upload</em></p>
</div>

<div align="center">
  <img src="./images/processing.png" alt="AI Processing Pipeline" width="700" />
  <p><em>Real-time AI analysis and event extraction</em></p>
</div>

<div align="center">
  <img src="./images/result.png" alt="Result Dashboard" width="700" />
  <p><em>Results dashboard with filtering and export options</em></p>
</div>

<div align="center">
  <img src="./images/timeline.png" alt="Timeline Visualization" width="700" />
  <p><em>Interactive timeline of extracted events</em></p>
</div>

<div align="center">
  <img src="./images/sof_events_csv.png" alt="CSV output" width="700" />
  <p><em>Exported CSV output</em></p>
</div>

<div align="center">
  <img src="./images/sof_events_json.png" alt="JSON output" width="700" />
  <p><em>Exported JSON output</em></p>
</div>


---

## Performance & Security

**Performance**

* Speed: 30-45 seconds per document
* Accuracy: 95%+ on maritime SoF documents
* Multiple File Support: PDF, DOCX, PNG, JPG, JPEG

**Security**

* JWT-based authentication
* File validation and input sanitization
* Encrypted data handling

---

## Innovation Highlights

* Custom prompt engineering for maritime context
* Google Gemini API for natural language understanding
* Automated event structuring with timeline generation

---

## Business Impact

* Reduces manual effort by 90%
* Eliminates errors in extraction
* Automates compliance-ready documentation

---

## Local Development Setup

```bash
# Clone
git clone https://github.com/lol782/sof-event-extractor.git
cd sof-event-extractor

# Setup
chmod +x setup.sh
./setup.sh
```

Access:

* Frontend → `http://localhost:3000`
* Backend API → `http://localhost:8000`

### Key Endpoints

* `POST /api/auth/register` – Register user
* `POST /api/auth/login` – User login
* `POST /api/process/upload` – Upload documents
* `GET /api/process/result/{job_id}` – Results

### Environment Variables

**Backend**

```env
SECRET_KEY=your-jwt-secret-key
GOOGLE_API_KEY=your-google-gemini-api-key
```

**Frontend**

```env
REACT_APP_API_URL=https://your-backend-url.onrender.com
```

---

## Project Structure

```
sof-event-extractor/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── models/
│   └── utils/
│       ├── auth.py
│       ├── sof_pipeline.py
|       |..
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── pages/
│   │   └── config.js
│   ├── public/
│   └── package.json
├── images/
└── setup.sh
```

---

### Upcoming Features

- **Advanced Search**: Full-text search across processed documents
- **Analytics Dashboard**: Comprehensive reporting and insights
- **Multi-language Support**: Support for multiple languages
- **Enhanced AI**: Improved accuracy with custom models

---

## Acknowledgments

* **Google Gemini API** for AI-powered document analysis
* **FastAPI** for backend framework
* **React + Tailwind CSS** for modern frontend
* **Render.com** for deployment

---

## Connect with the Developers

<div align="center">
  <a href="https://www.linkedin.com/in/rajadigvijaysingh/" target="_blank">
    <img src="https://img.shields.io/badge/Raja_Digvijay_Singh-grey?style=for-the-badge&logo=linkedin&logoColor=white" alt="Raja Digvijay Singh">
  </a>
  <a href="https://linkedin.com/in/rahul-koranga-656785258" target="_blank">
    <img src="https://img.shields.io/badge/Rahul_Koranga-009688?style=for-the-badge&logo=linkedin&logoColor=white" alt="Rahul Koranga">
  </a>
  <a href="https://www.linkedin.com/in/sourab-singh-bora-3b896424b" target="_blank">
    <img src="https://img.shields.io/badge/Sourab_Singh_Bora-red?style=for-the-badge&logo=linkedin&logoColor=white" alt="Sourab Singh Bora">
  </a>
</div>
