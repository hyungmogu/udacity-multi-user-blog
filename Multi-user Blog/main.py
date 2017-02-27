# Import standard library
import json
# Import related third party library
import webapp2
# Import local application/library
from handler import Handler,CommentHandler,LikeHandler,LoginHandler
from database import User,Blog,Comment


#API
class PostComment(CommentHandler):

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
        cookie_val = self.request.cookies.get("user_id")

        # Check if user has enough authority to create a blog post.
        # 
        # Also, determine whether to insert 'Login' or 'Logout' button.
        if(self.is_signed_in(cookie_val)):
            self.render("createBlog.html", error="", signed_in=True)
        else:
            self.redirect("/blog/login")

    def post(self):
        title = self.request.get("title")
        content = self.request.get("content")
        cookie_val = self.request.cookies.get("user_id")

        if not self.is_signed_in(cookie_val):
            self.redirect("/blog/login")
            return
        if not title and content:
            error = ("Either title or content is missing. Please make sure "
                    "both are filled in, and try again.")
            self.render("createBlog.html", error=error)
            return

        # Here, cookie is non-empty.  Its value can be retrieved safely.
        user = User.get_by_id(int(cookie_val.split("|")[0]))

        blog_entry = Blog(title=title, content=content, author=user, 
                                number_of_likes=0)
        blog_id = blog_entry.put().id()

        self.redirect("/blog/%s" %blog_id)


class UpdateBlog(Handler):

    def get(self, post_id):
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))

        # Check if user is authorized to modify the blog post.
        #
        # Also, determine whether to insert login or logout button.
        if not blog:
            self.response.set_status(404)
            self.redirect("/blog/not_found")
            return
        if not self.is_signed_in(cookie_val):
            self.response.set_status(401)
            self.redirect("/blog/login")
            return
        if not self.is_author(cookie_val,blog):
            self.response.set_status(403)
            self.redirect("/blog/not_authorized")
            return

        self.render("updateBlog.html", blog=blog, signed_in=True)       

    def post(self, post_id):
        title = self.request.get("title")
        content = self.request.get("content")
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))

        if not blog:
            self.response.set_status(404)
            self.redirect("/blog/not_found")
            return
        if not self.is_signed_in(cookie_val):
            self.response.set_status(401)
            self.redirect("/blog/login")
            return
        if not self.is_author(cookie_val,blog):
            self.response.set_status(403)
            self.redirect("/blog/not_authorized")
            return
        if not title and content:
            error = ("Either title or texts are empty. Please fill both in "
                     "before trying again.")
            self.render("updateBlog.html", title=title, content=content,
                        error=error, signed_in=True)
            return  

        blog.title = title
        blog.content = content
        blog_id = blog.put().id()

        self.response.set_status(200)
        self.redirect("/blog/%s" % blog_id)


class DeleteBlog(Handler):

    def get(self, post_id):
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))

        if not blog:
            self.response.set_status(404)
            self.redirect("/blog/not_found")
            return
        if not self.is_signed_in(cookie_val):
            self.response.set_status(401)
            self.redirect("/blog/login")
            return
        if not self.is_author(cookie_val, blog):
            self.response.set_status(403)
            self.redirect("/blog/not_authorized")
            return

        self.render("deleteBlog.html", blog=blog, signed_in=True)

    def post(self, post_id):
        blog = Blog.get_by_id(int(post_id))
        cookie_val = self.request.cookies.get("user_id")
 
        if not blog:
            self.response.set_status(404)
            self.redirect("/blog/not_found")
            return
        if not self.is_signed_in(cookie_val):
            self.response.set_status(401)
            self.redirect("/blog/login")
            return
        if not self.is_author(cookie_val, blog):
            self.response.set_status(403)
            self.redirect("/blog/not_authorized")
            return

        blog.delete()

        self.response.set_status(200)
        self.redirect("/blog")


