# Import standard library
import json
# Import related third party library
import webapp2
# Import local application/library
from handler import Handler,CommentHandler,LikeHandler,LoginHandler
from database import User,Blog,Comment


#API
class PostComment(CommentHandler):

    def send_response(self, status_code, message=''):
        self.response.set_status(status_code)
        self.response.headers["Content-Type"] = "application/json"
        if message:
            self.response.out.write(message)

    def post(self, post_id):
        data = json.loads(self.request.body)
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))
        title = data["title"]
        content = data["content"]
        user = User.get_by_id(int(cookie_val.split("|")[0]))
        
        if not self.blog_exists(blog): 
            message = "Invalid. The requested page doesn't exist."
            self.send_response(404, message)
            return
        if not self.is_signed_in(cookie_val):
            message = "Invalid. Only signed in User can post comments"
            self.send_response(401, message)
            return
        if not (title and content):
            message = "Invalid. Title and texts must not be empty."
            self.send_response(400, message)
            return

        comment = Comment(title=title, content=content, blog=blog, author=user)
        comment_id = comment.put().id()

        message = json.dumps({
            "success": "Comment successfully added to database.", 
            "id": comment_id, "title": title, "content": content, 
            "author": user.username, 
            "date_created": comment.date_created.strftime("%B %d %Y %I:%M%p")
        })
        self.send_response(200,message)


class DeleteComment(CommentHandler):

    def send_response(self, status_code, message=''):
        self.response.set_status(status_code)
        self.response.headers["Content-Type"] = "application/json"
        if message:
            self.response.out.write(message)

    def delete(self, post_id):
        blog = Blog.get_by_id(int(post_id))
        comment = Comment.get_by_id(int(self.request.get("id")))
        cookie_val = self.request.cookies.get("user_id")

        if not self.blog_exists(blog):
            message = "Invalid. The blog page does not exist."
            self.send_response(404,message)
            return
        if not self.comment_exists(comment):
            message = "Invalid. The comment does not exist."
            self.send_response(400,message)
            return
        if not self.is_signed_in(cookie_val):
            message = "Invalid. Must be signed in to edit comment."
            self.send_response(401,message)
            return
        if not self.is_author(cookie_val, comment):
            message = "Invalid. Must be its author to edit this."
            self.send_response(403,message)
            return

        comment.delete()  

        message = json.dumps({
            "success": "The comment has been deleted successfully."
        })
        self.send_response(200,message)


class UpdateComment(CommentHandler):

    def send_response(self, status_code, message=''):
        self.response.set_status(status_code)
        self.response.headers["Content-Type"] = "application/json"
        if message:
            self.response.out.write(message)

    def put(self, post_id):
        data = json.loads(self.request.body)
        comment = Comment.get_by_id(int(data["id"]))
        blog = Blog.get_by_id(int(post_id))
        cookie_val = self.request.cookies.get("user_id")
        new_title = data["title"]
        new_content = data["content"]

        if not(new_content and new_title):
            message = "Invalid. Both title and comment must not be empty."
            self.send_response(400,message)
            return
        if not self.blog_exists(blog):
            self.send_response(404)
            return 
        if not self.comment_exists(comment):
            message = "Invalid. The comment does not exist."
            self.send_response(400,message)
            return
        if not self.is_signed_in(cookie_val):
            message = "Invalid. Must be signed in to edit comments."
            self.send_response(400,message)
            return
        if not self.is_author(cookie_val,comment):
            message = "Invalid. Only its author is allowed to edit."
            self.send_response(400,message)
            return

        comment.title = new_title
        comment.content = new_content
        comment.put()

        message = json.dumps({
            "success": "The comment has been updated successfully."
        })
        self.send_response(200,message)
        self.response.set_status(200)


class ValidateBeforeEdit(CommentHandler):

    def send_response(self, status_code, message=''):
        self.response.set_status(status_code)
        self.response.headers["Content-Type"] = "application/json"
        if message:
            self.response.out.write(message)

    def get(self, post_id):
        cookie_val = self.request.cookies.get("user_id")
        comment = Comment.get_by_id(int(self.request.get("id")))

        if not self.is_signed_in(cookie_val):
            message = "Invalid. User must be signed-in to edit this comment."
            self.send_response(401,message)
            return
        if not self.is_author(cookie_val,comment):
            message = "Invalid. Only its author is allowed to edit."
            self.send_response(403,message)
            return

        message = json.dumps({"success": "Allowed"})
        self.send_response(200,message)


