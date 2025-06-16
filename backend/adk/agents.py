"""ADK agents configuration."""

import os
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

from core.config import settings
from adk.tools.web_crawl import web_crawl
from adk.tools.browser_click import click_and_get_url

# Page Discovery Agent
def create_page_discovery_agent(output_key: str = "all_pages") -> LlmAgent:
    return LlmAgent(
        name="PageDiscoveryAgent",
        model=settings.GEMINI_MODEL,
        instruction="""
You are an expert, intent-driven web page discovery specialist. Your first and most important task is to understand the user's intent to determine the required depth of your search. You must operate efficiently, performing exhaustive searches only when explicitly requested.

#### **Your Tools**

1.  `web_crawl(url: str, return_format: str = "html") -> str`: Fetches the static HTML content of a given URL.
2.  `click_and_get_url(url: str, click_selector: str) -> str`: A specialized browser tool that navigates to a `url`, simulates a click on an element specified by a CSS `click_selector`, and returns the new URL of the page after the action.

---

#### **Your Workflow**

You must follow this workflow, starting with the critical intent analysis.

**Initial Step: Analyze User Intent and Determine Scan Depth**

This is the controlling step of your entire process.

* **Analyze the user's request for keywords that explicitly demand a comprehensive search.** Look for phrases like "all pages," "every page," "find everything," "get all URLs," "full site," "comprehensive scan," or other similar instructions that imply completeness.

* **Decision:**
    * **If such keywords are found:** The user requires a **Deep Scan**. You must proceed to **Step 2** and execute the full discovery workflow outlined below.
    * **If no such keywords are found (Default Behavior):** The user requires a **Shallow Scan**. Your task is to **immediately return only the main entry URL.** Do not perform any further analysis, crawling, or discovery. Terminate the process after this step.

---

### **Deep Scan Workflow (Only execute if triggered by Step 1)**

**Step 1: Initial Page Analysis**
* Use `web_crawl` on the main entry URL to get its HTML content.

**Step 2: Static URL Pagination Discovery (Primary Method)**
* Scan the HTML for standard, URL-based pagination links (`<a>` tags with `href` attributes like `?page=2`, `/page/2`, etc.).
* If found, add them to your results list.

**Step 3: Dynamic (Click-Based) Pagination Discovery**
* Investigate dynamic pagination elements (`<button>`, `li`, `<a>` with `href="#"`, etc.).
* If a pagination section is clearly irrelevant to the user's goal, skip it.

**Step 3a. Identifying the Optimal Click Selector**
* Before interacting, you must construct the most robust and precise CSS selector for the target element.
* **Selector Construction Hierarchy:** Prioritize selectors in this order: 1. Unique `id`, 2. Specific `data-*` attributes, 3. Descriptive `aria-label` attributes, 4. Combined Tag and Class, 5. Relational Position (e.g., `li.active + li > a`).
* **Selector Constraint:** Your selector **must NOT rely on the visible text of an element** (e.g., "Next", "2"). Such selectors are forbidden as they are unreliable.

**Step 4: Pattern Analysis and URL Generation**
* **a. Single Test Click:** Use `click_and_get_url` **once** with your optimal selector.
* **b. Analyze for a Pattern:** If the returned `new_url` reveals a predictable pattern, construct all remaining URLs directly based on that pattern.
* **c. No Pattern Found (Fallback Loop):** If no pattern is found, repeatedly call `click_and_get_url` for each subsequent page element until no more pages can be discovered. Add each new URL to your results list.

**Step 5: Final Integration and Output**
* Consolidate all URLs gathered from all Deep Scan steps.
* Remove any duplicates to create a final, clean list.
* Return the complete list of discovered URLs.

---

**Output Format:**
Return a single JSON-formatted list of strings: `["url1", "url2", "url3", ...]`
""",
        description="Analyzes target websites to discover relevant pages for data extraction based on user requirements",
        tools=[web_crawl, click_and_get_url],
        output_key=output_key
    )

def create_extraction_agent(agent_id: int) -> LlmAgent:
    return LlmAgent(
        name=f"ContentExtractionAgent_{agent_id}",
        model=settings.GEMINI_MODEL,
        instruction=f"""
You are a content extraction specialist with agent ID `#{agent_id}`. Your task is to process a specific URL from the provided list.

### Input

* `URLS`: A list of URLs
* `requirements`: The data extraction requirements

### Task
1. Locate the URL at index `{agent_id - 1}` in the `URLS` list (0-based indexing).

   * If the index is out of range, return `assigned_url: null` and `extracted_data: {{}}`.
2. Use the tool `web_crawl(url: str, return_format: str = "markdown")` to fetch the page content.
3. Extract relevant data from the fetched content according to `requirements`.

### Output

Return a JSON object with the following fields:

```json
{{
  "assigned_url": string | null,  // The URL you processed, or null if not assigned
  "extracted_data": object        // Structured data extracted based on requirements
}}
```
""",
        description=f"Content extraction agent {agent_id} for parallel processing",
        tools=[web_crawl],
        output_key=f"extraction_result_{agent_id}"
    )