class ReadBlog(Handler):

    def get(self, post_id):
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))
        comments = (Comment.all().filter("blog =", blog.key()).
                    order("-date_created"))

        # Determine whether to insert 'Login' or 'Logout' button.
        if(self.is_signed_in(cookie_val)):
            self.render("readBlog.html", blog=blog, signed_in=True, 
                        comments=comments)
        # Insert login button
        else:
            self.render("readBlog.html", blog=blog, comments=comments)


class ReadSignUp(LoginHandler):

    def get(self):
        cookie_val = self.request.cookies.get("user_id")

        if not self.is_signed_in(cookie_val):
            # Empty cookie, so it can be filled correctly after signup.
            self.response.headers.add_header("Set-Cookie","user_id=;Path=/")

            self.render("signUp.html", title="Sign-Up")
        else:
            self.redirect("/blog/welcome")

    def post(self):
        username  = self.request.get("username")
        password  = self.request.get("password")
        verify_pw = self.request.get("verify")
        email     = self.request.get("email")

        # Re-render page with feedback if error exists.
        errors = self.check_form_info(username,password,verify_pw,email)
        if errors["errors_exist"]:
            self.render_front(
                username=username, password=password, verify_pw=verify_pw, 
                email=email, errors=errors
            )
            return

        # Store newly created user to database.  
        hashed_password = self.make_pw_hash(password)
        user_id = self.register(username,hashed_password,email)

        # Generate a cookie and keep user signed in.
        cookie_val = "user_id=%s;Path=/" % self.make_secure_val(user_id)
        self.response.headers.add_header("Set-Cookie", cookie_val)

        self.redirect("/blog/welcome")

    def render_front(self, title="", username="", password="", verify_pw="", 
                     email="", errors=""):
        self.render("signUp.html", title=title, username=username, 
                    password=password, verify_pw=verify_pw, email=email,
                    errors=errors)


class ReadWelcome(Handler):

    def get(self):
        cookie_val = self.request.cookies.get("user_id")

        if not self.is_signed_in(cookie_val):
            self.redirect("/blog/login")
            return

        # Query user to display username in the welcome message.
        user_id = cookie_val.split("|")[0]
        user = User.get_by_id(int(user_id))

        # Render page with 'Logout' button.
        self.render("welcome.html", user=user, signed_in=True)


class ReadLogin(LoginHandler):

    def get(self):
        cookie_val = self.request.cookies.get("user_id")

        if self.is_signed_in(cookie_val):
            self.redirect("/blog/welcome")
            return

        self.render("login.html")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")      

        if not username and password:
            message = ("Either username or password fields are empty. Please "
                       "fill in, and try again.")
            self.render("login.html", error=error, username=username, 
                        password=password)
            return
        if not self.is_login_successful(username, password, user):
            message = ("Either username or password are incorrect. Please "
                       "try again.")
            self.render("login.html", error=error, username=username,
                        password=password)
            return

        user_id = user[0].key().id()
        cookie_val = "user_id=%s;Path=/" % self.make_secure_val(user_id)
        self.response.headers.add_header("Set-Cookie", cookie_val)      
        
        self.redirect("/blog/welcome")

            
class ReadLogout(LoginHandler):

    def get(self):
        # Clear out cookie.  This prevents automatic re-login.
        self.response.headers.add_header("Set-Cookie", "user_id=;Path=/")

        self.redirect("/blog/login")


class ReadNotFound(Handler):

    def get(self):
        cookie_val = self.request.cookies.get("user_id")

        # Determine whether to insert 'Login' or 'Logout' button.
        if(self.is_signed_in(cookie_val)):
            # Insert logout button.
            self.render("404.html", signed_in=True)
        else:
            # Insert login button.
            self.render("404.html")


class ReadNotAuthorized(Handler):

    def get(self):
        cookie_val = self.request.cookies.get("user_id")
        
        # Determine whether to insert 'Login' or 'Logout' button.
        if(self.is_signed_in(cookie_val)):
            # Insert logoout button.
            self.render("403.html", signed_in=True)
        else:
            # Insert login button.
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