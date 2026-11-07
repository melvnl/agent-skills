---
type: llm
---

PASS if the reply identifies that receive_message doesn't request MessageAttributeNames so correlation attributes are not returned, that the consumer doesn't extract and bind the producer's correlation id (only message_id is logged), and recommends fixing both.

FAIL if the reply only comments on style, or treats message_id alone as sufficient correlation.
