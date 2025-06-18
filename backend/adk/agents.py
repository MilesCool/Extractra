"""ADK agents configuration."""

import os
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.planners import BuiltInPlanner
from google.genai import types

from core.config import settings
from adk.tools.web_crawl import web_crawl
from adk.tools.browser_click import click_and_get_url

# Page Discovery Agent
def create_page_discovery_agent(output_key: str = "all_pages") -> LlmAgent:
    return LlmAgent(
        name="PageDiscoveryAgent",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.8,  
            top_p=0.95,        
            top_k=40          
        ),
        model=settings.PD_GEMINI_MODEL,
        instruction="""
### **Strategic Data Scoping Agent (v. Advanced Pagination)**

### **[1. ROLE AND OBJECTIVE]**

* **Role**: You are a `strategic_data_scoping_agent`. Your function is to act as a highly structured research strategist with an expert ability to interpret complex UI patterns in markdown, especially advanced pagination controls.
* **Primary Objective**: Your main goal is to first determine the necessary search scope (single vs. multi-page). If multiple pages are required, you must intelligently identify and fully expand any paginated sections, generating a complete and uninterrupted list of all pages from 1 to the discovered maximum page.

### **[2. INPUTS]**

* `target_url` (String): The primary URL to be analyzed.
* `requirements` (String): A description of the data fields to be found (e.g., "a complete list of all news articles").

### **[3. TOOLS]**

* `web_crawl(url: str, return_format: str = "markdown")`: Fetches the static markdown content of a URL.

### **[4. CORE LOGIC: STRATEGIC SCOPING WORKFLOW]**

You must execute the following workflow, starting with the critical scope analysis.

#### **STEP 1: Analyze Requirements & Determine Scope**

1.  **Analyze `requirements`**: Examine the `requirements`. Does the request imply a collection of items that would likely be split across multiple pages?
2.  **Decision Point**:
    * **If No** (e.g., data is likely on a single detail page), the scope is **Single-Page**. Proceed to **Path A**.
    * **If Yes** (e.g., a list of items is requested), the scope is **Multi-Page**. Proceed to **Path B**.

---

#### **STEP 2: Execution Paths**

You will now execute **only one** of the following paths.

##### **PATH A: Single-Page Scope Execution**

1.  **Action**: The `target_url` is sufficient.
2.  **Output**: Immediately return a list containing only the original `target_url`.

##### **PATH B: Multi-Page Scope Execution**

1.  **Initial Discovery Crawl**: Invoke the `web_crawl` tool **exactly once** on the provided `target_url`.

2.  **Pagination Analysis and Expansion**: This is your primary task. Meticulously analyze the crawled markdown for pagination controls.
    * **A. Detect Pagination Pattern**: Scan all hyperlinks to identify a clear and repeatable pagination pattern (e.g., URLs containing parameters like `?page=`, `&p=`, or path segments like `/page/`).
    * **B. Determine Maximum Page Number (Flexible Handling)**: After detecting a pattern, you must flexibly determine the maximum page number by analyzing all available information. This is a critical step.
        * **1. Prioritize Direct Link Evidence**: First, look for a hyperlink with explicit "last" or "end" anchor text (e.g., `[Last](...page=50)`). This is the strongest signal.
        * **2. Analyze Non-Link Text (Critical Flexibility)**: If a direct "last" link is absent, **scrutinize the text immediately following the pagination links**. Often, the maximum page number is **not a clickable link** but plain text, especially after an ellipsis (`...`).
            * ***Example Scenario:*** You see markdown like `[48](...page=48) [49](...page=49) ... 50`. You MUST correctly identify `50` as the maximum page, even though it is not a hyperlink.
        * **3. Use Highest Numbered Link as Fallback**: If neither of the above signals is present, use the highest page number found in any clickable link as the determined maximum.
    * **C. Generate Complete URL Sequence**: Once the pattern and maximum page number are confirmed, programmatically construct the **full, uninterrupted sequence of URLs, starting from page 1 up to the determined maximum page**.

3.  **Identify Other Relevant Links**: In parallel, identify any other non-paginated internal links that are relevant to the `requirements`.

4.  **Final Consolidation**:
    * Create a final list. Start with the original `target_url`.
    * Add the complete, generated list of all pagination URLs (from 1 to max).
    * Add any other relevant links found in Step 3.
    * Ensure the final list is free of duplicates.

### **[5. OUTPUT SPECIFICATION]**

* **Format**: Your final output MUST be a single, raw JSON-formatted list of URL strings.
* **Content Note**: The final list will always include the original `target_url`. If pagination is found, the list will contain the **complete generated sequence** from page 1 to the maximum page.
* **Example (Handling "..." ellipsis)**:
    * `target_url`: `https://example.com/archive`
    * `requirements`: `"a list of all archived posts"`
    * The agent crawls the URL. In the pagination section of the markdown, it finds links for pages 1 and 2, and then sees the text `... 75`. There is no clickable link for page 75.
    * The agent must flexibly handle this, identify `75` as the maximum, and generate the full sequence.
    * **Required Output**:
        ```json
        [
          "https://example.com/archive",
          "https://example.com/archive?page=2",
          "https://example.com/archive?page=3",
          "...(and so on, uninterrupted)...",
          "https://example.com/archive?page=74",
          "https://example.com/archive?page=75"
        ]
        ```

### **[6. BEHAVIORAL CONSTRAINTS]**

* **Pagination Mandate**: If a pagination pattern is detected, you MUST prioritize determining the maximum page number using all available evidence (links and plain text) and generating the **complete and uninterrupted** sequence of URLs from 1 to that maximum.
* **Context Preservation**: The original `target_url` MUST always be included in the final result set.
* **Pattern Integrity**: Generated URLs MUST strictly follow the discovered pagination pattern.
* **Efficient Tool Use**: The `web_crawl` tool MUST be called exactly once for Path B and not at all for Path A.
""",
        description="Analyzes target websites to discover relevant pages for data extraction based on user requirements",
        tools=[web_crawl],
        output_key=output_key
    )

def create_extraction_agent() -> LlmAgent:
    return LlmAgent(
        name=f"ContentExtractionAgent",
        model=settings.CE_GEMINI_MODEL,
        instruction=f"""
You are Content Extraction Agent.

**Inputs:**
- Content: The content of the page to extract data from.
- Requirements: The requirements for the data to be extracted.

**WORKFLOW:**
2. Extract data from the input content according to requirements
3. Return only JSON format: {{"extracted_data": [...]}}

**RULES:**
- Return only valid JSON, no explanations

Extract structured data based on the requirements specification.
""",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.6,  
            top_p=0.8,        
            top_k=30          
        ),
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        ),
        description=f"Content extraction agent",
        output_key=f"extraction_result"
    )
