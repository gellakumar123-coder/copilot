# 🏗 Azure AI Foundry RAG Architecture

This document explains how the system works end-to-end.

---

## Components

### 1. Copilot Studio
- Hosts conversational bot  
- Calls backend through Actions (OpenAPI)  

### 2. API Management
- Security gateway  
- JWT + throttling + logging  

### 3. Azure Function (RAG Orchestrator)
- Retrieves documents  
- Calls LLM  
- Adds citations  

### 4. Azure AI Search
- Hybrid + vector search  
- Index stores enterprise documents  

### 5. Azure AI Foundry
- Embeddings model  
- GPT-4o / GPT-4.1 / Phi-3  

### 6. Security
- Entra ID  
- Managed Identity  
- Key Vault  
- RBAC  

---

## Sequence Diagram

