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
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
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
