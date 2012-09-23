import os
import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

class Handler(webapp2.RequestHandler):
    def write(self, *args, **kws):
        self.response.out.write(*args, **kws)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kws):
        self.write(self.render_str(template, **kws))

class MainPage(Handler):
    def get(self):
        self.write("ascii chan")

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
