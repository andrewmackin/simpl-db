import unittest
import shutil
import os
from dbms import Database

class TestDuplicateInsertion(unittest.TestCase):
    def setUp(self):
        self.data_dir = 'test_data_duplicate'
        shutil.rmtree(self.data_dir, ignore_errors=True)
        os.makedirs(self.data_dir, exist_ok=True)
        self.db = Database(data_dir=self.data_dir)

    def test_duplicate_insertion(self):
        self.db.execute("CREATE TABLE users (id, name)")
        insert_result1 = self.db.execute("INSERT INTO users VALUES (1, 'Alice')")
        insert_result2 = self.db.execute("INSERT INTO users VALUES (1, 'Bob')")

        result = self.db.execute("SELECT * FROM users")
        expected = [{'id': 1, 'name': 'Bob'}]
        self.assertEqual(result, expected, "Duplicate insertion test failed.")
        self.assertEqual(insert_result1, "1 row inserted into users.")
        self.assertEqual(insert_result2, "1 row inserted into users.")

    def tearDown(self):
        shutil.rmtree(self.data_dir, ignore_errors=True)
