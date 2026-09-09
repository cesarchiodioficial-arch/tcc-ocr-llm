"""Avaliação experimental — Experimento A (OCR isolado) vs Experimento B (OCR + LLM).

ESPECIFICACAO.md §15 / Artigo §3.11-3.12.

O QUE ESTE SCRIPT FAZ
    Para cada nota fiscal listada no arquivo de referência:
      1. executa o OCR (Tesseract) uma única vez;
      2. Experimento A: extrai os 5 campos só com heurísticas/regex (baseline);
      3. Experimento B: extrai os 5 campos com o LLM configurado;
      4. compara cada campo com o valor de referência informado pelo pesquisador;
      5. calcula campos corretos, ausentes/incorretos, taxa de acerto e tempo.
    Gera uma tabela CSV + Markdown em evaluation/results/.

O QUE ESTE SCRIPT **NÃO** FAZ
    Não inventa valores de referência nem resultados. Os valores esperados são
    fornecidos pelo pesquisador em evaluation/reference_values.csv.

USO
    python -m scripts.evaluate --reference evaluation/reference_values.csv --dir samples
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.services import ocr_service
from app.services.baseline_extractor import baseline_extract
from app.services.llm_service import LLMExtractionError, extract_fields
from app.services.validation_service import normalize_extracted
from app.models.schemas import ESSENTIAL_FIELDS, ExtractedFields
from app.utils.cnpj import normalize_cnpj
from app.utils.dates import to_iso
from app.utils.money import parse_money
from app.utils.time_utils import now_iso

_MIME_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def _canonical(field_name: str, value: object) -> object | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    if field_name == "cnpj":
        return normalize_cnpj(text)
    if field_name == "issue_date":
        return to_iso(text) or text
    if field_name == "total_value":
        money = parse_money(text)
        return float(money) if money is not None else None
    return text.casefold()


@dataclass
class DocResult:
    file_name: str
    approach: str
    correct: int = 0
    incorrect: int = 0
    missing: int = 0
    evaluated: int = 0
    duration_ms: int = 0
    per_field: dict = field(default_factory=dict)

    @property
    def accuracy(self) -> float:
        return (self.correct / self.evaluated * 100) if self.evaluated else 0.0


def _compare(reference: dict, extracted: ExtractedFields, file_name: str, approach: str, duration_ms: int) -> DocResult:
    result = DocResult(file_name=file_name, approach=approach, duration_ms=duration_ms)
    extracted_dict = extracted.model_dump()
    for name in ESSENTIAL_FIELDS:
        ref = _canonical(name, reference.get(name))
        got = _canonical(name, extracted_dict.get(name))
        if ref is None:
            # sem valor de referência para este campo → não entra na taxa de acerto
            result.per_field[name] = "sem-referencia"
            continue
        result.evaluated += 1
        if got is None:
            result.missing += 1
            result.per_field[name] = "ausente"
        elif got == ref:
            result.correct += 1
            result.per_field[name] = "ok"
        else:
            result.incorrect += 1
            result.per_field[name] = f"incorreto ({got!r} != {ref!r})"
    return result


def _load_reference(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"arquivo de referência vazio: {path}")
    required = {"file_name", *ESSENTIAL_FIELDS}
    missing_cols = required - set(rows[0].keys())
    if missing_cols:
        raise SystemExit(f"colunas ausentes no CSV de referência: {sorted(missing_cols)}")
    return rows


def _find_file(base_dir: Path, file_name: str) -> Path | None:
    candidate = base_dir / file_name
    if candidate.is_file():
        return candidate
    matches = list(base_dir.glob(file_name))
    return matches[0] if matches else None


def run(reference_path: Path, base_dir: Path) -> list[DocResult]:
    if not reference_path.is_file():
        raise SystemExit(
            f"não encontrei {reference_path}.\n"
            "Crie o arquivo a partir de evaluation/reference_values.example.csv "
            "e preencha os valores esperados de cada nota."
        )
    if not ocr_service.tesseract_available():
        raise SystemExit(
            "Tesseract não está disponível neste ambiente. Rode a avaliação dentro do "
            "container:  docker compose run --rm app python -m scripts.evaluate"
        )

    rows = _load_reference(reference_path)
    results: list[DocResult] = []

    for row in rows:
        file_name = row["file_name"]
        path = _find_file(base_dir, file_name)
        if path is None:
            print(f"[AVISO] arquivo não encontrado, pulando: {file_name}", file=sys.stderr)
            continue

        mime = _MIME_BY_SUFFIX.get(path.suffix.lower())
        if mime is None:
            print(f"[AVISO] extensão não suportada, pulando: {file_name}", file=sys.stderr)
            continue

        data = path.read_bytes()
        try:
            ocr_text, _, ocr_ms = ocr_service.run_ocr(data, mime)
        except (ocr_service.OcrError, ocr_service.CorruptFileError) as exc:
            print(f"[ERRO OCR] {file_name}: {exc}", file=sys.stderr)
            continue

        # Experimento A — OCR isolado (baseline)
        start = time.perf_counter()
        baseline = normalize_extracted(baseline_extract(ocr_text))
        a_ms = ocr_ms + int((time.perf_counter() - start) * 1000)
        results.append(_compare(row, baseline, file_name, "A_ocr_only", a_ms))

        # Experimento B — OCR + LLM
        start = time.perf_counter()
        try:
            data_b, _ = extract_fields(ocr_text)
            data_b = normalize_extracted(data_b)
        except LLMExtractionError as exc:
            print(f"[ERRO LLM] {file_name}: {exc}", file=sys.stderr)
            data_b = ExtractedFields()
        b_ms = ocr_ms + int((time.perf_counter() - start) * 1000)
        results.append(_compare(row, data_b, file_name, "B_ocr_llm", b_ms))

    return results


def _write_outputs(results: list[DocResult], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_iso().replace(":", "").replace("-", "")
    csv_path = out_dir / f"results_{stamp}.csv"
    md_path = out_dir / f"results_{stamp}.md"

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["file_name", "approach", "evaluated", "correct", "incorrect", "missing", "accuracy_pct", "duration_ms"]
        )
        for r in results:
            writer.writerow(
                [r.file_name, r.approach, r.evaluated, r.correct, r.incorrect, r.missing, f"{r.accuracy:.1f}", r.duration_ms]
            )

    lines = ["# Resultado da avaliação", "", f"Gerado em {now_iso()}", ""]
    for approach in ("A_ocr_only", "B_ocr_llm"):
        subset = [r for r in results if r.approach == approach]
        if not subset:
            continue
        total_eval = sum(r.evaluated for r in subset)
        total_correct = sum(r.correct for r in subset)
        acc = (total_correct / total_eval * 100) if total_eval else 0.0
        avg_ms = int(sum(r.duration_ms for r in subset) / len(subset))
        lines += [
            f"## {approach}",
            "",
            f"- documentos: {len(subset)}",
            f"- campos avaliados: {total_eval}",
            f"- campos corretos: {total_correct}",
            f"- taxa de acerto: **{acc:.1f}%**",
            f"- tempo médio por documento: {avg_ms} ms",
            "",
            "| arquivo | corretos | incorretos | ausentes | acerto % | ms |",
            "|---|---|---|---|---|---|",
        ]
        for r in subset:
            lines.append(
                f"| {r.file_name} | {r.correct} | {r.incorrect} | {r.missing} | {r.accuracy:.1f} | {r.duration_ms} |"
            )
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Avaliação A vs B da POC")
    parser.add_argument("--reference", default="evaluation/reference_values.csv", type=Path)
    parser.add_argument("--dir", default="samples", type=Path)
    parser.add_argument("--out", default="evaluation/results", type=Path)
    args = parser.parse_args()

    results = run(args.reference, args.dir)
    if not results:
        raise SystemExit("nenhum documento avaliado.")

    csv_path, md_path = _write_outputs(results, args.out)
    print(f"OK — {len(results)} linhas de resultado")
    print(f"CSV: {csv_path}")
    print(f"MD : {md_path}")
    print(md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
