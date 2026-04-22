# RegEngine integration notes

Reference points captured for this repo:

- Ingest endpoint: `POST /api/v1/webhooks/ingest`
- Export endpoint: `GET /v1/fsma/export/fda-request`
- Forward trace: `GET /v1/fsma/trace/forward/{tlc}`
- Backward trace: `GET /v1/fsma/trace/backward/{tlc}`

Documented event payload fields:

- `cte_type`
- `traceability_lot_code`
- `product_description`
- `quantity`
- `unit_of_measure`
- `location_name`
- `timestamp`
- `kdes`

Mock export columns expected by this repo:

- Traceability Lot Code
- Traceability Lot Code Description
- Product Description
- Quantity
- Unit of Measure
- Location Description
- Location Identifier (GLN)
- Date
- Time
- Reference Document Type
- Reference Document Number
