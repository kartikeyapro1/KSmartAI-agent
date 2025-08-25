# run.py
import os
from dotenv import load_dotenv
import uvicorn

if __name__ == "__main__":
    load_dotenv()
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    # keep reload=False to avoid multiple child processes on Windows
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
