#!/bin/bash
# Run all visible tests (backend + frontend) for the Python Todo starter.
# Mirrors `npm test` in the Node project.

set -e

echo "==> Backend tests (pytest)"
cd /workspace/server
.venv/bin/pytest tests -v

echo ""
echo "==> Frontend tests (jest)"
cd /workspace/client
npx jest --verbose

echo ""
echo "==> All visible tests passed"
