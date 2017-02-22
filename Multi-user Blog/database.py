from google.appengine.ext import db

# DATABASE
class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.EmailProperty(required=True)

class Blog(db.Model):
    title = db.StringProperty(required=True)
    subtitle = db.StringProperty()
    content = db.TextProperty(required=True)
    date_created = db.DateTimeProperty(auto_now_add=True)
    author = db.ReferenceProperty(User)
    number_of_likes = db.IntegerProperty()
    liked_by = db.StringListProperty()

class Comment(db.Model):
    title = db.StringProperty(required=True)
    date_created = db.DateTimeProperty(auto_now_add=True)
    content = db.TextProperty(required=True)
    author = db.ReferenceProperty(User)
    blog = db.ReferenceProperty(Blog)