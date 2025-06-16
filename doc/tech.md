# Extractra - Technical Architecture Document (Based on Google ADK)

## 1. System Overview

### 1.1 Technology Stack
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS
- **Backend**: Python FastAPI, Google Agent Development Kit (ADK), Crawl4AI
- **Authentication**: Clerk
- **Deployment**: Stateless service, no user history storage

### 1.2 ADK Architecture Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js Web   │    │   FastAPI       │    │  ADK Framework  │
│   Application   │◄──►│   API Gateway   │◄──►│  Multi-Agent    │
│                 │    │                 │    │  Orchestration  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Clerk       │    │  Task Manager   │    │    Web Crawl    │
│ Authentication  │    │  (ADK State)    │    │   Tool Service  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 2. Frontend Architecture (Next.js) - Unchanged

### 2.1 Project Structure
```
src/
├── app/
│   ├── (auth)/
│   │   ├── sign-in/
│   │   └── sign-up/
│   ├── dashboard/
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── task/
│   │   └── [taskId]/
│   │       └── page.tsx
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── ui/
│   ├── auth/
│   ├── task/
│   └── layout/
├── lib/
│   ├── clerk.ts
│   ├── api.ts
│   └── utils.ts
└── types/
    └── index.ts
```

### 2.2 Core Module Interfaces (Unchanged)

#### 2.2.1 Authentication Module
```typescript
interface AuthModule {
  clerkConfig: ClerkConfiguration;
  useAuth(): AuthState;
  ProtectedRoute: React.Component;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
```

#### 2.2.2 Task Management Module
```typescript
interface TaskModule {
  createTask(request: TaskRequest): Promise<TaskResponse>;
  getTaskStatus(taskId: string): Promise<TaskStatus>;
  subscribeToProgress(taskId: string): EventSource;
}

interface TaskRequest {
  requirements: string;
  targetUrl: string;
  userId: string;
}

interface TaskStatus {
  taskId: string;
  status: 'pending' | 'discovery' | 'extraction' | 'integration' | 'completed' | 'failed';
  progress: number; // 0-100
  currentAgent: 'page_discovery' | 'content_extraction' | 'result_integration';
  agentState: ADKAgentState;
  message: string;
  result?: StructuredData;
  error?: string;
}

interface ADKAgentState {
  activeAgent: string;
  executionPlan: ExecutionStep[];
  currentStep: number;
  totalSteps: number;
}
```

## 3. Backend Architecture (FastAPI + ADK + Crawl4AI)

### 3.1 ADK Project Structure
```
backend/
├── adk/
│   ├── __init__.py
│   ├── agents.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── web_crawl.py
│   │   ├── ...
│   └── config/
│       ├── __init__.py
│       └── adk_config.py
├── api/
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── tasks.py
│   │   └── auth.py
│   └── __init__.py
├── core/
│   ├── config.py
└── main.py
├── requirements.txt
└── Dockerfile
```

## 4. ADK Core Modules

### 4.1 Tools Module
```python
async def web_crawl():
    """web crawl tool (based on Crawl4AI)"""
    pass
```

