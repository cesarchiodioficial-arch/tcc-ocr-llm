"""Testes do relatório de correções humanas (lê MongoDB via mongomock)."""

import mongomock

from app.repository.documents_repository import DocumentsRepository
from scripts.corrections_report import _to_markdown, build_report


def _repo_with(docs):
    repo = DocumentsRepository(client=mongomock.MongoClient())
    for doc in docs:
        repo.insert(doc)
    return repo


def test_report_aggregates_corrections_and_status():
    repo = _repo_with(
        [
            {
                "_id": "1",
                "status": "VALIDATED",
                "validation": {
                    "validated": True,
                    "corrections": [
                        {"field": "cnpj"}, {"field": "total_value"},
                    ],
                },
            },
            {
                "_id": "2",
                "status": "VALIDATED",
                "validation": {"validated": True, "corrections": []},
            },
            {
                "_id": "3",
                "status": "FAILED",
                "validation": {"validated": False, "corrections": []},
            },
        ]
    )
    report = build_report(repo)
    assert report["total_documents"] == 3
    assert report["total_human_corrections"] == 2
    assert report["corrections_by_field"]["cnpj"] == 1
    assert report["corrections_by_field"]["total_value"] == 1
    assert report["corrections_by_field"]["issuer_name"] == 0
    assert report["validated_with_correction"] == 1
    assert report["validated_without_correction"] == 1
    assert report["by_status"]["FAILED"] == 1
    assert report["processed_successfully"] == 2  # os 2 VALIDATED
    assert report["success_rate_pct"] == round(2 / 3 * 100, 1)

    md = _to_markdown(report)
    assert "Correções por campo" in md
    assert "| cnpj | 1 |" in md
