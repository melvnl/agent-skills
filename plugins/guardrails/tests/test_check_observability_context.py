import os
import unittest

from helpers import HookTestCase, decision, reason


class CheckObservabilityContextTest(HookTestCase):
    SCRIPT = "post-tool-use/check-observability-context.py"

    def write(self, content):
        path = os.path.join(self.project, "worker.py")
        open(path, "w").write(content)
        return self.hook({"tool_name": "Write", "tool_input": {"file_path": path, "content": content}})

    def test_publish_without_attributes_flagged(self):
        code, out, _ = self.write("sqs.send_message(\n    QueueUrl=url,\n    MessageBody=body,\n)\n")
        self.assertEqual(decision(out), "block")
        self.assertIn("worker.py:1", reason(out))
        code, out, _ = self.write("sns.publish(TopicArn=arn, Message=msg)\n")
        self.assertEqual(decision(out), "block")

    def test_receive_without_attribute_names_flagged(self):
        code, out, _ = self.write("resp = sqs.receive_message(QueueUrl=url, WaitTimeSeconds=20)\n")
        self.assertIn("MessageAttributeNames", reason(out))

    def test_correct_and_unrelated_calls_pass(self):
        for content in ["sqs.send_message(QueueUrl=url, MessageBody=b, MessageAttributes=correlation_attributes())\n",
                        "sqs.receive_message(QueueUrl=url, MessageAttributeNames=['All'])\n",
                        "redis_client.publish('channel', payload)\n",
                        "event_bus.publish(event)\n"]:
            self.assertIsNone(self.write(content)[1], content)

    def test_malformed_input_fails_open(self):
        self.assertMalformedInputFailsOpen()


if __name__ == "__main__":
    unittest.main()
