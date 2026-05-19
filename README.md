# Python Todo API — Project Question Starter

FastAPI backend + React frontend. Candidates implement the REST API and connect it to the UI.

## Stack

- **Backend**: Python 3.12, FastAPI, pymongo (MongoDB)
- **Frontend**: React 18, Vite
- **Tests**: pytest (backend), Jest + React Testing Library (frontend)

## Project structure

```
server/
  app.py          # FastAPI app factory — YOUR WORK
  requirements.txt
client/
  src/
    App.jsx       # React UI — YOUR WORK (connect API calls)
    App.css
    main.jsx
  index.html
```

## API Contract

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/todos` | List todos (supports `status`, `priority`, `q`, `sort`, `limit`, `offset`) |
| POST | `/api/todos` | Create todo |
| GET | `/api/todos/:id` | Get single todo |
| PUT | `/api/todos/:id` | Update todo |
| PATCH | `/api/todos/:id/toggle` | Toggle completed |
| DELETE | `/api/todos/:id` | Delete todo |
| DELETE | `/api/todos?status=completed` | Bulk delete completed |
| POST | `/api/todos/reorder` | Reorder todos |

## Getting started

1. Create virtual environment and install deps:
   ```bash
   cd server
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. Start the backend:
   ```bash
   .venv/bin/uvicorn app:create_app --host 0.0.0.0 --port 3000 --reload
   ```

3. Start the frontend (in another terminal):
   ```bash
   cd client
   npm install
   npm run dev
   ```

4. Run visible tests (backend + frontend):
   ```bash
   bash run-visible-tests.sh
   ```
   Or run individually:
   ```bash
   # Backend
   cd server && .venv/bin/pytest tests -v

   # Frontend
   cd client && npm test
   ```

## What to implement

- [ ] Complete the CRUD endpoints in `server/app.py` (some are TODO)
- [ ] Add filtering, sorting, and pagination to `GET /api/todos`
- [ ] Add validation (title length, priority enum, dueDate format, tags limit, position)
- [ ] Connect the React frontend to the actual API endpoints in `client/src/App.jsx`
- [ ] Handle errors gracefully with user-friendly messages

Good luck!
