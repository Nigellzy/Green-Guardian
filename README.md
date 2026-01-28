# Green-Guarding Project - Team BigBacks

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-green)
![Gemini AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![OneMap](https://img.shields.io/badge/API-OneMap%20SG-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

An interactive dashboard application designed to visualize, analyze, and mitigate urban heat issues in Singapore. This project integrates geospatial data from OneMap with Google's Gemini AI to provide intelligent insights and perception analysis regarding urban heat distribution.

## 📋 Table of Contents
- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Technologies Used](#-technologies-used)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
- [Contributors](#-contributors)

## 🔭 Project Overview
The **Urban Heat Perception Dashboard** serves as a centralized platform for monitoring urban heat data. It combines real-time data aggregation, geospatial visualization, and AI-driven context enrichment to help users understand heat patterns across different planning areas in Singapore.

## ✨ Key Features
- **Interactive Map Visualization:** Dynamic heatmaps using Folium and OneMap API.
- **AI-Driven Insights:** Utilizes Google Gemini to analyze context and perception data.
- **Geospatial Integration:** Seamless mapping of coordinates to Singapore's Planning Areas.
- **Real-time Dashboard:** Built with Flask to display analytics and AI responses instantly.
- **Rule-Based Triggers:** Enhanced trigger rules for automated alerts or mitigation suggestions.

## 🛠 Technologies Used
- **Backend:** Python, Flask
- **AI & ML:** Google GenAI (Gemini)
- **Data Processing:** Pandas, Geopandas, Shapely
- **Mapping:** Folium, OneMap API
- **Frontend:** HTML/CSS (Inter font), Markdown rendering

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher installed.
- Valid API keys for Google Gemini or OneMap (if required).

### Steps
1. **Clone the repository** (if applicable) or navigate to the project folder:
   ```bash
   cd BigbacksBigplans
   ```

2. **Install Dependencies**:
   It is recommended to use a virtual environment.
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Ensure you have any necessary environment variables set up (e.g., API keys).
   Refer to .env.template file on where to get API keys from

## 💻 Usage Guide

1. **Start the Dashboard**:
   Run the main dashboard script:
   ```bash
   python dashboard.py
   ```

2. **Access the Application**:
   Open your web browser and navigate to:
   [http://localhost:5000](http://localhost:5000)

   The dashboard should load, displaying the map and sidebar analysis panels.

## 👥 Contributors
- **Claire Chong**
- **Justin Lim**
- **Nigel Lum**
- **Wai Yee Yuen**

---


