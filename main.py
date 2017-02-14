import os
import webapp2
import jinja2
import hmac
import string
import random
import hashlib
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                                autoescape=True)

SECRET = "A!03bcAs249Gka134!4*@1`asdAq"


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw): 
        return self.response.out.write(*a,**kw)
    def render_str(self, template, **params):
        template_file = jinja_env.get_template(template)
        return template_file.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template,**kw))
    def hash_str(self, s, secret=SECRET):
        """Converts the input into a hashed value. 

        md5 hash algorithm is used.

        @Args:
            s (String) - String to be hashed
            
        @Outputs:
            (String) - Hashed value of the input
        """
        return hmac.new(str(secret),str(s)).hexdigest() 

    def make_secure_val(self, s):
        """ Converts input parameter into a hashed value, and returns 
        string consisting of the input and the hashed value separated 
        by "|" symbol. 
        
        It is used for the variable 'user_id' during the generation of 
        cookie.
        
        @Args:
            s (String)
        
        @Outputs:
            (String) - The input and hashed value separated by "|".
        """
        return "%s|%s" %(s, self.hash_str(s)) 

    def is_signed_in(self,cookie_val):
        """ Checks if user is signed in. 

        User is signed in if "user_id" in cookie is valid.

        Finally, checks if user exists in database.

        @Args:
            cookie_val (String)

        @Outputs:
            (Boolean) - False when cookie is invalid, and True if not.
        """
        # Check if the cookie value is empty.
        # Return false if empty.
        if not cookie_val:
            return False 
        # Check if the cookie value is in right format.
        # Return False if its in wrong format.
        try:
            val,hashed_val = cookie_val.split("|")
        except:
            return False 
        # Check if the cookie value is not tempered / corrupted.
        # Return false when the two values don't match.
        if not (self.hash_str(val) == hashed_val): 
            return False 
        # Check if the user exists in database.
        # Return False when no users are found.
        if not User.get_by_id(int(val)):
            return False 
        # Return true when all is well
        return True

    def is_authorized(self,cookie_val,blog):
        # Harvest numeric user_id from the cookie_value
        user_id = int(cookie_val.split("|")[0]) 
        # Harvest the user id of author from the queried blog
        author_id = int(blog.author.key().id())
        print(user_id,author_id)
        # Check if the two user_ids match
        # If they match, return true
        if user_id == author_id:
            return True
        # Otherwise, return false 
        else:
            return False



class ReadMainPage(Handler):
    def get(self):
        cookie_val = self.request.cookies.get('user_id')
        # Query 10 most recent blog entries in descending order.
        query = Blog.gql("ORDER BY dateCreated DESC")
        blogs = query.fetch(limit=10)
        # Render page.
        if self.is_signed_in(cookie_val):
            self.render('mainPage.html', blogs=blogs, signed_in=True)
        else:
            self.render('mainPage.html', blogs=blogs)

class CreatePost(Handler):
    def get(self):
        cookie_val = self.request.cookies.get('user_id')
        if self.is_signed_in(cookie_val):
            self.render('createPost.html', error="", signed_in= True)
        else:
            self.redirect('/blog/login')

    def post(self):
        title = self.request.get('title')
        content = self.request.get('content')
        cookie_val = self.request.cookies.get('user_id')
        # Check if the retrieved information are non-empty.
        # If all is well, proceed to storing information to database.
        if self.is_signed_in(cookie_val):
            if (title and content):
                user = User.get_by_id(int(cookie_val.split("|")[0]))
                blog_entry = Blog(title=title, content=content, author=user)
                blog_key = blog_entry.put()
                blog_id = blog_key.id()
                self.redirect('/blog/%s' %blog_id)                  
            # If either title or content are missing, tell user to fill out the missing content.
            else:
                error = "Either title or content is missing. Please fill both in, and try again."
                self.render('createPost.html', error=error)
        else:
            self.redirect('/blog/login')  

