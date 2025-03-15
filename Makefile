SHELL := /bin/bash
.SHELLFLAGS := -e -o pipefail -c
.PHONY: FORCE

build: .transcribe

.transcribe: Dockerfile requirements.txt *.py
	docker build \
		--build-arg UID=$(shell id -u) --build-arg GID=$(shell id -g) \
		-t transcribe .
	touch .transcribe


run: build FORCE
	@if [ -z "$(link)" ]; then \
		echo "Usage: make run link=<YouTube_URL>"; \
		exit 1; \
	fi
	mkdir -p models
	docker run --rm -v $(shell pwd)/output:/app/data \
		-v $(shell pwd)/models:/models \
		--env-file .env \
		transcribe "$(link)"

