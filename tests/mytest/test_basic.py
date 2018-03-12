import unittest

"""
When I'm on ~/dev/figure_portfolio directry
 `python -m unittest tests.test_basic` and
 `python setup.py test` works.
"""

from figure_portfolio import figure_portfolio

class TestCore(unittest.TestCase):

    text = '<div created="201801" modified="201802" '
    text2 = 'tags="yellow [[blue dot]]" title="Blue Moon" type="text/x-markdown">\n'
    text3 = '<pre>Hello moon\n'
    text4 = '</pre></div>\n'

    @classmethod
    def setUpClass(cls):
        # procedures before tests are started. This code block is executed only once
        pass

    @classmethod
    def tearDownClass(cls):
        # procedures after tests are finished. This code block is executed only once
        pass

    def setUp(self):
        # procedures before every tests are started. This code block is executed every time
        pass
	
    def tearDown(self):
        # procedures after every tests are finished. This code block is executed every time
        pass

    def test_twread_mockfile(self):
        infile = open("tests\\tw5md_mock.html", encoding="utf-8")
        # this is how TiddlyWiki file is parsed
        tw = figure_portfolio.TiddlyWikiParse(infile)
        tw.read_header()
        r_tiddlerlst = []
        r_tiddler = tw.read_tiddler()
        while r_tiddler:
            r_tiddlerlst.append(r_tiddler)
            r_tiddler = tw.read_tiddler()
        tw.read_trailer()
        infile.close()
        tw.tiddlers = r_tiddlerlst

        infile = open("tests\\tw5md_mock.html", encoding="utf-8")
        lst = infile.readlines()
        infile.close()
        for i in range(len(tw.headerlines)):
            self.assertEqual(lst[i], tw.headerlines[i])
        lptr = len(tw.headerlines)
        for i in range(len(r_tiddlerlst)):
            for j in range(len(r_tiddlerlst[i].text)):
                self.assertEqual(lst[lptr], r_tiddlerlst[i].text[j])
                lptr += 1
        for i in range(len(tw.trailerlines)):
            self.assertEqual(lst[lptr], tw.trailerlines[i])
            lptr += 1
        self.assertEqual(lptr, len(lst))
        self.assertEqual('$:/config/markdown/dialect', tw.tiddlers[0].title)
        self.assertEqual('20180206151146040', tw.tiddlers[0].created)
        self.assertEqual('Generated tiddler markdown', tw.tiddlers[1].title)
        self.assertEqual('20180209221111649', tw.tiddlers[1].created) 
        self.assertEqual(['blue', '[[red dot]]'],  tw.tiddlers[1].tags)
        self.assertEqual('Recently Added', tw.tiddlers[2].title)
        self.assertEqual('20180206144335953', tw.tiddlers[2].created) 
        self.assertEqual(['blue', '[[red dot]]'],  tw.tiddlers[1].tags)

        tw.tags()
        self.assertEqual(['blue', '[[red dot]]'],  tw.taglist)

        i, created = tw.find_tiddler('Recently Added')        
        self.assertEqual(2, i)
        self.assertEqual('20180206144335953', created)

    def test_read_mock(self):
        infile = "tests\\tw5md_mock.html"
        tw = figure_portfolio.TiddlyWikiParse(infile)
        tw.read()

        with open("tests\\tw5md_mock.html", encoding="utf-8") as infile:
            lst = infile.readlines()

        for i in range(len(tw.headerlines)):
            self.assertEqual(lst[i], tw.headerlines[i])
        lptr = len(tw.headerlines)
        for i in range(len(tw.tiddlers)):
            for j in range(len(tw.tiddlers[i].text)):
                self.assertEqual(lst[lptr], tw.tiddlers[i].text[j])
                lptr += 1
        for i in range(len(tw.trailerlines)):
            self.assertEqual(lst[lptr], tw.trailerlines[i])
            lptr += 1
        self.assertEqual(lptr, len(lst))

    def test_Tiddler(self):
        test_text = [
        '<div created="2018" modified="0210" tags="a [[b c]]" title="Spring">\n',
        '<pre>&lt;&lt;timeline field:&quot;created&quot;&gt;&gt;</pre>\n',
        '</div>\n']
        tiddler = figure_portfolio.Tiddler(test_text)
        tiddler.parse()

        test_title = 'Spring'
        test_tags = ['a', '[[b c]]']
        test_created = '2018'
        self.assertEqual(test_title, tiddler.title)
        self.assertEqual(test_tags, tiddler.tags)
        self.assertEqual(test_created, tiddler.created)

    def test_tiddlytag(self):
        tags = [('python', 'python'), ('blue sky', '[[blue sky]]')]
        for rawtag, tiddly_tag in tags:
            result = figure_portfolio.tiddlytag(rawtag)
            self.assertEqual(tiddly_tag, result)  

    def test_markdownimage(self):
        img = 'mytest.png'
        self.assertEqual('![image](mytest.png){:width="1000"}\n', 
            figure_portfolio.markdownimage(img))

    def test_tiddler_generate(self):
        # makes a tiddler block
        tid = figure_portfolio.tiddler_generate('Blue Moon', 'Hello moon', 
            ['yellow', '[[blue dot]]'], '201801', '201802')
        self.assertEqual(TestCore.text + TestCore.text2, tid.text[0])
        self.assertEqual(TestCore.text3, tid.text[1])
        self.assertEqual(TestCore.text4, tid.text[2])
        self.assertEqual('Blue Moon', tid.title)
        self.assertEqual('201801', tid.created)
        self.assertEqual(['yellow', '[[blue dot]]'], tid.tags)

    def test_new_tiddler(self):
        infile = "tests\\tw5md_mock.html"
        tw = figure_portfolio.TiddlyWikiParse(infile)
        tw.read()
        tw.tags()        # (a)

        tw.new_tiddler('Blue Moon', 'Hello moon\n', ['yellow', '[[blue dot]]'], 
            replace=True)
        self.assertEqual(TestCore.text[:14], tw.tiddlers[3].text[0][:14])
        self.assertEqual(TestCore.text2, tw.tiddlers[3].text[0][-69:])
        self.assertEqual('Blue Moon', tw.tiddlers[3].title)
        self.assertEqual(['yellow', '[[blue dot]]'], tw.tiddlers[3].tags)

        # case for existing tiddler
        text41 = 'tags="yellow [[red dot]]" title="Recently Added" type="text/x-markdown">\n'
        text42 = '<pre># Hello moon\n'
        text43 = '* Hello sun\n'
        text44 = '</pre></div>\n'
        tw.new_tiddler('Recently Added', '# Hello moon\n* Hello sun', 
            ['yellow', '[[red dot]]'], replace=True)
        self.assertEqual(TestCore.text[:19], tw.tiddlers[2].text[0][:19])
        self.assertEqual(text41, tw.tiddlers[2].text[0][-73:])
        self.assertEqual(text42, tw.tiddlers[2].text[1])
        self.assertEqual(text43, tw.tiddlers[2].text[2])
        self.assertEqual(text44, tw.tiddlers[2].text[3])
        self.assertEqual('Blue Moon', tw.tiddlers[3].title)
        self.assertEqual(['yellow', '[[blue dot]]'], tw.tiddlers[3].tags)
        
        self.assertEqual(['blue', '[[red dot]]'], tw.taglist) # retained from (a)

        # make a new taglist tiddler
        tw.taglist_tiddler()        
        text50 = ['<pre>!!! blue\n',
            '&lt;&lt;list-links &quot;[tag[blue]]\n',
            '&gt;&gt;!!! red dot\n',
            '&lt;&lt;list-links &quot;[tag[red dot]]\n',
            '&gt;&gt;\n',
            '</pre></div>\n']
        for i in range(len(text50)):
            self.assertEqual(text50[i], tw.tiddlers[-1].text[i + 1])
        self.assertEqual('Tag List', tw.tiddlers[-1].title)
        with self.assertRaises(AttributeError):
            tw.tiddlers[-1].tag
        
        tw.tags()
        
        # overwrite an existing taglist tiddler
        self.assertEqual(['blue', '[[red dot]]', 'yellow', '[[blue dot]]'], 
            tw.taglist)
        tw.taglist_tiddler()
        index, created = tw.find_tiddler('Tag List')
        tw.tiddlers[index].text
        text60 = [ '<pre>!!! blue\n',
            '&lt;&lt;list-links &quot;[tag[blue]]\n',
            '&gt;&gt;!!! red dot\n',
             '&lt;&lt;list-links &quot;[tag[red dot]]\n',
             '&gt;&gt;!!! yellow\n',
             '&lt;&lt;list-links &quot;[tag[yellow]]\n',
             '&gt;&gt;!!! blue dot\n',
             '&lt;&lt;list-links &quot;[tag[blue dot]]\n',
             '&gt;&gt;\n',
             '</pre></div>\n']
        for i in range(len(text60)):
            self.assertEqual(text60[i], tw.tiddlers[index].text[i + 1])
        self.assertEqual('Tag List', tw.tiddlers[index].title)
        with self.assertRaises(AttributeError):
            tw.tiddlers[-1].tag

        text70 = [ 'tags="yellow [[red dot]]" title="Recently Added-01" type="text/x-markdown">\n', 
            '<pre># Hello jupiter\n', 
            '* Hello saturn\n', 
            '</pre></div>\n']
        tw.new_tiddler('Recently Added', '# Hello jupiter\n* Hello saturn', 
            ['yellow', '[[red dot]]'], replace=False)
        self.assertEqual(text70[0], tw.tiddlers[-1].text[0][-76:])
        self.assertEqual(text70[1], tw.tiddlers[-1].text[1])
        self.assertEqual(text70[2], tw.tiddlers[-1].text[2])
        self.assertEqual(text70[3], tw.tiddlers[-1].text[3])
        self.assertEqual('Recently Added-01', tw.tiddlers[-1].title)
        self.assertEqual(['yellow', '[[red dot]]'], tw.tiddlers[-1].tags)

        #### chek code
#    text = '<div created="201801" modified="201802" '
#    text2 = 'tags="yellow [[blue dot]]" title="Blue Moon" type="text/x-markdown">\n'
#    text3 = '<pre>Hello moon\n'
#    text4 = '</pre></div>'
    def test_new_tiddlywiki(self):
        """Round trip check: read the generated file tw2 to see any change is
        found"""
        infile = "tests\\tw5md_mock.html"
        tw = figure_portfolio.TiddlyWikiParse(infile)
        tw.read()

        outfile = "tests\\test_output.txt"
        tw.publish(outfile)

        tw2 = figure_portfolio.TiddlyWikiParse(outfile)
        tw2.read()
        for hl1, hl2 in zip(tw.headerlines, tw2.headerlines):
            self.assertEqual(hl1, hl2)
        for tid1, tid2 in zip(tw.tiddlers, tw2.tiddlers):
            for tid1_l, tid2_l in zip(tid1.text, tid2.text):
                self.assertEqual(tid1_l, tid2_l)
        for tl_1, tl_2 in zip(tw.trailerlines, tw2.trailerlines):
                self.assertEqual(tl_1, tl_2)
        



if __name__ == '__main__':
    unittest.main()