import webapp2
import jinja2
import os
import cgi
import hashlib
import re

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                              autoescape=True)

class WikiEntry(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class Handler(webapp2.RequestHandler):

    def _write(self, *args, **kwargs):
        self.response.out.write(*args, **kwargs)

    def _render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kwargs):
        self._write(self._render_str(template, **kwargs))

class SubmitNewEntry(Handler):
    def render_submit(self, **kwargs):
        self.render("submit.html", **kwargs)

    def get(self):
        self.render_submit(topic="", post="", error="")

    def post(self, *args, **kwargs):
        title = self.request.get("title")
        content = self.request.get("content")

        if title and content:
            b = WikiEntry(title=title, content=content)
            b.put()
            self.redirect("/")
        else:
            error = "Please provide title and post"
            self.render_submit(title=title, content=content, error=error)

class WikiPage(Handler):
    def render_wiki_page(self, **kwargs):
        self.render("wiki.html", **kwargs)

    def get(self, pagename):
        # get the page by pagename, if it does not exist, redirect to create
        # page.

        pagename = pagename.rsplit('/')[-1]
        if not pagename:
            pagename = 'index'
        page = db.GqlQuery(r"SELECT * FROM WikiEntry WHERE title=:1 limit 1;", pagename).get()

        if page is None:
            redirect_page = "/_edit/%s" % pagename
            self.redirect(redirect_page)
        else:
            self.render_wiki_page(content=page.content)

class EditPage(Handler):
    def render_wiki_page(self, **kwargs):
        self.render("edit.html", **kwargs)

    def post(self, *args, **kwargs):
        title = self.request.get("title")
        content = self.request.get("content")
        if not title:
            title='/';
        page = db.GqlQuery("SELECT * FROM WikiEntry WHERE title=:1 limit 1;", title).get()
        if not page:
            page = WikiEntry(title=title, content=content)
            page.put()
        else:
            page.title = title
            page.content = content
            page.put()
        self.redirect("/%s" % title)


    def get(self, editpage):
        # edit this page.
        pagename = editpage.rsplit('/')[-1]
        page = db.GqlQuery("SELECT * FROM WikiEntry WHERE title=:1 limit 1;", pagename).get()
        if not page:
            self.render_wiki_page(content="", title=pagename)
        else:
            self.render_wiki_page(content=page.content, title=page.title)

def verify_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return USER_RE.match(username)

def verify_password(password):
    USER_PASS = re.compile(r"^.{3,20}$")
    return USER_PASS.match(password)

def verify_email(email):
    USER_EMAIL = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return USER_EMAIL.match(email)


class Signup(Handler):

    def write_form(self, email_error="",
                         email="",
                         verify_password_error="",
                         password_error="",
                         username_error="",
                         username=""):

        form_contents = {'email_error': email_error,
                         'email': email,
                         'verify_password_error': verify_password_error,
                         'password_error': password_error,
                         'username_error': username_error,
                         'username': username
                        }
        self.render('form.html', **form_contents)

    def get(self):
        self.write_form(email_error="", email="",
                   verify_password_error="", password_error="",
                   username_error="", username="")

    def post(self):
        username = self.request.get('username')
        username = cgi.escape(username)
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')
        email = cgi.escape(email)

        if (verify_username(username) and verify_password(password) and \
            verify_password(verify) and  password == verify and \
            (verify_email(email) or email == "")):

            password = hashlib.sha256(password + 'salt').hexdigest()
            usercookie = 'userid=%s,%s' %(username, password)
            usercookie = usercookie.encode('utf-8')
            self.response.headers.add_header('Set-Cookie', usercookie, Path='/')
            redirect_url = "/welcome"
            self.redirect(redirect_url)
        else:
            if not verify_username(username):
                username_error = "Invalid Username"
            else:
                username_error = ""
            if not verify_password(password):
                password_error = "Invalid Password"
            else:
                password_error = ""
            if not password == verify:
                verify_password_error = "Password verification Error"
            else:
                verify_password_error = ""
            if email:
                if verify_email(email):
                    email_error = "Invalid Email"
            else:
                email_error = ""

            self.write_form(email_error=email_error,
                            email=email,
                            verify_password_error=verify_password_error,
                            password_error=password_error,
                            username_error=username_error,
                            username=username)

class Login(Handler):

    def write_form(self, login_error="",
                         username=""):

        form_contents = {'login_error': login_error,
                         'username': username
                        }
        self.render('login.html', **form_contents)

    def get(self):
        self.write_form(login_error="", username="")

    def post(self):
        username = self.request.get('username')
        username = cgi.escape(username)
        password = self.request.get('password')

        if (verify_username(username) and verify_password(password)):
            password = hashlib.sha256(password + 'salt').hexdigest()
            usercookie = 'userid=%s,%s' %(username, password)
            usercookie = usercookie.encode('utf-8')
            self.response.headers.add_header('Set-Cookie', usercookie, Path='/')
            redirect_url = "/welcome"
            self.redirect(redirect_url)

        else:
            if not verify_username(username):
                login_error = "Invalid Login"
            else:
                login_error = ""
            if not verify_password(password):
                login_error = "Invalid Login"
            else:
                login_error = ""

            self.write_form(login_error=login_error,
                            username=username)

class Logout(Handler):
    def get(self):
        usercookie = 'userid='
        usercookie = usercookie.encode('utf-8')
        self.response.headers.add_header('Set-Cookie', usercookie, Path='/')
        redirect_url = "/signup"
        self.redirect(redirect_url)


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

app = webapp2.WSGIApplication([('/signup', Signup),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/_edit' + PAGE_RE, EditPage),
                               (PAGE_RE, WikiPage),
                               ('/newpost', SubmitNewEntry),
                               ], debug=True)
