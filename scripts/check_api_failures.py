"""Verificacao HTTP real em processo proprio, sem banco, retry ou servidor externo."""

import json
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def local_server(fixture_path=None):
    """Porta efemera; apenas processo criado aqui pode ser encerrado."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    # Janela bind-release: se outro processo ocupar, o filho falha e o ensaio para.
    child_env = dict(os.environ)
    child_env.pop("ILC_MOCK_FIXTURE", None)
    if fixture_path is not None:
        child_env["ILC_MOCK_FIXTURE"] = str(fixture_path)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "mock_api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-access-log",
        ],
        cwd=ROOT,
        env=child_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 10
        with httpx.Client(trust_env=False, timeout=0.5) as client:
            while True:
                if process.poll() is not None:
                    raise RuntimeError("Servidor filho encerrou durante a partida")
                try:
                    response = client.get(url + "/openapi.json")
                    response.raise_for_status()
                    break
                except httpx.TransportError:
                    # Sondagem limitada de prontidao, nao retry dos cenarios.
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Partida excedeu 10 segundos") from None
                    time.sleep(0.05)
        yield url, process.pid
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if process.poll() is None:
            raise RuntimeError("Processo filho nao encerrou")


def check_running(url: str) -> list[dict]:
    results = []
    with httpx.Client(trust_env=False, timeout=2.0) as client:
        response = client.get(url + "/events?limit=5")
        response.raise_for_status()
        page = response.json()
        if len(page["items"]) != 5 or page["total"] != 13:
            raise AssertionError("Endpoint normal divergiu da fixture")
        results.append(
            {
                "scenario": "normal",
                "outcome": "HTTP_200",
                "status": 200,
                "items": len(page["items"]),
                "total": page["total"],
            }
        )

        started = time.monotonic()
        try:
            client.get(url + "/scenarios/delay?seconds=1", timeout=0.2)
        except httpx.ReadTimeout:
            elapsed = time.monotonic() - started
            if elapsed > 3:
                raise AssertionError(
                    "Timeout ultrapassou limite de observacao"
                ) from None
            results.append(
                {
                    "scenario": "delay",
                    "outcome": "READ_TIMEOUT",
                    "status": None,
                    "body": None,
                    "client_timeout_seconds": 0.2,
                    "server_delay_seconds": 1,
                    "elapsed_seconds": round(elapsed, 3),
                }
            )
        else:
            raise AssertionError("Cenario delay nao provocou ReadTimeout")

        response = client.get(url + "/scenarios/http-503")
        body = response.text
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            if response.status_code != 503 or response.json() != {
                "scenario": "http_503",
                "error": "SIMULATED_UNAVAILABLE",
            }:
                raise AssertionError("Status/corpo HTTP inesperado") from None
            results.append(
                {
                    "scenario": "http_503",
                    "outcome": "HTTP_STATUS_ERROR",
                    "status": response.status_code,
                    "body": body,
                }
            )
        else:
            raise AssertionError("503 tratado como sucesso")

        response = client.get(url + "/scenarios/invalid-json")
        response.raise_for_status()
        if response.status_code != 200:
            raise AssertionError("Esperado HTTP 200 antes da falha de JSON")
        try:
            response.json()
        except json.JSONDecodeError:
            if response.text != '{"scenario":"invalid_json",':
                raise AssertionError("Corpo invalido divergiu do contrato") from None
            results.append(
                {
                    "scenario": "invalid_json",
                    "outcome": "JSON_DECODE_ERROR",
                    "status": response.status_code,
                    "body": response.text,
                }
            )
        else:
            raise AssertionError("JSON invalido tratado como valido")

        response = client.get(url + "/events?limit=5")
        response.raise_for_status()
        if response.json() != page:
            raise AssertionError("Cenarios alteraram endpoint normal")
    return results


def check_stopped(url: str) -> dict:
    started = time.monotonic()
    # Tempo para o SO reportar recusa, separado do timeout de leitura.
    timeout = httpx.Timeout(0.5, connect=5.0)
    with httpx.Client(trust_env=False, timeout=timeout) as client:
        try:
            client.get(url + "/events")
        except httpx.ConnectError:
            return {
                "scenario": "server_stopped",
                "outcome": "CONNECT_ERROR",
                "connect_timeout_seconds": 5.0,
                "status": None,
                "body": None,
                "elapsed_seconds": round(time.monotonic() - started, 3),
            }
    raise AssertionError("Servidor parado nao gerou ConnectError")


def run() -> dict:
    with local_server() as (url, pid):
        results = check_running(url)
    # Somente apos wait() confirmar o encerramento do filho.
    results.append(check_stopped(url))
    return {
        "verification": "PASS",
        "url": url,
        "pid": pid,
        "child_stopped": True,
        "results": results,
    }


if __name__ == "__main__":
    try:
        report = run()
    except (
        AssertionError,
        RuntimeError,
        httpx.HTTPError,
        ValueError,
        OSError,
        subprocess.SubprocessError,
    ) as exc:
        print(
            json.dumps(
                {
                    "verification": "FAIL",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit(1) from None
    print(json.dumps(report, indent=2, ensure_ascii=False))
