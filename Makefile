.DEFAULT_GOAL := help

help: ## Show help
	@echo "Commands:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## setup
	pip3 install -r requirements.txt -r requirements-dev.txt

.PHONY: diff
diff: ## diff
	cdk diff

.PHONY: deploy
deploy: ## deploy
	cdk deploy --require-approval never

.PHONY: check
check: ## check
	python scripts/mod_aurora.py 