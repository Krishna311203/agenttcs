# Title: Azure Multi-Agent Orchestration with Azure OpenAI Lab

## Overview

In this lab, you will act as an AI Engineer and build an AI-powered multi-agent orchestration service using Azure OpenAI.

The solution will:

- Accept user requests for operations such as report generation, document summarization, key insight extraction, and validation
- Use an Orchestrator Agent to decompose complex user input into smaller, manageable tasks
- Use multiple specialized Worker Agents (e.g., summarization, analysis, validation) powered only by Azure OpenAI
- Coordinate structured execution of tasks through the orchestrator to ensure ordered, reliable processing
- Store intermediate and final results in a shared memory/state store so agents can collaborate
- Aggregate worker outputs into a coherent final response that is returned to the user

## Project Objectives

By completing this project, you will:

- Design and configure a simple multi-agent orchestration API
- Create and configure an Azure OpenAI resource and chat model deployment
- Implement an Orchestrator Agent that breaks down user requests into tasks and coordinates their execution
- Implement Worker Agents that call Azure OpenAI for summarization, insight extraction, and validation
- Implement a shared memory/state component for cross-agent collaboration
- Build and validate an end-to-end multi-agent pipeline that overcomes single-agent limitations

## Prerequisites

- Azure Subscription
- Access to:
  - Azure Portal
  - Azure OpenAI
  - Linux sandbox environment (pre-provisioned lab VM) with Python
- Basic knowledge of:
  - Python
  - REST APIs
  - JSON data

## What You Will Learn

- Create Azure OpenAI resource  
- Deploy a chat model in Azure OpenAI for use by all agents  
- Design a simple multi-agent orchestration pattern with an orchestrator and worker agents  
- Implement an Orchestrator Agent and Worker Agents in Python using Azure OpenAI only  
- Use shared memory/state to enable collaboration between multiple specialized agents  
- Build a REST API that exposes multi-agent orchestration capabilities  

## Difficulty Level

Practitioner

## How to Login to Azure

1. Copy the **Login ID** and **Temporary Access Password** from the Lab Details page and click **Access Lab**.
   
   ![Lab Details Page](images/1.1.1.png)

2. Paste your **Login ID** and click **Next**.
   
   ![Microsoft Sign-in Page](images/1.1.2.png)

3. Paste your **Temporary Access Password** and click **Sign in**.
   
   ![Password Entry Page](images/1.1.3.png)

4. You will be logged into the Azure Portal and ready to start the lab.

## Activity 1: Azure OpenAI Resource and Model Setup

### Step 1: Navigate to Azure OpenAI

1. In the Azure Portal search bar, type **Azure OpenAI**
2. Select **Azure OpenAI** from the results  
   ![](images/2.png)
3. Click **+ Create → Azure OpenAI**  
   ![](images/3.png)

### Step 2: Configure Azure OpenAI Resource

1. Enter details:
   - **Resource Group:** `multiagent-rg`
   - **Name:** `multiagent-openai<unique>`
   - **Region:** `East US`
   - **Pricing Tier:** `Standard S0`
2. Click **Review + Create → Create**

   ![](images/4.png)

### Step 3: Go to Resource

1. Wait for deployment to complete  
   ![](images/5.png)
2. Click **Go to Resource**

### Step 4: Open Foundry Portal

1. Go to the created Azure OpenAI resource
2. Click **Go to Foundry Portal**  
   ![](images/6.png)

### Step 5: Deploy Chat Model

1. Navigate to **Deployments**
2. Click **Create Deployment → Base Deployment**  
   ![](images/7.png)
3. Configure:
   - **Model:** `gpt-4o-mini`  
   - **Deployment Name:** `multiagent-chat-model`  
     ![](images/8.png)
4. Click **Deploy**

### Step 6: Get API Details

1. In the Azure OpenAI resource, go to **Keys and Endpoint**
2. Copy:
   - Endpoint URL
   - API Key  
     ![](images/9.png)

You will use these values in your Python application.

## Activity 2: Setup Python Environment on Lab VM

In this Activity, you will use the **Linux VM lab (sandbox) environment**

### Step 1: Verify Python Installation

1. Open terminal emulator app on desktop.
Run:

```bash
python3 --version
```

You should see a Python 3.x version. If multiple versions are installed, you will still use `python3` in this lab.

### Step 2: Install Dependencies

