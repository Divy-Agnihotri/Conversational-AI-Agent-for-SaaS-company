# AI Agent with Classification, RAG, and Lead Capture

## Overview

This project implements an intelligent conversational agent using a graph-based orchestration approach. The agent processes user input, classifies intent, retrieves relevant information using Retrieval-Augmented Generation (RAG), and captures high-intent leads through a structured validation flow.

The system is designed to simulate a lightweight sales/support assistant capable of:

* Handling greetings
* Answering product and pricing queries
* Detecting high-intent users
* Capturing and validating lead information
* Maintaining short conversational memory

---

## Features

* **Intent Classification** into four categories:

  * `casual_greeting`
  * `product_or_pricing_inquiry`
  * `high_intent_lead`
  * `other`

* **RAG-based Question Answering**

  * Uses FAISS vector store with HuggingFace embeddings
  * Retrieves relevant product and policy data from a JSON source

* **Lead Capture Flow**

  * Prompts users for Name, Email, and Platform
  * Validates structured input via LLM
  * Simulates API call for storing lead data

* **Stateful Conversations**

  * Maintains last 6 turns of conversation history
  * Enables context-aware responses

* **Graph-based Control Flow**

  * Built using LangGraph for modular and scalable orchestration

* **Modern Chat UI (Streamlit Frontend)**

  * ChatGPT-style interface
  * Session-based state management
  * Real-time interaction with backend agent

---

## Project Structure

```
.
├── main.py / backend.py  # Core application logic
├── frontend.py           # Streamlit UI
├── data.json             # Product plans and policies
├── README.md             # Project documentation
```

---

## How to Run the Project Locally

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd <repo-name>
```

---

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # On Windows
```

---

### 3. Install Dependencies

```bash
pip install langgraph langchain-community faiss-cpu sentence-transformers google-generativeai streamlit
```

---

### 4. Set API Key

```bash
set GEMINI_API_KEY=your_api_key_here   # Windows (PowerShell)
```

---

### 5. Prepare Data

Ensure a `data.json` file exists:

```json
{
  "plans": [
    {
      "name": "Pro Plan",
      "price": "$10",
      "features": ["Feature A", "Feature B"]
    }
  ],
  "policies": {
    "refund": "30-day refund policy"
  }
}
```

---

## ▶️ Running the Project

### Option 1: Run via CLI (Basic)

```bash
python main.py
```

This uses a terminal-based interaction loop.

---

### Option 2: Run with Frontend (Recommended)

To use the modern chat UI, you need to replace the CLI loop with a callable backend function.

---

### 🔧 Step 1: Replace CLI Loop

Remove the `while True` loop from your backend and add this function:

```python
def chat_with_bot(state, user_input):
    state["user_input"] = user_input
    state = graph.invoke(state)
    return state, state["answer"]
```

Also add an initializer:

```python
def initialize_state():
    return {
        "user_input": "",
        "category": "",
        "answer": "",
        "history": [],
        "awaiting_lead_info": False,
        "lead_data": ""
    }
```

---

### 🎨 Step 2: Frontend Code (Streamlit)

Download the file named `frontend.py`from the repo

---

### 🚀 Step 3: Run the Frontend

Open PowerShell in the project folder and run:

```bash
streamlit run frontend.py
```

This will launch a browser-based chat interface.

---

## Architecture Overview

This project uses **LangGraph** to build a **stateful, non-linear conversational workflow**.

Unlike traditional linear pipelines, LangGraph allows the system to:

* Dynamically route execution between different nodes
* Maintain shared state across multiple turns
* Handle conditional flows (e.g., lead capture loop)

The entire agent is structured as a graph where each step is a node, and transitions are decided at runtime based on user input and system state.

---
![Flowchart](https://github.com/Divy-Agnihotri/Conversational-AI-Agent-for-SaaS-company/blob/main/Complete%20System%20Flow%20(StateGraph).png)

### Core Functions & Nodes

#### 1. **Classifier Node**

* **Function:** `classify_input`
* Classifies user input into:

  * greeting
  * product/pricing inquiry
  * high-intent lead
  * other

---

#### 2. **Router**

* **Function:** `route`
* Routes execution based on:

  * `category` (intent)
  * `awaiting_lead_info` (state flag override)

---

#### 3. **RAG Pipeline**

* **Functions:** `product_node` → `rag_answer`
* Retrieves data via FAISS + embeddings
* Generates answers using LLM + conversation history

---

#### 4. **Lead Capture Flow**

**a. Lead Trigger**

* **Function:** `lead_node`
* Activates on high-intent input
* Sets `awaiting_lead_info = True`
* Prompts for Name, Email, Platform

**b. Lead Validation**

* **Function:** `validate_lead_node`
* Extracts and validates structured input
* If valid → stores lead (`mock_lead_capture`)
* If invalid → exits lead flow and re-routes

---

#### 5. **Other Nodes**

* `greeting_node` → handles greetings
* `other_node` → fallback responses

---

#### 6. **State & Memory**

* **Function:** `update_history`
* Stores last 6 conversation turns
* Enables context-aware responses

---

### Session Management

* Each user interaction is tied to a **persistent `GraphState`**
* In the frontend (Streamlit):

  * Stored using `st.session_state`
* In production (e.g., WhatsApp):

  * Stored per user (phone number) using:

    * Redis / Database / in-memory store

This ensures:

* Multi-turn conversations
* Lead flow continuity
* Context retention across messages

---

### WhatsApp Webhook Integration

To deploy this agent on WhatsApp:

1. Webhook receives incoming message
2. Identify user via phone number
3. Load or initialize that user’s `GraphState`
4. Invoke agent:

```python
state["user_input"] = incoming_message
state = graph.invoke(state)
```

5. Send back:

```python
state["answer"]
```

6. Save updated state for future messages

---


This design allows the agent to seamlessly switch between **Q&A mode and lead capture mode**, while maintaining context across sessions and platforms.


## Future Improvements

* Replace mock lead capture with real CRM integration
* Add streaming responses for better UX
* Improve validation with structured parsers instead of LLM
* Expand knowledge base and improve retrieval quality
* Add authentication and analytics
