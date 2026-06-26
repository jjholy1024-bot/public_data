# Project Implementation Record - Data & Logic (Jinhyeock)

This document records the implemented features and remaining tasks for the Map-Based International Organization Vacancy MVP.

## Completed Tasks

### 1. Data Collection & Preprocessing (`collect_data.py`)
* **MOFA API Integration:** Connects to the Ministry of Foreign Affairs Open APIs.
  * **Recent Vacancies:** Fetches current career postings (configured to 100 rows).
  * **Internship Vacancies:** Fetches youth-targeted internship postings using title `인턴십` (configured to 50 rows).
* **Gemini API Translation & Summarization Pipeline:**
  * Uses `gemini-flash-lite-latest` (Gemini 1.5 Flash Lite) to bypass the strict daily requests quota (20 RPD) of Gemini 2.x models on free-tier projects (which provides 1,500 RPD).
  * Translates titles, cleans HTML tags, and condenses descriptions into clean 2-3 sentence Korean summaries (`ai_summary`).
  * Normalizes country and city names into standard English strings (e.g. "Switzerland", "Geneva").
* **Static Coordinates Lookup & Fallback Geocoding:**
  * Maps normalized English country/city strings to precise coordinates (`lat`, `lng`) via an internal coordinates lookup table.
  * Falls back to Gemini's estimated coordinates for any new or unregistered cities, ensuring coordinates are always available.
* **API Optimization & Caching:**
  * Reads previously processed JSON feeds (`public/data/general_jobs.json` and `public/data/internship_jobs.json`) to skip calling Gemini for existing postings (`seq`).
  * Drastically reduces execution time and API key usage on subsequent runs (daily runs take only a few seconds).
  * Implements rate-limiting delays (4 seconds sleep) and a robust retry mechanism with exponential backoff for transient errors (429, 500, 503, 504).

### 2. GitHub Actions Automation Workflow (`.github/workflows/data_pipeline.yml`)
* Configured to run automatically every day at 2:00 AM KST (`0 17 * * *` UTC) and supports manual triggering via `workflow_dispatch`.
* Clones the repository, installs python dependencies, runs `collect_data.py` (injecting `GOOGLE_API_KEY` from Github Secrets), and automatically commits and pushes updated JSON feeds back to the repository if changes are found.
* This automated commit triggers automatic static hosting redeployments (Netlify/Vercel) on the frontend.

## Output Assets
The script generates the following feeds conformant to the data protocol:
* **General Careers Feed:** [general_jobs.json](file:///D:/public_data_pro/public/data/general_jobs.json)
* **Internships Feed:** [internship_jobs.json](file:///D:/public_data_pro/public/data/internship_jobs.json)

---

## Remaining Tasks (Partner's Role - UI & Frontend)
* Design wireframes and React frontend components.
* Build interactive global map (using Leaflet / Google Maps) to display vacancy pins using `lat` and `lng`.
* Implement frontend search, filtering, and job recommendations based on user skills matching the listing's `ai_keywords`.