Run the following commands one by one in the sandbox terminal:
> Use **Right Click** and select the paste option to paste copied code or content.

```bash
sudo apt update -y
```

### Step 3: Create Virtual Environment

```bash
python3 -m venv myenv
```
```bash
source myenv/bin/activate
```
```bash
pip install fastapi uvicorn[standard] sqlalchemy aiosqlite openai
```
![](images/10.png)
> ⚠️ You should see **(myenv)** at the start of your terminal. Always activate the virtual environment before running the app:
> ```bash
> source myenv/bin/activate
> ```

## Activity 3: Configure Azure OpenAI Client

In this activity, you will create a simple Python module that wraps Azure OpenAI and is shared by all agents (orchestrator and workers). You will use only Azure OpenAI as the LLM provider.

### Step 1: Create `azure_openai_client.py`

```bash
cat > azure_openai_client.py << 'EOF'
import os
from openai import AzureOpenAI

AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT", "<YOUR-AOAI-ENDPOINT>")
AOAI_KEY = os.getenv("AOAI_KEY", "<YOUR-AOAI-KEY>")
AOAI_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT", "multiagent-chat-model")

client = AzureOpenAI(
    api_version="2025-01-01-preview",
    azure_endpoint=AOAI_ENDPOINT,
    api_key=AOAI_KEY,
)

def chat_completion(system_prompt: str, user_content: str, max_tokens: int = 400) -> str:
    response = client.chat.completions.create(
        model=AOAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        max_completion_tokens=max_tokens
    )
    return response.choices[0].message.content
EOF
```

### Step 2: Update Endpoint, Key, and Deployment

```bash
nano azure_openai_client.py
```

Replace the following lines:

```python
AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT", "<YOUR-AOAI-ENDPOINT>")
AOAI_KEY = os.getenv("AOAI_KEY", "<YOUR-AOAI-KEY>")
AOAI_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT", "multiagent-chat-model")
```

Then save: **Ctrl+X → Y → Enter**

> Important: This module must be the only place where you call an LLM. Do not integrate any non-Azure providers.

## Activity 4: Define Entities, Database & Persistence

In this activity, you will define the entities that represent orchestration jobs, tasks, and shared memory, and configure persistence using SQLite and SQLAlchemy.

### Step 1: Create `models.py`

```bash
cat > models.py << 'EOF'
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class OrchestrationJob(Base):
    __tablename__ = "orchestration_jobs"

    id = Column(String, primary_key=True)
    userRequest = Column(Text, nullable=False)
    inputDocument = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="PENDING")
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finalResult = Column(JSON, nullable=True)

    tasks = relationship("AgentTask", back_populates="job", cascade="all, delete-orphan")

class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("orchestration_jobs.id"), nullable=False)
    type = Column(String, nullable=False)  # SUMMARIZATION, INSIGHTS, VALIDATION
    status = Column(String, nullable=False, default="PENDING")
    inputPayload = Column(JSON, nullable=True)
    outputPayload = Column(JSON, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("OrchestrationJob", back_populates="tasks")

class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("orchestration_jobs.id"), nullable=False)
    task_id = Column(String, ForeignKey("agent_tasks.id"), nullable=False)
    agent_type = Column(String, nullable=False)  # ORCHESTRATOR, SUMMARIZER, ANALYST, VALIDATOR
    task_type = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    is_valid = Column(Boolean, nullable=True)
    meta_data = Column(JSON, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

class Config(Base):
    __tablename__ = "config"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    provider = Column(String, nullable=False, default="azure-openai")
EOF
```

### Step 2: Create Database Initialization Script

```bash
cat > db.py << 'EOF'
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = "sqlite+aiosqlite:///./multiagent.db"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
EOF
```

## Activity 5: Build Orchestrator and Worker Agents

In this activity, you will create Python modules that implement the Orchestrator Agent and specialized Worker Agents. All agents will use the shared Azure OpenAI client.

### Step 1: Create `workers.py`

