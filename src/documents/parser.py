"""Deterministic educational formats; never approves or infers fields."""

import io
import re
from xml.etree.ElementTree import ParseError

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring
from pypdf import PdfReader
from pypdf.errors import PyPdfError

VERSION = "educational-v1"
FIELDS = (
    "declared_delivery_id",
    "delivered_at",
    "received_quantity",
    "quantity_unit",
    "receiver_name",
)
MAX_BYTES = 1_048_576


class DocumentError(Exception):
    """Stable public category; no source content or path in the error."""


def normalize_delivered_at(value):
    """Joao: implement timezone validation and UTC normalization here."""
    if value is None:
        return
    raise DocumentError("AUTHOR_TRANSFORMATION_PENDING")


def parse(raw, media_type):
    if len(raw) > MAX_BYTES:
        raise DocumentError("FILE_TOO_LARGE")
    if not raw:
        raise DocumentError("EMPTY_FILE")
    if media_type not in ("application/pdf", "application/xml"):
        raise DocumentError("UNSUPPORTED_FORMAT")
    try:
        if media_type == "application/xml":
            root = fromstring(
                raw, forbid_dtd=True, forbid_entities=True, forbid_external=True
            )
            if root.tag != "delivery_receipt" or root.attrib:
                raise DocumentError("INVALID_XML_STRUCTURE")
            values = {}
            for child in root:
                if (
                    child.tag not in FIELDS
                    or child.tag in values
                    or len(child)
                    or child.attrib
                ):
                    raise DocumentError("INVALID_XML_STRUCTURE")
                values[child.tag] = child.text
        else:
            if not raw.startswith(b"%PDF-"):
                raise DocumentError("FORMAT_MISMATCH")
            reader = PdfReader(io.BytesIO(raw), strict=True)
            if reader.is_encrypted:
                raise DocumentError("ENCRYPTED_PDF")
            if not 1 <= len(reader.pages) <= 5:
                raise DocumentError("PDF_PAGE_LIMIT")
            chunks = []
            for page in reader.pages:
                stream = page.get_contents()
                if stream is not None and len(stream.get_data()) > MAX_BYTES:
                    raise DocumentError("PDF_STREAM_LIMIT")
                chunks.append(page.extract_text() or "")
            content = "\n".join(chunks)
            if not content.strip():
                raise DocumentError("NO_EXTRACTABLE_TEXT")
            values = {}
            for line in content.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                key = key.strip()
                if key in FIELDS:
                    if key in values:
                        raise DocumentError("DUPLICATE_FIELD")
                    values[key] = value
        result = {field: (values.get(field) or "").strip() or None for field in FIELDS}
        quantity = result["received_quantity"]
        if quantity is not None:
            if not re.fullmatch(r"[0-9]+", quantity) or int(quantity) > 2147483647:
                raise DocumentError("INVALID_FIELD_TYPE")
            result["received_quantity"] = int(quantity)
        result["delivered_at"] = normalize_delivered_at(result["delivered_at"])
        return result
    except DocumentError:
        raise
    except DefusedXmlException:
        raise DocumentError("XML_SECURITY_BLOCKED") from None
    except (ParseError, ValueError, TypeError, KeyError, OSError):
        raise DocumentError("PARSING_ERROR") from None
    except (PyPdfError, RecursionError, NotImplementedError):
        # Third-party PDF exceptions have several classes; sanitize at boundary.
        raise DocumentError("PARSING_ERROR") from None
