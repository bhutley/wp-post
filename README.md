# wp-post.py #

This program is for uploading a markdown file as a post to a Wordpress site. You can also specify images that are in the post, and it will upload the images as well, and embed the path to the image on the server into your post.

It depends on python-wordpress-xmlrpc being installed, as well as Beautiful Soup and markdown.

It takes the first h1 html tag of the generated output to be the title of the blog post. It looks for the configuration for each blog is in a file in your home directory called "~/wp-blogs.cfg". It uses this to get the username and password for each blog.

the .wp-blogs.cfg file should look like this:

    [Main]
    url = https://my-main-blog.com/
    user = username
    password = password
    
    [secondblog]
    url = https://second-blog.com/
    user = username2
    password = password2

If you don't specify a blog to use on the command line, it will use the 'Main' config by default.
