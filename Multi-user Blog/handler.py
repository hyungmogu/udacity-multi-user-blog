import os
import hmac
import string
import hashlib
import random
import json

import webapp2
import jinja2

from database import User,Blog,Comment

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                                autoescape=True)
SECRET = "A!03bcAs249Gka134!4*@1`asdAq"


# HANDLERS
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
            (String) - String to be hashed
            
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

    def is_author(self,cookie_val,blog):
        # Harvest numeric user_id from the cookie_value
        user_id = int(cookie_val.split("|")[0]) 
        # Harvest the user id of author from the queried blog
        author_id = int(blog.author.key().id())
        # Check if the two user_ids match
        # If they match, return true
        if user_id == author_id:
            return True
        # Otherwise, return false 
        else:
            return False

    def blog_exists(self,blog):
        if not blog:
            return False
        else:
            return True

class CommentHandler(Handler):

    def comment_exists(self,comment):
        if comment:
            return True
        else:
            return False  


class LikeHandler(Handler):

    def add_like(self,blog,user_id):
        blog.number_of_likes += 1
        blog.liked_by.append(user_id)
        blog.put()
        success = {"success": "successfully liked a post",
                    "new_count": blog.number_of_likes}
        self.response.set_status(200)
        self.response.out.write(json.dumps(success))

    def remove_like(self,blog,user_id):
        blog.number_of_likes -= 1
        blog.liked_by = [x for x in blog.liked_by if(int(x)!=int(user_id))]
        blog.put()
        success = {"success": "successfully unliked a post", 
                    "new_count": blog.number_of_likes}
        self.response.set_status(200)
        self.response.out.write(json.dumps(success))


class LoginHandler(Handler):

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
        """ Converts input into a hashed value. 

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
