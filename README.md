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

---

## Project Structure

```
.
├── main.py              # Core application logic
├── data.json            # Product plans and policies
├── README.md            # Project documentation
```

---

## How to Run the Project Locally

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd <repo-name>
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install langgraph langchain-community faiss-cpu sentence-transformers google-generativeai
```

### 4. Set API Key

Update the API key in your script or export it as an environment variable:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 5. Prepare Data

Ensure a `data.json` file exists with the following structure:

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

### 6. Run the Application

```bash
python main.py
```

You can now interact with the agent via the terminal.

---

## Architecture Explanation

This project uses LangGraph to define a stateful, node-based workflow for the AI agent. LangGraph was chosen because it provides explicit control over conversational flow, making it ideal for multi-step interactions like classification, retrieval, and lead capture. Unlike linear pipelines, LangGraph allows conditional routing and state persistence across nodes, which is essential for handling branching logic and multi-turn conversations.

The system revolves around a shared `GraphState`, which carries all relevant data through the pipeline. This includes the user input, detected category, generated response, conversation history, and flags such as `awaiting_lead_info`. Each node reads and updates this state, ensuring continuity and context awareness.

The flow begins with a classifier node that determines user intent using a language model. Based on this classification, the router directs execution to the appropriate node. For product-related queries, a RAG pipeline retrieves relevant information from a FAISS vector store and generates a contextual response. For high-intent users, the system transitions into a lead capture flow, where structured user data is requested and validated. If validation fails, the input is re-routed back into the classification loop.

Conversation history is maintained as a rolling window of the last six turns, enabling the agent to provide contextually relevant responses without excessive memory overhead.

---

## WhatsApp Deployment (Using Webhooks)

To integrate this agent with WhatsApp, you would typically use the WhatsApp Business API (or a provider like Twilio).

### Steps:

1. **Set Up WhatsApp API**

   * Register for WhatsApp Business API access
   * Configure a webhook URL for incoming messages

2. **Create a Web Server**

   * Use a framework like Flask or FastAPI
   * Expose an endpoint (e.g., `/webhook`) to receive POST requests

3. **Handle Incoming Messages**

   * Extract the user message from the webhook payload
   * Maintain a session store (e.g., Redis or in-memory dict) keyed by user phone number
   * Retrieve or initialize the user's `GraphState`

4. **Invoke the Agent**

   ```python
   state["user_input"] = incoming_message
   updated_state = graph.invoke(state)
   ```

5. **Send Response Back**

   * Use WhatsApp API to send `updated_state["answer"]` back to the user

6. **Persist State**

   * Store updated state for future interactions

### Key Considerations:

* **Session Management:** Each phone number should map to its own state
* **Scalability:** Use a database or cache instead of in-memory storage
* **Validation:** Sanitize and validate incoming webhook data
* **Latency:** Optimize LLM calls for faster response times

This webhook-based architecture allows real-time, bidirectional communication between WhatsApp users and your AI agent.

---

## Future Improvements

* Replace mock lead capture with real CRM integration
* Add streaming responses for better UX
* Improve validation with structured parsers instead of LLM
* Expand knowledge base and improve retrieval quality
* Add authentication and analytics

---
