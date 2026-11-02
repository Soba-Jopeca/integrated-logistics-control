"""Inicializacao fixa em loopback para demonstracao local."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("mock_api.app:app", host="127.0.0.1", port=8000)
