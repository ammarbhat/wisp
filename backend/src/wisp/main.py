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

        const ws = new WebSocket("ws://localhost:8000/ws");

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


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def first_websocket(websocket: WebSocket, db=Depends(get_db)):
    await websocket.accept()
    texts = db.query(Note).all()
    for q in texts:
        await websocket.send_text(q.message)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)
            message = Note(message=data)
            db.add(message)
            db.commit()
    except WebSocketDisconnect:
        await websocket.close()
