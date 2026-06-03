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

    def test_get_time_slice_since_only(self):
        """Verify the query when only the 'since' parameter is provided."""
        since = "2023-01-01T00:00:00"
        result = query.get_time_slice(since)

        self.assertTrue(result.startswith("SELECT CreatedDate,"))
        self.assertIn(f"AND LastModifiedDate >= {since}", result)
        self.assertNotIn("AND LastModifiedDate <", result)

    def test_get_time_slice_with_til(self):
        """Verify the query when both 'since' and 'til' parameters are provided."""
        since = "2023-01-01T00:00:00"
        til = "2023-02-01T00:00:00"
        result = query.get_time_slice(since, til)

        self.assertIn(f"AND LastModifiedDate >= {since}", result)
        self.assertIn(f"AND LastModifiedDate < {til}", result)

    def test_query_includes_all_fields(self):
        """Check that expected fields/pieces of the query exist."""
        result = query.get_time_slice("2023-01-01T00:00:00")
        self.assertIn("CCDB_ID__c", result)
        self.assertIn("FROM Case WHERE CCDB_Eligible__c = true", result)
