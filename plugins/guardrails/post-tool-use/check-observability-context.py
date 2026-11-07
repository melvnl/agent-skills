#!/usr/bin/env python3
"""check-observability-context: flag SQS/SNS calls that drop correlation context.

PostToolUse on Write, Edit and MultiEdit of Python files. Deterministic checks on calls the edit
introduces: an SQS `send_message`/`send_message_batch` (has QueueUrl) or SNS `publish` (has TopicArn or
TargetArn) without `MessageAttributes`, and an SQS `receive_message` without `MessageAttributeNames`
(attributes are then not returned). Whether context is propagated another way is a judgment for the
distributed-tracing-and-correlation skill, so this is feedback, not a block.
Config: `disabled: ["check-observability-context"]`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import config, hookio, pyscan  # noqa: E402

NAME = "check-observability-context"
PUBLISH = re.compile(r"\.(send_message_batch|send_message|publish_batch|publish)\s*\(")
RECEIVE = re.compile(r"\.receive_message\s*\(")


def main(data):
    project = hookio.project_dir(data)
    path = hookio.tool_input(data).get("file_path", "")
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit") or not path.endswith(".py"):
        return
    if not config.enabled(config.load(project), NAME):
        return
    rel = config.relative(path, project) or os.path.basename(path)
    lines = hookio.introduced_lines(data)
    issues = []
    for lineno, call in pyscan.calls(lines, PUBLISH):
        is_aws = re.search(r"\b(QueueUrl|TopicArn|TargetArn|PublishBatchRequestEntries|Entries)\s*=", call)
        if is_aws and "MessageAttributes" not in call:
            issues.append("%s:%s publish/send without MessageAttributes (correlation ids not propagated)" % (rel, lineno))
    for lineno, call in pyscan.calls(lines, RECEIVE):
        if "MessageAttributeNames" not in call:
            issues.append("%s:%s receive_message without MessageAttributeNames (attributes are not returned)" % (rel, lineno))
    if issues:
        hookio.feedback("%s: %s. Propagate the project's correlation id (and trace context) as message attributes "
                        "on publish, and request and bind them on receive; or state how context is carried instead."
                        % (NAME, "; ".join(issues[:6])), limit=1200)


if __name__ == "__main__":
    hookio.run(main, NAME)
