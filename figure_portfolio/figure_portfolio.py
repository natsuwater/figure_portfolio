# -*- coding: utf-8 -*-
"""
figure_portfolio.py
~~~~~~~~~~~~~~~~~~~

Created on Fri Feb  9 21:41:28 2018

@author: N. Mizutani
"""

import datetime
import re
import html
from html.parser import HTMLParser
import os
import tempfile
import shutil

class MyHTMLParser(HTMLParser):
    """Extract information out of div element. """
    def handle_starttag(self, tag, attrs):
        if tag == "div":
            self.divattrs = dict(attrs)

regtag = re.compile(r'(?:\[\[)[\w ]+(?:\]\])'
            '|\w+') 
# [[ any number of (a-zA-Z0-9(SPC))]] or any number of (a-zA-Z0-9) 
# (?: [[) drops out '[[' part and (?: ]]) drops out '[[' ']]')
# t = 'blue [[red dot]] [[my red Z]] brown'
# regtag.findall(t) # returns ['blue', '[[red dot]]', '[[my red Z]]', 'brown']

class Tiddler(object):
    """Keeps the tiddler text, title, created and modified date, tags."""
    def __init__(self, text):
        """Constructor

        :param list text: List of the text lines for the tiddler object.
        """
        self.text = text
        self.taglist = []
        
    def parse(self):
        """Parse the Tiddler contents. """
        parser = MyHTMLParser()
        parser.feed(''.join(self.text))
        self.title = parser.divattrs.get('title')
        self.created = parser.divattrs.get('created')
        if not self.title.startswith(r'$:/'):
            divtags = parser.divattrs.get('tags')
            if divtags:
                self.tags = regtag.findall(divtags)
        
    def __repr__(self):
        return self.title + ": " + ''.join(self.text)[:40]

class TiddlyWikiParse(object):
    def __init__(self, infile): 
        """Constructor. `infile` is opened by the call `self.read()`. """
        self.infile = infile

    def read_header(self):
        """Reads the part from the top to just before the tiddlers. """
        endofheader = '<div id="storeArea" style="display:none;">\n'
        headerlines = []
        headerlines.append(self.infile.readline())
        while headerlines[-1] != endofheader:
            headerlines.append(self.infile.readline())
        self.headerlines = headerlines
        
    def read_tiddler(self):
        """Reads all the tiddlers. """
        endoftiddlerblock = '<!--~~ Library modules ~~-->\n'
        startoftiddler = '<div created='
        endoftiddler = '</div>\n'
        lines = []
        lines.append(self.infile.readline())
        while not lines[-1].startswith(startoftiddler):
            if lines[-1] == endoftiddlerblock:
                self.buffer = lines
                return None
            lines.append(self.infile.readline())
        while not lines[-1].endswith(endoftiddler):
            lines.append(self.infile.readline())
        r_tiddler = Tiddler(lines)
        r_tiddler.parse()
        return r_tiddler

    def read_trailer(self):
        """Read the trailing part. """
        trailerlines = self.buffer
        line = self.infile.readline()
        while line:
            trailerlines.append(line)
            line = self.infile.readline()
        self.trailerlines = trailerlines

    def read(self): 
        """Read all the text of a tiddly wiki file."""
        tiddlers = []
        with open(self.infile, encoding="utf-8", mode='r') as infile:
            self.infile = infile

            self.read_header()
            r = self.read_tiddler()
            while r:
                tiddlers.append(r)
                r = self.read_tiddler()
            self.read_trailer()
        
        self.tiddlers = tiddlers
        self.tags()

    def tags(self):
        """Collect the tag used in the tiddlers."""
        self.taglist = []
        for td in self.tiddlers:
            try:
                for tag in td.tags:
                    if tag not in self.taglist:   # might be simpler with set
                        self.taglist.append(tag)  # however, list keep the order
            except AttributeError:
                pass

    def find_tiddler(self, title):
        """Find a tiddler by its title.
        
        :param str title: Title of tiddler.
        """
        for i, td in enumerate(self.tiddlers):
            if title == td.title: #replace = True
                return i, self.tiddlers[i].created
        return None, None

    def taglist_tiddler(self):
        """Generate a tiddler `Tag List` listing all tags. """
        title = 'Tag List'
        modified = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        index, created = self.find_tiddler(title)
        if created == None:
            created = modified
        ptext = ''
        for t in self.taglist:
            if t.startswith("[[") and t.endswith("]]"):
                t = t[2:-2]
            ptext += '!!! {}\n'.format(t)
            ptext += '<<list-links "[tag[{}]]">>\n'.format(t)
        tags = ''
        # "20180210 0511 39454"
        tid = tiddler_generate(title, ptext, tags, created, modified)
        if index:
            self.tiddlers[index] = tid
        else:
            self.tiddlers.append(tid)
            
    def new_tiddler(self, title, ptext, tags, replace):
        """Collect the parameter and call `tiddler_generate()`.
        
        :param str title: Title of the new tiddler.
        :param str ptext: Markdown style text content of the tiddler.
        :param tags: Tags added to the tiddler.
        :type tags: str or list
        :param boolean replace: Replace the existing tiddler when an old one exists. 
        """
        tidtype = 'text/x-markdown'
        modified = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        index, created = self.find_tiddler(title)
        if replace:
            tlnext = title
            if created == None:
                created = modified
        else:
            if index:
                for i in range(1, 100):
                    tlnext = title + '-{0:02d}'.format(i)
                    index, created = self.find_tiddler(tlnext)
                    if index == None:
                        break
                else: 
                    msg = "Warning: Overwriting the 100 th tiddler '{}' "
                    print(msg.format(tlnext))
            else:
                tlnext = title
        tid = tiddler_generate(tlnext, ptext, tags, created, modified, tidtype)
        tid.title = tlnext
        if index:
            self.tiddlers[index] = tid
        else:
            self.tiddlers.append(tid)

    def publish(self, outfile):
        """Write the tiddly wiki to `outfile`. """
        with open(outfile, encoding='utf-8', mode='w') as twout:
            for head_l in self.headerlines:
                twout.write(head_l)
            for tid in self.tiddlers:
                for tid_l in tid.text:
                    twout.write(tid_l)
            for trail_l in self.trailerlines:
                twout.write(trail_l)

