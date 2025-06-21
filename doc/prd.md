# Extractra - Product Requirements Document

## 1. Product Overview

### 1.1 Product Vision
Build an intelligent multi-agent system that can automatically discover, extract, and integrate web data based on user requirements and target website URLs.

### 1.2 Product Goals
- Automate the complex process of web data extraction
- Provide intelligent page discovery and content filtering
- Deliver structured, clean, and integrated data outputs
- Support iterative refinement based on user feedback

### 1.3 Target Users
- Data analysts and researchers
- Business intelligence teams
- Market research professionals
- Content aggregation services
- Academic researchers

## 2. System Architecture

### 2.1 High-Level Architecture
The system consists of three core agents working with LLM Service and Crawl4AI Service:

```
User Input → Page Discovery Agent ↔ LLM Service
                ↓                    ↑
          Content Extraction Agent ↔ Crawl4AI Service
                ↓
        Result Integration Agent → User Output
```

### 2.2 Core Components

#### 2.2.1 Page Discovery Agent
**Purpose**: Orchestrate the discovery and filtering of relevant page links from target websites

**Key Responsibilities**:
- Parse user extraction requirements
- Coordinate with Crawl4AI to get page content in Markdown format
- Leverage LLM Service to analyze page content and discover sub-page links
- Use LLM Service to evaluate page relevance against user requirements
- Compile target page URL list (main page + filtered sub-pages)

**Input**: User requirements + Target website URL
**Output**: Main page URL + Filtered sub-page URLs list

#### 2.2.2 Content Extraction Agent
**Purpose**: Orchestrate the extraction of structured data from discovered pages

**Key Responsibilities**:
- Receive main page URL and sub-page URLs list from Page Discovery Agent
- Coordinate with Crawl4AI to get all page content in Markdown format
- Leverage LLM Service to extract relevant data based on user requirements
- Parallel processing of sub-page content extraction via LLM Service
- Standardize extraction formats across all pages
- Compile extracted data into structured format

**Input**: Main page URL + Sub-page URLs list
**Output**: Main page data + Sub-pages data list

#### 2.2.3 LLM Service
**Purpose**: Provide intelligent analysis and content processing capabilities

**Key Responsibilities**:
- Analyze Markdown content to understand page structure and discover links
- Evaluate page relevance against user requirements
- Extract structured data from Markdown content based on user needs
- Provide intelligent content filtering and classification
- Handle complex reasoning tasks for data extraction and analysis

**Input**: Markdown content + User requirements + Analysis instructions
**Output**: Analysis results + Structured data + Relevance scores

#### 2.2.4 Crawl4AI Service
**Purpose**: Provide web crawling and content conversion capabilities

**Key Responsibilities**:
- Crawl web pages and convert to clean Markdown format
- Handle various web page formats and structures
- Provide efficient batch crawling capabilities
- Ensure consistent content formatting across different pages

**Input**: URLs list
**Output**: Markdown content list

#### 2.2.5 Result Integration Agent
**Purpose**: Integrate and clean extracted data

**Key Responsibilities**:
- Analyze data relationships between main page and sub-pages
- Establish data mapping and connections
- Remove duplicates and clean data
- Handle data conflicts and anomalies
- Merge related data records
- Generate unified data structure
- Validate data quality
- Produce final dataset

**Input**: Main page data + Sub-pages data list
**Output**: Integrated structured data

## 3. Detailed Workflow

### 3.1 Page Discovery Agent Workflow

```mermaid
graph TD
    A[User Input: Requirements & URL] --> B[Parse User Requirements]
    B --> C[Crawl Main Page with Crawl4AI]
    C --> D[Send MD to LLM Service for Analysis]
    D --> E[LLM Service: Analyze Structure & Discover Links]
    E --> F[Crawl Sub-pages with Crawl4AI]
    F --> G[Send Sub-pages MD to LLM Service]
    G --> H[LLM Service: Evaluate Relevance]
    H --> I{Meets Requirements?}
    I -->|Yes| J[Add URL to Target List]
    I -->|No| K[Skip Page URL]
    J --> L{More Pages?}
    K --> L
    L -->|Yes| H
    L -->|No| M[Output URL Package]
```

### 3.2 Content Extraction Agent Workflow

```mermaid
graph TD
    A[Receive Page URLs] --> B[Crawl Main Page with Crawl4AI]
    A --> C[Batch Crawl Sub-pages with Crawl4AI]
    B --> D[Get Main Page Markdown]
    C --> E[Get Sub-pages Markdown List]
    D --> F[Send Main Page MD to LLM Service]
    F --> G[LLM Service: Extract Main Page Data]
    E --> H[Parallel Sub-page Processing]
    H --> I[Send Sub-page 1 MD to LLM Service]
    H --> J[Send Sub-page 2 MD to LLM Service]
    H --> K[Send Sub-page N MD to LLM Service]
    I --> L[LLM Service: Extract Sub-page 1 Data]
    J --> M[LLM Service: Extract Sub-page 2 Data]
    K --> N[LLM Service: Extract Sub-page N Data]
    G --> O[Main Page Results]
    L --> P[Sub-page Results List]
    M --> P
    N --> P
    O --> Q[Compile Final Output]
    P --> Q
```
## 4. Key Features

### 4.1 Intelligent Page Discovery
- Automated website structure analysis
- Smart sub-page link discovery and filtering
- Content relevance evaluation without full content extraction
- Efficient URL compilation and organization

