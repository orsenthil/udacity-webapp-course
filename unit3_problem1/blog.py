import webapp2
import jinja2
import os
import datetime

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                              autoescape=True)

class BlogPost(db.Model):
    topic = db.StringProperty(required=True)
    post = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class Handler(webapp2.RequestHandler):

    def write(self, *args, **kwargs):
        self.response.out.write(*args, **kwargs)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kwargs):
        self.write(self.render_str(template, **kwargs))

class BlogMainPageHandler(Handler):
    def render_front_page(self, **kwargs):
        self.render("front.html", **kwargs)

    def get(self):
        # Gql for all the blog entries.
        allposts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created desc;")
        self.render_front_page(allposts=allposts)

class SubmitNewEntry(Handler):
    def render_submit(self, **kwargs):
        self.render("submit.html", **kwargs)

    def get(self):
        self.render_submit(topic="", post="", error="")

    def post(self, *args, **kwargs):
        topic = self.request.get("subject")
        post = self.request.get("content")

        if topic and post:
            b = BlogPost(topic=topic, post=post)
            b.put()
            self.redirect("/")
        else:
            error = "Please provide title and post"
            self.render_submit(topic=topic, post=post, error=error)

class PermaLinkEntryHandler(Handler):
    def render_blog_post(self, **kwargs):
        self.render("blog.html", **kwargs)

    def get(self, postid):
        post = BlogPost.get_by_id(int(postid))
        self.render_blog_post(topic=post.topic, post=post.post)

app = webapp2.WSGIApplication([('/', BlogMainPageHandler),
                               ('/newpost', SubmitNewEntry),
                               ('/(\d+)', PermaLinkEntryHandler)], debug=True)
