# Retail Order & Inventory Management System

**React + TypeScript · FastAPI · PostgreSQL · MongoDB · Docker · Kubernetes · GitHub Actions · ChatGPT Review Insights**

A production-style full-stack retail operations platform for managing products, customers, inventory, orders, fulfillment, and customer reviews. The project extends my retail analytics work one layer closer to the source: after analyzing sales and profitability, I built the operational system that creates and manages that business data.

## What I built

- React + TypeScript operations dashboard with hand-written responsive CSS
- FastAPI backend organized into API, schema, model, database, and service layers
- PostgreSQL for transactional products, customers, inventory, orders, and order items
- MongoDB for flexible product reviews and audit/activity events
- Product and customer create/read/update/delete workflows with business-safe deletion rules
- Transaction-safe order creation with row-level inventory locking and automatic stock deduction
- Inventory restocking and low-stock visibility
- Order fulfillment state transitions: `created → processing → shipped → completed`
- **ChatGPT Review Insights** that summarizes real stored reviews into an executive summary, common positives, concerns, and recommended product actions
- pytest backend tests
- Jest + React Testing Library frontend tests
- Dockerfiles + Docker Compose local orchestration
- Kubernetes manifests for API, frontend, PostgreSQL, and MongoDB
- GitHub Actions CI validating backend, frontend, and Docker builds
- Reproducible demo seed script
- Architecture and database design documentation

## Architecture

```text
                         ┌─────────────────────────┐
                         │ React + TypeScript SPA  │
                         │ Retail Operations UI    │
                         └────────────┬────────────┘
                                      │ REST/JSON
                                      ▼
                         ┌─────────────────────────┐
                         │       FastAPI API       │
                         │ Services + Validation   │
                         └───────┬─────────┬───────┘
                                 │         │
                   transactions  │         │ documents
                                 ▼         ▼
                    ┌────────────────┐   ┌────────────────┐
                    │   PostgreSQL   │   │    MongoDB     │
                    │ products       │   │ reviews        │
                    │ customers      │   │ audit_events   │
                    │ inventory      │   └───────┬────────┘
                    │ orders/items   │           │
                    └────────────────┘           │ on demand
                                                 ▼
                                     ┌─────────────────────┐
                                     │ OpenAI Responses API│
                                     │ ChatGPT Review      │
                                     │ Insights            │
                                     └─────────────────────┘
```

## Core data model

### PostgreSQL — transactional system of record
- `products`
- `customers`
- `inventory`
- `orders`
- `order_items`

### MongoDB — flexible document workloads
- `reviews`
- `audit_events`

## Key workflows

### Order creation and inventory protection

1. Validate the customer and requested products.
2. Lock each relevant inventory row with `SELECT ... FOR UPDATE`.
3. Reject an order if available stock is insufficient.
4. Calculate line totals and the overall order total.
5. Create the order and order-item records.
6. Decrement inventory inside the same PostgreSQL transaction.
7. Commit the transaction and record an audit event in MongoDB.

This demonstrates why order/inventory operations belong in a relational database: the related writes must remain consistent.

### Inventory operations

The dashboard highlights SKUs at or below their reorder level and exposes a restock action. Inventory changes are persisted in PostgreSQL and logged to MongoDB.

### Order fulfillment

Orders move through controlled states:

```text
created → processing → shipped → completed
    └────────────→ cancelled
processing ──────→ cancelled
```

Invalid state transitions are rejected by the service layer.

### Product reviews + ChatGPT Review Insights

Product reviews are stored in MongoDB. When a user requests AI insights, the backend retrieves the stored reviews and sends only those reviews to the OpenAI Responses API. The prompt explicitly instructs the model not to invent facts beyond the supplied feedback.

The result contains:
- executive summary
- common positives
- common concerns
- recommended product actions

`OPENAI_API_KEY` is optional. Products, customers, inventory, orders, fulfillment, and reviews all work without it.

## Repository structure

```text
backend/
  app/
    api/routes.py
    core/config.py
    db/postgres.py
    db/mongo.py
    models/models.py
    schemas/schemas.py
    services/retail_service.py
    services/review_service.py
    main.py
  tests/test_health.py
  seed_demo.py
  requirements.txt
  Dockerfile

frontend/
  src/
    App.tsx
    App.test.tsx
    styles.css
    main.tsx
  package.json
  tsconfig.json
  vite.config.ts
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

## Fastest demo: Docker Compose

```bash
cp .env.example .env
docker compose up --build -d
```

Then seed demo data:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=. python seed_demo.py
```

Open:
- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`

The seed script creates sample retail products, customers, inventory, an order, and product reviews so the dashboard can be demonstrated immediately.

## Enable ChatGPT Review Insights

Add an OpenAI API key to `.env`:

```text
OPENAI_API_KEY=your_key_here
```

Then restart the API container and use **Generate ChatGPT Review Insights** from the product-review panel.

## Local development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
cd backend
PYTHONPATH=. pytest -q

cd ../frontend
npm test -- --runInBand
npm run build
```

## CI/CD

The GitHub Actions workflow runs three independent jobs on pushes and pull requests:

1. **Backend** — starts PostgreSQL + MongoDB service containers, installs Python dependencies, and runs pytest.
2. **Frontend** — installs Node dependencies, runs Jest/React Testing Library, and performs a production TypeScript/Vite build.
3. **Docker** — builds both the FastAPI and frontend container images.

## Kubernetes

The `k8s/` directory contains local-cluster manifests for Minikube or Kind:

```bash
kubectl apply -f k8s/
kubectl get pods,svc
```

The image names in the manifests are intentionally deployment placeholders; build/tag the images for your local registry or container registry before applying them.

## Documentation

- [System Architecture](docs/ARCHITECTURE.md)
- [Database Design](docs/DATABASE.md)

## JD skill mapping

| Skill | Evidence in this project |
|---|---|
| React | TypeScript operations SPA |
| HTML/CSS/modern JS | TSX + hand-written responsive CSS |
| Python | FastAPI backend and domain services |
| OOP / software design | service, schema, ORM model, API and DB separation |
| SQL / relational DB | PostgreSQL transactional data model |
| MongoDB / NoSQL | reviews + audit events |
| Automated testing | pytest + Jest + React Testing Library |
| Docker | separate backend/frontend images + Compose |
| Kubernetes | API/frontend/Postgres/Mongo manifests |
| CI/CD | automated test/build/image pipeline in GitHub Actions |
| Git | iterative repository development and CI-triggered commits |
| AI integration | optional ChatGPT review-summary workflow |

## Portfolio story

My earlier retail projects focused on sales forecasting, pricing, and profitability analysis. This project moves upstream and demonstrates how I would engineer the operational application responsible for generating that data: maintaining the product catalog, managing customers and stock, creating orders safely, tracking fulfillment, collecting customer feedback, and exposing review insights to product teams.

The result is one project that demonstrates **frontend engineering, backend API design, OOP, relational and NoSQL databases, testing, containerization, orchestration, CI/CD, and practical AI integration** in a coherent retail use case.
