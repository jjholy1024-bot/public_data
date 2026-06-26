# 🗺️ Map-Based International Organization Vacancy Information Service (MVP)

This specification document outlines the MVP (Minimum Viable Product) development for the 'Map-Based International Organization Recruitment Information Service,' utilizing public foreign affairs data and AI. This document serves as the ground truth to synchronize the data protocol and UI/UX design components between team members.

---

## 1. Project Overview
* **Core Value Proposition:** Simplifies the discovery of scattered international organization vacancies through an intuitive global map interface and instantly matches opportunities tailored to the user's specific skills and qualifications.
* **Target Audience:** Undergraduate/graduate students and young job seekers aspiring to secure internships or employment within international organizations.
* **Competition Requirements Met & Data Sources:**
  * Utilizes the official **'Latest Vacancy Open API'** (comprehensive career postings) provided by the Ministry of Foreign Affairs ➔ Outputs to `general_jobs.json`.
  * Utilizes the official **'Internship Vacancy Open API'** provided by the Ministry of Foreign Affairs, with the `title` parameter strictly fixed to **"인턴십"** to isolate youth-targeted datasets ➔ Outputs to `internship_jobs.json`.
  * Implements a data pre-processing pipeline integrated with **Google Gemini API (gemini-1.5-flash)** for optimal efficiency, cost-effectiveness (free tier development), and high processing speed.

---

## 2. System Architecture (Serverless Build-Type)
To eliminate live runtime infrastructure costs, ensure near-zero UI latency (Zero Latency), and maintain maximum system stability, we adopt a **Serverless Static Deployment Architecture**.

* **Data Collection & Processing (Jinhyeock):** Runs automatically in a GitHub Actions virtual environment every day at 2:00 AM KST.
  * A Python script invokes both Ministry of Foreign Affairs APIs separately.
  * It integrates with the Gemini API to clean HTML-tagged content, extract skill keywords, and generate concise Korean summaries.
  * The script exports two distinct static assets inside the `public/data/` directory: `general_jobs.json` and `internship_jobs.json`.
* **Frontend (Partner):** React (Static hosting deployed via Netlify or Vercel).
  * Loads both JSON payloads into client-side memory upon user connection or toggles the respective data source based on the view state.
* **User Interface:** Instantly filters and triggers map updates via client-side JavaScript when a user clicks a country or updates filters—completely bypassing live runtime server queries.

---

## 3. Role Allocation

### 🛠️ Data & Logic (Jinhyeock)
* Connect to both Ministry of Foreign Affairs Open APIs and parse the returned XML payloads using Python (with `title: "인턴십"` fixed for the internship endpoint).
* Integrate the Gemini API pipeline into the pre-processing phase to handle data ingestion and extract job-specific skill tags (`ai_keywords`).
* Design prompt engineering logic for Gemini to condense complex raw text into an accessible 2-3 sentence Korean summary (`ai_summary`).
* Construct a static lookup table that links country/city string data with precise latitude and longitude coordinates.
* Export two isolated JSON data feeds (`general_jobs.json`, `internship_jobs.json`) to the public path and configure the GitHub Actions automated workflow.

### 🎨 UI/UX Design & Frontend Implementation (Partner)
* Design responsive high-fidelity wireframes and interactive web prototypes using Figma.
* Render the interactive global map visualization using React libraries (e.g., Leaflet, Mapbox, or Google Maps API).
* Implement the UI toggle switching logic to swap the entire data source feed (`general_jobs` ↔ `internship_jobs`) based on the active view mode.
* Code the client-side recommendation algorithm to sort job listings based on the size of the intersection between user-selected capability chips and the item's `ai_keywords`.
* Build the UI wrapper components (sliding sidebars or modals) that render job listing cards upon country selection.

---

## 4. Data Protocol (★Core Integration Rule)
The frontend application will be developed under the assumption that the following two structured JSON arrays are static and accessible within the `public/data/` directory. Both files share the exact same internal object schema, eliminating the need for a runtime discriminator type attribute.

* **General Careers Feed Path:** `public/data/general_jobs.json`
* **Internships Feed Path:** `public/data/internship_jobs.json`

### 📄 JSON Data Feed Format Reference
```json
[
  {
    "seq": "35383",
    "title": "[Overseas][Internship] UN Secretariat DPPA-DPO Political Affairs Intern Recruitment Notice",
    "country": "United States",
    "city": "New York",
    "lat": 40.7128,
    "lng": -74.0060,
    "regDt": "2026-06-17",
    "applyUrl": "[https://unjobnet.org/jobs/detail/86739179](https://unjobnet.org/jobs/detail/86739179)",
    "workType": "Hybrid",
    "ai_keywords": ["Political Affairs", "Peacebuilding", "Intelligence Gathering", "Report Writing", "Fluent English"],
    "ai_summary": "유엔사무국 뉴욕 본부에서 북아프리카 지역의 정치 안보 정세를 분석하고 상황보고서 작성을 지원할 인턴을 모집합니다. 아랍어/프랑스어 능통자를 우대합니다."
  },
  {
    "seq": "35395",
    "title": "[Domestic][Career] ASEAN-Korea Centre Culture & Tourism Unit Project Assistant Hiring",
    "country": "South Korea",
    "city": "Seoul",
    "lat": 37.5665,
    "lng": 126.9780,
    "regDt": "2026-06-23",
    "applyUrl": "[https://aseankorea.saramin.co.kr/main/index](https://aseankorea.saramin.co.kr/main/index)",
    "workType": "On-site",
    "ai_keywords": ["Culture & Tourism", "Planning", "ASEAN Cooperation", "Admin Support"],
    "ai_summary": "한-아세안센터 문화관광국에서 아세안 지역 문화교류 및 관광 진흥 프로젝트를 지원할 팀원을 모집합니다. 관련 분야 전공자 및 영어 통번역 가능자를 우대합니다."
  }
]