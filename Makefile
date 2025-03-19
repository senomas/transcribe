SHELL := /bin/bash
.SHELLFLAGS := -e -o pipefail -c
.PHONY: FORCE

VER := 1.0

build: .transcribe

push: build
	docker push docker.senomas.com/transcribe:$(VER)

.transcribe: Dockerfile requirements.txt *.py
	docker build \
		--build-arg UID=$(shell id -u) --build-arg GID=$(shell id -g) \
		-t docker.senomas.com/transcribe:$(VER) .
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
		docker.senomas.com/transcribe:$(VER) "$(link)"

