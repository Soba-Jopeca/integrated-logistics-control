"""Run from repository root: python -m scripts.local_app --database ..."""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from scripts.migration_config import TEST_DATABASE
from src.application.service import (
    AppError,
    connect,
    details,
    filter_deliveries,
    list_deliveries,
    process_upload,
)

TZ = ZoneInfo("America/Sao_Paulo")


def display(rows):
    return [
        {
            k: v.astimezone(TZ).isoformat()
            if isinstance(v, datetime)
            else str(v)
            if v is not None
            else None
            for k, v in row.items()
        }
        for row in rows
    ]


def main():
    st.set_page_config(page_title="ILC | Entregas", layout="wide")
    st.title("Acompanhamento e conferência")
    st.caption("Ambiente local • dados sintéticos • horários em America/Sao_Paulo")
    import os

    if os.environ.get("ILC_APP_DATABASE") != TEST_DATABASE:
        st.error("Inicie pelo comando autorizado com --database ilc_f2p02b_test.")
        return
    engine = None
    try:
        engine = connect(os.environ["ILC_APP_DATABASE"])
        st.button(
            "Atualizar dados"
        )  # Every interaction performs fresh DB reads; no data cache.
        rows, consulted = list_deliveries(engine)
        st.caption("Consultado em " + consulted.astimezone(TZ).isoformat())
        identifier = st.text_input("Buscar identificador")
        physical = st.selectbox(
            "Situação física", ["Todos", "DELIVERED", "NOT_CONFIRMED", "CONTESTED"]
        )
        documentary = st.selectbox(
            "Regularidade documental", ["Todos", "SEM_DOCUMENTO", "PENDENTE", "REGULAR"]
        )
        filtered = filter_deliveries(rows, identifier, physical, documentary)
        st.dataframe(display(filtered), hide_index=True)
        if not filtered:
            st.info("Nenhuma entrega corresponde aos filtros.")
            return
        selected = st.selectbox(
            "Detalhar entrega", [r["delivery_id"] for r in filtered]
        )
        state = next(r for r in filtered if r["delivery_id"] == selected)
        st.write("Situação física: " + state["physical_state"])
        st.write("Regularidade documental: " + state["documentary_state"])
        if state["completion_contested"]:
            st.warning("Conclusão contestada: consulte eventos e histórico.")
        for title, records in details(engine, selected).items():
            with st.expander(title):
                st.dataframe(display(records), hide_index=True)
        st.subheader("Processar comprovante sintético")
        st.caption(
            "Limite: 1 MiB. Envelope explícito; recebido/extraído não significa aprovado. Para substituir, use nova versão e indique o document_id anterior."
        )
        with st.form("upload"):
            uploaded = st.file_uploader("PDF textual ou XML", type=["pdf", "xml"])
            envelope_text = st.text_area(
                "Envelope JSON",
                value=json.dumps(
                    {
                        "schema_version": "1.0",
                        "source_system": "synthetic_app_p01",
                        "document_id": "APP-001",
                        "document_family_id": "APP-FAMILY-001",
                        "version": 1,
                        "supersedes_document_id": None,
                        "delivery_id": selected,
                        "media_type": "application/xml",
                    },
                    indent=2,
                ),
                height=260,
            )
            synthetic = st.checkbox(
                "Confirmo que o arquivo e o envelope contêm apenas dados sintéticos"
            )
            submit = st.form_submit_button("Extrair e conferir")
        if submit:
            st.session_state.pop("last_result", None)
            if uploaded is None or not synthetic:
                st.error("Selecione um arquivo e confirme o uso de dados sintéticos.")
            else:
                try:
                    envelope = json.loads(envelope_text)
                except (ValueError, TypeError):
                    st.error("Envelope JSON inválido.")
                    return
                if (
                    not isinstance(envelope, dict)
                    or envelope.get("delivery_id") != selected
                ):
                    st.error("O envelope deve indicar a entrega selecionada.")
                    return
                report = process_upload(
                    engine, uploaded.name, uploaded.getvalue(), envelope
                )
                st.session_state["last_result"] = report
                st.rerun()
        if "last_result" in st.session_state:
            st.caption(
                "Última tentativa nesta sessão; resultado persistido. Os detalhes acima foram consultados novamente."
            )
            report = st.session_state["last_result"]
            outcome = report.get("evaluation")
            if outcome:
                st.write("Resultado da conferência: " + outcome["result"])
                st.write(
                    "Motivos:",
                    outcome["reasons"]
                    or "Sem divergências detectadas pela regra determinística.",
                )
            else:
                st.warning(
                    "Processamento rejeitado: "
                    + str(report["extraction"].get("error_category"))
                )
            st.json(report)
    except AppError as exc:
        st.error(str(exc))
    except Exception:  # noqa: BLE001 — UI boundary masks unexpected failures
        # Boundary: never render a traceback, SQL, connection URL or credentials.
        st.error(
            "Não foi possível consultar ou processar os dados. Verifique a configuração e a disponibilidade do banco de teste. A operação não foi confirmada; atualize antes de reenviar."
        )
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    main()