class UpdateLike(LikeHandler):

    def send_response(self, status_code, message=''):
        self.response.set_status(status_code)
        self.response.headers["Content-Type"] = "application/json"
        if message:
            self.response.out.write(message) 

    def post(self, post_id):
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))

        if not self.is_signed_in(cookie_val):
            message = {"error": "Not signed in."}
            self.send_response(401,message)
            return
        if not self.blog_exists(blog):
            message = {"error": "Post doesn't exist."}
            self.send_response(404,message)
            return
        if self.is_author(cookie_val, blog):
            message = {"error": "Post cannot be liked by creator."}
            self.send_response(400,message)
            return

        user_id = cookie_val.split("|")[0]

        # Check if user already liked the post.
        # Remove if id already in a list.
        if(user_id in blog.liked_by):
            self.remove_like(blog, user_id)
        else:
            self.add_like(blog, user_id) 


# ROUTES
class ReadMain(Handler):

    def get(self):
        cookie_val = self.request.cookies.get("user_id")
        query = Blog.gql("ORDER BY date_created DESC")
        blogs = query.fetch(limit=10)
        # Determine whether to insert 'Login' or 'Logout' button.
        if(self.is_signed_in(cookie_val)):
            self.render("mainPage.html", blogs=blogs, signed_in=True)
        # Include 'login' button since user is not signed in.
        else:
            self.render("mainPage.html", blogs=blogs)


class CreateBlog(Handler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        # Check if user has enough authority to create a blog post.
        # 
        # Also, determine whether to insert 'Login' or 'Logout' button.
        if(self.is_signed_in(cookie_val)):
            self.render("createBlog.html", error="", signed_in=True)
        else:
            self.redirect("/blog/login")

    def post(self):
        # Harvest requirements.
        title = self.request.get("title")
        content = self.request.get("content")
        cookie_val = self.request.cookies.get("user_id")
        # Check if all req. has been met.
        if(self.is_valid(cookie_val, content, title)):
            # If all is wel, store information in database.
            user = User.get_by_id(int(cookie_val.split("|")[0]))
            blog_entry = Blog(title=title, content=content, author=user, 
                                    number_of_likes=0)
            # Finally, redirect user to the newly created page
            blog_id = (blog_entry.put()).id()
            self.redirect("/blog/%s" %blog_id)
        else:
            # If not signed in, redirect user to login page.
            if(not self.is_signed_in(cookie_val)):
                self.redirect("/blog/login")
            # If any contents are missing, return error to user. 
            elif(not(title and content)):
                error = ("Either title or content is missing. Please fill "
                        "both in, and try again.")
                self.render("createBlog.html", error=error)

    def is_valid(self, cookie_val, content,title):
        # Check if user signed in.
        if(not self.is_signed_in(cookie_val)):
            return False
        # Check contents are non-empty.
        elif(not(title and content)):
            return False
        return True


class UpdateBlog(Handler):

    def get(self, post_id):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))
        # Check if user is authorized to modify the blog post.
        #
        # Also, determine whether to insert login or logout button.
        if(self.is_get_valid(blog, cookie_val)):
            self.render("updateBlog.html", blog=blog, signed_in=True)       
        # If not authorized, redirect user to appropriate page.
        else:
            if(not blog):
                self.response.set_status(404)
                self.redirect("/blog/not_found")
            elif(not self.is_signed_in(cookie_val)):
                self.response.set_status(401)
                self.redirect("/blog/login")
            elif(not self.is_author(cookie_val,blog)):
                self.response.set_status(403)
                self.redirect("/blog/not_authorized")

    def post(self, post_id):
        # Harvest requirments.
        title = self.request.get("title")
        content = self.request.get("content")
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))
        # Check if all req. has been met.
        if(self.is_post_valid(blog, cookie_val, content,title)):
                # If all is well, store information in database.
                blog.title = title
                blog.content = content
                # Finally, redirect user to the newly created page
                blog_id = (blog.put()).id()
                self.response.set_status(200)
                self.redirect("/blog/%s" % blog_id)
        # if not, find out why, and take appropriate action.
        else:
            # Check if blog exists under the retrieved 'post_id'
            if(not blog):
                self.response.set_status(404)
                self.redirect("/blog/not_found")
            # Check if user has logged in.
            elif(not self.is_signed_in(cookie_val)):
                self.response.set_status(401)
                self.redirect("/blog/login")
            # Check if user is authorized to make changes to the blog.
            elif(not self.is_author(cookie_val,blog)):
                self.response.set_status(403)
                self.redirect("/blog/not_authorized")
            # Check if either inputs are empty.
            elif(not(title and content)):
                # Re-render page with error.
                error = ("Either title or texts are empty. Please fill "
                        "both in before trying again.")
                self.render("updateBlog.html", title=title, content=content,
                            error=error, signed_in=True)               

    def is_get_valid(self, blog, cookie_val):
        # Check if blog exists.
        if(not blog):
            return False
        # Check if user has logged in.        
        elif(not self.is_signed_in(cookie_val)):
            return False
        # Check if user is authorized to edit this blog post.
        elif(not self.is_author(cookie_val, blog)):
            return False
        return True

    def is_post_valid(self, blog, cookie_val, scontent,title):
        # Check if blog exists.
        if(not blog):
            return False
        # Check if user has logged in.
        elif(not self.is_signed_in(cookie_val)):
            return False
        # Check if user is authorized to edit this blog post.
        elif(not self.is_author(cookie_val, blog)):
            return False
        # Check if either inputs are empty.
        elif(not(title and content)):
            return False
        return True


