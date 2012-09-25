import webapp2
import jinja2
import os

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                              autoescape=True)

class BlogPost(db.Model):
    title = db.StringProperty(required=True)
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
    def render_front_page(self):
        self.render("front.html")

    def get(self):
        self.render_front_page()

class SubmitNewEntry(Handler):
    def render_submit(self):
        self.render("submit.html")

    def get(self):
        self.render_submit()

class PermaLinkEntryHandler(Handler):
    def render_blog_post(self):
        self.render("blog.html")

    def get(self):
        self.render_blog_post()

app = webapp2.WSGIApplication([('/', BlogMainPageHandler),
                               ('/submit', SubmitNewEntry),
                               ('/(\d+)', PermaLinkEntryHandler)], debug=True)
