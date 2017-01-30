import os
import webapp2
import jinja2
import hmac
import string
import random
import hashlib
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)
secret = "A!03bcAs249Gka134!4*@1`asdAq"

class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw): 
		return self.response.out.write(*a,**kw)

	def render_str(self,template,**params):
		template_file = jinja_env.get_template(template)
		return template_file.render(params)

	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

	def hash_str(self,s,secret=secret):
		"""
		hash_str(self,s,secret=secret)

		Converts the input into a hashed value. This function uses md5 hash algorithm.

		Args:
			s (string) - string to be hashed
			
		Outputs:
			string - hashed value of the input
		"""

		return hmac.new(str(secret),str(s)).hexdigest() 

	def make_secure_val(self,s):
		"""
		make_secure_val(self,s)

		Converts the input into a string consisting of the input and its hashed value 
		separated by "|" symbol. It is used primarily for the variable 'user_id'
		during the generation of a cookie.
		
		Args:
			s (string)
		
		Outputs:
			string - the input and hashed value separated by "|" symbol.
		"""
		return "%s|%s" %(s,self.hash_str(s)) 

	def is_user_signed_in(self):
		"""
		is_user_signed_in(self)

		Checks if user is signed in. 

		User is signed in if "user_id" in cookie is valid.

		Args:
			cookie_value (String)

		Outputs:
			Boolean - False when cookie is invalid, and True if not.
		"""

		# Check if the cookie value is empty
		cookie_value = self.request.cookies.get('user_id')
		if not cookie_value:
			# Return false if empty
			return False 

		# Check if the cookie value is in right format. That is, the entry id of a user and its
		# hashed value separated by "|" symbol
		try:
			val,hashed_val = cookie_value.split("|")
		except:
			# Return False if its in wrong format. It could be the result of tempering
			return False 

		# Check if the hashed value and the hashed entry id of a user are the same.
		if not (self.hash_str(val) == hashed_val):
			# Return false when they don't match. It means the cookie has been tempered.
			return False 

		# Check if the user exists in database
		if User.get_by_id(int(val)) == None:
			# Return False when no users are found. Could be the result of tempering, or accidental wipeout of database.
			return False 

		# Return true when all is well
		return True

class ReadMainPage(Handler):
	def get(self):

		# Query 10 most recent blog entries in descending order
		query = Blog.gql("ORDER BY dateCreated DESC")
		blogs = query.fetch(limit=10)

		# Render page
		if self.is_user_signed_in():
			self.render('mainPage.html',blogs=blogs,signed_in=True)
		else:
			self.render('mainPage.html', blogs=blogs)


class CreatePost(Handler):
	def get(self):
		if self.is_user_signed_in():

			# Return template containing form for adding blog post
			self.render('createPost.html', error="", signed_in= True)

		else:
			self.redirect('/blog/login')

	def post(self):

		# Harvest form-information
		title = self.request.get('title')
		content = self.request.get('content')

		# Check if content in title and content are non-empty
		if (title and content):

			#If all is well, proceed to storing information to database
			blog_entry = Blog(title=title,content=content)
			blog_key = blog_entry.put()
			blog_id = blog_key.id()

			#Once done, redirect user to the blog post
			self.redirect('/blog/%s' %blog_id)			

		else:
			#if any information is missing, tell user to fill out the missing content and resubmit it
			error = "Either title or content is missing. Please fill both in, and try again."
			self.render('createPost.html',error=error)	

class UpdatePost(Handler):
	def get(self,post_id):

		# Check if user signed in
		# Render Page if signed in
		if self.user_signed_in():
			# Query specific blog entry by key ID
			blog = Blog.get_by_id(int(post_id))

			# Render template
			self.render('updatePost.html',blog=blog, signed_in=True)

		# Otherwise, redirect user to sign-up page
		else:
			self.redirect('/blog/login') 
	def post(self,post_id):

		# Harvest form-information
		title = self.request.get('title')
		content = self.request.get('content')

		# Check if content in title and content are non-empty
		if (title and content):
			#if all is well, store information to database
			blog = Blog.get_by_id(int(post_id))
			blog.title = title
			blog.content = content
			blog_key = blog.put()
			blog_id = blog_key.id()

		# Redirect user to the updated post
		self.redirect('/blog/%s' % blog_id)