```bash
cat > workers.py << 'EOF'
import uuid
from azure_openai_client import chat_completion
from models import AgentTask, AgentMemory

SUMMARIZER_SYSTEM_PROMPT = (
    "You are a summarization agent. Produce a concise, factual summary of the provided document text. "
    "Do not add information that is not present in the text."
)

INSIGHTS_SYSTEM_PROMPT = (
    "You are an analysis agent. Extract 3-5 key insights from the provided document text. "
    "Return them as bullet points."
)

VALIDATOR_SYSTEM_PROMPT = (
    "You are a validation agent. Based ONLY on the provided document text, answer the validation question "
    "with a JSON object: {\"is_valid\": true/false, \"reason\": \"short explanation\"}."
)

async def run_summarization_task(session, job, task: AgentTask, document_text: str):
    user_content = f"Document text:\n{document_text}"
    summary = chat_completion(SUMMARIZER_SYSTEM_PROMPT, user_content, max_tokens=300)

    task.outputPayload = {"summary": summary}
    task.status = "COMPLETED"

    memory = AgentMemory(
        id=str(uuid.uuid4()),
        job_id=job.id,
        task_id=task.id,
        agent_type="SUMMARIZER",
        task_type="SUMMARIZATION",
        content=summary,
        metadata={"length": len(summary)}
    )
    session.add(memory)

async def run_insights_task(session, job, task: AgentTask, document_text: str):
    user_content = f"Document text:\n{document_text}"
    insights = chat_completion(INSIGHTS_SYSTEM_PROMPT, user_content, max_tokens=300)

    task.outputPayload = {"insights": insights}
    task.status = "COMPLETED"

    memory = AgentMemory(
        id=str(uuid.uuid4()),
        job_id=job.id,
        task_id=task.id,
        agent_type="ANALYST",
        task_type="INSIGHTS",
        content=insights
    )
    session.add(memory)

async def run_validation_task(session, job, task: AgentTask, document_text: str, validation_question: str):
    user_content = f"Document text:\n{document_text}\n\nValidation question: {validation_question}"
    result = chat_completion(VALIDATOR_SYSTEM_PROMPT, user_content, max_tokens=200)

    task.outputPayload = {"validation": result}
    task.status = "COMPLETED"

    memory = AgentMemory(
        id=str(uuid.uuid4()),
        job_id=job.id,
        task_id=task.id,
        agent_type="VALIDATOR",
        task_type="VALIDATION",
        content=result
    )
    session.add(memory)
EOF
```

### Step 2: Create `orchestrator.py`

```bash
cat > orchestrator.py << 'EOF'
import uuid
import asyncio
import httpx
import json
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import selectinload  # Added for Eager Loading
from sqlalchemy.ext.asyncio import AsyncSession
from azure_openai_client import chat_completion
from models import OrchestrationJob, AgentTask, AgentMemory
from workers import run_summarization_task, run_insights_task, run_validation_task

ORCHESTRATOR_SYSTEM_PROMPT = (
    "You are an orchestrator agent. Given a user request, decide which of the following task types are needed: "
    "SUMMARIZATION, INSIGHTS, VALIDATION. Return a JSON array of task objects with fields: "
    "{\"type\": \"SUMMARIZATION|INSIGHTS|VALIDATION\", \"validationQuestion\": \"...\" (only for VALIDATION)}. "
    "Do not include any other text."
)

async def fetch_document_text(url: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text

async def decompose_request(user_request: str) -> List[dict]:
    user_content = f"User request: {user_request}"
    raw = chat_completion(ORCHESTRATOR_SYSTEM_PROMPT, user_content, max_tokens=300)
    try:
        tasks = json.loads(raw)
        if not isinstance(tasks, list):
            return []
        return tasks
    except Exception:
        return []

async def create_job_with_tasks(session: AsyncSession, user_request: str, input_document: str | None, options: dict | None) -> OrchestrationJob:
    job = OrchestrationJob(
        id=str(uuid.uuid4()),
        userRequest=user_request,
        inputDocument=input_document,
        status="PENDING"
    )
    session.add(job)
    await session.flush()

    if options:
        task_specs = []
        if options.get("enableSummarization"):
            task_specs.append({"type": "SUMMARIZATION"})
        if options.get("enableInsights"):
            task_specs.append({"type": "INSIGHTS"})
        if options.get("enableValidation"):
            task_specs.append({"type": "VALIDATION", "validationQuestion": "Does the document mention GDPR compliance?"})
    else:
        task_specs = await decompose_request(user_request)
        if not task_specs:
            task_specs = [{"type": "SUMMARIZATION"}]

    for spec in task_specs:
        task = AgentTask(
            id=str(uuid.uuid4()),
            job_id=job.id,
            type=spec["type"],
            status="PENDING",
            inputPayload={"validationQuestion": spec.get("validationQuestion")}
        )
        session.add(task)

    orchestrator_memory = AgentMemory(
        id=str(uuid.uuid4()),
        job_id=job.id,
        task_id="ORCHESTRATOR",
        agent_type="ORCHESTRATOR",
        task_type="PLANNING",
        content=str(task_specs)
    )
    session.add(orchestrator_memory)

    return job

async def run_job(session: AsyncSession, job_id: str):
    # FIX: Use selectinload to eagerly load tasks and prevent greenlet errors
    stmt = (
        select(OrchestrationJob)
        .options(selectinload(OrchestrationJob.tasks))
        .where(OrchestrationJob.id == job_id)
    )
    
    result = await session.execute(stmt)
    job = result.scalar_one_or_none()
    
    if not job or job.status in ("CANCELLED", "COMPLETED", "FAILED"):
        return

    job.status = "RUNNING"
    await session.commit() # Commit status change to RUNNING immediately

    try:
        if job.inputDocument:
            document_text = await fetch_document_text(job.inputDocument)
        else:
            document_text = job.userRequest

        tasks = list(job.tasks)

        coros = []
        for task in tasks:
            task.status = "RUNNING"
            if task.type == "SUMMARIZATION":
                coros.append(run_summarization_task(session, job, task, document_text))
            elif task.type == "INSIGHTS":
                coros.append(run_insights_task(session, job, task, document_text))
            elif task.type == "VALIDATION":
                question = (task.inputPayload or {}).get("validationQuestion") or "Is the document valid?"
                coros.append(run_validation_task(session, job, task, document_text, question))

        if coros:
            await asyncio.gather(*coros)

        summary = None
        insights = None
        validation = None
        for task in tasks:
            if task.type == "SUMMARIZATION" and task.outputPayload:
                summary = task.outputPayload.get("summary")
            if task.type == "INSIGHTS" and task.outputPayload:
                insights = task.outputPayload.get("insights")
            if task.type == "VALIDATION" and task.outputPayload:
                validation = task.outputPayload.get("validation")

        job.finalResult = {
            "summary": summary,
            "insights": insights,
            "validation": validation
        }
        job.status = "COMPLETED"
        
    except Exception as e:
        print(f"Error executing job {job_id}: {e}")
        job.status = "FAILED"
    
    await session.commit()
EOF
```

