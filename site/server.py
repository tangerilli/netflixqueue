import sys
import os

import cherrypy
from cherrypy.process import wspbus, plugins
 
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import String, Integer
try:
    import json
except:
    import simplejson as json

# Helper to map and register a Python class a db table
Base = declarative_base()
 
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email_address = Column(String)
 
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
 
    @staticmethod
    def list(session):
        return session.query(QueueItem).all()
        
    def to_json(self):
        return json.dumps({"movie_id":self.movie_id, "movie_title":self.movie_title, "queued":True})
 
 
class SAEnginePlugin(plugins.SimplePlugin):
    def __init__(self, bus):
        """
        The plugin is registered to the CherryPy engine and therefore
        is part of the bus (the engine *is* a bus) registery.
 
        We use this plugin to create the SA engine. At the same time,
        when the plugin starts we create the tables into the database
        using the mapped class of the global metadata.
 
        Finally we create a new 'bind' channel that the SA tool
        will use to map a session to the SA engine at request time.
        """
        plugins.SimplePlugin.__init__(self, bus)
        self.sa_engine = None
        self.bus.subscribe("bind", self.bind)
 
    def start(self):
        db_path = os.path.abspath(os.path.join(os.curdir, 'queues.db'))
        self.sa_engine = create_engine('sqlite:///%s' % db_path, echo=True)
        Base.metadata.create_all(self.sa_engine)
 
    def stop(self):
        if self.sa_engine:
            self.sa_engine.dispose()
            self.sa_engine = None
 
    def bind(self, session):
        session.configure(bind=self.sa_engine)
 
class SATool(cherrypy.Tool):
    def __init__(self):
        """
        The SA tool is responsible for associating a SA session
        to the SA engine and attaching it to the current request.
        Since we are running in a multithreaded application,
        we use the scoped_session that will create a session
        on a per thread basis so that you don't worry about
        concurrency on the session object itself.
 
        This tools binds a session to the engine each time
        a requests starts and commits/rollbacks whenever
        the request terminates.
        """
        cherrypy.Tool.__init__(self, 'on_start_resource',
                               self.bind_session,
                               priority=20)
 
        self.session = scoped_session(sessionmaker(autoflush=True,
                                                  autocommit=False))
 
    def _setup(self):
        cherrypy.Tool._setup(self)
        cherrypy.request.hooks.attach('on_end_resource',
                                      self.commit_transaction,
                                      priority=80)
 
    def bind_session(self):
        cherrypy.engine.publish('bind', self.session)
        cherrypy.request.db = self.session
 
    def commit_transaction(self):
        cherrypy.request.db = None
        try:
            self.session.commit()
        except:
            self.session.rollback()  
            raise
        finally:
            self.session.remove()
    
class Queue(object):
    @cherrypy.expose
    def index(self, email_address):
        #TODO: Return queue based on accepted content types
        return "queue list for %s goes here" % email_address
    
    @cherrypy.expose
    def add(self, email_address, movie_id, title=None):
        try:
            # Get the user
            user = self.get_user(email_address)
            # Make sure this movie isn't already in the queue
            if self.get_queue(user, movie_id).all():
                return json.dumps({"result":"ok"})
            item = QueueItem(movie_id, title, user)
            cherrypy.request.db.add(item)
            return json.dumps({"result":"ok"})
        except Exception, e:
            return json.dumps({"result":"error", "error_msg":str(e)})

    @cherrypy.expose
    def delete(self, email_address, movie_id):
        try:
            # TODO: Remove duplication here
            # Get the user
            user = self.get_user(email_address)
            queued_items = self.get_queue(user, movie_id).all()
            if queued_items:
                for queued_item in queued_items:
                    cherrypy.request.db.delete(queued_item)
                print "Removing %s" % movie_id
            return json.dumps({"result":"ok"})
        except Exception, e:
            return json.dumps({"result":"error", "error_msg":str(e)})
    
    @cherrypy.expose
    def get(self, email_address, movie_id):
        try:
            user = self.get_user(email_address)
            queued_items = self.get_queue(user, movie_id).all()
            if queued_items:
                return queued_items[0].to_json()
            else:
                return json.dumps({"queued":False})
        except Exception, e:
            return json.dumps({"queued":False})
    
    def get_user(self, email_address):
        return cherrypy.request.db.query(User).filter(User.email_address == email_address).first()

    def get_queue(self, user, movie_id=None):
        qry = cherrypy.request.db.query(QueueItem).filter(QueueItem.user == user)
        if movie_id:
            qry = qry.filter(QueueItem.movie_id == movie_id)
        return qry

class Users(object):
    @cherrypy.expose    
    def index(self):
        # TODO: Do something more useful here?
        return "Users"

class Root(object):
    users = Users()
    
    @cherrypy.expose
    def index(self):
        # TODO: Return API info?
        return "Netflix Queue Service"

def setup_routes():
    #Setup routes
    d = cherrypy.dispatch.RoutesDispatcher()

    # For Routes 1.12+ only...
    d.mapper.explicit = False
    d.connect('users', '/users', Users())
    d.connect('queue', '/users/:email_address/queue', Queue(), conditions={'method':['GET']})
    d.connect('queue', '/users/:email_address/queue/:movie_id', Queue(), conditions={'method':['POST']}, action="add")
    d.connect('queue', '/users/:email_address/queue/:movie_id', Queue(), conditions={'method':['DELETE']}, action="delete")
    d.connect('queue', '/users/:email_address/queue/:movie_id', Queue(), conditions={'method':['GET']}, action="get")
    d.connect('main', '/', Root())
    return d
    
def main(argv):
    # Start the web server
    SAEnginePlugin(cherrypy.engine).subscribe()
    cherrypy.tools.db = SATool()
    cherrypy.tree.mount(None, config={'/': {'tools.db.on': True, 'request.dispatch':setup_routes()}})
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__=="__main__":
    sys.exit(main(sys.argv))