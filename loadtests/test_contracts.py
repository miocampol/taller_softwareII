import unittest

from loadtests.contracts import bulk_payload, validate_bulk, validate_page


class ContractTests(unittest.TestCase):
    def test_valid_pages_and_empty_out_of_range_page(self):
        row = {"id": 1, "email": "test@example.com"}
        body = {"total": 1, "data": [row], "current_page": 1, "per_page": 50}
        self.assertIsNone(validate_page(body, "/api/users/emails", 1, 50))
        body.update(data=[], current_page=2)
        self.assertIsNone(validate_page(body, "/api/users/emails", 2, 50))

    def test_malformed_and_sensitive_responses_fail(self):
        self.assertIsNotNone(validate_page([], "/api/users", 1, 50))
        body = {"total": 1, "data": [{"id": 1, "email": "x", "password": "x"}],
                "current_page": 1, "per_page": 50}
        self.assertIsNotNone(validate_page(body, "/api/users", 1, 50))

    def test_exactly_twenty_is_rejected(self):
        body = {"total": 1, "data": [{"id": 1, "email": "x", "birth_date": "2006-10-09"}],
                "current_page": 1, "per_page": 50, "cutoff_date": "2006-10-09"}
        self.assertIsNotNone(validate_page(body, "/api/users/over-twenty", 1, 50))
        body["data"][0]["birth_date"] = "2006-10-08"
        self.assertIsNone(validate_page(body, "/api/users/over-twenty", 1, 50))

    def test_bulk_payloads_are_unique_and_response_must_match(self):
        first, second = bulk_payload(), bulk_payload()
        emails = [row["email"] for batch in [first, second] for row in batch["users"]]
        self.assertEqual(6, len(set(emails)))
        body = {"users": [dict(row, id=index + 1) for index, row in enumerate(first["users"])]}
        self.assertIsNone(validate_bulk(body, first))
        self.assertIsNotNone(validate_bulk(body, second))
        self.assertIsNotNone(validate_bulk({"users": []}, first))


if __name__ == "__main__":
    unittest.main()
