from google.appengine.ext import db

#GQL automatically adds key ID when an entry is added

class Blog(db.Model):
	title = db.StringProperty(required=True)
	content = db.TextProperty(required=True)
	dateCreated = db.DateTimeProperty(auto_now_add=True)

