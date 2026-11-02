import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from app import service, store


class TaskServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data_file = Path(self.temp.name) / "tasks.json"
        sample_file = Path(__file__).resolve().parents[1] / "data" / "tasks.json"
        self.sample = json.loads(sample_file.read_text(encoding="utf-8"))
        self.data_file.write_text(json.dumps(self.sample), encoding="utf-8")
        self.patcher = patch.object(store, "DATA_FILE", self.data_file)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_no_filters_preserves_all_records(self):
        self.assertEqual(service.list_tasks(), self.sample)

    def test_status_filters(self):
        for status in ("open", "done"):
            with self.subTest(status=status):
                expected = [task for task in self.sample if task["status"] == status]
                self.assertEqual(service.list_tasks(status=status), expected)

    def test_search_matches_title_and_description_case_insensitively(self):
        for query, expected_ids in (("LAUNCH", [1]), ("report", [4]), ("CALLBACK", [2])):
            with self.subTest(query=query):
                self.assertEqual(
                    [task["id"] for task in service.list_tasks(q=query)], expected_ids
                )

    def test_search_and_status_compose(self):
        self.assertEqual(
            [task["id"] for task in service.list_tasks(status="open", q="PLAN")], [3]
        )
        self.assertEqual(service.list_tasks(status="done", q="PLAN"), [])
        self.assertEqual(service.list_tasks(q="nonexistent search term"), [])

    def test_completion_persists_timestamp_and_preserves_other_tasks(self):
        completed = service.complete_task(3)
        self.assertEqual(completed["status"], "done")
        self.assertIsNotNone(datetime.fromisoformat(completed["completed_at"]).tzinfo)
        self.assertEqual(service.get_task(3), completed)
        stored = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertEqual(stored[2], completed)
        self.assertEqual(stored[:2] + stored[3:], self.sample[:2] + self.sample[3:])

    def test_missing_task_does_not_change_storage(self):
        before = self.data_file.read_bytes()
        self.assertIsNone(service.complete_task(999))
        self.assertEqual(self.data_file.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
