"""Recorte de paginas sobre uma sequencia estavel de eventos."""


def paginate(
    events: list[dict], offset: int, limit: int
) -> tuple[list[dict], int | None]:
    """Retorna os itens da pagina e a proxima posicao, ou None."""
    if type(offset) is not int or not 0 <= offset <= len(events):
        raise ValueError("offset invalido")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit invalido")

    page = events[offset : offset + limit]
    next_offset = offset + len(page)

    if next_offset >= len(events):
        next_offset = None

    return page, next_offset
