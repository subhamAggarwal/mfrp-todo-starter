/**
 * Visible frontend test suite for the Python Todo starter.
 *
 * Candidate visible tests: some PASS (base works), some FAIL (candidate must implement).
 * Uses a direct window.fetch mock — no MSW needed.
 */

jest.setTimeout(30000);

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import App from './App';

let fetchMock;

function mockJson(body, status = 200) {
    return Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(body) });
}

beforeEach(() => {
    fetchMock = jest.fn(() => mockJson({ todos: [] }));
    window.fetch = fetchMock;
});

afterEach(() => {
    jest.restoreAllMocks();
});

describe('Todo App (visible) – Rendering', () => {
    test('Renders main heading', () => {
        render(<App />);
        expect(screen.getByRole('heading', { name: 'Todos' })).toBeInTheDocument();
    });

    test('Renders add todo input with placeholder', () => {
        render(<App />);
        const input = screen.getByPlaceholderText('What needs to be done?');
        expect(input).toBeInTheDocument();
        expect(input).toHaveAttribute('aria-label', 'add todo');
    });

    test('Renders add button', () => {
        render(<App />);
        expect(screen.getByRole('button', { name: 'add todo' })).toBeInTheDocument();
    });

    test('Renders filter chips (All, Active, Completed)', () => {
        render(<App />);
        expect(screen.getByRole('tab', { name: 'All' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Active' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: 'Completed' })).toBeInTheDocument();
    });

    test('Renders search input', () => {
        render(<App />);
        const search = screen.getByPlaceholderText('Search...');
        expect(search).toBeInTheDocument();
        expect(search).toHaveAttribute('aria-label', 'search todos');
    });

    test('Renders items-left counter', () => {
        render(<App />);
        const counter = screen.getByTestId('items-left');
        expect(counter).toBeInTheDocument();
        expect(counter).toHaveTextContent('0 items left');
    });

    test('Renders empty state when no todos', async () => {
        render(<App />);
        await waitFor(() => {
            expect(screen.getByText('No todos found')).toBeInTheDocument();
        });
    });
});

describe('Todo App (visible) – Adding todos', () => {
    test('Adding a todo clears the input and shows it in the list', async () => {
        const user = userEvent.setup();
        fetchMock
            .mockReturnValueOnce(mockJson({ todos: [] }))
            .mockReturnValueOnce(mockJson({ todo: { id: '1', title: 'Buy groceries', completed: false } }, 201))
            .mockReturnValueOnce(mockJson({ todos: [{ id: '1', title: 'Buy groceries', completed: false }] }));

        render(<App />);
        const input = screen.getByPlaceholderText('What needs to be done?');
        const button = screen.getByRole('button', { name: 'add todo' });

        await user.type(input, 'Buy groceries');
        await user.click(button);

        await waitFor(() => expect(input).toHaveValue(''));
        expect(await screen.findByText('Buy groceries')).toBeInTheDocument();
    });

    test('Adding a todo via Enter clears the input', async () => {
        const user = userEvent.setup();
        fetchMock
            .mockReturnValueOnce(mockJson({ todos: [] }))
            .mockReturnValueOnce(mockJson({ todo: { id: '1', title: 'New task', completed: false } }, 201))
            .mockReturnValueOnce(mockJson({ todos: [{ id: '1', title: 'New task', completed: false }] }));

        render(<App />);
        const input = screen.getByPlaceholderText('What needs to be done?');
        await user.type(input, 'New task{Enter}');

        await waitFor(() => expect(input).toHaveValue(''));
    });
});

describe('Todo App (visible) – Toggling todos', () => {
    test('Toggling a todo checkbox changes its completed state', async () => {
        fetchMock.mockReturnValueOnce(mockJson({
            todos: [{ id: '1', title: 'Task 1', completed: false }],
        })).mockReturnValueOnce(mockJson({ todo: { id: '1', title: 'Task 1', completed: true } }));

        const user = userEvent.setup();
        render(<App />);
        await screen.findAllByRole('checkbox'); // wait for items to load
        const checkbox = screen.getByRole('checkbox');
        expect(checkbox).not.toBeChecked();

        await user.click(checkbox);
        await waitFor(() => expect(checkbox).toBeChecked());
    });
});

describe('Todo App (visible) – Deleting todos', () => {
    test('Deleting a todo removes it from the list', async () => {
        fetchMock
            .mockReturnValueOnce(mockJson({ todos: [{ id: '1', title: 'Task 1', completed: false }] }))
            .mockReturnValueOnce(mockJson({ todo: { id: '1', title: 'Task 1' } }))
            .mockReturnValueOnce(mockJson({ todos: [] }));

        const user = userEvent.setup();
        render(<App />);
        await screen.findAllByRole('checkbox'); // wait for items to load

        const deleteButton = screen.getByRole('button', { name: /delete Task 1/i });
        await user.click(deleteButton);

        await waitFor(() => expect(screen.queryByText('Task 1')).not.toBeInTheDocument());
    });

    test('Clear completed removes completed todos', async () => {
        fetchMock
            .mockReturnValueOnce(mockJson({
                todos: [
                    { id: '1', title: 'Active', completed: false },
                    { id: '2', title: 'Completed', completed: true },
                ],
            }))
            .mockReturnValueOnce(mockJson({ deletedCount: 1 }))
            .mockReturnValueOnce(mockJson({ todos: [{ id: '1', title: 'Active', completed: false }] }));

        const user = userEvent.setup();
        render(<App />);
        await screen.findAllByRole('checkbox'); // wait for items to load

        const clearButton = screen.getByText('Clear completed');
        await user.click(clearButton);

        await waitFor(() => expect(screen.queryByText('Completed')).not.toBeInTheDocument());
    });
});
