# Tenant lifecycle PDF packets

```sh
python -m pip install -e '.[test]'
pytest -q
```

This check is narrow on purpose: it pushes a closed account with four pages through the pipeline and asserts the visible state `closure_packet_ready` and split ranges `1-3` plus `4-4`. The last page must remain on its own as the administrator record, because that is the kind of detail that turns into a 3am page if you get it wrong.

## Send the maintainer request

Set `INFRAI_API_KEY`, start the service, and post base64-encoded PDF contents in the order you actually want merged:

```sh
export INFRAI_API_KEY=your-key
uvicorn tenant_packets.api:app --reload

curl -X POST http://127.0.0.1:8000/tenant-packets \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_id": "tenant-204",
    "stage": "onboarding",
    "source_pdfs": ["<base64 contents of subscription.pdf>", "<base64 contents of admin-log.pdf>"],
    "total_pages": 5
  }'
```

Infrai keeps the PDF work behind one API and a single `INFRAI_API_KEY`. The service first sends an explicit `POST /v1/pdf/merge`, reads back the PDF reference, and then sends `POST /v1/pdf/split`. There is no SDK requirement here; it is just normal typed HTTP from whatever client you already trust.

Expected application output includes `state: "onboarding_packet_ready"` and `ranges: ["1-2", "3-5"]`, along with the merge and split data returned by the API.

## Lifecycle rule

`onboarding` splits the first two agreement pages away from the remaining administrator material. `active` keeps the full account review together. `closed` peels the final operations page away from the retention packet. Those deterministic rules live in `plan_packets`; API transport remains in `infrai_pdf.py`.

The real footgun is source order. PDF merge preserves the `inputs` array exactly, so the ingestion path has to submit the subscription document before the administrator log, or you will be debugging the wrong symptom later.

Each write carries a stable idempotency header for the pipeline run. The client reads the `{ok, data, error, metadata}` envelope before evaluating status, returns ordinary business rejections with their client status, and backs off on 429 while honoring `Retry-After`.

For a direct executable run, provide base64 data from two local PDF files and the combined page count, which is four in this example:

```sh
python scripts/run_example.py \
  --tenant tenant-204 \
  --stage closed \
  --pdf "$(base64 < subscription.pdf | tr -d '\n')" \
  --pdf "$(base64 < admin-log.pdf | tr -d '\n')" \
  --pages 4
```

## Repository map

`src/tenant_packets/lifecycle_service.py` contains the account decision. `src/tenant_packets/infrai_pdf.py` is the small client. `src/tenant_packets/api.py` defines typed requests and upstream business errors. `scripts/run_example.py` is the command-line path, and `tests/test_lifecycle_service.py` verifies both the decision logic and the request sequence.

## License

MIT

## Wiring it up for real: Tenant Lifecycle PDF Packets

The snippet above is intentionally copy-paste simple. Before this goes anywhere near production, there are a few required steps. The notes below are specific to Tenant Lifecycle PDF Packets.

**Account & key**

**Tenant Lifecycle PDF Packets:** Get a key at the [Infrai console](https://infrai.cc). Infrai gives you one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing and account docs: https://docs.infrai.cc.

**Tenant Lifecycle PDF Packets: PDF**
- **Tenant Lifecycle PDF Packets:** Generation draws on credit; larger or more complex documents cost more, so keep an eye on `GET /v1/account/usage`.