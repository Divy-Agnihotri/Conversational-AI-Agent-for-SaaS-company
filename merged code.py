import os
import json
from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from google import genai

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


# 🔑 Set API key
os.environ["GEMINI_API_KEY"] = "getyourown"

client = genai.Client()


# 🧾 State
class GraphState(TypedDict):
    user_input: str
    category: str
    answer: str
    history: List[str]

    awaiting_lead_info: bool   # 👈 key flag
    lead_data: str             # 👈 formatted string from LLM


# =========================
# 📦 LOAD & PREPARE DATA
# =========================

def load_docs_from_json(path: str):
    with open(path, "r") as f:
        data = json.load(f)

    docs = []

    # Plans → chunked
    for plan in data["plans"]:
        docs.append(f"{plan['name']} costs {plan['price']}")

        for feature in plan["features"]:
            docs.append(f"{plan['name']} includes {feature}")

    # Policies
    for key, value in data["policies"].items():
        docs.append(f"{key.capitalize()} policy: {value}")

    return docs


# Load data
docs = load_docs_from_json("data.json")

# 🧠 Embeddings + Vector Store
embedding_model = HuggingFaceEmbeddings()
vectorstore = FAISS.from_texts(docs, embedding_model)

# Retriever
retriever = vectorstore.as_retriever()


# =========================
# 🤖 CLASSIFIER NODE
# =========================

def classify_input(state: GraphState) -> GraphState:
    prompt = f"""
    Classify the user's input into ONE of these categories:

    1. casual_greeting → simple greetings or small talk  
       (e.g., "hi", "hello", "hey", "good morning")

    2. product_or_pricing_inquiry → user is asking about plans, features, pricing, or policies  
       (e.g., "what does the pro plan include?", "pricing?", "do you have refunds?")

    3. high_intent_lead → user shows strong intent to buy, sign up, or try  
       (e.g., "I want to buy", "I'll take the pro plan", "sign me up", "how do I start?",  
       "I want to try the Pro plan for my YouTube channel")

    4. other → anything not related to above categories

    RULES:
    - Return ONLY one of these exact labels:
      casual_greeting, product_or_pricing_inquiry, high_intent_lead, other
    - No explanation
    - Choose high_intent_lead ONLY if the user clearly shows decision or commitment

    Input: "{state['user_input']}"
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    category = response.text.strip().lower()

    return {
        **state,
        "category": category,
        "answer": ""
    }


# =========================
# 🔍 RAG FUNCTION
# =========================

def rag_answer(query: str, history: list) -> str:
    # Retrieve
    retrieved_docs = retriever.invoke(query)

    context = "\n".join([doc.page_content for doc in retrieved_docs])
    history_text = "\n".join(history[-6:])

    prompt = f"""
    You are a helpful assistant.

    Conversation History (last 6 turns):
    {history_text}

    Context:
    {context}

    Question:
    {query}

    Answer using BOTH context and conversation history.
    If unsure, say "I don't know".
    """

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    return response.text.strip()


# =========================
# 🔀 ROUTER
# =========================

def route(state: GraphState):

    if state.get("awaiting_lead_info"):
        return "validate_lead_node"

    if state["category"] == "casual_greeting":
        return "greeting_node"
    elif state["category"] == "product_or_pricing_inquiry":
        return "product_node"
    elif state["category"] == "high_intent_lead":
        return "lead_node"
    else:
        return "other_node"
    
# =========================
# 🔀 FUNCTIONS FOR LEAD NODE
# =========================
def validate_lead_node(state: GraphState):

    prompt = f"""
    Check if the following input contains:
    - name
    - email
    - platform

    If YES → return:
    name: <name>
    email id: <email>
    platform: <platform>

    If NO → return ONLY:
    NO

    Input:
    "{state['user_input']}"
    """

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    output = response.text.strip()

    if "email id:" in output.lower():
        mock_lead_capture(output)
        answer = "Thanks! Processing your details..."

        return {
            **state,
            "lead_data": output,
            "awaiting_lead_info": False,
            "answer": answer,
            "history": update_history(state, answer)  # 👈 FIX
        }

    # ❌ invalid input
    answer = "That doesn't look like valid details. I'll help you with your query instead."

    return {
        **state,
        "awaiting_lead_info": False,
        "category": "",
        "answer": answer,
        "history": update_history(state, answer)  # 👈 FIX
    }


def mock_lead_capture(data: str):
    print(f"✅ Lead captured: {data}")




# =========================
# 🧩 NODES
# =========================


def update_history(state: GraphState, answer: str):
    new_entry = f"User: {state['user_input']}\nAssistant: {answer}"

    history = state.get("history", [])
    history.append(new_entry)

    # keep only last 6 turns
    history = history[-6:]

    return history

def greeting_node(state: GraphState):
    answer = "Hello! How can I help you today?"

    return {
        **state,
        "answer": answer,
        "history": update_history(state, answer)
    }


def product_node(state: GraphState):
    answer = rag_answer(state["user_input"], state["history"])

    return {
        **state,
        "answer": answer,
        "history": update_history(state, answer)
    }

def lead_node(state: GraphState):
    answer = "Great! Please provide your Name, Email ID, and Platform (e.g., YouTube, Instagram)."

    return {
        **state,
        "awaiting_lead_info": True,
        "answer": answer,
        "history": update_history(state, answer)  # 👈 FIX
    }

def other_node(state: GraphState):
    answer = "I can help with plan details, pricing, and policies. Try asking about those!"

    return {
        **state,
        "answer": answer,
        "history": update_history(state, answer)
    }



# =========================
# 🏗️ GRAPH
# =========================

builder = StateGraph(GraphState)

builder.add_node("classifier", classify_input)
builder.add_node("greeting_node", greeting_node)
builder.add_node("product_node", product_node)
builder.add_node("lead_node", lead_node)
builder.add_node("validate_lead_node", validate_lead_node)
builder.add_node("other_node", other_node)


builder.set_entry_point("classifier")

builder.add_conditional_edges(
    "classifier",
    route,
    {
        "greeting_node": "greeting_node",
        "product_node": "product_node",
        "lead_node": "lead_node",
        "validate_lead_node": "validate_lead_node",
        "other_node": "other_node",
    },
)

builder.add_edge("greeting_node", END)
builder.add_edge("product_node", END)
builder.add_edge("lead_node", END)
builder.add_conditional_edges(
    "validate_lead_node",
    lambda state: "classifier" if not state.get("awaiting_lead_info") and state.get("category") == "" else END,
    {
        "classifier": "classifier",
        END: END
    }
)
builder.add_edge("other_node", END)

graph = builder.compile()


# =========================
# 🚀 RUN
# =========================

if __name__ == "__main__":

    # 👇 INITIALIZE STATE ONCE (VERY IMPORTANT)
    state = {
        "user_input": "",
        "category": "",
        "answer": "",
        "history": [],
        "awaiting_lead_info": False,
        "lead_data": ""
    }

    while True:
        user_input = input("\nEnter input (or 'exit'): ")

        if user_input.lower() == "exit":
            break

        # 👇 update only input, NOT whole state
        state["user_input"] = user_input

        # 👇 pass full state (this preserves history + lead flow)
        state = graph.invoke(state)

        print("\n" + state["answer"])
