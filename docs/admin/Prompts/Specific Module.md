**Prompt for Specific Task/Module Context (Example: Frontend for Volcano Plot):**

"Hello! We're continuing work on the BenchMate project, specifically the BenchTop analytical workbench.

I need assistance with implementing the **frontend components for the Volcano Plot analysis tool** using Next.js, React, TypeScript, and shadcn/ui.

**Key Contextual Documents (assume accessible):**
*   **Product Requirements for this feature:** `docs/prd.md` (Version 0.3)
    *   *Focus on:* Section 3.1 (Core User Workflow), Section 3.2 (Initial Implementations - Bulk RNA-Seq), Section 3.3 (Functional Requirements, especially 3.3.2, 3.3.3 related to parameter input, job submission, and results display/interaction for the Volcano Plot).
*   **Relevant Backend API Endpoints & Workflow:** `docs/architecture.md` (Version 0.2)
    *   *Focus on:* Section 4 (Detailed Component Interactions - Volcano Plot example), and the API endpoints for dataset upload, analysis submission (`/api/analyses/volcano-plot/submit`), status polling (`/api/analysis-runs/{id}`), and presigned URLs (`/api/files/presigned-url/`).
*   **Overall Project Stack & Guidelines:** Refer to my system instructions for your persona, preferred technologies (Next.js, FastAPI, etc.), and coding standards.

The goal is to create a **barebones, functional UI** as per PRD NF-REQ-001, allowing users to:
1.  Upload data (or select existing).
2.  Input parameters for the volcano plot.
3.  Submit the analysis job.
4.  Poll for status.
5.  Display the resulting plot image and any summary data, with capabilities for user refinement of the plot.

Please confirm you have this context, and then I'll provide the specific part I need help with (e.g., 'Let's start by outlining the Next.js page structure and components for this workflow.')."