class DeletePost(Handler):

	def get(self,post_id):
		# Check if user is signed in
		if self.is_user_signed_in():
			
			# Render template
			blog = Blog.get_by_id(int(post_id))

			if blog != None:
				self.render('deletePost.html',blog=blog, signed_in=True)
			else:
				self.redirect('/blog')
		else:
			self.redirect('/blog/login')

	def post(self,post_id):
		# Retrieve post by id
		blog = Blog.get_by_id(int(post_id))

		# Delete post
		blog.delete()

		# Redirect user back to main page once done 
		self.redirect('/blog')


class ReadPost(Handler):
	def get(self,post_id):

		# Query the blog post by id
		blog = Blog.get_by_id(int(post_id))

		# Return template with the query result
		if self.is_user_signed_in():
			self.render('readPost.html',blog=blog,signed_in = True)
		else:
			self.render('readPost.html',blog=blog)

class ReadSignUpPage(Handler):

	def get(self):
		
		# Check if User is signed in 
		if not self.is_user_signed_in():
			# If not valid, proceed to signup page
			# But first, empty the cookie
			self.response.headers.add_header('Set-Cookie','user_id=;Path=/')
			self.render('signUp.html',title="Sign-Up")

		# If cookie is valid, the user is signed-in. Redirect user to welcome page
		else:
			self.redirect('/blog/welcome')

	def post(self):

		# Get form inputs
		username  = self.request.get('username')
		password  = self.request.get('password')
		verify_pw = self.request.get('verify')
		email     = self.request.get('email')

		# Check form information
		errors = self.check_form_info(username,password,verify_pw,email)
		
		# If errors exist, re-render template with errors
		if errors["errors_exist"]:
			self.render_front(username=username,password=password,verify_pw=verify_pw,email=email,errors=errors)

		else:
			# If all is well, store newly created user to database
			hashed_password = self.make_pw_hash(password)
			user_id = self.register(username,hashed_password,email)

			# And finish by generating a cookie. This is to keep user signed in.
			cookie_val = self.make_secure_val(user_id)
			self.response.headers.add_header('Set-Cookie','user_id=%s;Path=/' %cookie_val)

			# Redirect user to welcome page
			self.redirect('/blog/welcome')

	def render_front(self,title="",username="",password="",verify_pw="",email="",errors=""):
		self.render('signUp.html',
			title=title,
			username=username,
			password=password,
			verify_pw=verify_pw,
			email=email,
			errors=errors)

	def username_already_exists(self,username):
		"""
		username_already_exists(self,username)

		Checks if username exists in database. 

		This method ensures the uniqueness of usernames.

		Args
			username (String) 

		Outputs
			boolean - True if returned value not empty. False otherwise.
		"""

		# see parametric binding for more details (https://cloud.google.com/appengine/docs/python/datastore/gqlqueryclass)
		query = User.gql("WHERE username=:username", username = username)
		result = query.fetch(limit=1)
		if result:
			return True
		return False


	def check_form_info(self,username="",password="",verify_pw="",email=""):
		"""
		check_form_info(self,username="",password="",verify_pw="",email="")

		Checks the correctness of information. It checks whether all information are present, 
		whether the username already exists, and whether the values from password and verify-password
		input field are equal.

		If all informations are present without errors, 'errors_exist' will return FALSE.

		If one or more errors are present, 'errors_exist' will return TRUE.

		Args:
			username  (String)
			password  (String)
			verify_pw (String)
			email     (String)

		Outputs:
			Dictionary - Dictionary of errors. The values for each key are boolean.
			It consists of the following keys:

				- errors_exist      (Boolean)
				- username_empty    (Boolean)
				- password_empty    (Boolean)
				- verify_pw_empty   (Boolean)
				- email_empty       (Boolean)
				- username_exists   (Boolean)
				- password_mismatch (Boolean)

		"""
		errors = {
				"errors_exist": False,
				"username_empty": False,
				"password_empty": False,
				"verify_pw_empty": False,
				"email_empty": False,
				"username_exists": False,
				"password_mismatch":False
				}
		# Checks if all harvested information are non-empty
		if not (username and password and verify_pw and email):
			# Check each field if any one of them is missing
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
		# Check if username already exists
		if self.username_already_exists(username):
			errors["username_exists"] = True
			errors["errors_exist"] = True

		# Check if the password and verify password match
		if not (password == verify_pw):
			errors["password_mismatch"] = True
			errors["errors_exist"] = True

		return errors

	def register(self,username,hashed_password,email):
		"""
		register(self,username,hashed_password,email)

		Registers an user to database.

		Args
			username        (string)
			hashed_password (string)
			email           (string)

		Output
			String - The id of username
		"""
		user = User(username=username,password=hashed_password,email=email)
		user_key = user.put()
		return str(user_key.id())

	def make_pw_hash(self,password):
		"""
		make_pw_hash(self,password)

		Converts a string into a hased value using randomly generated salt.
		This method uses sha256 algorithm.

		Args:
			password (String)

		Outputs:
			String - hashed password and its salt separated by a comma
		"""
		salt = self.make_salt()			
		hashed_password = hmac.new(salt,password,hashlib.sha256).hexdigest()
		return "%s,%s" % (hashed_password,salt)

	def make_salt(self):
		"""
		make_salt(self)

		Randomly generates alphanumeric string

		Args:

			None

		Output

			String - Alphanumeric string
		"""
		return "".join([random.choice(string.letters+string.digits) for i in range(10)])

