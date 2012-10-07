import webapp2
import jinja2
import os
import datetime
import json
import cgi
import hashlib
import re

from google.appengine.ext import db
from google.appengine.api import memcache

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

def get_all_posts():
    key = "front"
    allposts = memcache.get(key)
    if allposts is None:
        allposts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created desc;")
        memcache.set(key, allposts)
    return allposts

class BlogMainPageHandler(Handler):
    def render_front_page(self, **kwargs):
        self.render("front.html", **kwargs)

    def get(self):
        # Gql for all the blog entries.
        allposts = get_all_posts()
        if allposts:
            latest = allposts[0]
            time_delta = datetime.datetime.now() - latest.created
            seconds = time_delta.seconds
        else:
            seconds = 0
        self.render_front_page(allposts=allposts, seconds=seconds)

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

def verify_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return USER_RE.match(username)

def verify_password(password):
    USER_PASS = re.compile(r"^.{3,20}$")
    return USER_PASS.match(password)

def verify_email(email):
    USER_EMAIL = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return USER_EMAIL.match(email)

class SignupHandler(Handler):

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

class WelcomeHandler(webapp2.RequestHandler):

    def get(self):
        username = self.request.cookies.get("userid")
        username = username.split(',')[0]
        output = "Welcome, %s" % username
        self.response.out.write(output)

class LoginHandler(Handler):

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

class LogoutHandler(Handler):
    def get(self):
        usercookie = 'userid='
        usercookie = usercookie.encode('utf-8')
        self.response.headers.add_header('Set-Cookie', usercookie, Path='/')
        redirect_url = "/signup"
        self.redirect(redirect_url)

class PermaLinkJsonHandler(Handler):
    def get(self, postid):
        post_entry = {}
        post = BlogPost.get_by_id(int(postid))
        post_entry['subject'] = post.topic
        post_entry['content'] = post.post
        post_entry['created'] = post.created.strftime('%a %d %b %H:%M:%S %Y')

        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = json.dumps(post_entry)
        self.write(response_json)

class MainPageJsonHandler(Handler):
    def get(self):
        allposts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created desc;")
        main_page_list = []
        for post in allposts:
            entry_dict = {}
            entry_dict['subject'] = post.topic
            entry_dict['content'] = post.post
            entry_dict['created'] = post.created.strftime('%a %d %b %H:%M:%S %Y')
            main_page_list.append(entry_dict)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = json.dumps(main_page_list)
        self.write(response_json)


app = webapp2.WSGIApplication([('/\.json', MainPageJsonHandler),
                               ('/', BlogMainPageHandler),
                               ('/newpost', SubmitNewEntry),
                               ('/(\d+)\.json', PermaLinkJsonHandler),
                               ('/(\d+)', PermaLinkEntryHandler),
                               ('/signup', SignupHandler),
                               ('/welcome', WelcomeHandler),
                               ('/login', LoginHandler),
                               ('/logout', LogoutHandler)
                               ], debug=True)
