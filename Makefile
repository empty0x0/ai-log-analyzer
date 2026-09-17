.PHONY: demo down seed test clean logs mock

# Start all services (postgres, backend, frontend, envoy)
demo:
	@echo "Starting AI Log Analyzer..."
	@touch infra/gcp-token
	docker compose up -d --build
	@echo ""
	@echo "Services starting..."
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo "  Envoy:    http://localhost:10000"

# Start with mock LLM (no real API keys needed)
mock:
	@echo "Starting with mock LLM..."
	@touch infra/gcp-token
	docker compose --profile mock up -d --build
	@echo ""
	@echo "Mock LLM available at http://localhost:10001"

# Stop all services
down:
	docker compose --profile mock down

# Seed database with sample data
seed:
	@echo "Seeding database with sample logs..."
	@curl -s -X POST http://localhost:8000/logs/upload \
		-H "X-API-Key: changeme" \
		-F "file=@samples/nginx.log" \
		-F "source=nginx" || echo "Create samples/nginx.log first"

# Run tests
test:
	@echo "Running backend tests..."
	cd backend && poetry run pytest -v
	@echo ""
	@echo "Running frontend lint..."
	cd frontend && pnpm lint

# Backend lint only
lint:
	cd backend && poetry run ruff check .

# View logs
logs:
	docker compose logs -f

# Clean up volumes
clean:
	docker compose --profile mock down -v
	rm -rf backend/__pycache__ backend/app/__pycache__
	rm -rf frontend/.next frontend/node_modules

# Initialize local development (without Docker)
init:
	@echo "Setting up local development environment..."
	cd backend && poetry install
	cd frontend && pnpm install
	cp .env.example .env
	@echo "Edit .env with your API keys"

# Health check
health:
	@curl -s http://localhost:8000/health | jq . || echo "Backend not running"
