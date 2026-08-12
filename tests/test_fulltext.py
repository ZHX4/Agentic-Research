from pathlib import Path

import httpx

from agentic_research.literature.fulltext import FullTextAcquirer, FullTextManifest, parse_full_text
from agentic_research.literature.transport import HttpClient, RateLimiter
from agentic_research.schemas import Paper


def test_missing_fulltext_url_is_recorded_as_failed(tmp_path: Path) -> None:
    client = HttpClient(user_agent="test", rate_limiter=RateLimiter(0))
    try:
        manifest = FullTextAcquirer(client=client, output_dir=tmp_path).acquire(
            Paper(paper_id="p1", title="No URL")
        )
        assert manifest.status == "failed"
        assert manifest.requested_url is None
        assert "No full-text candidate URL" in (manifest.error or "")
    finally:
        client.close()


def test_html_acquisition_and_parsing(tmp_path: Path) -> None:
    html = b"<html><head><title>Test Paper</title></head><body><script>x=1</script><h1>Hello</h1><p>World</p></body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=html, headers={"content-type": "text/html; charset=utf-8"}, request=request)

    client = HttpClient(user_agent="test", rate_limiter=RateLimiter(0), transport=httpx.MockTransport(handler))
    try:
        paper = Paper(
            paper_id="p1",
            title="Test",
            url="https://example.org/paper.html",
        )
        manifest = FullTextAcquirer(client=client, output_dir=tmp_path).acquire(paper)
        assert manifest.status == "downloaded"
        assert manifest.media_type == "text/html"
        parsed = parse_full_text(manifest)
        assert parsed.title == "Test Paper"
        assert "Hello" in parsed.text
        assert "x=1" not in parsed.text
    finally:
        client.close()


def test_pdf_parser_reads_text(tmp_path: Path) -> None:
    import fitz

    pdf_path = tmp_path / "paper.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Hello PDF")
    document.save(pdf_path)
    document.close()

    manifest = FullTextManifest(
        paper_id="p1",
        source="test",
        requested_url="https://example.org/paper.pdf",
        final_url="https://example.org/paper.pdf",
        media_type="application/pdf",
        status="downloaded",
        local_path=str(pdf_path),
        byte_size=pdf_path.stat().st_size,
    )
    parsed = parse_full_text(manifest)
    assert "Hello PDF" in parsed.text
    assert parsed.page_count == 1
