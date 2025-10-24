.PHONY: docs-sync docs-build docs-serve docs-clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  docs-sync   - Sync eoapi-k8s documentation"
	@echo "  docs-build  - Build documentation site"
	@echo "  docs-serve  - Serve documentation locally"
	@echo "  docs-clean  - Clean documentation build files"

# Sync eoapi-k8s documentation
docs-sync:
	@echo "Syncing eoapi-k8s documentation..."
	@mkdir -p docs/src/deployment/kubernetes
	@if [ ! -d "eoapi-k8s" ]; then \
		git clone https://github.com/developmentseed/eoapi-k8s.git; \
	fi
	@cd eoapi-k8s && git fetch && git checkout main
	@if [ -f "eoapi-k8s/docs/docs-config.json" ]; then \
		find eoapi-k8s/docs -name "*.md" -not -name "README.md" -exec cp {} docs/src/deployment/kubernetes/ \;; \
		ASSETS_DIR=$$(grep -o '"assets_dir": *"[^"]*"' eoapi-k8s/docs/docs-config.json | cut -d'"' -f4); \
		if [ -n "$$ASSETS_DIR" ] && [ -d "eoapi-k8s/docs/$$ASSETS_DIR" ]; then \
			cp -r "eoapi-k8s/docs/$$ASSETS_DIR" docs/src/deployment/kubernetes/; \
		fi; \
		find eoapi-k8s/docs -name "*.svg" -exec cp {} docs/src/deployment/kubernetes/ \;; \
	fi
	@echo "" >> docs/src/deployment/kubernetes/index.md
	@echo "---" >> docs/src/deployment/kubernetes/index.md
	@echo "" >> docs/src/deployment/kubernetes/index.md
	@echo "*Documentation last synchronized: $$(date -u +"%Y-%m-%d %H:%M:%S UTC")*" >> docs/src/deployment/kubernetes/index.md
	@echo "Documentation sync complete!"

# Build documentation
docs-build: docs-sync
	@cd docs && mkdocs build

# Serve documentation locally
docs-serve: docs-sync
	@cd docs && mkdocs serve

# Clean documentation build files
docs-clean:
	@rm -rf docs/build docs/src/deployment/kubernetes eoapi-k8s
	@echo "Documentation cleaned!"
