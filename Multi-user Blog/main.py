import json

import webapp2

from handler import Handler,CommentHandler,LikeHandler,LoginHandler
from database import User,Blog,Comment


#API
class PostComment(CommentHandler):

    def post(self,post_id):
        # Harvest requirements.
        data = json.loads(self.request.body)
        cookie_val = self.request.cookies.get("user_id")
        blog = Blog.get_by_id(int(post_id))
        title = data["title"]
        content = data["content"]
        # Check if user is allowed to post a comment.
        if self.is_post_valid(blog,cookie_val,content,title):
            # Harvest more requirements.
            user = User.get_by_id(int(cookie_val.split("|")[0]))
            # Store information.
            comment = Comment(title=title, content=content, blog=blog, 
                            author=user)
            comment_id = (comment.put()).id()
            # Return user back to page.
            self.response.set_status(200)
            self.response.out.write(json.dumps({"success":"Comment successfully added to database.","id":comment_id, "title": title, "content": content,"author": user.username,"date_created":(comment.date_created).strftime("%B %d, %Y %I:%M%p")}))             
        else:
            if not self.blog_exists(blog):
                self.response.set_status(404)
            elif not self.is_signed_in(cookie_val):
                self.response.set_status(401)
            elif not (title and content):
                self.response.set_status(400)
                self.response.headers["Content-Type"]="application/json"
                self.response.out.write(json.dumps({"error":"Invalid. Title and texts must not be empty."}))

    def is_post_valid(self,blog,cookie_val,content,title):
        if not self.blog_exists(blog):
            return False
        # Check is user 
        elif not self.is_signed_in(cookie_val):
            return False
        # Check if title and content are non-empty.
        elif not (title and content):
            return False
        return True

class DeleteComment(CommentHandler):

    def delete(self,post_id):
        blog = Blog.get_by_id(int(post_id))
        comment = Comment.get_by_id(int(self.request.get("id")))
        cookie_val = self.request.cookies.get("user_id")
        # Check if the operation on the comment is valid.
        if self.is_valid(blog,comment,cookie_val):
            comment.delete()  
            self.response.set_status(200)
            self.response.headers["Content-Type"] = "application/json"
            self.response.out.write(json.dumps({"success":"The comment has been " 
                                                "deleted successfully."}))
        else:
            if not self.blog_exists(blog):
                self.response.set_status(404)
                self.response.headers["Content-Type"] = "application/json"
                self.response.out.write(json.dumps({"error": "Invalid. The blog "
                                                    "page does not exist."}))
            elif not self.comment_exists(comment):
                self.response.set_status(400)
                self.response.headers["Content-Type"] = "application/json"
                self.response.out.write(json.dumps({"error": "Invalid. The "
                                                    "comment does not exist."}))
            elif not self.is_signed_in(cookie_val):
                self.response.set_status(401)
                self.response.headers["Content-Type"] = "application/json"
                self.response.out.write(json.dumps({"error": "Invalid. Must be "
                                                    "signed in to edit comment."}))
            elif not self.is_author(cookie_val,comment):
                self.response.set_status(403)
                self.response.headers["Content-Type"] = "application/json"
                self.response.out.write(json.dumps({"error":"Invalid. Must be "
                                                    "the creator of the comment "
                                                    "to edit."}))

    def is_valid(self,blog,comment,cookie_val):
        if not self.blog_exists(blog):
            return False
        elif not self.comment_exists(comment):
            return False
        elif not self.is_signed_in(cookie_val):
            return False
        elif not self.is_author(cookie_val,comment):
            return False
        return True   

