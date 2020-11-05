.DEFAULT_GOAL := help
help:
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

build-tests: ## builds docker container
	docker build -f docker/tests/Dockerfile -t traceflow-tests .

run-tests: ## runs tests through the docker container
	docker run traceflow-tests
