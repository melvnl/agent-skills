---
type: llm
---

PASS if the reply points out that the outbound call doesn't propagate the request/correlation id header to the bureau service and recommends injecting it (using the project's existing id, e.g. get_request_id()), and that the bureau log lacks the id.

FAIL if the reply misses the propagation gap, or proposes generating a new uuid for the outbound call.