class UpdateComment(CommentHandler):

    def put(self,post_id):
        # Harvest requirements.
        data = json.loads(self.request.body)
        comment = Comment.get_by_id(int(data["id"]))
        blog = Blog.get_by_id(int(post_id))
        cookie_val = self.request.cookies.get("user_id")
        new_title = data["title"]
        new_content = data["content"]
        # Ensure all req. has been met before applying changes.
        if self.is_valid(blog,comment,cookie_val,new_content,new_title):
            comment.title = new_title
            comment.content = new_content
            comment.put()
            self.response.set_status(200)
            self.response.headers["Content-Type"] = "application/json"
            self.response.out.write(json.dumps({"success":"The comment has been "
                                                "successfully updated."}))
        # If not satisfied, identify where and return it back to user.
        else:
            if not (new_content and new_title):
                self.response.set_status(400)
                self.response.headers["Content-Type"] = "application/json"
                self.response.out.write(json.dumps({"error":"Invalid. Both title "
                                                    "and comment must not be "
                                                    "empty."}))
            elif not self.blog_exists(blog):
                self.response.set_status(404)
                self.response.headers["Content-Type"] = "application/json"
                self.response.out.write(json.dumps({"error": "Invalid. The blog "
                                                    "page does not exist."}))
            elif not self.comment_exists(comment):
                self.response.set_status(404)
                self.response.headers["Content-Type"] = "application/json"
                self.response.out.write(json.dumps({"error": "Invalid. The "
                                                    "comment does not exist."}))
            elif not self.is_signed_in(cookie_val):
                self.response.set_status(401)
                self.response.headers["Content-Type"] = "application/json"
                self.response.out.write(json.dumps({"error": "Invalid. Must be "
                                                    "signed in to edit comment."}))
            elif not self.is_author(cookie_val,comment):
                self.response.set_status(401)
                self.response.headers["Content-Type"] = "application/json"
                self.response.out.write(json.dumps({"error":"Invalid. Must be "
                                                    "the creator of the comment "
                                                    "to edit."}))

    def is_valid(self,blog,comment,cookie_val,new_content,new_title):
        # Check if content and title are non-empty.
        if not (new_content and new_title):
            return False
        # Check if blog with post_id is non-empty.
        elif not self.blog_exists(blog):
            return False
        # Check if comment with comment_id is non-empty. 
        elif not self.comment_exists(comment):
            return False
        # Check if user has logged in.
        elif not self.is_signed_in(cookie_val):
            return False
        # Check if user has authority to apply changes to the comment.
        elif not self.is_author(cookie_val,comment):
            return False
        return True    


class ValidateBeforeEdit(CommentHandler):

    def get(self,post_id):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        comment = Comment.get_by_id(int(self.request.get("id")))
        # Check if user has authority to edit the comment.
        if self.is_signed_in(cookie_val) and self.is_author(cookie_val,comment):
            self.response.set_status(200)
            self.response.headers["Content-Type"] = "application/json"
            self.response.out.write(json.dumps({"success":"User is allowed to "
                                                "edit this post."}))                    
        # If not satisfied, return message to user.
        else:
            self.response.set_status(401)
            self.response.headers["Content-Type"] = "application/json"
            self.response.out.write(json.dumps({"error": "User is either not "
                                                "signed in or is not authorized "
                                                "to edit this comment."}))         


class UpdateLike(LikeHandler):

    def post(self,post_id):
        # Harvest requirements.
        cookie_val = self.request.cookies.get('user_id')
        user_id = cookie_val.split("|")[0]
        blog = Blog.get_by_id(int(post_id))
        # Before adding/removing likes, first check if the op is valid.
        # Proceed if all is well.
        if self.is_valid(cookie_val,blog):
            # Check if user already liked the post.
            # This determines whether to like/unlike post.
            if user_id in blog.liked_by:
                self.remove_like(blog,user_id)
            else:
                self.add_like(blog,user_id) 
        else:
            if not self.is_signed_in(cookie_val):
                error = "Not signed in."
                self.response.set_status(401)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(error)
            # Check if blog exists.
            elif not self.blog_exists(blog):
                error = "Post doesn't exist."
                self.response.set_status(404)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(error)
                self.response
            # Check if user is the author.
            elif self.is_author(cookie_val,blog):
                error = "Post cannot be liked by creator."
                self.response.set_status(400)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(error)
    
    def is_valid(self,cookie_val,blog):
        # Check if user is signed in.
        if not self.is_signed_in(cookie_val):
            return False
        # Check if blog exists.
        elif not self.blog_exists(blog):
            return False
        # Check if user is the author.
        elif self.is_author(cookie_val,blog):
            return False
        return True


