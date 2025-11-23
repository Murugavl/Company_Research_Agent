# Company Research Assistant

An AI-powered assistant that researches companies, detects conflicting information, and generates structured account plans through natural conversation. Built with Streamlit, Gemini, and Tavily Search.

## Features

- **Automated Company Research** using Tavily + Gemini.
- **Conflict Detection** that flags inconsistent information and asks the user whether to dig deeper.
- **Structured Account Plan Generation** with sections such as:
  - Overview  
  - Products & Services  
  - Market Position  
  - Competitors  
  - Financial Snapshot  
  - Key Contacts  
  - Opportunities  
  - Risks  
  - Recommended Actions
- **Section-Level Updates** where the user can rewrite only the part they want.
- **Chat-Based Interaction** with professional, concise responses.

## How It Works (Workflow)

1. User asks about a company.  
2. The system normalizes the company name.  
3. Tavily fetches multi-source information.  
4. Gemini processes and summarizes the research.  
5. Conflict detection checks for inconsistent or uncertain data.  
6. If conflicts exist, the agent asks the user whether to dig deeper.  
7. Otherwise, a complete account plan is generated.  
8. User can modify any section with follow-up instructions.

## Project Structure
    app.py  
    agent/
    ├── agent_core.py
    ├── tools.py
    ├── account_plan.py
    └── logger.py
    requirements.txt
    Dockerfile
    docker-compose.yml
    .env
    README.md

## Installation

### 1. Clone the repository

    git clone https://github.com/Murugavl/Company_Research_Agent.git
    
    cd Company_Research_Agent

### 2. Create & Activate a Virtual Environment
Windows

    python -m venv venv
    venv\Scripts\activate
macOS/Linux

    python3 -m venv venv
    source venv/bin/activate

### 3. Install Dependencies
    pip install -r requirements.txt

### 4. Add Environment Variables
Create a .env file in the project root:

    GEMINI_API_KEY=your_gemini_api_key
    TAVILY_API_KEY=your_tavily_api_key

### 5. Run the application
    streamlit run app.py

**Open in browser:**
  
    http://localhost:8501/

## Docker Setup
#### Build image
    docker build -t research-agent .

#### Run container
    docker run -p 8501:8501 --env-file .env research-agent

#### Open in browser:
  
    http://localhost:8501/

## Usage Example

**User:** tell me about Eightfold AI  

**Assistant:** Provides an overview + structured summary.

**User:**  update its risks  

**Assistant:**  Returns only the updated *Risks* section.
