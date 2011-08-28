from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import String, Integer

from framework import Base

import simplejson as json 
 
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email_address = Column(String)
    
    def __init__(self, email_address):
        Base.__init__(self)
        self.email_address = email_address
 
class QueueItem(Base):
    __tablename__ = 'queue_items'
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer)
    movie_title = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    user = relationship("User", backref=backref('queued_items', order_by=id))
 
    def __init__(self, movie_id, movie_title, user):
        Base.__init__(self)
        self.movie_id = movie_id
        self.movie_title = movie_title
        self.user = user
 
    def __str__(self):
        return self.movie_title
 
    def __unicode__(self):
        return self.movie_title
        
    def get_netflix_url(self):
        return "http://ca.movies.netflix.com/WiMovie/Star_Trek/%s" % self.movie_id
    netflix_url = property(get_netflix_url)
    
    def get_url(self):
        return "/users/%s/queue/%s" % (self.user.email_address, self.movie_id)
    url = property(get_url)
 
    @staticmethod
    def list(session):
        return session.query(QueueItem).all()
        
    def to_dict(self):
        return {"movie_id":self.movie_id, "movie_title":self.movie_title, 
                "queued":True, "URI":self.url, "netflix_url":self.netflix_url}
