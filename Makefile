build:
	docker compose up --build -d
	cd ui && npm install
	cd ui && npm start
health:
	docker compose ps
	curl http://127.0.0.1:5050/health
dist:
	./scripts/build-backend.sh
	cd ui && npm install
	cd ui && npm run dist