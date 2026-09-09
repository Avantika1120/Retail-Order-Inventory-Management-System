# Retail Order & Inventory Management System

**React + TypeScript · FastAPI · PostgreSQL · MongoDB · Docker · Kubernetes · GitHub Actions · ChatGPT Review Insights**

A production-style full-stack retail platform for managing products, customers, orders, inventory, and customer reviews. The project connects naturally to my analytics portfolio: after analyzing retail sales and profitability, I built the operational system that creates and manages the underlying business data.

## What I built

- React + TypeScript frontend with hand-written CSS
- FastAPI backend organized into routers, services, models, repositories, and schemas
- PostgreSQL for transactional entities: products, customers, inventory, orders, and order items
- MongoDB for product reviews and audit/activity events
- Transaction-safe order creation that validates stock and decrements inventory
- Inventory restocking workflow
- Product review creation and product-level review retrieval
- **ChatGPT Review Insights** endpoint that summarizes customer reviews into themes, pros, concerns, and a short executive summary when `OPENAI_API_KEY` is configured
- pytest backend tests
- Jest + React Testing Library frontend tests
- Dockerfiles and Docker Compose orchestration
- Kubernetes manifests for API, frontend, Postgres, and MongoDB
- GitHub Actions CI for backend tests, frontend tests/build, and Docker image builds
- Architecture and database documentation

## Architecture

```text
Browser
  |
  v
React + TypeScript frontend
  |
  v
FastAPI REST API
  |--------------------------|
  v                          v
PostgreSQL                MongoDB
Products                  Reviews
Customers                 Audit events
Inventory
Orders + OrderItems
  |
  +--> optional OpenAI Responses API --> ChatGPT Review Insights
```

## Core entities

### PostgreSQL
- `products`
- `customers`
- `inventory`
- `orders`
- `order_items`

### MongoDB
- `reviews`
- `audit_events`

## Key business workflows

### 1. Create an order
1. Validate the customer.
2. Validate each product.
3. Lock/check available stock.
4. Calculate line totals and order total.
5. Persist `Order` and `OrderItem` records.
6. Decrement inventory in the same transaction.
7. Write an audit event to MongoDB.

### 2. Restock inventory
Operations users can increase on-hand quantity through the inventory endpoint; the service records the change and emits an audit event.

### 3. Product reviews + ChatGPT summary
Reviews are stored in MongoDB because they are document-shaped and can evolve independently from the transactional order schema. For a selected product, the API can aggregate review text and ask the OpenAI Responses API for a concise structured summary. The AI feature is optional; all CRUD and inventory/order functionality works without an API key.

## Repository structure

```text
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
    main.py
  tests/
  requirements.txt
  Dockerfile

frontend/
  src/
    components/
    pages/
    services/
    types/
  package.json
  Dockerfile

k8s/
  api.yaml
  frontend.yaml
  postgres.yaml
  mongodb.yaml

.github/workflows/ci.yml
docker-compose.yml
docs/ARCHITECTURE.md
docs/DATABASE.md
.env.example
```

## Run locally with Docker

```bash
cp .env.example .env
docker compose up --build
```

Then open:
- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Local development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
cd backend && pytest
cd frontend && npm test -- --runInBand
```

## Kubernetes

The `k8s/` folder contains manifests for local deployment with Minikube or Kind.

```bash
kubectl apply -f k8s/
```

Use `kubectl get pods,svc` to verify the deployment. Screenshots can be added to `docs/screenshots/` after running the cluster locally.

## JD skill mapping

| Skill | Evidence in this project |
|---|---|
| React | TypeScript SPA and reusable components |
| HTML/CSS/JS | JSX/TSX plus hand-written CSS |
| Python | FastAPI backend and service layer |
| OOP | service/repository/model separation |
| SQL / relational DB | PostgreSQL transactional schema |
| MongoDB / NoSQL | reviews and audit logs |
| Automated testing | pytest + Jest/RTL |
| Docker | frontend/backend images + Compose |
| Kubernetes | deployment/service manifests |
| CI/CD | GitHub Actions tests and image builds |
| Git | repository-based development workflow |
| AI integration | optional ChatGPT review-summary feature |

## Portfolio story

My earlier retail projects focused on analyzing store sales, forecasting demand, and evaluating profitability. This project moves one layer closer to the source: it demonstrates how I would design and build the software system responsible for products, customers, inventory movements, orders, and product feedback before that information reaches an analytics warehouse or dashboard.