def tiddlytag(tg):
    """Format the tags for tiddlywiki5;   
    when the tag includes white space, it is surrounded by '[[' ']]'.

    :param str tg: A tag.
    :return: Decorated tag.
    """
    if ' ' in tg:
        return '[[' + tg + ']]'   
    else:
        return tg

def markdown_ptext(image, description):
    """Generate the tiddler text conbining the image and description.

    :param image: The path to the imagefile.
    :type image: list or str    
    :param description str: Text part of the tiddler.  
    :return: The tiddler text.
    """    
    if type(image) == list:
        ptxt = [markdownimage(im) for im in image]
        ptxt = ''.join(ptxt) + description
    else:   
        ptxt = markdownimage(image) + description
    return ptxt

def markdownimage(img, width=1000):
    """Format the image embedding using the markdown notation.

    :param str img: Relative path to the image.
    :param int width: Width of the image.
    :return: Markdown string.
    """
    return '![image](' + img + '){:width="' + str(width) + '"}\n'

def tiddler_generate(title, ptext, tags, created, modified, tidtype=''):
    """Create a `Tiddler`.

    :param str title: Title of the tiddler
    :param str ptext: Markdown style text of the tiddler
    :param tags: Tags
    :type tags: str or list
    :param str created: The date and time the tiddler is originally generated. 
    :param str modified: The date and time the tiddler is last edited.
    :param str tidtype: Tiddler type `markdown` or empty for native format. 
    :returns: Generated Tiddler.
    """
    tagstr = ''
    if type(tags) == list:
        for t in tags:
            tagstr += ' {0}'.format(t)
        tagstr = tagstr.strip()
    else:
        tagstr = tags
    tidd_hdr = '<div created="{created}" modified="{modified}" '
    tidd_hdr += 'tags="{tags}" title="{title}" type="{tidtype}">\n'
    tidd_hdr = tidd_hdr.format(created=created, modified=modified, tags=tagstr, 
        title=title, tidtype=tidtype)
    tidd_tlr = '\n</pre></div>'
    tidd_cnts = '<pre>{description}'.format(description=html.escape(ptext))
    tmp = tidd_hdr + tidd_cnts + tidd_tlr
    tmp = tmp.split('\n')
    tmp = [t + '\n' for t in tmp]
    tid = Tiddler(tmp)
    tid.parse()
    
    return tid

def relative_path_to_image(outfile, image):
    """Convert image file path relative to the html file (Wrapper). """ 
    opath = os.path.normpath(outfile)
    if type(image) == list:
        image = [trim_path_to_image(opath, im) for im in image]
    else:   
        image = trim_path_to_image(opath, image)
    return image

def trim_path_to_image(outfile, impath):
    """Convert image file path relative to the html file.

    :param str outfile: Path to the output file.
    :param str impath: Path to the image file.
    :return: Relative path from `outfile` to `impath`. 
    """
    opath_ele = os.path.normpath(outfile).split('\\')
    im_ele = os.path.normpath(impath).split('\\')
    olen, ilen = len(opath_ele), len(im_ele)
    for i in range(min(olen, ilen)):
            if im_ele[i] != opath_ele[i]:
                break
    r_impath = os.path.join( "..\\" * (olen - 1 - i), 
            *im_ele[i:])            
    return os.path.normpath(r_impath)

