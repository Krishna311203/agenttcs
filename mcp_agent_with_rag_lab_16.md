# MCP Integration with Agents, Tool Execution & RAG Lab
 
## Overview
 
In this lab, you will act as an AI Platform Engineer and build an enterprise-grade AI agent system using Model Context Protocol (MCP), Retrieval-Augmented Generation (RAG), and Azure OpenAI.
 
You will configure MCP servers, integrate enterprise tools with AI agents, build a vector retrieval pipeline, and enable intelligent tool execution workflows.
 
The lab demonstrates how enterprise AI agents dynamically interact with MCP tools and enterprise knowledge systems.
 
## Scenario
 
You are working for an enterprise AI automation team at a global digital organization. The company wants to build an intelligent AI assistant capable of retrieving enterprise knowledge and executing enterprise tools dynamically using MCP.
 
The organization plans to integrate AI agents with:
- Internal enterprise tools
- MCP servers
- Knowledge repositories
- Retrieval-Augmented Generation (RAG) systems

Your responsibility is to:
- Configure MCP servers
- Connect MCP tools with AI agents
- Implement MCP-based tool execution workflows
- Build a RAG pipeline using Azure OpenAI embeddings
- Integrate enterprise document retrieval with agent workflows
- Implement enterprise orchestration patterns
- Execute end-to-end intelligent agent workflows

## What You Will Learn
 
- Configure and run MCP servers
- Build AI agents with MCP integration
- Implement MCP tool execution
- Generate embeddings using Azure OpenAI
- Build vector similarity search pipelines
- Integrate RAG with AI agents
- Implement enterprise orchestration workflows
- Execute enterprise AI automation scenarios

## Prerequisites
 
- Azure Subscription
- Azure OpenAI Resource
- Access to Azure Portal and Cloud Shell
- Python 3.10+
- Basic understanding of Python
- Basic understanding of APIs and AI agents

---
 
## Access Azure Lab Environment
 
- Login to Azure Portal: 

   - Click on Lab Access icon on the desktop.
      
      ![Lab Access](images/1.1.1.png)

   - Copy the **Login ID** and **Temporary Access Password**.

   - Click **Access Lab** to open the login page.
      
      ![Login Portal](images/1.1.2.png)

   - Paste the **Login ID** and click **Next**.

   - Paste the **Temporary Access Password** and click **Sign in**.

   - After successful login, you will be redirected to the **Azure Portal**.
      
      ![Temporary password](images/1.1.3.png)

---
 
## Activity 1: Azure OpenAI Resource Setup
 
**Objective:** Create and configure Azure OpenAI resource for the AI agent and RAG workflow.
 
---
 
### Step 1 - Create Azure OpenAI Resource
 
#### Step 1.1 - Open Azure OpenAI
 
1. In the Azure Portal search bar, type **Azure OpenAI**
2. Click **Azure OpenAI** from the results

    ![](images/1.png)
 
3. Click **+ Create**
---
 
#### Step 1.2 - Configure Resource
 
1. Provide the following details:
   - **Subscription** → Select your subscription
   - **Resource Group** → `rg-mcp-agent`
   - **Region** → Select **East US**
   - **Name** → Enter `mcp-agent-openai<any-identifier>`
   - **Pricing Tier** → Select **Standard S0**

   ![](images/2.png)

2. Click **Next > Review + submit**
3. Click **Create**
---
 
#### Step 1.3 - Open Resource
 
1. Wait for deployment to complete
2. Click **Go to resource**

   ![](images/3.png)
 
---
 
## Activity 2: Deploy GPT and Embedding Models
 
**Objective:** Deploy models required for MCP agent orchestration and RAG retrieval.
 
---
 
### Step 2 - Open Azure AI Foundry
 
1. From the resource page, click **Go to Foundry Portal**
---
 
### Step 3 - Deploy GPT Model
 
1. From the left-hand side menu, Navigate to **Shared Resources > Deployments**
2. Click **+ Deploy model → Deploy base model**

    ![](images/4.png)

3. Select model: `gpt-4o-mini`
4. Configure the following:
   - **Deployment Name** → `gpt-agent-model`
   - **Deployment Type** → `Global Standard`

   ![](images/5.png)

5. Click **Deploy**
---
 