This orchestrator:

- Decomposes the user request into tasks (either via explicit options or via Azure OpenAI)
- Creates specialized tasks for summarization, insights, and validation
- Coordinates execution of worker agents
- Aggregates outputs into a coherent `finalResult`

## Activity 6: Build FastAPI Application and REST Endpoints

In this activity, you will expose the multi-agent orchestration system via REST APIs.

### Step 1: Create `main.py`

```bash
cat > main.py << 'EOF'
import asyncio
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from db import AsyncSessionLocal, init_db
from models import OrchestrationJob, AgentTask, Config
from orchestrator import create_job_with_tasks, run_job

app = FastAPI(title="Azure OpenAI Multi-Agent Orchestration API")

# Enable CORS for browser-based testing (Swagger/REST clients)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobOptions(BaseModel):
    enableSummarization: Optional[bool] = False
    enableInsights: Optional[bool] = False
    enableValidation: Optional[bool] = False

class CreateJobRequest(BaseModel):
    userRequest: str = Field(..., min_length=5)
    inputDocument: Optional[str] = None
    options: Optional[JobOptions] = None

@app.on_event("startup")
async def on_startup():
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Config).where(Config.key == "llm_provider")
        )
        existing = result.scalar_one_or_none()
        if not existing:
            cfg = Config(
                key="llm_provider",
                value="azure-openai",
                provider="azure-openai"
            )
            session.add(cfg)
            await session.commit()

@app.post("/api/jobs", status_code=201)
async def create_job(payload: CreateJobRequest):
    async with AsyncSessionLocal() as session:
        job = await create_job_with_tasks(
            session,
            user_request=payload.userRequest,
            input_document=str(payload.inputDocument) if payload.inputDocument else None,
            options=payload.options.dict() if payload.options else None
        )
        await session.commit()
        
        # Refresh ensures tasks are loaded into the 'job' object before the session closes
        await session.refresh(job, ["tasks"])
        
        # Extract data for the response while inside the session context
        job_id = job.id
        job_status = job.status
        job_created = job.createdAt
        task_list = [{"id": t.id, "type": t.type, "status": t.status} for t in job.tasks]

    asyncio.create_task(run_job_background(job_id))
    
    return {
        "jobId": job_id,
        "status": job_status,
        "createdAt": job_created,
        "tasks": task_list
    }

async def run_job_background(job_id: str):
    async with AsyncSessionLocal() as session:
        await run_job(session, job_id)

@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None):
    async with AsyncSessionLocal() as session:
        stmt = select(OrchestrationJob)
        if status:
            stmt = stmt.where(OrchestrationJob.status == status)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        return {
            "items": [{"jobId": j.id, "status": j.status} for j in jobs],
            "total": len(jobs)
        }

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(OrchestrationJob)
            .options(selectinload(OrchestrationJob.tasks))
            .where(OrchestrationJob.id == job_id)
        )
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "jobId": job.id,
            "status": job.status,
            "userRequest": job.userRequest,
            "inputDocument": job.inputDocument,
            "tasks": [
                {
                    "id": t.id,
                    "type": t.type,
                    "status": t.status,
                    "output": t.outputPayload
                } for t in job.tasks
            ],
            "finalResult": job.finalResult
        }

@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OrchestrationJob).where(OrchestrationJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status in ("COMPLETED", "FAILED"):
            raise HTTPException(status_code=400, detail="Cannot cancel a completed or failed job")
        job.status = "CANCELLED"
        await session.commit()
        return {"jobId": job.id, "status": job.status}
EOF
```

