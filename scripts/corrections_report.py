"""Relatório de correções humanas REAIS registradas no MongoDB.

ESPECIFICACAO.md §15 / Artigo §3.12 — "quantidade de correções realizadas
durante a validação humana".

Enquanto `scripts/evaluate.py` mede o experimento A×B offline sobre o texto
OCR, este script lê a collection `documents` (populada quando as notas são
submetidas pela API e conferidas via `PUT /api/v1/documents/{id}`) e agrega:

- total de documentos e distribuição por `status`;
- total de correções humanas e correções por campo;
- documentos validados com / sem correção.

Não inventa dados: só reporta o que está persistido.

USO
    docker compose --profile eval run --rm eval python -m scripts.corrections_report
    # ou, com Mongo acessível localmente:
    python -m scripts.corrections_report
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

from app.models.schemas import ESSENTIAL_FIELDS
from app.repository.documents_repository import DocumentsRepository, RepositoryUnavailableError


def build_report(repo: DocumentsRepository) -> dict:
    if not repo.ping():
        raise SystemExit("MongoDB indisponível — suba o `docker compose up` antes.")

    status_counts: Counter[str] = Counter()
    per_field: Counter[str] = Counter()
    total_corrections = 0
    total_docs = 0
    validated_with_correction = 0
    validated_without_correction = 0

    try:
        cursor = repo.iter_all({"status": 1, "validation": 1})
        docs = list(cursor)
    except RepositoryUnavailableError as exc:
        raise SystemExit(f"erro ao ler o MongoDB: {exc}")

    for doc in docs:
        total_docs += 1
        status_counts[str(doc.get("status", "?"))] += 1
        validation = doc.get("validation") or {}
        corrections = validation.get("corrections") or []
        total_corrections += len(corrections)
        for correction in corrections:
            per_field[correction.get("field", "?")] += 1
        if validation.get("validated"):
            if corrections:
                validated_with_correction += 1
            else:
                validated_without_correction += 1

    success_states = {"VALIDATION_PENDING", "VALIDATED", "EXTRACTED", "OCR_COMPLETED"}
    processed_ok = sum(n for s, n in status_counts.items() if s in success_states)

    return {
        "total_documents": total_docs,
        "by_status": dict(status_counts),
        "processed_successfully": processed_ok,
        "success_rate_pct": round(processed_ok / total_docs * 100, 1) if total_docs else 0.0,
        "total_human_corrections": total_corrections,
        "corrections_by_field": {f: per_field.get(f, 0) for f in ESSENTIAL_FIELDS},
        "validated_with_correction": validated_with_correction,
        "validated_without_correction": validated_without_correction,
    }


def _to_markdown(report: dict) -> str:
    lines = [
        "# Correções humanas — dados reais do MongoDB",
        "",
        f"- documentos: {report['total_documents']}",
        f"- processados com sucesso: {report['processed_successfully']} "
        f"({report['success_rate_pct']}%)",
        f"- total de correções humanas: {report['total_human_corrections']}",
        f"- validados COM correção: {report['validated_with_correction']}",
        f"- validados SEM correção: {report['validated_without_correction']}",
        "",
        "## Documentos por status",
        "",
        "| status | qtde |",
        "|---|---|",
    ]
    for status, count in sorted(report["by_status"].items()):
        lines.append(f"| {status} | {count} |")
    lines += ["", "## Correções por campo", "", "| campo | correções |", "|---|---|"]
    for field_name, count in report["corrections_by_field"].items():
        lines.append(f"| {field_name} | {count} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Relatório de correções humanas (MongoDB)")
    parser.add_argument("--json", action="store_true", help="saída em JSON")
    args = parser.parse_args()

    report = build_report(DocumentsRepository())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_to_markdown(report))


if __name__ == "__main__":
    main()
