#!/usr/bin/env python

import webapp2
import jinja2
import os
import cgi
import re
import hashlib

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

def verify_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return USER_RE.match(username)

def verify_password(password):
    USER_PASS = re.compile(r"^.{3,20}$")
    return USER_PASS.match(password)

def verify_email(email):
    USER_EMAIL = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return USER_EMAIL.match(email)

class Handler(webapp2.RequestHandler):

    def write(self, *args, **kwargs):
        self.response.out.write(*args, **kwargs)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kwargs):
        self.write(self.render_str(template, **kwargs))

class MainHandler(Handler):

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

class HelloHandler(Handler):
    def get(self):
        self.write("hello,world")

app = webapp2.WSGIApplication([('/signup', MainHandler),
                               ('/welcome', WelcomeHandler),
                               ('/', HelloHandler)], debug=True)