### Step 2: Run the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

You should see the FastAPI application start without errors.

   ![](images/11.png)

## Activity 7: Test the API Endpoints

In this activity, you will validate that the multi-agent orchestration system works end-to-end and that the orchestrator coordinates specialized agents correctly.

### Step 1: Create a New Job (Happy Path)

Open a new instance of the terminal. Use `curl` or a REST client:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "userRequest": "Read this document and 1) summarize it, 2) extract three key insights, and 3) validate if it mentions GDPR compliance.",
    "inputDocument": "https://www.gutenberg.org/cache/epub/1/pg1.txt",
    "options": {
      "enableSummarization": true,
      "enableInsights": true,
      "enableValidation": true
    }
  }'
```

Verify:

- Response status is `201`
- Response contains `jobId`, `status`, and a non-empty `tasks` array
   
   ![](images/12.png)

### Step 2: Get Job Status and Final Result

After a few seconds, check the job:

```bash
curl http://localhost:8000/api/jobs/<JOB_ID_FROM_PREVIOUS_STEP>
```

   ![](images/13.png)

Verify:

- `status` eventually becomes `COMPLETED`
- `tasks` show `COMPLETED` for each worker
- `finalResult` contains:
  - `summary` (from summarization agent)
  - `insights` (from analysis agent)
  - `validation` (from validation agent)

### Step 3: Submit Job with Minimal Options

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "userRequest": "Generate a short summary of this document.",
    "inputDocument": "https://raw.githubusercontent.com/Azure/azure-sdk-for-python/main/sdk/identity/azure-identity/README.md"
  }'
```

   ![](images/14.png)

Verify:

- Job is created successfully
- At least one `SUMMARIZATION` task is created by the orchestrator

### Step 4: Validation Error on Missing User Request

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "userRequest": "",
    "inputDocument": "https://example.com/doc.txt"
  }'
```

Verify:

- FastAPI will return a `422 Unprocessable Entity` for an empty string, not a 400
- Response body contains an error message about `userRequest`

### Step 5: List Jobs with Status Filter

```bash
curl "http://localhost:8000/api/jobs?status=COMPLETED"
```

Verify:

- Response contains `items` and `total`
- Each item has `jobId` and `status`

### Step 6: Cancel an In-Progress Job

1. Create a job with a large document.
2. Immediately call:

```bash
curl -X DELETE http://localhost:8000/api/jobs/<JOB_ID>
```

Verify:

- Response shows `status` as `CANCELLED`
- Subsequent GET on the job shows `status` remains `CANCELLED`

## Summary

In this lab, you learned how to:

- Create and configure an Azure OpenAI resource and chat model deployment
- Design a multi-agent orchestration pattern that overcomes single-agent limitations
- Implement an Orchestrator Agent that decomposes complex user requests into smaller tasks
- Implement specialized Worker Agents (summarization, insights, validation) that collaborate via shared memory
- Use only Azure OpenAI as the LLM provider for all agents
- Build and test a REST API that coordinates multi-agent execution and returns a coherent final output