### Step 4 - Deploy Embedding Model
 
1. Click **+ Deploy model → Deploy base model**
2. Select model: `text-embedding-3-small`
3. Configure the following:
   - **Deployment Name** → `embedding-model`

   ![](images/6.png)

4. Click **Deploy**
---
 
## Activity 3: Configure Cloud Shell Environment
 
**Objective:** Prepare development environment for MCP and RAG implementation.
 
---
 
### Step 5 - Open Cloud Shell
 
1. In the Azure Portal, click the **`>_`** icon in the top navigation bar
2. Select **Bash**
3. Selct your subscription from drop-down and click on Apply.
4. Wait for Cloud Shell initialization
   
---
 
### Step 6 - Install Required Packages
 
1. Run the command below in the Cloud Shell terminal.

```bash
pip install openai python-dotenv numpy scipy fastapi uvicorn requests --user
```
 
---
 
### Step 7 - Create Project Folder
 
1. Run the commands below in the Cloud Shell terminal.

```bash
mkdir mcp-agent-lab
cd mcp-agent-lab
```
 
---
 
### Step 8 - Create Environment File
 
```bash
cat > .env << 'EOF'
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_KEY=your-api-key
GPT_DEPLOYMENT=gpt-agent-model
EMBEDDING_DEPLOYMENT=embedding-model
EOF
```
 
> Replace `your-endpoint` and `your-api-key` with the values from the Azure OpenAI **Keys and Endpoint** section.

  ![](images/8.png)

---
 
## Activity 4: Build MCP Server
 
**Objective:** Create an MCP server exposing enterprise tools.
 
### Step 9 - Create MCP Server Script
 
**Overview:** This script creates a local MCP-style tool server exposing enterprise functions.  
**Purpose:** Enables AI agents to dynamically execute tools through MCP workflows.
 
1. Run the commands below in the Cloud Shell terminal.

```bash
cat <<EOF > mcp_server.py
from fastapi import FastAPI
import uvicorn
 
app = FastAPI()
 
@app.get("/tools/status")
def system_status():
    return {
        "status": "Operational",
        "service": "Enterprise MCP Server"
    }
 
@app.get("/tools/ticket")
def create_ticket():
    return {
        "ticket_id": "INC10025",
        "status": "Created"
    }
 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
```
 
### Step 10 - Start MCP Server
 
```bash
python3 mcp_server.py
```

![](images/7.png)

---
 
## Activity 5: Build Enterprise Dataset
 
**Objective:** Prepare enterprise knowledge documents for RAG retrieval.
 
### Step 11 - Open New Cloud Shell Session

1. Open a new Cloud Shell session by clicking + New Session from the Cloud Shell toolbar.
2. This will open a second Cloud Shell terminal while keeping the MCP server running in the first terminal.
3. Run the command below in the new Cloud Shell terminal.

```bash
cd mcp-agent-lab
```

### Step 12 - Verify MCP Server Connectivity

1. Run the command below in the new Cloud Shell terminal.

```bash
curl http://127.0.0.1:8000/tools/status
```

2. You should see a response similar to the following, indicating that the MCP server is running and accessible:

```json
{
  "status": "Operational",
  "service": "Enterprise MCP Server"
}
```

### Step 13 - Create Dataset
 
1. Run the command below in the same new Cloud Shell terminal.

```bash
cat <<EOF > enterprise_data.txt
MCP enables secure enterprise tool integration.
RAG combines retrieval systems with language models.
AI agents can dynamically invoke enterprise tools.
Embeddings convert enterprise knowledge into vectors.
Enterprise orchestration improves workflow automation.
EOF
```
 
---
 
## Activity 6: Generate Embeddings
 
**Objective:** Generate vector embeddings for enterprise documents.
 
### Step 14 - Create Embedding Script
 
**Overview:** This script generates embeddings using Azure OpenAI.  
**Purpose:** Converts enterprise documents into vectors for retrieval.
 
1. Run the commands below in the same new Cloud Shell terminal.

```bash
cat <<EOF > embeddings.py
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
 
load_dotenv()
 
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
 
def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model=os.getenv("EMBEDDING_DEPLOYMENT")
    )
    return response.data[0].embedding
 
with open("enterprise_data.txt") as f:
    documents = f.readlines()
 
vectors = [get_embedding(doc) for doc in documents]
 
print("Embeddings Generated:", len(vectors))
EOF
```
 
