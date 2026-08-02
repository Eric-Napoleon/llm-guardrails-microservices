# LLM Guardrails Microservices

## Overview

This project implements a distributed Large Language Model (LLM) system using a microservice architecture. The application consists of three independent services that communicate via REST APIs to provide a guarded interface for interacting with an LLM.

The system demonstrates enterprise computing concepts including distributed services, API communication, database integration, and configurable guardrails for sanitising both user prompts and model responses.

---

## Architecture

The application consists of three microservices:

### LLM Service

- Provides access to the Mistral API
- Exposes a REST endpoint for prompt completion
- Returns generated responses as JSON

### Guardrails Service

- Stores configurable guardrail rules
- Uses Firebase Realtime Database
- Supports CRUD operations for guardrails
- Uses regular expressions and replacement strings to sanitise text

### Auberge Service

- Acts as the gateway between clients and the LLM
- Applies input guardrails before sending prompts to the LLM
- Applies output guardrails before returning responses
- Provides a secure interface for LLM interactions

---

## Technologies

- Python
- Flask
- REST APIs
- Mistral API
- Firebase Realtime Database
- Regular Expressions
- JSON

---

## Features

- Microservice architecture
- RESTful API design
- Input sanitisation
- Output sanitisation
- Configurable guardrails
- Firebase persistence
- LLM integration
- Secure request pipeline

---

## Project Structure

```text
.
├── auberge.py
├── guardrails.py
├── llm.py
└── README.md
```

---

## API Overview

### LLM

```
POST /llm
```

Request

```json
{
  "prompt": "Hello"
}
```

Response

```json
{
  "output": "Hello!"
}
```

---

### Guardrails

```
PUT /guardrails/{id}
GET /guardrails/{id}
DELETE /guardrails/{id}
GET /guardrails
```

---

### Auberge

```
POST /auberge
```

The Auberge service sanitises the prompt using stored guardrails before forwarding it to the LLM, then sanitises the generated response before returning it to the client.

---

## Learning Outcomes

This project demonstrates:

- Enterprise application development
- Distributed systems
- Microservice communication
- REST API implementation
- Database integration
- Secure AI application design
- LLM integration
