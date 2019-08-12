import unittest

class BashQuoteTests(unittest.TestCase):


    def test_bash_quote_special(self):
        from argv_quote import BASH_RESERVED_WORDS, bash_quote

        for word in BASH_RESERVED_WORDS:
            self.assertEqual("\\" + word, bash_quote(word))

        for char in ('\t',
                     ' ', '!', '"', '#',
                     '$', '&', "'", '(',
                     ')', '*', ':', ';',
                     '<', '>', '?', '@',
                     '[', ']', '^', '`',
                     '{', '|', '}', '~'):
            self.assertEqual("\\" + char, bash_quote(char))

    def test_bash_quote_strings(self):
        from argv_quote import bash_quote

        self.assertEqual("'this is a simple path with spaces'",
                     bash_quote('this is a simple path with spaces'))

        self.assertEqual("don\\'t", bash_quote("don't"))
        self.assertEqual('"don\'t do it"', bash_quote("don't do it"))


class WindowsQuoteTests(unittest.TestCase):

    def testEmbeddedSpace(self):
        from argv_quote import win_concact_quote, win_quote
        self.assertEqual( 'x x x "z z"', win_concact_quote('x x x', 'z z'))

        self.assertEqual('x y "z z" zed', win_quote('x', 'y', 'z z', 'zed'))

    def testBackslashes(self):
        import argv_quote
        self.assertEqual(r'"C:\Program Files\my program\thing.exe" "\\someserver\funny share\path\\" "a\"quote\"here"',
            argv_quote.win_quote(r'C:\Program Files\my program\thing.exe',
                                  '\\\\someserver\\funny share\\path\\',
                                  'a"quote"here'))

class OsDefinedQuoteTests(unittest.TestCase):

    def testOsSelection(self):
        import sys
        from argv_quote import quote
        if sys.platform == 'win32':
            self.assertEqual('"I am" Windows not bash', quote('I am', 'Windows', 'not', 'bash'))
        else:
            self.assertEqual("'I am' in \\bash", quote('I am', 'in', 'bash'))
