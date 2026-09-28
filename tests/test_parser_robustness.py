import os
import unittest
import warnings
from functools import lru_cache

from congressionalrecord.govinfo import cr_parser as cr

DAY = "tests/test_files/CREC-2005-07-20"


def granule(name):
    return os.path.join(DAY, "html", name + ".htm")


@lru_cache(maxsize=None)
def day():
    """The fixture day's MODS, read once; the parser never modifies it."""
    return cr.ParseCRDir(DAY)


class testBeautifulSoupArguments(unittest.TestCase):
    def test_parse_uses_no_deprecated_argument(self):
        crdir = day()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            cr.ParseCRFile(granule("CREC-2005-07-20-pt1-PgH6115-2"), crdir)
        ours = [
            str(w.message)
            for w in caught
            if issubclass(w.category, DeprecationWarning)
            and os.path.realpath(w.filename) == os.path.realpath(cr.__file__)
        ]
        self.assertEqual(ours, [])
