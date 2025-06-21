# Extractra 🌐

> Intelligent Multi-Agent Web Data Extraction System - Built with Google Agent Development Kit (ADK)

## 📖 Project Overview

Extractra is an intelligent web data extraction platform that uses a multi-agent system to automatically discover, extract, and integrate website data. Through the Google ADK framework, the system can understand user requirements, intelligently analyze website structures, and provide structured data output.

### 🎯 Core Features

- **Intelligent Page Discovery**: Automatically analyze website structure and discover relevant pages
- **Parallel Content Extraction**: Multi-agent parallel processing for efficient data extraction
- **Smart Data Integration**: Automatic deduplication, cleaning, and data formatting
- **Real-time Progress Tracking**: WebSocket real-time extraction progress display
- **CSV Export**: Support for exporting structured data to CSV format

## 🚀 Quick Start

### 📋 Prerequisites

- **Node.js**: 18+ 
- **Python**: 3.11+
- **Docker**: 20.10+ (optional)
- **Google Cloud**: ADK service configuration

### 🔧 Local Development

#### 1. Clone the Repository

```bash
git clone https://github.com/your-username/extractra.git
cd extractra
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# - GOOGLE_CLOUD_PROJECT
# - GOOGLE_CLOUD_LOCATION
# - PD_GEMINI_MODEL
# - CE_GEMINI_MODEL

# Install Playwright browsers
playwright install chromium

# Start backend service
python main.py
```

Backend service will start at `http://localhost:8080`

#### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd fronted

# Install dependencies
npm install
# or use pnpm
pnpm install

# Configure environment variables
# VITE_API_BASE_URL=http://localhost:8080
# VITE_WS_BASE_URL=ws://localhost:8080

# Start development server
npm run dev 
# or use pnpm
pnpm dev
```

Frontend application will start at `http://localhost:8080`

### 🐳 Docker Deployment

#### Build and Run Backend

```bash
# Build backend image from project root
docker build -f backend/Dockerfile -t extractra-backend .

# Run backend container
docker run -d \
  -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=your-project \
  -e GOOGLE_CLOUD_LOCATION=us-central1 \
  --name extractra-backend \
  extractra-backend
```

#### Build and Run Frontend

```bash
# Build frontend image
cd fronted
docker build \
  --build-arg VITE_API_BASE_URL=http://localhost:8080 \
  --build-arg VITE_WS_BASE_URL=ws://localhost:8080 \
  -t extractra-frontend .

# Run frontend container
docker run -d \
  -p 3000:8080 \
  --name extractra-frontend \
  extractra-frontend
```

## 📚 Usage Guide

### 1. Create Extraction Task

1. Visit Extractra homepage
2. Enter target website URL
3. Describe the data you want to extract
4. Click "Start Extraction"

### 2. Monitor Extraction Progress

The system displays progress across three stages:
- **Page Discovery**: Analyze website structure and discover relevant pages
- **Content Extraction**: Parallel extraction of data from pages
- **Result Integration**: Clean and integrate data

### 3. Download Results

After extraction completion, you can:
- Preview data table
- Download CSV file
- View extraction statistics

## 🛠️ Technology Stack

### Frontend
- **React 18** + **TypeScript**
- **Vite** - Fast build tool
- **shadcn/ui** - Modern UI component library
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **WebSocket** - Real-time communication

### Backend
- **FastAPI** - Modern Python web framework
- **Google ADK** - Agent Development Kit
- **Crawl4AI** - Web scraping and content extraction
- **Playwright** - Browser automation
- **Pydantic** - Data validation and serialization

### Deployment
- **Docker** - Containerized deployment
- **Google Cloud Run** - Serverless container platform
- **Google Cloud Build** - CI/CD pipeline

## 🔧 Configuration

### Backend Environment Variables

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=location

# LLM Model Configuration
PD_GEMINI_MODEL=gemini-2.0-flash-exp
CE_GEMINI_MODEL=gemini-2.0-flash-exp
GOOGLE_GENAI_USE_VERTEXAI=true

# Service Configuration
HOST=0.0.0.0
PORT=8080
DEBUG=false
LOG_LEVEL=INFO

# Frontend Domain (CORS Configuration)
FRONTED_DOMAIN=https://your-frontend-domain.com
```

### Frontend Environment Variables

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8080
VITE_WS_BASE_URL=ws://localhost:8080
```

## 📁 Project Structure

```
Extractra/
├── backend/                 # Backend service
│   ├── adk/                # ADK agent system
│   │   ├── agents.py       # Agent definitions
│   │   └── tools/          # Tool modules
│   ├── api/                # API routes
│   │   └── v1/            # API v1 version
│   ├── core/              # Core configuration
│   ├── models/            # Data models
│   ├── services/          # Business services
│   ├── main.py            # Application entry point
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Docker configuration
├── fronted/               # Frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   ├── lib/           # Utility libraries
│   │   └── types/         # Type definitions
│   ├── public/            # Static assets
│   ├── package.json       # Frontend dependencies
│   └── Dockerfile         # Docker configuration
├── doc/                   # Project documentation
│   ├── prd.md            # Product requirements
│   └── tech.md           # Technical architecture
└── README.md             # Project documentation
```

This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web crawling and markdown conversion.

**Extractra** - Making web data extraction intelligent and simple ✨