class DeleteBlog(Handler):

    def get(self, post_id):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))
        # Check if all req. has been met to delete a post.
        if(self.is_valid(blog, cookie_val)):
            # Since user is logged in, display 'Logout' button.
            self.render("deleteBlog.html", blog=blog, signed_in=True)
        else:
            if(not blog):
                self.response.set_status(404)
                self.redirect("/blog/not_found")
            elif(not self.is_signed_in(cookie_val)):
                self.response.set_status(401)
                self.redirect("/blog/login")
            elif(not self.is_author(cookie_val, blog)):
                self.response.set_status(403)
                self.redirect("/blog/not_authorized")

    def post(self, post_id):
        # Harvest requirements.
        blog = Blog.get_by_id(int(post_id))
        cookie_val = self.request.cookies.get("user_id")
        # Check whether all req. has been met to delete a post.  This 
        # is double confirmation.  It is done to make sure no one is 
        # doing it illegitimately.
        if(self.is_valid(blog, cookie_val)):
                blog.delete()
                self.response.set_status(200)
                self.redirect("/blog")
        # If not met, find out why, and return feedback.
        else:
            # Check if blog exists.
            if(not blog):
                self.response.set_status(404)
                self.redirect("/blog/not_found")
            # Check if user has logged in.
            elif(not self.is_signed_in(cookie_val)):
                self.response.set_status(401)
                self.redirect("/blog/login")
            # Check if user is authorized to delete a blog post.
            elif(not self.is_author(cookie_val, blog)):
                self.response.set_status(403)
                self.redirect("/blog/not_authorized")

    def is_valid(self, blog, cookie_val):
        # Check if blog exists.
        if(not blog):
            return False
        # Check if user has logged in.
        elif(not self.is_signed_in(cookie_val)):
            return False
        # Check if user is authorized to delete blog post.
        elif(not self.is_author(cookie_val, blog)):
            return False
        return True


class ReadBlog(Handler):

    def get(self, post_id):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))
        # Query all comments.
        comments = (Comment.all().filter("blog =", blog.key()).
                    order("-date_created"))
        # Determine whether to insert 'Login' or 'Logout' button.
        if(self.is_signed_in(cookie_val)):
            self.render("readBlog.html", blog=blog, signed_in=True, 
                        comments=comments)
        # If not logged in, insert 'login' button.
        else:
            self.render("readBlog.html", blog=blog, comments=comments)

    def has_comments(self,comments):
        if(comments):
            return True
        else:
            return False


class ReadSignUp(LoginHandler):

    def get(self):
        cookie_val = self.request.cookies.get("user_id")
        # Empty the cookie, before proceeding to signup page
        if(not self.is_signed_in(cookie_val)):
            self.response.headers.add_header("Set-Cookie","user_id=;Path=/")
            self.render("signUp.html", title="Sign-Up")
        # If cookie is valid, redirect user to welcome page.
        else:
            self.redirect("/blog/welcome")

    def post(self):
        # Harvest requirements.
        username  = self.request.get("username")
        password  = self.request.get("password")
        verify_pw = self.request.get("verify")
        email     = self.request.get("email")
        # Check if inputs are filled correctly. And if errors exist, 
        # re-render with feedback.
        errors = self.check_form_info(username,password,verify_pw,email)
        if(errors["errors_exist"]):
            self.render_front(username=username, password=password, 
                                verify_pw=verify_pw, email=email, 
                                errors=errors)
        # If all is well, store newly created user to database.  And 
        # finish by generating a cookie.  This keeps user signed in.
        else:
            hashed_password = self.make_pw_hash(password)
            user_id = self.register(username,hashed_password,email)
            cookie_val = self.make_secure_val(user_id)
            self.response.headers.add_header("Set-Cookie",
                                            "user_id=%s;Path=/" %cookie_val)
            self.redirect("/blog/welcome")

    def render_front(self, title="", username="", password="", verify_pw="", 
                    email="", errors=""):
        self.render("signUp.html",title=title, username=username, 
                    password=password, verify_pw=verify_pw, email=email,
                    errors=errors)


