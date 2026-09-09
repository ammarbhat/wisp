from fastapi import FastAPI, WebSocket, Depends, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from wisp.databases import engine, Base, get_db
from wisp.schemas import Note
from sqlalchemy.orm import sessionmaker

app = FastAPI()
Base.metadata.create_all(bind=engine)
Session = sessionmaker(engine)
html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Notes Chat</title>
    <style>
        body {
            font-family: system-ui, sans-serif;
            max-width: 480px;
            margin: 40px auto;
            padding: 0 16px;
        }
        #status {
            font-size: 0.85em;
            margin-bottom: 12px;
        }
        #status.connected { color: green; }
        #status.disconnected { color: crimson; }

        #messages {
            list-style: none;
            padding: 0;
            border: 1px solid #ddd;
            border-radius: 6px;
            max-height: 320px;
            overflow-y: auto;
            margin-bottom: 12px;
        }
        #messages li {
            padding: 8px 12px;
            border-bottom: 1px solid #eee;
        }
        #messages li:last-child { border-bottom: none; }

        form {
            display: flex;
            gap: 8px;
        }
        #messageText {
            flex: 1;
            padding: 8px;
        }
        button {
            padding: 8px 14px;
        }
    </style>
</head>
<body>
    <h1>Notes Chat</h1>
    <div id="status" class="disconnected">Connecting…</div>

    <ul id="messages"></ul>

    <form onsubmit="sendMessage(event)">
        <input type="text" id="messageText" autocomplete="off" placeholder="Type a message…" />
        <button type="submit">Send</button>
    </form>

    <script>
        const statusEl = document.getElementById("status");
        const messagesEl = document.getElementById("messages");

        // The backend's ConnectionManager expects a client_id in the URL path.
        // Generate a random one per browser tab so each connection is distinct.
        const clientId = Date.now();
        const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

        ws.onopen = () => {
            statusEl.textContent = "Connected";
            statusEl.className = "connected";
        };

        ws.onclose = () => {
            statusEl.textContent = "Disconnected";
            statusEl.className = "disconnected";
        };

        ws.onerror = () => {
            statusEl.textContent = "Connection error";
            statusEl.className = "disconnected";
        };

        ws.onmessage = (event) => {
            const li = document.createElement("li");
            li.textContent = event.data;
            messagesEl.appendChild(li);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        };

        function sendMessage(event) {
            event.preventDefault();
            const input = document.getElementById("messageText");
            if (!input.value.trim()) return;
            ws.send(input.value);
            input.value = "";
        }
    </script>
</body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        await websocket.close()
        self.active_connections.remove(websocket)

    async def send_personal_text(self, websocket: WebSocket, message: str):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for conn in self.active_connections:
            await conn.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def first_websocket(websocket: WebSocket, client_id: int, db=Depends(get_db)):
    await manager.connect(websocket)
    texts = db.query(Note).all()
    for q in texts:
        await manager.broadcast(q.message)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{client_id}: {data}")
            message = Note(message=data)
            db.add(message)
            db.commit()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