class UpdatePost(Handler):
    def get(self,post_id):
        cookie_val = self.request.cookies.get('user_id')
        blog = Blog.get_by_id(int(post_id))
        if blog:
            # Check if user signed in.
            # Check if user is authorized to modify the post.
            # If all is well, proceed to the page.
            # If not, tell user is not authorized.
            if self.is_signed_in(cookie_val):
                if self.is_authorized(cookie_val,blog):
                    self.render('updatePost.html', blog=blog, signed_in=True)
                else:
                    self.redirect('/blog/notauthorized')          
            else:

                self.redirect('/blog/login')
        else:
            self.redirect('/blog') 
    def post(self,post_id):
        title = self.request.get('title')
        content = self.request.get('content')
        cookie_val = self.request.cookies.get('user_id')
        blog = Blog.get_by_id(int(post_id))
        if blog:
            if self.is_signed_in(cookie_val):
                # Check if content in title and content are non-empty.
                # If all is well, store information to database.
                if (title and content):
                    blog.title = title
                    blog.content = content
                    blog_key = blog.put()
                    blog_id = blog_key.id()
                    self.redirect('/blog/%s' % blog_id)
                else:
                    self.render('updatePost.html', title=title, content=content,
                                signed_in=True)
            else:
                self.redirect('/blog/login')
        else:
            self.redirect('/blog')

class DeletePost(Handler):
    def get(self,post_id):
        cookie_val = self.request.cookies.get('user_id')
        blog = Blog.get_by_id(int(post_id))
        # Check if user is signed in.
        # If signed in, check if blog exists. 
        # If all is well, proceed to delete page.
        if blog:
            if self.is_signed_in(cookie_val):
                if self.is_authorized(cookie_val,blog):    
                    self.render('deletePost.html', blog=blog, signed_in=True)
                else:
                    self.redirect('/blog/notauthorized')
            else:
                self.redirect('/blog/login')
        else:
            self.redirect('/blog')

    def post(self,post_id):
        blog = Blog.get_by_id(int(post_id))
        cookie_val = self.request.cookies.get('user_id')
        if blog:
            if self.is_signed_in(cookie_val):
                blog.delete() 
                self.redirect('/blog')
            else:
                self.redirect('/blog/login')
        else:
            self.redirect('/blog')


class ReadPost(Handler):
    def get(self,post_id):
        cookie_val = self.request.cookies.get('user_id')
        blog = Blog.get_by_id(int(post_id))
        if self.is_signed_in(cookie_val):
            self.render('readPost.html', blog=blog, signed_in = True)
        else:
            self.render('readPost.html', blog=blog)