### 4.2 Centralized Content Extraction
- Unified content crawling and extraction process
- Concurrent processing of multiple pages
- Standardized data extraction formats
- Error handling and retry mechanisms

### 4.3 Advanced Data Integration
- Cross-page data relationship analysis
- Intelligent duplicate detection and removal
- Data conflict resolution
- Quality validation and verification

### 4.4 User Feedback Loop
- User satisfaction assessment
- Feedback collection and processing
- Iterative refinement capability
- Requirement adjustment support

## 5. Technical Requirements

### 5.1 Core Technologies
- **LLM Service**: Intelligent analysis, content understanding, and data extraction
- **Crawl4AI**: Web crawling and Markdown content conversion
- **Markdown Processing**: Content standardization and format handling
- **Parallel Processing**: Concurrent page processing capabilities
- **Data Integration**: Advanced data merging and cleaning algorithms

### 5.2 Performance Requirements
- Support for large-scale website crawling
- Efficient parallel processing of multiple pages
- Real-time feedback and adjustment capabilities
- Scalable architecture for growing data volumes

### 5.3 Data Quality Requirements
- Accurate content extraction with minimal errors
- Comprehensive duplicate detection and removal
- Robust conflict resolution mechanisms
- Data integrity validation

## 6. User Journey

### Primary User Journey
1. **Input Phase**: User provides requirements and target URL
2. **Discovery Phase**: System discovers and filters relevant page URLs
3. **Extraction Phase**: System crawls and extracts structured data from all pages
4. **Integration Phase**: System cleans and integrates all data
5. **Output Phase**: System delivers final structured dataset
6. **Feedback Phase**: User reviews and provides feedback if needed
7. **Refinement Phase**: System adjusts based on feedback (if required)

### Workflow
```mermaid
graph TD
    A[User Input: Requirements & Target URL] --> B[Page Discovery Agent]
    B --> |Main Page URL + Filtered Sub-page URLs List| C[Content Extraction Agent]
    C --> |Main Page Data + Sub-pages Data List| D[Result Integration]
    D --> E[Return to User]
    E --> F{User Satisfied?}
    F -->|No| G[Collect User Feedback]
    G --> B
    F -->|Yes| H[Task Complete]
    
    class A,E,G,H userNode
    class B,C,D agentNode
    class F decisionNode
```

### Flow Diagram
```mermaid
sequenceDiagram
    participant User
    participant PageDiscoveryAgent as "Page Discovery Agent"
    participant ContentExtractionAgent as "Content Extraction Agent"
    participant Crawl4AI as "Crawl4AI"
    participant LLMService as "LLM Service"
    Participant ResultIntegration as "ResultIntegration"

    User->>PageDiscoveryAgent: User Requirements + Target URL
    
    Note over PageDiscoveryAgent: Parse User Requirements
    
    PageDiscoveryAgent->>Crawl4AI: Crawl Main Page
    Crawl4AI-->>PageDiscoveryAgent: Main Page Content (MD)
    
    PageDiscoveryAgent->>LLMService: Analyze Main Page MD + User Requirements
    LLMService-->>PageDiscoveryAgent: Main Page Analysis + Sub-page Links
    
    Note over PageDiscoveryAgent: Compile Target Page URLs
    
    PageDiscoveryAgent->>ContentExtractionAgent: Main Page URL + Filtered Sub-page URLs List
    
    ContentExtractionAgent->>Crawl4AI: Crawl Main Page for Content
    Crawl4AI-->>ContentExtractionAgent: Main Page Content (MD)
    
    ContentExtractionAgent->>Crawl4AI: Batch Crawl Sub-pages for Content
    Crawl4AI-->>ContentExtractionAgent: Sub-pages Content (MD List)
    
    ContentExtractionAgent->>LLMService: Extract Main Page Data from MD + User Requirements
    LLMService-->>ContentExtractionAgent: Main Page Structured Data
    
    par Parallel Sub-page Processing
        ContentExtractionAgent->>LLMService: Extract Sub-page 1 Data from MD + User Requirements
        LLMService-->>ContentExtractionAgent: Sub-page 1 Structured Data
    and
        ContentExtractionAgent->>LLMService: Extract Sub-page 2 Data from MD + User Requirements
        LLMService-->>ContentExtractionAgent: Sub-page 2 Structured Data
    and
        ContentExtractionAgent->>LLMService: Extract Sub-page N Data from MD + User Requirements
        LLMService-->>ContentExtractionAgent: Sub-page N Structured Data
    end
    
    Note over ContentExtractionAgent: Standardize Extraction Formats
    Note over ContentExtractionAgent: Compile Extracted Data
    
    ContentExtractionAgent->>ResultIntegration: Main Page Data + Sub-pages Data List
    
    Note over ResultIntegration: Analyze Data Relationships
    Note over ResultIntegration: Establish Data Mapping
    Note over ResultIntegration: Remove Duplicates & Clean
    Note over ResultIntegration: Merge Related Records
    Note over ResultIntegration: Generate Unified Structure
    
    ResultIntegration->>User: Integrated Structured Data
    
    alt User Feedback Loop
        User->>PageDiscoveryAgent: Feedback for Refinement
        Note over PageDiscoveryAgent: Adjust Requirements
        Note over PageDiscoveryAgent: Re-process if needed
    else
        User->>User: Task Complete
    end
```