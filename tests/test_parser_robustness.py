import copy
import os
import unittest
import warnings
from functools import lru_cache
from unittest.mock import patch

from congressionalrecord.govinfo import cr_parser as cr

DAY = "tests/test_files/CREC-2005-07-20"


def granule(name):
    return os.path.join(DAY, "html", name + ".htm")


@lru_cache(maxsize=None)
def day():
    """The fixture day's MODS, read once; the parser never modifies it."""
    return cr.ParseCRDir(DAY)


def speeches(parser):
    return [
        (item["speaker"], item["text"])
        for item in parser.crdoc["content"]
        if item["kind"] == "speech"
    ]


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


class testSpeakerPatternPerDocument(unittest.TestCase):
    """Each document matches speeches against its own MODS speaker list."""

    # Four of its speeches are Ms. MILLENDER-McDONALD's, which only its
    # speaker list matches; OTHER's list names someone else.
    DOC = granule("CREC-2005-07-20-pt1-PgH6115-2")
    OTHER = granule("CREC-2005-07-20-pt1-PgE1539-3")

    def setUp(self):
        self.crdir = day()

    def test_parse_leaves_the_class_table_unchanged(self):
        before = copy.deepcopy(cr.ParseCRFile.item_types)
        # Two different speaker lists, so a write cannot match by chance.
        for path in (self.DOC, self.OTHER):
            cr.ParseCRFile(path, self.crdir)
            self.assertEqual(cr.ParseCRFile.item_types, before)

    def test_documents_parsed_in_sequence_keep_their_own_patterns(self):
        doc = cr.ParseCRFile(self.DOC, self.crdir)
        other = cr.ParseCRFile(self.OTHER, self.crdir)
        self.assertNotEqual(doc.re_newspeaker, other.re_newspeaker)
        self.assertEqual(doc.item_types["speech"]["patterns"], [doc.re_newspeaker])
        self.assertEqual(other.item_types["speech"]["patterns"], [other.re_newspeaker])

    def test_document_begun_mid_parse_leaves_the_speakers_alone(self):
        alone = speeches(cr.ParseCRFile(self.DOC, self.crdir))
        self.assertIn("Ms. MILLENDER-McDONALD", [s for s, _ in alone])
        item, other = cr.crItem, []

        def other_document_first(parser):
            # What a second thread does: start another document mid-parse.
            if not other:
                other.append(None)
                other[0] = cr.ParseCRFile(self.OTHER, self.crdir)
            return item(parser)

        with patch(
            "congressionalrecord.govinfo.cr_parser.crItem",
            side_effect=other_document_first,
        ):
            interleaved = cr.ParseCRFile(self.DOC, self.crdir)
        self.assertIsNotNone(other[0])
        self.assertEqual(speeches(interleaved), alone)