class ReadSignUpPage(Handler):
    def get(self):
        cookie_val = self.request.cookies.get('user_id')
        # Empty the cookie, before proceeding to signup page
        if not self.is_signed_in(cookie_val):
            self.response.headers.add_header('Set-Cookie','user_id=;Path=/')
            self.render('signUp.html', title="Sign-Up")
        # If the cookie is valid, redirect user to welcome page.
        else:
            self.redirect('/blog/welcome')

    def post(self):
        username  = self.request.get('username')
        password  = self.request.get('password')
        verify_pw = self.request.get('verify')
        email     = self.request.get('email')
        # Check if inputs are filled correctly.
        # If errors exist, re-render template with errors.
        errors = self.check_form_info(username,password,verify_pw,email)
        if errors["errors_exist"]:
            self.render_front(username=username,
                                password=password,
                                verify_pw=verify_pw,
                                email=email,
                                errors=errors)
        # If all is well, store newly created user to database.
        # And finish by generating a cookie.  This keeps user signed in.
        else:
            hashed_password = self.make_pw_hash(password)
            user_id = self.register(username,hashed_password,email)
            cookie_val = self.make_secure_val(user_id)
            self.response.headers.add_header('Set-Cookie',
                                            'user_id=%s;Path=/' %cookie_val)
            self.redirect('/blog/welcome')

    def render_front(self, title="", username="", password="", verify_pw="", 
                    email="", errors=""):
        self.render('signUp.html',title=title,
                                    username=username,
                                    password=password,
                                    verify_pw=verify_pw,
                                    email=email,
                                    errors=errors)

    def username_already_exists(self, username):
        """Checks if username exists in database. 

        This method ensures the uniqueness of usernames.

        @Args:
            username (String) 

        @Outputs:
            boolean - True if returned value not empty. False otherwise.
        """
        query = User.gql("WHERE username=:username", username = username)
        result = query.fetch(limit=1)
        if result:
            return True
        return False


    def check_form_info(self, username="", password="", verify_pw="", 
                        email=""):
        """Checks if inputs are filled correctly. 

        If all informations are present without errors, 'errors_exist' 
        will return FALSE.

        If one or more errors are present, 'errors_exist' will return 
        TRUE.

        @Args:
            username  (String)
            password  (String)
            verify_pw (String)
            email     (String)

        @Outputs:
            Dictionary - dictionary of errors, consisting of:
                - errors_exist      (Boolean)
                - username_empty    (Boolean)
                - password_empty    (Boolean)
                - verify_pw_empty   (Boolean)
                - email_empty       (Boolean)
                - username_incorrect(Boolean)
                - username_exists   (Boolean)
                - password_mismatch (Boolean)
        """
        errors = {"errors_exist": False, "username_empty": False,
                "password_empty": False, "verify_pw_empty": False, 
                "email_empty": False, "username_incorrect": False,
                "username_exists": False, "password_mismatch":False}
        # Checks if inputs are non-empty.
        # If so, checks each field and see which of them are missing.
        if not (username and password and verify_pw and email):
            if not username:
                errors["username_empty"] = True
                errors["errors_exist"] = True
            if not password:
                errors["password_empty"] = True
                errors["errors_exist"] = True
            if not verify_pw:
                errors["verify_pw_empty"] = True
                errors["errors_exist"] = True
            if not email:
                errors["email_empty"] = True
                errors["errors_exist"] = True
            return errors
        # Check if username has any spaces.
        if len(username.split(" ")) > 1:
            errors["errors_exist"] = True
            errors["username_incorrect"] = True
        # Check if username already exists.
        if self.username_already_exists(username):
            errors["username_exists"] = True
            errors["errors_exist"] = True
        # Check if the password and verify password match.
        if not (password == verify_pw):
            errors["password_mismatch"] = True
            errors["errors_exist"] = True

        return errors

    def register(self,username,hashed_password,email):
        """Registers an user to database.

        @Args:
            username        (string)
            hashed_password (string)
            email           (string)

        @Output:
            String - id of username
        """
        user = User(username=username,password=hashed_password,email=email)
        user_key = user.put()
        return str(user_key.id())

    def make_pw_hash(self,password):
        """ Converts input into a hased value. 

        This method uses sha256 algorithm and randomly generated salt.

        @Args:
            password (String)

        @Outputs:
            String - Hashed input and its salt separated by a comma.
        """
        salt = self.make_salt()         
        hashed_password = hmac.new(salt,password,hashlib.sha256).hexdigest()
        return "%s,%s" % (hashed_password,salt)

    def make_salt(self):
        """ Randomly generates 10 characters of alphanumeric string.

        @Args:
            None

        @Output
            String - Alphanumeric string
        """
        return "".join([random.choice(string.letters+string.digits) 
                        for i in range(10)])

class ReadWelcomePage(Handler):
    def get(self):
        cookie_val = self.request.cookies.get('user_id')
        if self.is_signed_in(cookie_val):
            user_id = cookie_val.split("|")[0]
            result = User.get_by_id(int(user_id))
            self.render("welcome.html",user= result,signed_in = True)
        else:
            self.redirect('/blog/login')

