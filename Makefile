.PHONY: db-up db-down etl train graph app test clean all

DB_URL=postgresql://shark:sharkpass@localhost:5432/sharkgraph

db-up:
	docker-compose up -d db
	@echo "Waiting for Postgres to be ready..."
	@sleep 3

db-down:
	docker-compose down

etl:
	python etl/ingest.py
	python etl/transform.py
	python etl/load.py
	python etl/dq_checks.py

train:
	python modeling/train_deal_model.py
	python modeling/train_shark_model.py
	python modeling/evaluate.py

graph:
	python graph/build_graph.py
	python graph/compute_metrics.py
	python graph/export_graph_tables.py

app:
	streamlit run app/app.py

test:
	pytest tests/ -v

clean:
	rm -f models/*.pkl models/*.json
	rm -f reports/*.html reports/*.csv

all: etl graph train
	@echo "Pipeline complete: ETL -> Graph -> ML"
