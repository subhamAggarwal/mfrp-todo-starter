import React, { useEffect, useState, useCallback, useRef } from 'react';

const API = (path) => `${import.meta.env.BASE_URL}${path.replace(/^\//, '')}`;
const STORAGE_KEY = 'todo-draft';

export default function App() {
    const [todos, setTodos] = useState([]);
    const [title, setTitle] = useState('');
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [editTitle, setEditTitle] = useState('');
    const [toast, setToast] = useState(null);
    const editInputRef = useRef(null);

    useEffect(() => {
        const draft = localStorage.getItem(STORAGE_KEY);
        if (draft) setTitle(draft);
    }, []);

    useEffect(() => {
        localStorage.setItem(STORAGE_KEY, title);
    }, [title]);

    useEffect(() => {
        if (editingId && editInputRef.current) {
            editInputRef.current.focus();
        }
    }, [editingId]);

    const reload = async (queryParams = {}) => {
        try {
            const queryString = new URLSearchParams(queryParams).toString();
            const url = queryString ? `/api/todos?${queryString}` : '/api/todos';
            const res = await fetch(API(url));
            if (!res.ok) throw new Error(`GET ${url} -> ${res.status}`);
            const json = await res.json();
            setTodos(json.todos || []);
            setError(null);
        } catch (e) {
            setError(e.message);
            showToast(`Failed to load todos: ${e.message}`);
        }
    };

    useEffect(() => {
        const queryParams = {};
        if (filter !== 'all') queryParams.status = filter;
        if (searchQuery) queryParams.q = searchQuery;
        reload(queryParams);
    }, [filter, searchQuery]);

    const showToast = (message) => {
        setToast(message);
        setTimeout(() => setToast(null), 3000);
    };

    const create = async (e) => {
        e.preventDefault();
        const trimmed = title.trim();
        if (!trimmed) return;
        // TODO: POST new todo to API, then reload list
        console.log('TODO: create todo', trimmed);
    };

    const toggle = async (todo) => {
        // TODO: PATCH toggle to API, then update local state
        console.log('TODO: toggle todo', todo.id);
    };

    const remove = async (id) => {
        // TODO: DELETE todo from API, then reload list
        console.log('TODO: remove todo', id);
    };

    const clearCompleted = async () => {
        // TODO: DELETE completed todos from API, then reload list
        console.log('TODO: clear completed');
    };

    const startEdit = (todo) => {
        setEditingId(todo.id);
        setEditTitle(todo.title);
    };

    const cancelEdit = () => {
        setEditingId(null);
        setEditTitle('');
    };

    const saveEdit = async (id) => {
        const trimmed = editTitle.trim();
        if (!trimmed) return;
        // TODO: PUT update to API, then reload list
        console.log('TODO: save edit', id, trimmed);
        setEditingId(null);
        setEditTitle('');
    };

    const handleKeyDown = (e, todo) => {
        if (e.key === 'Enter') {
            if (editingId === todo.id) {
                saveEdit(todo.id);
            } else {
                startEdit(todo);
            }
        } else if (e.key === 'Escape') {
            cancelEdit();
        }
    };

    const handleAddKeyDown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            // TODO: trigger create on Enter
        }
    };

    const activeCount = todos.filter((t) => !t.completed).length;
    const filteredTodos = todos;

    return (
        <main className="container">
            <h1>Todos</h1>
            {error && <p className="error">{error}</p>}
            
            <form onSubmit={create}>
                <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    onKeyDown={handleAddKeyDown}
                    placeholder="What needs to be done?"
                    aria-label="add todo"
                />
                <button type="submit" aria-label="add todo">Add</button>
            </form>

            <div className="controls">
                <div className="filter-chips" role="tablist">
                    {['all', 'active', 'completed'].map((f) => (
                        <button
                            key={f}
                            role="tab"
                            aria-selected={filter === f}
                            className={filter === f ? 'active' : ''}
                            onClick={() => setFilter(f)}
                        >
                            {f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    ))}
                </div>
                <input
                    type="text"
                    placeholder="Search..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search"
                    aria-label="search todos"
                />
            </div>

            <div className="status-bar">
                <span data-testid="items-left">{activeCount} item{activeCount !== 1 ? 's' : ''} left</span>
                {activeCount < todos.length && (
                    <button onClick={clearCompleted} className="clear-btn">
                        Clear completed
                    </button>
                )}
            </div>

            {filteredTodos.length === 0 ? (
                <div className="empty-state">
                    <p>No todos found</p>
                    {searchQuery && <p>Try a different search term</p>}
                </div>
            ) : (
                <ul>
                    {filteredTodos.map((t) => (
                        <li key={t.id} role="listitem" className={t.completed ? 'done' : ''}>
                            <label>
                                <input
                                    type="checkbox"
                                    role="checkbox"
                                    checked={!!t.completed}
                                    onChange={() => toggle(t)}
                                    aria-label={`Mark ${t.title} as ${t.completed ? 'incomplete' : 'complete'}`}
                                />
                                {editingId === t.id ? (
                                    <input
                                        ref={editInputRef}
                                        type="text"
                                        value={editTitle}
                                        onChange={(e) => setEditTitle(e.target.value)}
                                        onBlur={() => saveEdit(t.id)}
                                        onKeyDown={(e) => handleKeyDown(e, t)}
                                        className="edit-input"
                                    />
                                ) : (
                                    <span
                                        onDoubleClick={() => startEdit(t)}
                                        title="Double-click to edit"
                                    >
                                        {t.title}
                                    </span>
                                )}
                            </label>
                            {t.priority && (
                                <span className={`priority-badge ${t.priority}`}>
                                    {t.priority}
                                </span>
                            )}
                            <button
                                className="remove"
                                onClick={() => remove(t.id)}
                                aria-label={`delete ${t.title}`}
                            >
                                ×
                            </button>
                        </li>
                    ))}
                </ul>
            )}

            {toast && <div className="toast">{toast}</div>}
        </main>
    );
}