# ROUTES
class ReadMain(Handler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get('user_id')
        # Query 10 most recent blog posts.
        query = Blog.gql("ORDER BY date_created DESC")
        blogs = query.fetch(limit=10)
        # Determine whether to insert 'Login' or 'Logout' button.
        if self.is_signed_in(cookie_val):
            self.render('mainPage.html', blogs=blogs, signed_in=True)
        else:
            self.render('mainPage.html', blogs=blogs)


class CreateBlog(Handler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get('user_id')
        # Check if user has enough authority to create a blog post.
        if self.is_signed_in(cookie_val):
            # Since user is logged in, insert 'Logout' button.
            self.render('createPost.html', error="", signed_in= True)
        else:
            # Otherwise, make user login.
            self.redirect('/blog/login')

    def post(self):
        # Harvest requirements.
        title = self.request.get('title')
        content = self.request.get('content')
        cookie_val = self.request.cookies.get('user_id')
        # Check that there are no problem with creating a blog post.
        if self.is_valid(cookie_val,content,title):
            # If all is well, store information to database.
            user = User.get_by_id(int(cookie_val.split("|")[0]))
            blog_entry = Blog(title=title, content=content, author=user, 
                                    number_of_likes=0)
            # Finally, redirect user to the newly created page
            blog_id = (blog_entry.put()).id()
            self.redirect('/blog/%s' %blog_id)
        else:
            # If not signed in, redirect user to login page.
            if not self.is_signed_in(cookie_val):
                self.redirect("/blog/login")
            # If any contents are missing, return error to user. 
            elif not (title and content):
                error = ("Either title or content is missing. Please fill both "
                        "in, and try again.")
                self.render('createPost.html', error=error)

    def is_valid(self,cookie_val,content,title):
        # Check if user signed in.
        if not self.is_signed_in(cookie_val):
            return False
        # Check contents are non-empty.
        elif not (title and content):
            return False
        return True

class UpdateBlog(Handler):

    def get(self,post_id):
        # Harvest requirements.
        cookie_val = self.request.cookies.get('user_id')
        blog = Blog.get_by_id(int(post_id))
        # Check if user is authorized to modify the blog post.
        if self.is_get_valid(blog,cookie_val):
            # If all is well, proceed to the page.
            # Since user is logged in, insert logout button.
            self.render('updateBlog.html', blog=blog, signed_in=True)       
        else:
            if not blog:
                self.response.set_status(404)
                self.redirect("/blog/not_found")
            elif not self.is_signed_in(cookie_val):
                self.response.set_status(401)
                self.redirect("/blog/login")
            elif not self.is_author(cookie_val,blog):
                self.response.set_status(403)
                self.redirect("/blog/not_authorized")

    def post(self,post_id):
        # Harvest requirments.
        title = self.request.get('title')
        content = self.request.get('content')
        cookie_val = self.request.cookies.get('user_id')
        blog = Blog.get_by_id(int(post_id))
        # Check whether all req. has been met.
        if self.is_post_valid(blog,cookie_val,content,title):
                # If all is well, store information to database.
                blog.title = title
                blog.content = content
                # Finally, redirect user to the newly created page
                blog_id = (blog.put()).id()
                self.response.set_status(200)
                self.redirect('/blog/%s' % blog_id)
        else:
            if not blog:
                self.response.set_status(404)
                self.redirect("/blog/not_found")
            elif not self.is_signed_in(cookie_val):
                self.response.set_status(401)
                self.redirect("/blog/login")
            elif not self.is_author(cookie_val,blog):
                self.response.set_status(403)
                self.redirect("/blog/not_authorized")
            elif not (title and content):
                # Re-render page with error.
                error = ("Either title or texts are empty. Please fill "
                        "both in before trying again.")
                self.render('updateBlog.html', title=title, content=content,
                            error=error, signed_in=True)               

    def is_get_valid(self,blog,cookie_val):
        if not blog:
            return False
        elif not self.is_signed_in(cookie_val):
            return False
        elif not self.is_author(cookie_val,blog):
            return False
        return True

    def is_post_valid(self,blog,cookie_val,content,title):
        if not blog:
            return False
        elif not self.is_signed_in(cookie_val):
            return False
        elif not self.is_author(cookie_val,blog):
            return False
        elif not (title and content):
            return False
        return True


class DeleteBlog(Handler):

    def get(self,post_id):
        # Harvest requirements.
        cookie_val = self.request.cookies.get('user_id')
        blog = Blog.get_by_id(int(post_id))
        # Check if user has all req. to delete a post.
        if self.is_valid(blog,cookie_val):
            # Since user is logged in, display 'Logout' button.
            self.render('deleteBlog.html', blog=blog, signed_in=True)
        else:
            if not blog:
                self.response.set_status(404)
                self.redirect("/blog/not_found")
            elif not self.is_signed_in(cookie_val):
                self.response.set_status(401)
                self.redirect("/blog/login")
            elif not self.is_author(cookie_val,blog):
                self.response.set_status(403)
                self.redirect("/blog/not_authorized")

    def post(self,post_id):
        # Harvest requirements.
        blog = Blog.get_by_id(int(post_id))
        cookie_val = self.request.cookies.get('user_id')
        # Check whether all req. has been met before deleting a post.
        if self.is_valid(blog,cookie_val):
                blog.delete()
                self.response.set_status(200)
                self.redirect("/blog")
        else:
            if not blog:
                self.response.set_status(404)
                self.redirect("/blog/not_found")
            elif not self.is_signed_in(cookie_val):
                self.response.set_status(401)
                self.redirect("/blog/login")
            elif not self.is_author(cookie_val,blog):
                self.response.set_status(403)
                self.redirect("/blog/not_authorized")

    def is_valid(self,blog,cookie_val):
        if not blog:
            return False
        elif not self.is_signed_in(cookie_val):
            return False
        elif not self.is_author(cookie_val,blog):
            return False
        return True


class ReadBlog(Handler):

    def get(self,post_id):
        # Harvest requirements.
        cookie_val = self.request.cookies.get('user_id')
        blog = Blog.get_by_id(int(post_id))
        # Query all comments for the post
        comments = (Comment.all().filter("blog =",blog.key()).
                    order('-date_created'))
        # Determine whether to insert 'Login' or 'Logout' button.
        # As well, determine what type of message to put for comments.
        if self.is_signed_in(cookie_val):
            self.render('readPost.html', blog=blog, signed_in = True, 
                        comments=comments)
        else:
            self.render('readPost.html', blog=blog,comments=comments)

    def has_comments(self,comments):
        if comments:
            return True
        else:
            return False


class ReadSignUp(LoginHandler):

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
            self.render_front(username=username, password=password, 
                                verify_pw=verify_pw, email=email, errors=errors)
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
        self.render('signUp.html',title=title, username=username, 
                    password=password, verify_pw=verify_pw, email=email,
                    errors=errors)


class ReadWelcome(Handler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get('user_id')
        # Show this page to logged-users only.
        if self.is_signed_in(cookie_val):
            # Query user to display username in the welcome message.
            user_id = cookie_val.split("|")[0]
            result = User.get_by_id(int(user_id))
            # Also, include 'Logout' button, since user has singed in.
            self.render("welcome.html",user= result,signed_in = True)
        else:
            # Otherwise, make user login.
            self.redirect('/blog/login')


class ReadLogin(LoginHandler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get('user_id')
        # Check if user has logged in.
        if self.is_signed_in(cookie_val):
            self.redirect('/blog/welcome')
        # If not logged in, continue to login page.
        else:
            self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')      
        # Checks whehter the inputs are correctly filled.
        if (username and password):
            query = User.gql("WHERE username=:username",username=username)
            user = query.fetch(limit=1)
            if self.is_login_successful(username,password,user):
                # Create cookie and store user info if successful.
                user_id = user[0].key().id()
                cookie_val = self.make_secure_val(user_id)
                self.response.headers.add_header('Set-Cookie',
                                                'user_id=%s;Path=/'%cookie_val)      
                self.redirect('/blog/welcome')
            else:
                # Else, re-render page with the following message.
                error = ("Either username or password are incorrect. Please try "
                        "again.")
                self.render('login.html', error=error, username=username,
                            password=password)
        else:
            # Else, re-render page with the following message.
            error = ("Either username or password fields are empty. Please fill "
                    "in, and try again.")
            self.render('login.html', error=error, username=username, 
                        password=password)
 
            
class ReadLogout(LoginHandler):

    def get(self):
        # Clear out the cookie. 
        # This prevents user from automatic re-login.
        self.response.headers.add_header('Set-Cookie','user_id=;Path=/')
        self.redirect('/blog/login')


class ReadNotFound(Handler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        #  Determine whether to insert 'Login' or 'Logout' button.
        if self.is_signed_in(cookie_val):
            self.render("readNotFound.html",signed_in=True)
        else:
            self.render("readNotFound.html")


class ReadNotAuthorized(Handler):

    def get(self):
        # Harvest requirements.
        cookie_val = self.request.cookies.get("user_id")
        #  Determine whether to insert 'Login' or 'Logout' button.
        if self.is_signed_in(cookie_val):
            self.render("readNotAuthorized.html",signed_in=True)
        else:
            self.render("readNotAuthorized.html")


app = webapp2.WSGIApplication([('/blog',ReadMain), ('/blog/',ReadMain),
                                ('/blog/newpost', CreateBlog),
                                ('/blog/newpost/', CreateBlog),
                                ('/blog/(.*\d)',ReadBlog),
                                ('/blog/(.*\d)/',ReadBlog),
                                ('/blog/(.*\d)/edit',UpdateBlog),
                                ('/blog/(.*\d)/edit/',UpdateBlog),
                                ('/blog/(.*\d)/delete',DeleteBlog),
                                ('/blog/(.*\d)/delete/',DeleteBlog),
                                ('/blog/signup',ReadSignUp),
                                ('/blog/signup/',ReadSignUp),
                                ('/blog/welcome',ReadWelcome),
                                ('/blog/welcome/',ReadWelcome),
                                ('/blog/login',ReadLogin),
                                ('/blog/login/',ReadLogin),
                                ('/blog/logout',ReadLogout),
                                ('/blog/logout/',ReadLogout),
                                ('/blog/(.*\d)/like',UpdateLike),
                                ('/blog/(.*\d)/like/',UpdateLike),
                                ('/blog/(.*\d)/comment/new',PostComment),
                                ('/blog/(.*\d)/comment/new/',PostComment),
                                ('/blog/(.*\d)/comment/delete',DeleteComment),
                                ('/blog/(.*\d)/comment/delete/',DeleteComment),
                                ('/blog/(.*\d)/comment/edit',UpdateComment),
                                ('/blog/(.*\d)/comment/edit/',UpdateComment),
                                ('/blog/(.*\d)/comment/validate',ValidateBeforeEdit),
                                ('/blog/(.*\d)/comment/validate/',ValidateBeforeEdit),
                                ('/blog/not_found',ReadNotFound),
                                ('/blog/not_found/',ReadNotFound),
                                ('/blog/not_authorized',ReadNotAuthorized),
                                ('/blog/not_authorized/',ReadNotAuthorized)], 
                                debug=True)