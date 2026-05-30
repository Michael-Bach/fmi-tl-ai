import io
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FMI-TEW-Intelligence/1.0)"}
_MAX_CHARS = 14_000


def load_url(url: str) -> str:
    response = requests.get(url, headers=_HEADERS, timeout=20, allow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    lines = [l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip()]
    return "\n".join(lines)[:_MAX_CHARS]


def load_pdf_bytes(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = [page.extract_text() for page in reader.pages if page.extract_text()]
    return "\n\n".join(pages)[:_MAX_CHARS]


def load_text(text: str) -> str:
    return text.strip()[:_MAX_CHARS]
