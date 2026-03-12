# PharmaIQ: Multi-Agent Pharmaceutical Intelligence Platform

PharmaIQ is an advanced multi-agent system designed to optimize pharmaceutical operations through intelligent monitoring, forecasting, and orchestration. It combines operational excellence (SOMA), predictive intelligence (PULSE), and strategic planning (Planner) with comprehensive critique feedback loops.

## 🎯 Overview

PharmaIQ leverages multi-agent AI architecture to address complex pharmaceutical challenges:

- **SOMA (Specialized Operations & Monitoring Agent)**: Monitors cold chain integrity, schedules staff, and ensures operational compliance
- **PULSE (Predictive Utilization & Logistics Surveillance Engine)**: Forecasts epidemics and adjusts pharmaceutical demand dynamically
- **Planner**: Orchestrates complex multi-domain tasks and coordinates recommendations across agents
- **Critique Agents**: Validate and improve decisions from all primary agents

## 📁 Project Structure

```
PharmaIQ/
├── backend/
│   ├── agents/                 # Multi-agent system
│   │   ├── soma_agent.py
│   │   ├── soma_critique_agent.py
│   │   ├── pulse_agent.py
│   │   ├── pulse_critique_agent.py
│   │   ├── planner_agent.py
│   │   ├── planner_critique_agent.py
│   │   └── base_critique.py
│   ├── mcp_servers/            # Model Context Protocol servers
│   │   ├── base_mcp.py
│   │   ├── cold_chain_mcp.py
│   │   ├── disease_surveillance_mcp.py
│   │   ├── erp_mcp.py
│   │   ├── hrms_mcp.py
│   │   └── distributor_mcp.py
│   ├── graph/                  # LangGraph orchestration
│   │   └── pharmaiq_graph.py
│   ├── data/                   # Data management
│   │   ├── simulators/
│   │   │   ├── store_simulator.py
│   │   │   ├── cold_chain_simulator.py
│   │   │   ├── disease_simulator.py
│   │   │   └── inventory_simulator.py
│   │   └── seed_data.py
│   ├── database/               # Database managers
│   │   ├── sqlite_manager.py
│   │   └── chroma_manager.py
│   ├── rag/                    # Retrieval-Augmented Generation
│   │   └── knowledge_base.py
│   └── api/                    # FastAPI application
│       └── main.py
├── prompts/                    # Versioned prompts
│   ├── registry.py             # Central prompt loader
│   └── versions/
│       ├── soma/
│       │   ├── v1_0/
│       │   │   ├── system.txt
│       │   │   ├── cold_chain_analysis.txt
│       │   │   ├── staff_scheduling.txt
│       │   │   └── metadata.json
│       │   └── v1_1/
│       │       └── [enhanced prompts]
│       ├── soma_critique/v1_0/
│       ├── pulse/v1_0/
│       ├── pulse_critique/v1_0/
│       ├── planner/v1_0/
│       └── planner_critique/v1_0/
├── frontend/                   # React.js application
│   ├── public/
│   └── src/
│       ├── components/
│       │   ├── Dashboard/
│       │   │   ├── DashboardHome.jsx
│       │   │   ├── MetricCard.jsx
│       │   │   └── AlertFeed.jsx
│       │   ├── ColdChain/
│       │   │   ├── ColdChainMonitor.jsx
│       │   │   ├── FridgeGrid.jsx
│       │   │   └── TemperatureChart.jsx
│       │   ├── Epidemic/
│       │   │   ├── EpidemicRadar.jsx
│       │   │   ├── DiseaseMap.jsx
│       │   │   └── ForecastPanel.jsx
│       │   ├── Staffing/
│       │   │   ├── StaffScheduler.jsx
│       │   │   └── ComplianceStatus.jsx
│       │   ├── Inventory/
│       │   │   ├── ExpiryTracker.jsx
│       │   │   └── ProcurementOrders.jsx
│       │   ├── Audit/
│       │   │   ├── AuditLog.jsx
│       │   │   ├── DecisionTrace.jsx
│       │   │   └── CritiqueViewer.jsx
│       │   └── shared/
│       │       ├── Sidebar.jsx
│       │       ├── Header.jsx
│       │       └── StatusBadge.jsx
│       ├── pages/
│       │   ├── DashboardPage.jsx
│       │   ├── ColdChainPage.jsx
│       │   ├── EpidemicPage.jsx
│       │   ├── StaffingPage.jsx
│       │   ├── InventoryPage.jsx
│       │   └── AuditPage.jsx
│       ├── services/
│       │   ├── api.js
│       │   └── websocket.js
│       ├── store/
│       │   └── pharmaStore.js
│       ├── App.jsx
│       └── main.jsx
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Features

### Multi-Agent System

**SOMA Agent**
- Cold chain temperature monitoring and compliance
- Predictive maintenance for refrigeration units
- Staff scheduling with skill matching
- Operational risk identification

**PULSE Agent**
- Epidemic trend forecasting with confidence intervals
- Disease surveillance data analysis
- Pharmaceutical demand prediction
- Regional distribution optimization

**Planner Agent**
- Complex task decomposition
- Cross-domain reasoning and coordination
- Multi-objective planning
- Resource allocation optimization

**Critique Agents**
- Validate agent outputs for accuracy
- Identify gaps and risks
- Suggest improvements
- Rate decision quality

### Data Integration

- **Cold Chain MCP**: Real-time refrigeration monitoring
- **Disease Surveillance MCP**: Epidemic data integration
- **ERP MCP**: Inventory and financial data
- **HRMS MCP**: Staff management and scheduling
- **Distributor MCP**: Supply chain network management

### Database & Storage

- **SQLite**: Structured operational data
- **Chroma**: Vector embeddings for RAG
- **Redis**: Caching and real-time state

### Frontend Dashboard

- Real-time monitoring dashboards
- Cold chain visualization
- Epidemic radar and forecasting
- Staff scheduling interface
- Inventory management
- Comprehensive audit trails
- Decision trace visualization
- Critique feedback viewer

## 🛠️ Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- SQLite3
- Redis (optional)

### Backend Setup

1. Clone the repository:
```bash
cd PharmaIQ
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Initialize database:
```bash
python backend/database/sqlite_manager.py
```