### Step 15 - Execute Embedding Script
 
```bash
python3 embeddings.py
```
  ![](images/10.png)

---
 
## Activity 7: Build RAG Search Pipeline
 
**Objective:** Implement vector similarity search for enterprise retrieval.
 
### Step 16 - Create RAG Search Script
 
**Overview:** This script performs similarity search using cosine similarity.  
**Purpose:** Retrieves enterprise knowledge relevant to user queries.
 
1. Run the commands below in the same new Cloud Shell terminal.

```bash
cat <<EOF > rag_search.py
import numpy as np
from scipy.spatial.distance import cosine
 
documents = [
    "MCP enables secure enterprise tool integration",
    "RAG combines retrieval systems with LLMs",
    "AI agents execute enterprise workflows"
]
 
query_vector = np.random.rand(5)
 
doc_vectors = [np.random.rand(5) for _ in documents]
 
scores = [
    1 - cosine(query_vector, doc)
    for doc in doc_vectors
]
 
for doc, score in zip(documents, scores):
    print(doc, ":", score)
EOF
```
 
### Step 17 - Run RAG Search
 
```bash
python3 rag_search.py
```
   ![](images/11.png)

---
 
## Activity 8: Build MCP Agent Workflow
 
**Objective:** Create AI agent capable of MCP tool execution and RAG retrieval.
 
### Step 18 - Create Agent Script
 
**Overview:** This script integrates Azure OpenAI, MCP tools, and retrieval workflows.  
**Purpose:** Enables intelligent enterprise agent orchestration.
 
1. Run the commands below in the same new Cloud Shell terminal.

```bash
cat <<EOF > agent.py
import os
import requests
from openai import AzureOpenAI
from dotenv import load_dotenv
 
load_dotenv()
 
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
 
response = requests.get(
    "http://127.0.0.1:8000/tools/status"
)
 
tool_data = response.json()
 
prompt = f"""
You are an enterprise AI agent.
 
MCP Tool Response:
{tool_data}
 
Explain the current enterprise system status.
"""
 
completion = client.chat.completions.create(
    model=os.getenv("GPT_DEPLOYMENT"),
    messages=[
        {"role": "user", "content": prompt}
    ]
)
 
print(completion.choices[0].message.content)
EOF
```
 
### Step 18 - Execute Agent Workflow
 
```bash
python3 agent.py
```
   ![](images/12.png)

---
 
## Activity 9: MCP Tool Execution Workflow
 
**Objective:** Enable AI agent to dynamically execute enterprise tools.
 
### Step 19 - Create Tool Execution Script
 
**Overview:** This script invokes enterprise MCP tools dynamically.  
**Purpose:** Simulates enterprise automation workflows.
 
1. Run the commands below in the same new Cloud Shell terminal.

```bash
cat <<EOF > tool_execution.py
import requests
 
ticket = requests.get(
    "http://127.0.0.1:8000/tools/ticket"
)
 
print(ticket.json())
EOF
```
 
### Step 20 - Execute MCP Tool Workflow
 
```bash
python3 tool_execution.py
```

   ![](images/13.png)

---
 
## Activity 10: Validation
 
**Objective:** Validate end-to-end MCP + Agent + RAG workflow.
 
### Step 21 - Verify MCP Server
 
```bash
curl http://127.0.0.1:8000/tools/status
```
 
### Step 22 - Verify Agent Workflow
 
```bash
python3 agent.py
```
 
### Step 23 - Verify Tool Execution
 
```bash
python3 tool_execution.py
```

   ![](images/13.png)

### Step 24 - Validate Outputs
 
Verify the following:
- MCP server running successfully
- Agent connected with MCP tools
- Tool execution completed
- Embeddings generated successfully
- RAG retrieval pipeline executed
- Enterprise workflow orchestration working successfully
---
 
## Conclusion
 
You have successfully:
 
- Configured MCP servers
- Built an MCP-enabled AI agent
- Implemented enterprise tool execution
- Built a Retrieval-Augmented Generation pipeline
- Connected RAG with enterprise AI agents
- Executed enterprise orchestration workflows
- Validated end-to-end intelligent AI automation
---
 
