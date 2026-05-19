#!/bin/bash
# Run all visible tests (backend + frontend) for the Python Todo starter.
# Mirrors `npm test` in the Node project: runs both suites regardless of
# individual failures, then reports a combined exit code.

echo "==> Backend tests (pytest)"
cd /workspace/server
.venv/bin/pytest tests -v
BACKEND_RC=$?

echo ""
echo "==> Frontend tests (jest)"
cd /workspace/client
npx jest --verbose
FRONTEND_RC=$?

echo ""
echo "==> Summary: backend exit=$BACKEND_RC, frontend exit=$FRONTEND_RC"

# Exit non-zero if either suite failed
if [ $BACKEND_RC -ne 0 ] || [ $FRONTEND_RC -ne 0 ]; then
    exit 1
fi
exit 0
