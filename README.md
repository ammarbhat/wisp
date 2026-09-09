# Realtime Notes Chat (WebSockets)

A small FastAPI project extending a notes CRUD API with real-time chat
using WebSockets, built to learn how persistent, bidirectional
connections work and how to broadcast messages to multiple connected
clients.

## What it does

- Serves a simple HTML/JS chat page at `/`.
- Each browser tab connects to `/ws/{client_id}`, where `client_id`
  identifies that connection.
- Messages sent by one client are broadcast to every currently
  connected client.
- Chat messages are also saved as `Note` records in the database.

## Running it

```bash
uvicorn main:app --reload
```

Then open `http://localhost:8000` in two or more browser tabs to see
messages broadcast between them.

## How it works

A regular HTTP request/response ends the moment the server replies.
WebSockets are different: once a client connects, the connection stays
open, and either side — client or server — can send data at any time
without waiting to be asked.

Because each connection is handled by its own isolated instance of the
websocket endpoint function, one connection has no way to "see" or
message another on its own. To broadcast, every open connection needs
to be tracked somewhere shared across all of them.

That's what `ConnectionManager` does: it keeps a single list
(`active_connections`) of every currently open connection, shared by
the whole app rather than owned by any one connection. It exposes:

- `connect()` — accepts a new connection and adds it to the list.
- `disconnect()` — removes a connection from the list.
- `send_personal_text()` — sends a message to just one connection.
- `broadcast()` — sends a message to every connection in the list.

When a client sends a message, the server broadcasts it to everyone,
using each connection's id to label who sent it. When a client
disconnects, cleanup happens in a `finally` block so the connection is
always removed from the list — whether it disconnected normally or the
loop exited due to an unrelated error. Individual sends inside
`broadcast()` are wrapped in their own try/except so one stale
connection can't stop the message from reaching everyone else.

## Notes

This project is a learning exercise, not a portfolio piece — the goal
was understanding connection lifecycles and shared state across
concurrent connections, not production-grade chat infrastructure.