# PharmaIQ Architecture Documentation

## 1. System Overview
PharmaIQ is a multi-agent pharmaceutical intelligence platform designed to optimize supply chain operations and ensure public health safety. It uses an agentic workflow to monitor cold chain integrity, forecast disease outbreaks, and coordinate complex responses.

## 2. Multi-Agent Orchestration (LangGraph)
The core of PharmaIQ is built on **LangGraph**, which facilitates a cyclic, state-aware workflow.

- **Cyclic State Machine**: Unlike linear chains, LangGraph allows for reflection and revision loops.
- **State Management**: The `PharmaIQState` object persists across agent turns, tracking decisions and critiques.
- **Workflow**:
  1. **Planner**: Decodes the user request into sub-tasks.
  2. **Specialized Agents**: SOMA and PULSE execute specific domain logic.
  3. **Critique Agents**: Validate outputs against regulatory and operational standards.
  4. **Synthesis**: The Planner combines agent outputs into a unified action plan.

## 3. Specialized Agents
### SOMA (Specialized Operations & Monitoring Agent)
- **Focus**: Operational integrity, cold chain monitoring, and staffing.
- **Key Tasks**: Temperature breach classification, staff scheduling, and compliance monitoring.
- **Tools**: Integrated with Cold Chain and HRMS MCP servers.

### PULSE (Predictive Utilization & Logistics Surveillance Engine)
- **Focus**: Public health trends and demand forecasting.
- **Key Tasks**: Epidemic trend analysis and pharmaceutical demand scaling.
- **Tools**: Integrated with Disease Surveillance MCP server.

### Planner & Critique Agents
- **Planner Agent**: The central controller that manages task decomposition and synthesis.
- **Critique Agents**: Each primary agent (SOMA, PULSE, Planner) has a corresponding critique agent that ensures quality and safety.

## 4. Data Integration (MCP)
PharmaIQ uses the **Model Context Protocol (MCP)** to decouple agents from specific data sources:
- **Cold Chain MCP**: Real-time IOT sensor data.
- **Disease Surveillance MCP**: Epidemiological data.
- **ERP MCP**: Inventory and finance data.
- **HRMS MCP**: Staffing and compliance records.

## 5. Knowledge Base (RAG)
PharmaIQ utilizes Retrieval-Augmented Generation to ground AI decisions in regulatory reality.
- **Vector Database**: **ChromaDB** stores regulatory guidelines and historical breach patterns.
- **Contextual Injection**: Relevant documents are retrieved and injected into agent prompts during execution.

## 6. Tech Stack
- **Backend**: Python (FastAPI), LangChain, LangGraph.
- **AI Models**: Google Gemini 2.0 Flash.
- **Storage**: SQLite (Audit/Transactional), ChromaDB (Vector Knowledge).
- **Frontend**: React.js with Tailwind CSS for audit transparency and monitoring.
