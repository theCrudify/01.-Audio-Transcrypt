"""Entrypoint shortcut for root directory."""
from app.main import app, pick_free_port

if __name__ == "__main__":
    import uvicorn

    port = pick_free_port()
    print(f"Starting app on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