class ReadWelcome(Handler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        # Check if user has already logged in.
        if(self.is_signed_in(cookie_val)):
            # Query user to display username in the welcome message.
            user_id = cookie_val.split("|")[0]
            result = User.get_by_id(int(user_id))
            # Also, insert 'Logout' button.
            self.render("welcome.html", user=result, signed_in=True)
        # If not logged in, redirect to login.  User shouldn't be here.
        else:
            self.redirect("/blog/login")


class ReadLogin(LoginHandler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        # Check if user has logged in.
        if(self.is_signed_in(cookie_val)):
            self.redirect("/blog/welcome")
        # If not logged in, continue to login page.
        else:
            self.render("login.html")

    def post(self):
        # Harvest requirements.
        username = self.request.get("username")
        password = self.request.get("password")      
        # Checks whehter the inputs are correctly filled.
        if(username and password):
            query = User.gql("WHERE username=:username", username=username)
            user = query.fetch(limit=1)
            if(self.is_login_successful(username, password, user)):
                # Create cookie and store user info if successful.  This
                # keeps user logged-in.
                user_id = user[0].key().id()
                cookie_val = self.make_secure_val(user_id)
                self.response.headers.add_header("Set-Cookie",
                                                "user_id=%s;Path=/"
                                                 % cookie_val)      
                self.redirect("/blog/welcome")
            # If incorrect, return response to user.
            else:
                error = ("Either username or password are incorrect. Please "
                        "try again.")
                self.render("login.html", error=error, username=username,
                            password=password)
        # If empty, return response to user.
        else:
            error = ("Either username or password fields are empty. Please "
                    "fill in, and try again.")
            self.render("login.html", error=error, username=username, 
                        password=password)
 
            
class ReadLogout(LoginHandler):

    def get(self):
        # Clear out cookie.  This prevents automatic re-login.
        self.response.headers.add_header("Set-Cookie", "user_id=;Path=/")
        self.redirect("/blog/login")


class ReadNotFound(Handler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        # Determine whether to insert 'Login' or 'Logout' button.
        if(self.is_signed_in(cookie_val)):
            self.render("404.html", signed_in=True)
        # If not logged in, insert login button.
        else:
            self.render("404.html")


class ReadNotAuthorized(Handler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        # Determine whether to insert 'Login' or 'Logout' button.
        if(self.is_signed_in(cookie_val)):
            self.render("403.html", signed_in=True)
        # If not logged in, insert login button.
        else:
            self.render("403.html")


app = webapp2.WSGIApplication([("/blog", ReadMain), ("/blog/", ReadMain),
                                ("/blog/newpost", CreateBlog),
                                ("/blog/newpost/", CreateBlog),
                                ("/blog/(.*\d)", ReadBlog),
                                ("/blog/(.*\d)/", ReadBlog),
                                ("/blog/(.*\d)/edit", UpdateBlog),
                                ("/blog/(.*\d)/edit/", UpdateBlog),
                                ("/blog/(.*\d)/delete", DeleteBlog),
                                ("/blog/(.*\d)/delete/", DeleteBlog),
                                ("/blog/signup", ReadSignUp),
                                ("/blog/signup/", ReadSignUp),
                                ("/blog/welcome", ReadWelcome),
                                ("/blog/welcome/", ReadWelcome),
                                ("/blog/login", ReadLogin),
                                ("/blog/login/", ReadLogin),
                                ("/blog/logout", ReadLogout),
                                ("/blog/logout/", ReadLogout),
                                ("/blog/(.*\d)/like", UpdateLike),
                                ("/blog/(.*\d)/like/", UpdateLike),
                                ("/blog/(.*\d)/comment/new", PostComment),
                                ("/blog/(.*\d)/comment/new/", PostComment),
                                ("/blog/(.*\d)/comment/delete", 
                                 DeleteComment),
                                ("/blog/(.*\d)/comment/delete/", 
                                 DeleteComment),
                                ("/blog/(.*\d)/comment/edit", UpdateComment),
                                ("/blog/(.*\d)/comment/edit/", UpdateComment),
                                ("/blog/(.*\d)/comment/validate", 
                                 ValidateBeforeEdit),
                                ("/blog/(.*\d)/comment/validate/", 
                                 ValidateBeforeEdit),
                                ("/blog/not_found", ReadNotFound),
                                ("/blog/not_found/", ReadNotFound),
                                ("/blog/not_authorized", ReadNotAuthorized),
                                ("/blog/not_authorized/", ReadNotAuthorized)], 
                                debug=True) 