import unittest

from feasp.feasp import SimpleSqlite


class TestSimpleSqlite(unittest.TestCase):

    def test_common(self):
        handler = SimpleSqlite(":memory:")
        handler.create_table("Student", ["Name", "Age"])
        handler.insert("Student", ("Lns_XueFeng", 22))
        handler.insert_many("Student", [("XueFeng", 22), ("XueXue", 25), ("XueLian", 28)])
        handler.delete("Student", {"Name": "Lns_XueFeng", "Age": 22})
        handler.update("Student", {"Name": "Lns-XueFeng"}, ("Name", "Lns_XueFeng"))
        result = handler.fetch_all("Student")
        handler.close()
        self.assertEqual(result, [('Lns-XueFeng', 22), ('XueFeng', 22), ('XueXue', 25), ('XueLian', 28)])

    def test_context(self):
        with SimpleSqlite(":memory:") as handler:
            handler.create_table("Student", ["Name", "Age"])
            handler.insert("Student", ("Lns_XueFeng", 22))
            handler.insert_many("Student", [("XueFeng", 22), ("XueXue", 25), ("XueLian", 28)])
            handler.delete("Student", {"Name": "Lns_XueFeng", "Age": 22})
            handler.update("Student", {"Name": "Lns-XueFeng"}, ("Name", "Lns_XueFeng"))
            result = handler.fetch_all("Student")
        self.assertEqual(result, [('Lns-XueFeng', 22), ('XueFeng', 22), ('XueXue', 25), ('XueLian', 28)])
