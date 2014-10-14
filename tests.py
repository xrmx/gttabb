import unittest
from gttabb import Cache

class CacheTest(unittest.TestCase):
    def test_insertion(self):
        cache = Cache()
        self.assertFalse('foo' in cache)
        cache['foo'] = 'bar'
        self.assertTrue('foo' in cache)
        self.assertEqual(cache['foo'], 'bar')

    def test_load_dump(self):
        cache = Cache('test.cache')
        self.assertEqual(cache['foo'], 'bar')
        cache['foo'] = 'baz'
        cache.dump()
        cache = Cache('test.cache')
        self.assertEqual(cache['foo'], 'baz')
        # reset to default value
        cache['foo'] = 'bar'
        cache.dump()

if __name__ == '__main__':
    unittest.main()