### 4.2 Agents Module (agents.py)
```python
page_discovery_agent = LlmAgent(
    name="PageDiscoveryAgent",
    model="gemini-2.0-flash-exp",
    instruction="""
You are a web page discovery specialist responsible for analyzing user requirements and identifying relevant sub-pages links from main page.

Your workflow:
1. **Requirement Analysis**: Parse the user's data extraction requirements to understand what information they need
2. **Main Page Analysis**: Use the web_crawl tool to fetch and analyze the target URL's main page content
3. **Link Discovery**: Extract and identify all relevant sub-page links from the main page that might contain the required data
4. **State Update**: Update the shared state with:
   - sub-page links list
   - Initial data structure requirements

Output Format:
- all_page_links: List of {url, title}, contain sub-page links and main page link
""",
    description="Analyzes target websites to discover relevant pages for data extraction based on user requirements",
    tools=["web_crawl"]
)

# Content Extraction Agent Template (for parallel processing)
content_extraction_agent_template = LlmAgent(
    name="ContentExtractionAgent",
    model="gemini-2.0-flash-exp",
    instruction="""
You are a content extraction specialist responsible for extracting structured data from web pages.

Your workflow:
1. **Page Processing**: Receive a specific page URL and extraction requirements from the discovery phase
2. **Content Retrieval**: Use web_crawl tool to fetch the assigned page's markdown content
3. **Data Extraction**: Extract relevant data points based on the specified requirements:
   - Text content (titles, descriptions, articles)
   - Structured data (tables, lists, forms)
   - Metadata (dates, authors, categories)
   - Links and references
4. **Data Standardization**: Format extracted data according to the unified schema:
   - Consistent field names and data types
   - Proper handling of missing or incomplete data
5. **Output Generation**: Return structured data in the specified format

Output Format:
- page_url: Source URL of processed page
- extracted_data: Structured data dictionary with standardized fields
- extraction_metadata: Processing time, data volume
- issues_encountered: Any problems or limitations during extraction

Handle edge cases like dynamic content, missing elements, or formatting inconsistencies gracefully.
    """,
    description="Extracts and standardizes structured data from individual web pages according to specified requirements",
    tools=["web_crawl"]
)

# Parallel Content Extraction Agent
parallel_content_extraction_agent = ParallelAgent(
    name="ParallelContentExtractionAgent",
    sub_agents=[
        # Multiple instances of content extraction agents will be created dynamically
        # based on the number of sub-pages discovered or the number of workers
    ],
    description="Orchestrates parallel processing of multiple web pages for simultaneous content extraction to improve efficiency and reduce total processing time"
)

# Main Sequential Pipeline Agent
sequential_pipeline_agent = SequentialAgent(
    name="ExtractAndSynthesisPipeline",
    sub_agents=[
        page_discovery_agent,
        parallel_content_extraction_agent,
        result_integration_agent
    ],
    description="Coordinates the complete data extraction workflow from initial page discovery through parallel content extraction to final data integration and refinement"
)
```

### 4.3 FastAPI Integration Module
```python
from fastapi import FastAPI

class TaskAPIRouter:
    """Task API router
    
    API endpoints:
    - POST /api/v1/tasks: Create new extraction task
    - GET /api/v1/tasks/{task_id}/status: Get task status
    - GET /api/v1/tasks/{task_id}/stream: Real-time progress stream
    - GET /api/v1/tasks/{task_id}/result: Get task result
    - DELETE /api/v1/tasks/{task_id}: Cleanup task data
    """
    pass
```

## 5. API Interface Specifications

### 5.1 Task Management APIs
```
POST /api/v1/tasks
- Description: Create new data extraction task
- Request: TaskRequest
- Response: TaskResponse

GET /api/v1/tasks/{task_id}/status
- Description: Get task status with ADK state information
- Response: TaskStatus

GET /api/v1/tasks/{task_id}/stream
- Description: Real-time task progress stream (Server-Sent Events)
- Response: Streaming ADK state updates

GET /api/v1/tasks/{task_id}/result
- Description: Get final task result
- Response: StructuredData

DELETE /api/v1/tasks/{task_id}
- Description: Cleanup task data and resources
- Response: Success message
```

### 5.2 ADK State APIs
```
GET /api/v1/tasks/{task_id}/agents/status
- Description: Get detailed status of all agents
- Response: ADK agent state information

GET /api/v1/tasks/{task_id}/execution-plan
- Description: Get task execution plan and current progress
- Response: Execution steps and progress details
```

## 6. Monitoring and Logging

### 6.1 ADK Monitoring Service
```python
class ADKMonitoringService:
    """ADK agent monitoring service
    
    Monitoring capabilities:
    - Agent execution time and success rate
    - Tool usage frequency and response time
    - Task completion rate and quality metrics
    - User feedback and satisfaction tracking
    """
    pass
```

### 6.2 Performance Metrics
- Agent execution duration and success rates
- Tool invocation frequency and response times
- Task completion rates
- User satisfaction feedback metrics

This ADK-based technical architecture document provides a more structured and scalable backend design that fully leverages ADK's multi-agent orchestration capabilities and workflow management features, with clear emphasis on the sequential workflow process and agent responsibilities.