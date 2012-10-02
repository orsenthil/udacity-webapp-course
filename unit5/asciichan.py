import os
import webapp2
import jinja2
import urllib2
from xml.dom import minidom

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

class Art(db.Model):
    title = db.StringProperty(required=True)
    art = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    coords = db.GeoPtProperty()

IP_URL = "http://api.hostip.info/?ip="

def get_coords(ip):
    # ip = "4.2.2.2" # Test URL
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except urllib2.URLError:
        return
    if content:
        try:
            d = minidom.parseString(content)
            elem = d.getElementsByTagName("gml:coordinates")[0]
            coords = elem.childNodes[0]
            lon, lat = coords.nodeValue.split(',')
            return db.GeoPt(lat, lon)
        except IndexError:
            return None

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"

def gmaps_img(points):
    markers = []
    for p in points:
        coords = 'markers=%d,%d' % (p.lat, p.lon)
        markers.append(coords)
    return GMAPS_URL + '&'.join(markers)

class Handler(webapp2.RequestHandler):
    def write(self, *args, **kws):
        self.response.out.write(*args, **kws)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kws):
        self.write(self.render_str(template, **kws))

class MainPage(Handler):

    def render_front(self, title="", art="", error=""):
        arts = db.GqlQuery("SELECT * from Art ORDER BY created DESC;")
        # prevent running of multiple queries
        arts = list(arts)
        points = []
        for a in arts:
            if a.coords:
                points.append(a.coords)
        img_url = gmaps_img(points)
        self.render("front.html", title=title, art=art, error=error, arts=arts, img_url=img_url)

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        if title and art:
            coords = get_coords(self.request.remote_addr)
            a = Art(title=title, art=art)
            if coords:
                a.coords = coords
            a.put()
            self.redirect("/")
        else:
            error = "We need both title and art"
            self.render_front(title=title, art=art, error=error)

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