class ReadWelcomePage(Handler):
	def get(self):

		# Check if user is signed in 
		if self.is_user_signed_in():
			# Otherwise, fetch user info and proceed to welcome page
			cookie_value = self.request.cookies.get('user_id')
			user_id = cookie_value.split("|")[0]
			result = User.get_by_id(int(user_id))
			print(result)

			self.render("welcome.html",user= result,signed_in = True )

		else:
			# if not signed in, redirect to login page
			self.redirect('/blog/login')

class ReadLoginPage(Handler):
	def get(self):
		# Check if user is signed in
		if self.is_user_signed_in():
			# If all is well, it means the user is signed-in. 
			# Redirect user to login page
			self.redirect('/blog/welcome')
		else:
			#if user not signed-in, proceed to login page
			self.render('login.html')

	def post(self):
		# Harvest form input
		username = self.request.get('username')
		password = self.request.get('password')
		
		# Check the validify of form input
		# First, check if the harvested information are non-empty
		if (username and password):
			# Retrieve user
			query = User.gql("WHERE username=:username",username=username)
			user = query.fetch(limit=1)

			# Here, we don't know if the fetched username and password are correct.
			# Check if the username exists, and if the password is correct 
			if self.is_login_successful(username,password,user):
				# Create cookie if the username exists and the password is correct.
				user_id = user[0].key().id()
				cookie_val = self.make_secure_val(user_id)
				self.response.headers.add_header('Set-Cookie','user_id=%s;Path=/'%cookie_val) 
				# Redirect user to welcome page		
				self.redirect('/blog/welcome')
			else:
				error = "Either username or password are incorrect. Please try again."
				self.render('login.html',error=error,username=username,password=password)
		else:
			error = "Either username or password fields are empty. Please fill in, and try again."
			self.render('login.html',error=error,username=username,password=password)

	def is_login_successful(self,username,password,user):
		"""
		is_login_successful(self,username,password,user)

		Determines whether the user is signed in by checking the validity of input. 

		Args:
			username (string)
			password (string)
			user     (list) - query result of anyone with the same username (should be no more than 1)

		Outputs:

			Boolean - True if username exists, and the entered password matches the stored password. It returns False otherwise
		"""
		if user:
			stored_hashed_password,salt = (user[0].password).split(",")
			hashed_password = hmac.new(str(salt),str(password),hashlib.sha256).hexdigest() #synthesize hashed password based on given salt

			# Check if the entered password matches the password of the username
			if stored_hashed_password == hashed_password:
				# Return True when passwords match. Login is successfull.
				return True 
			else:
				# Return False when passwords don't match. It means the entered password is incorrect.
				return False 
		else:
			# Return False if user list is empty.
			return False 

class ReadLogoutPage(Handler):

	def get(self):
		# Clear out the cookie. This prevents user from automatic re-login
		self.response.headers.add_header('Set-Cookie','user_id=;Path=/')
		
		#return use to signup page
		self.redirect('/blog/login')

class Blog(db.Model):
	title = db.StringProperty(required=True)
	content = db.TextProperty(required=True)
	dateCreated = db.DateTimeProperty(auto_now_add=True)

class User(db.Model):
	username = db.StringProperty(required=True)
	password = db.StringProperty(required=True)
	email = db.EmailProperty(required=True)

app = webapp2.WSGIApplication([('/blog',ReadMainPage), 
								('/blog/',ReadMainPage),
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