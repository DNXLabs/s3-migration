export PATH_DEPLOY=.deploy
export AWS_DEFAULT_REGION?=ap-southeast-2

.PHONY: create-env
create-env:
	@echo "make create-env"
	python3 -m venv .venv

.PHONY: install
install: create-env
	@echo "make install"
	source .venv/bin/activate && pip3 install -r requirements.txt

.PHONY: migrate
migrate: create-env install
	@echo "make migrate"
	source .venv/bin/activate && python3 ./src/migrate.py