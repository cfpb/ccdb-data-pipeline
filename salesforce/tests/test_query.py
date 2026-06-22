import unittest

import salesforce.query as query


class TestQuery(unittest.TestCase):
    def test_ensure_date_valid_iso(self):
        """Test that a valid ISO string is returned correctly."""
        input_date = "2023-01-01T12:00:00"
        result = query.ensure_date(input_date)
        self.assertEqual(result, "2023-01-01T12:00:00")

    def test_ensure_date_invalid_format(self):
        """Test that ensure_date raises ValueError for malformed strings."""
        with self.assertRaises(ValueError):
            query.ensure_date("01-01-2023")

    def test_get_all_data_since(self):
        """Verify the query with the 'since' parameter."""
        since = "2023-01-01T00:00:00"
        result = query.get_all_data_since(since)

        self.assertTrue(result.startswith("SELECT CreatedDate,"))
        self.assertIn(f"WHERE LastModifiedDate >= {since}", result)
        self.assertNotIn("CCDB_Eligible__c = true", result)

    def test_query_includes_all_fields(self):
        """Check that expected fields/pieces of the query exist."""
        result = query.get_all_data_since("2023-01-01T00:00:00")
        self.assertIn("CCDB_ID__c", result)
        self.assertIn("CCDB_Eligible__c", result)
