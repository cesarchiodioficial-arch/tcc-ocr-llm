from tests.support import make_invoice_png


def _create(client):
    return client.post(
        "/api/v1/documents",
        files={"file": ("nota.png", make_invoice_png(), "image/png")},
    ).json()


def test_correction_records_old_and_new(client, stub_ocr):
    created = _create(client)
    doc_id = created["_id"]

    response = client.put(
        f"/api/v1/documents/{doc_id}",
        json={"extracted_data": {"issuer_name": "Posto Avenida Ltda (corrigido)"}},
    )
    assert response.status_code == 200
    body = response.json()

    corrections = body["validation"]["corrections"]
    assert len(corrections) == 1
    assert corrections[0]["field"] == "issuer_name"
    assert corrections[0]["old_value"] == "POSTO AVENIDA LTDA"
    assert corrections[0]["new_value"] == "Posto Avenida Ltda (corrigido)"
    assert corrections[0]["corrected_at"]
    assert body["extracted_data"]["issuer_name"] == "Posto Avenida Ltda (corrigido)"
    assert body["validation"]["validated"] is False


def test_confirmation_sets_validated_status(client, stub_ocr, repo):
    created = _create(client)
    doc_id = created["_id"]

    response = client.put(f"/api/v1/documents/{doc_id}", json={"validated": True})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "VALIDATED"
    assert body["validation"]["validated"] is True
    assert body["validation"]["validated_at"]

    assert repo.get(doc_id)["status"] == "VALIDATED"


def test_no_correction_when_value_unchanged(client, stub_ocr):
    created = _create(client)
    doc_id = created["_id"]
    same = created["extracted_data"]["cnpj"]
    response = client.put(
        f"/api/v1/documents/{doc_id}", json={"extracted_data": {"cnpj": same}}
    )
    assert response.status_code == 200
    assert response.json()["validation"]["corrections"] == []


def test_put_unknown_id_404(client):
    from uuid import uuid4

    response = client.put(f"/api/v1/documents/{uuid4()}", json={"validated": True})
    assert response.status_code == 404


def test_human_correction_normalizes_to_internal_format(client, stub_ocr):
    """Correção humana normaliza data→ISO e CNPJ→dígitos, igual ao pipeline (P-09)."""
    created = _create(client)
    doc_id = created["_id"]

    response = client.put(
        f"/api/v1/documents/{doc_id}",
        json={
            "extracted_data": {
                "issue_date": "05/02/2026",
                "cnpj": "11.222.333/0001-81",
            }
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["extracted_data"]["issue_date"] == "2026-02-05"
    assert body["extracted_data"]["cnpj"] == "11222333000181"
    # o registro de correção guarda o valor já normalizado
    corr = {c["field"]: c["new_value"] for c in body["validation"]["corrections"]}
    assert corr["issue_date"] == "2026-02-05"
    assert corr["cnpj"] == "11222333000181"


def test_human_correction_keeps_invalid_value_flagged(client, stub_ocr):
    created = _create(client)
    doc_id = created["_id"]
    body = client.put(
        f"/api/v1/documents/{doc_id}",
        json={"extracted_data": {"cnpj": "12345678000199"}},  # dígitos errados
    ).json()
    assert body["extracted_data"]["cnpj"] == "12345678000199"  # mantém o que o humano digitou
    assert body["validation"]["field_checks"]["cnpj"]["valid"] is False
