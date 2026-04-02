.PHONY: install train export test run clean

install:
	pip install -r requirements.txt

install-training:
	pip install -r requirements-training.txt

data:
	python -m data_generator.build_rul_dataset

train:
	python -m rul_model.train --epochs 100

evaluate:
	python -m rul_model.evaluate

export:
	python -m rul_model.export_weights

test:
	pytest tests/ -v

run:
	python -m webapp.app

clean:
	rm -rf data_generator/generated/
	rm -rf rul_model/weights/*.pt
	rm -rf __pycache__ */__pycache__
	rm -rf .pytest_cache

all: install data train export test
