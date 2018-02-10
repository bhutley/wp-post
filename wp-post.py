#!/usr/bin/env python
#
# wp-post.py
#
# Author: Brett Hutley <brett@hutley.net>
#
# This program is for uploading a markdown file as a post to a
# Wordpress site. You can also specify images that are in the post,
# and it will upload the images as well, and embed the path to the
# image on the server into your post.
#
import sys, os
#from wordpresslib import WordPressClient, WordPressPost
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
import xmlrpclib
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods.media import UploadFile
import markdown
from bs4 import BeautifulSoup
from ConfigParser import SafeConfigParser
from optparse import OptionParser

def upload_image(client, filename):
    # prepare metadata
    basename = os.path.basename(filename)
    (root, ext) = os.path.splitext(basename)
    if ext != ".png" and ext != ".jpg":
        print("ERROR: Currently can only upload png or jpg files")
        exit(0)
    else:
        ext = ext[1:]

    data = {
        'name': basename,
        'type': 'image/' + ext,  # mimetype
        }

    # read the binary file and let the XMLRPC library encode it into base64
    with open(filename, 'rb') as img:
        data['bits'] = xmlrpc_client.Binary(img.read())

    response = client.call(UploadFile(data))
    #print(response)
    # response == {
    #       'id': 6,
    #       'file': 'picture.jpg'
    #       'url': 'http://www.example.com/wp-content/uploads/2012/04/16/picture.jpg',
    #       'type': 'image/jpg',
    # }
    return response

optp = OptionParser()
optp.add_option("-c", "--config", dest="config_file", metavar="FILE",
                default= os.path.join(os.path.expanduser("~"), ".wp-blogs.cfg"),
                help="wordpress blogs configuration file")
optp.add_option("-b", "--blog", dest="blog", default="Main",
                help="Blog to post to.")
optp.add_option("-P", "--publish", dest="publish", action="store_true", default=False,
                help="Whether to publish the post automatically.")
optp.add_option("-C", "--categories", dest="categories", default="",
                help="A comma-separated list of categories.")
optp.add_option("-T", "--tags", dest="tags", default="",
                help="A comma-separated list of tags.")

opts, args = optp.parse_args()

if not os.path.exists(opts.config_file):
    error("config file '%s' doesn't exist" % opts.config_file)
    exit(1)

config_parser = SafeConfigParser()
config_parser.read(opts.config_file)

url = config_parser.get(opts.blog, 'url')
user = config_parser.get(opts.blog, 'user')
password = config_parser.get(opts.blog, 'password')

if len(args) < 1 or not os.path.isfile(args[0]) or not args[0].endswith("md"):
    print("Usage: %s <file.md> [<image1.png> <image2.png>...]" % (sys.argv[0], ))
    exit(0)

filename = args[0]
file = open(filename, 'r')
md_content = file.readlines()
file.close()
if len(md_content) < 2:
    print("Error: No content for post")
    exit(0)

md = markdown.Markdown(
        extensions=['fenced_code']
        )
for i in xrange(0, len(md_content)):
    md_content[i] = unicode(md_content[i], errors = 'replace')
html = md.convert("".join(md_content))

soup = BeautifulSoup(html, 'html.parser')
title = soup.findAll('h1', limit=1)[0].text
if len(title) < 5:
    print("Couldn't parse the title! Do you have an h1 title?")
    exit(0)

xmlrpc_url = url+"xmlrpc.php"
wp = Client(xmlrpc_url, user, password)

images = {}

# now process any images...
for i in xrange(1, len(args)):
    img_path = args[i]
    basename = os.path.basename(img_path)
    response = upload_image(wp, img_path)
    images[basename] = response

# select blog id
#wp.selectBlog(0)
post = WordPressPost()	
if title is not None:
    post.title = title

    html2 = ''
    lines = html.split("\n")
    found_h1 = False
    for line in lines:
        if found_h1 == False and line.find("<h1>") >= 0:
            found_h1 = True
        else:
            for imgname in images.keys():
                n1 = line.find(imgname)
                if n1 >= 0:
                    resp = images[imgname]
                    server_path = resp['url']
                    line = line[0:n1] + server_path + line[n1 + len(imgname):]
            html2 += ("%s\n" % (line, ))
    html = html2

post.content = html

publish = False
if opts.publish == True:
    publish = True

if len(opts.tags) > 0:
    tags = opts.tags.split(",")
    if not hasattr(post, 'terms_names') or post.terms_names is None:
        post.terms_names = {}
    post.terms_names['post_tag'] = tags

if len(opts.categories) > 0:
    cats = opts.categories.split(",")
    if not hasattr(post, 'terms_names') or post.terms_names is None:
        post.terms_names = {}
    post.terms_names['category'] = cats

post_id = wp.call(NewPost(post))
#print post.description