class ReadLoginPage(Handler):
    def get(self):
        cookie_val = self.request.cookies.get('user_id')
        if self.is_signed_in(cookie_val):
            self.redirect('/blog/welcome')
        else:
            self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')      
        # Checks whehter the inputs are correctly filled.
        # Creates cookie if the username exists and the password is correct.
        if (username and password):
            query = User.gql("WHERE username=:username",username=username)
            user = query.fetch(limit=1)
            if self.is_login_successful(username,password,user):
                user_id = user[0].key().id()
                cookie_val = self.make_secure_val(user_id)
                self.response.headers.add_header('Set-Cookie',
                                                'user_id=%s;Path=/'%cookie_val)      
                self.redirect('/blog/welcome')
            else:
                error = "Either username or password are incorrect. Please try again."
                self.render('login.html', error=error, username=username,
                            password=password)
        else:
            error = "Either username or password fields are empty. Please fill in, and try again."
            self.render('login.html', error=error, username=username, 
                        password=password)

    def is_login_successful(self,username,password,user):
        """ Determines whether the user is signed in. 

        @Args:
            username (string)
            password (string)
            user     (list) - Query result of anyone with the same 
                              username.

        @Outputs:
            Boolean - True if username exists and if the entered 
                      password matches the stored password. Otherwise,
                      False is returned.
        """
        # First check if username exists.
        # Then, check if password match.
        # If passwords don't match, it's incorrect and False is returned.
        if user:
            stored_hashed_password,salt = (user[0].password).split(",")
            hashed_password = hmac.new(str(salt), str(password),
                                        hashlib.sha256).hexdigest()
            if stored_hashed_password == hashed_password:
                return True 
            else:
                return False
        # If username don't exist, return False. 
        else:
            return False 
            
class ReadLogoutPage(Handler):

    def get(self):
        # Clear out the cookie. 
        # This prevents user from automatic re-login.
        self.response.headers.add_header('Set-Cookie','user_id=;Path=/')
        self.redirect('/blog/login')

# class UpdatePostLikes(Handler):

#     def post(self,post_id):

#         # Harvest data from AJAX POST request
#         # Retrieve blog data.
#         blog = Blog.get_by_id(int(post_id))
#         # Check if blog exists.
#         # If not, send response and redirect user to not found page
#         if not blog:

#         # If exists, check if user signed in.
#         # If not signed in, send response then redirect user to 'login' page
#         if not is_signed_in(cookie_val):

#         # If signed in, check if a user already liked the post.
#         # If it is already liked, redirect to a page with error "User already liked the post".
#         if is_already_liked(post_id,cookie_val):

#         # If all is well, increment like count and add user_id to likes
#         # Also, send response and change the like button to unlike button
#         blog.like_count += 1
#         (blog.likes).append(user_id)
#         blog.put()

# class UpdateCommentLikes(Handler):

    


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.EmailProperty(required=True)

class Blog(db.Model):
    title = db.StringProperty(required=True)
    subtitle = db.StringProperty()
    content = db.TextProperty(required=True)
    dateCreated = db.DateTimeProperty(auto_now_add=True)
    author = db.ReferenceProperty(User)
    numberOfLikes = db.IntegerProperty()
    liked_by = db.StringListProperty()



app = webapp2.WSGIApplication([('/blog',ReadMainPage), ('/blog/',ReadMainPage),
                                ('/blog/newpost', CreatePost),
                                ('/blog/newpost/', CreatePost),
                                ('/blog/(.*\d)',ReadPost),
                                ('/blog/(.*\d)/',ReadPost),
                                ('/blog/(.*\d)/edit',UpdatePost),
                                ('/blog/(.*\d)/edit/',UpdatePost),
                                ('/blog/(.*\d)/delete',DeletePost),
                                ('/blog/(.*\d)/delete/',DeletePost),
                                ('/blog/signup',ReadSignUpPage),
                                ('/blog/signup/',ReadSignUpPage),
                                ('/blog/welcome',ReadWelcomePage),
                                ('/blog/welcome/',ReadWelcomePage),
                                ('/blog/login',ReadLoginPage),
                                ('/blog/login/',ReadLoginPage),
                                ('/blog/logout',ReadLogoutPage),
                                ('/blog/logout/',ReadLogoutPage)], debug=True)