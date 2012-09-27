import webapp2
import jinja2
import os
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *args, **kwargs):
        self.response.out.write(*args, **kwargs)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        t.render(**params)

    def render(self, template, **kwargs):
        self.write(self.render_str(template, **kwargs))

class MainPageHandler(Handler):
    def get(self):
        self.response.headers["Content-Type"] = "text/plain"
        visits = self.request.cookies.get("visits", 0)
        if visits.isdigit():
            visits = int(visits)
            visits += 1
        else:
            visits = 0
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % visits)

        if visits > 10000:
            self.write("You are the best ever!")
        else:
            self.write('You have been here %s times' % visits)

app = webapp2.WSGIApplication([('/', MainPageHandler)], debug=True)