6. Populate vector database:
```bash
python backend/data/seed_data.py
```

### Frontend Setup

1. Navigate to frontend:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure API endpoint:
```bash
cp .env.example .env.local
# Edit with your backend URL
```

## 🏃 Running the Application

### Start Backend API

```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173`

## 📊 Agent Configuration

Agents use versioned prompts managed by the PromptRegistry. Switch versions in `.env`:

```env
ACTIVE_PROMPT_VERSIONS=soma:v1_1,pulse:v1_0,planner:v1_0
```

### SOMA Versions

- **v1_0**: Basic cold chain and staff scheduling
- **v1_1**: Enhanced with predictive maintenance and skill matching

### PULSE Versions

- **v1_0**: Epidemic forecasting and demand adjustment

### Planner Versions

- **v1_0**: Task decomposition and cross-domain reasoning

## 🔄 Agent Workflow

```
User Request
    ↓
[Planner] → Decompose task
    ↓
[SOMA] → Analyze operations    [PULSE] → Forecast trends
    ↓                               ↓
[SOMA Critique] ←────────────────→ [PULSE Critique]
    ↓                               ↓
[Planner] → Orchestrate recommendations
    ↓
[Planner Critique] → Validate plan
    ↓
Execute & Monitor
```

## 📈 API Endpoints

### Agent Operations

```
POST /agents/soma/analyze          - Operational analysis
POST /agents/pulse/forecast        - Epidemic forecasting
POST /agents/planner/orchestrate   - Multi-domain planning
```

### Data Queries

```
GET  /data/cold-chain              - Cold chain status
GET  /data/diseases                - Disease surveillance
GET  /data/staff                   - Staff information
GET  /data/inventory               - Inventory levels
GET  /audit                        - Audit logs
```

### MCP Server Status

```
GET  /mcp/{server_name}/status     - Server health check
```

## 🔐 Security

- JWT authentication for API endpoints
- Environment-based configuration
- Audit logging for all decisions
- Role-based access control
- Data encryption for sensitive information

## 📝 License

This project is proprietary and confidential.

## 👥 Contributing

For contributions and bug reports, please contact the development team.

## 📞 Support

For support and questions, refer to the project documentation or contact the team.

---

**Version**: 1.0.0  
**Last Updated**: March 11, 2026