#%%    
def addtiddler(infile, title, outfile=None, image=None, description='', 
    tags='', replace=True):
    """Add a new tiddler to a TiddlyWiki file.

    :param str infile: TiddlyWiki file.
    :param str title: The title of the new tiddler.
    :param str outfile: Output file. When it is `None`, overwrites the input file.
    :param image: The image file(s) to be linked from the new tiddler.
    :type image: list or str
    :param description: The text content of the new tiddler (mark down text).
     Either `image` or `description` must have some content at least. 
    :type description: list or str
    :param tags: Tags to be added to the new tiddler. Multiple tag can be 
     string, `"red, blue triangle"` or a list `["red", "blue triangle"]`. 
     Alpha numeric + SPC + underscore can be used for the tag.
    :type tags: list or str
    :param boolean replace: Replace an existing tiddler with the same title (True)
     or rename the new one as 'title-1'(maximum 'title-99').
    """
    # infile = "tests\\tw5md_mock.html"
    tw = TiddlyWikiParse(infile)
    tw.read()

    if image == None:
        if description == '' or description == None:
            print("addtiddler() requires at least `image` or `description`.")
            return None
    else:
        if outfile == None:
            image = relative_path_to_image(infile, image)
        else:
            image = relative_path_to_image(outfile, image)

    if image != None:
        ptxt = markdown_ptext(image, description)
    else:
        ptxt = description

    tagold = tw.taglist
    if type(tags) != list:
        tags = tags.split(',')
    if type(tags) == list:
        tags = [tiddlytag(t.strip()) for t in tags]
    else:
        tags = [tiddlytag(tags)]

    tw.new_tiddler(title, ptxt, tags, replace)
    tw.tags()
    tagnew = tw.taglist
    if tagnew != tagold:
        tw.taglist_tiddler()

    if outfile == None:
        tempd = tempfile.gettempdir()
        tmpfile = os.path.join(tempd, os.path.split(infile)[1] + '.tmp')
    else:
        tmpfile = outfile
    tw.publish(tmpfile)
    print("published: ", tmpfile)
    if outfile == None:
       shutil.move(tmpfile, infile) 

#%%
"""
# tags are put together in one string (as from optparse) 
    addtiddler(infile='figure_portfolio\\tw5md_empty0.html', 
                outfile='figure_portfolio\\tw5md_empty0_n.html' ,
                image='\\tests\\p30.png', 
                description='This is the initial run \n for theis script', 
                tags='test, png image ', 
                title='Second Tiddler')

# tags are in a list of string
    addtiddler(infile='figure_portfolio\\tw5md_empty0_n.html', 
                outfile='figure_portfolio\\tw5md_empty0_n.html' ,
                image='\\tests\\p30.png', 
                description='This is the initial run \n for theis script', 
                tags=['test', 'png image '], 
                title='Third Tiddler')
# No image
    addtiddler( infile='figure_portfolio\\tw5md_empty0_n.html' ,
                outfile='figure_portfolio\\tw5md_empty0_n.html' ,
                description='This is the initial run \n for theis script', 
                tags='test, png image ', 
                title='Fifth tiddler')
# comma delimited but only one tag
    addtiddler( infile='figure_portfolio\\tw5md_empty0_n.html' ,
                description='This is the initial run \n for theis script', 
                tags='test, ', 
                title='Sixth tiddler',
                replace=False)

"""       

#%%
if __name__ == "__main__":
    # Parse commandline arguments if this module is run as a script.

    import optparse
    import glob
    parser = optparse.OptionParser()
    parser.add_option('-i', 
                        action='store', 
                        dest='infile', 
                        help='Path to input TiddlyWiki file. Required.')
    parser.add_option('--title', 
                        action='store',
                        dest='title',
                        help='Title for the new Tiddler. Required.')
    parser.add_option('-o', 
                        action='store', 
                        dest='outfile', 
                        help='Relative path to output TiddlyWiki file.  If not specified, tiddler will be added to INPUT.')
    parser.add_option ('--description', 
                        action='store', 
                        default='', 
                        dest='description', 
                        help='Text to be added below the image in the tiddler. Markdown (Maruku flavor) can be used.')
    parser.add_option('--image', 
                        action='store', 
                        dest='image', 
                        help='Path to image, "*.png" gets expanded.')
    parser.add_option('--tags', 
                        action='store', 
                        dest='tags', 
                        default='', 
                        help='Quoted space-delimited tags for this tiddler.  Ex: --tags "images temperature depth"')
    (options, args) = parser.parse_args()
    images = glob.glob(options.image)

    addtiddler(infile=options.infile, 
                outfile=options.outfile, 
                image=images, 
                description=options.description, 
                tags=options.tags, 
                title=options.title)

