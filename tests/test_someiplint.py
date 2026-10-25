import unittest
from someiplint import lint
class SomeIpTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(lint({"service_id":1,"version":{"major":1,"minor":0},"methods":[{"id":1,"name":"M","reliability":"reliable"}],"events":[]}),[])
    def test_collision(self):
        errors=lint({"service_id":1,"version":{"major":1,"minor":0},"methods":[{"id":2,"name":"M","reliability":"reliable"}],"events":[{"id":2,"reliability":"reliable"}]})
        self.assertTrue(any("collision" in e for e in errors))
if __name__=="__main__": unittest.main()
