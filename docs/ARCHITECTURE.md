# System Architecture

## Overview

This project separates transactional retail operations from flexible customer-feedback data.

```text
React + TypeScript SPA
        |
        v
FastAPI REST API
        |
   +----+-------------------+
   |                        |
   v                        v
PostgreSQL                MongoDB
Products                  Product reviews
Customers                 Audit events
Inventory
Orders / OrderItems
   |
   +--> OpenAI Responses API (optional)
        ChatGPT Review Insights
```

## Frontend

The React + TypeScript client is intentionally built with reusable components and hand-written CSS rather than relying entirely on a UI framework. It provides an operations dashboard for catalog, inventory, orders, reviews, and AI-generated review insights.

## Backend

FastAPI exposes REST endpoints while business logic is kept in service classes.

- `RetailService`: product creation, customers, inventory, ordering, restocking
- `ReviewService`: MongoDB review persistence and ChatGPT summarization
- SQLAlchemy models represent transactional relational entities
- Pydantic schemas validate API contracts

## Relational database responsibilities

PostgreSQL stores data where consistency and transactions matter most:

- products
- customers
- inventory
- orders
- order_items

Order creation uses a database transaction and a row-level inventory lock before stock is decremented. This avoids overselling during concurrent order creation.

## NoSQL responsibilities

MongoDB stores document-shaped data that can evolve with fewer schema constraints:

- customer product reviews
- audit/activity events

This makes it easy to add future review metadata such as sentiment, moderation status, language, or extracted themes without changing the core order schema.

## AI review insights

The AI feature is deliberately outside the core ordering path. Product reviews are retrieved from MongoDB and passed to the OpenAI Responses API only when a user explicitly requests a summary. If no API key is configured, product, customer, order, inventory, and review features continue to work normally.

## Local orchestration

Docker Compose starts four services:

1. PostgreSQL
2. MongoDB
3. FastAPI backend
4. React frontend served through Nginx

## Kubernetes

The `k8s/` manifests reproduce the same logical architecture in a local Minikube/Kind cluster. Container image names are placeholders for images built and tagged by the developer.

## CI/CD

GitHub Actions validates the project on every push/pull request by:

- installing backend dependencies
- starting PostgreSQL and MongoDB service containers
- running pytest
- installing frontend dependencies
- running Jest tests
- running the TypeScript/Vite production build
- building backend and frontend Docker images

The pipeline is designed to catch both application-level regressions and packaging/deployment failures.