# FoodDash – Restaurant Service

Part of the **FoodDash** food-delivery microservices application (BITS Pilani WILP, SEZG583 Scalable Services, Assignment 1, Amey Ogale – 2025MT03033).

The Restaurant Service owns **restaurants and menus**. It also validates and prices orders for the Order Service ([fooddash-order-service](../fooddash-order-service)).

| | |
|---|---|
| Language / framework | Python 3.12, FastAPI, SQLAlchemy 2 |
| Database | PostgreSQL 16 (`restaurant_db`, owned only by this service) |
| Port | 8001 (NodePort 30081 on minikube) |
| API docs | `/docs` (Swagger UI), `/openapi.json` |

## API

| Type | Method & path | Purpose |
|---|---|---|
| Command | `POST /api/v1/restaurants` | Register a restaurant |
| Query | `GET /api/v1/restaurants?city=&cuisine=&open_only=` | Browse/search restaurants |
| Query | `GET /api/v1/restaurants/{id}` | Restaurant details + menu |
| Command | `PATCH /api/v1/restaurants/{id}/status` | Open / close restaurant |
| Command | `POST /api/v1/restaurants/{id}/menu-items` | Add menu item |
| Query | `GET /api/v1/restaurants/{id}/menu` | View menu |
| Command | `PATCH /api/v1/menu-items/{id}` | Change price / availability |
| Query | `POST /api/v1/restaurants/{id}/validate-order` | Validate and price items (called by Order Service) |
| Health | `GET /health/live`, `GET /health/ready` | Kubernetes probes |

## Project structure

```
fooddash-restaurant-service/
├── app/
│   ├── main.py        # FastAPI app, startup, health probes
│   ├── config.py      # env-based settings
│   ├── database.py    # engine/session (database-per-service)
│   ├── models.py      # Restaurant, MenuItem tables
│   ├── schemas.py     # request/response contracts
│   ├── routes.py      # commands & queries
│   └── seed.py        # sample restaurants for demo
├── tests/test_api.py  # pytest (runs on SQLite)
├── k8s/               # namespace, Postgres (Secret, PVC, Deployment, Service), app (ConfigMap, Deployment, Service, HPA)
├── .github/workflows/ci.yml   # test -> build -> push image to GHCR
├── Dockerfile
├── docker-compose.yml # run this service + its DB alone
└── requirements.txt / requirements-dev.txt
```

## Run

```bash
# Locally (needs a Postgres; or use docker compose)
pip install -r requirements-dev.txt
pytest -q
docker compose up --build           # http://localhost:8001/docs

# On minikube
eval $(minikube docker-env)         # PowerShell: minikube docker-env --shell powershell | Invoke-Expression
docker build -t restaurant-service:1.0.0 .
kubectl apply -f k8s/
minikube service restaurant-service -n fooddash --url
```

| Env var | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://restaurant:restaurant@localhost:5432/restaurant_db` | DB connection |
| `SEED_DATA` | `true` | Insert sample restaurants on first start |
