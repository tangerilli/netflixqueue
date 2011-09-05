import sys
import os

import framework
from models import QueueItem, User

import cherrypy
import simplejson as json 

def allow_cross_origin(f):
    def responder(*args, **kwargs):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = cherrypy.request.headers.get("Origin", "")
        return f(*args, **kwargs)
    return responder

def get_user(email_address):
    user = cherrypy.request.db.query(User).filter(User.email_address == email_address).first()
    # TODO: For now, just create the user if it doesn't exist
    if user is None:
        user = User(email_address)
        cherrypy.request.db.add(user)
    return user

def get_queue(user, movie_id=None):
    qry = cherrypy.request.db.query(QueueItem).filter(QueueItem.user == user)
    if movie_id:
        qry = qry.filter(QueueItem.movie_id == movie_id)
    return qry
 
class QueueView(object):
    @allow_cross_origin
    @cherrypy.expose
    def index(self, email_address):
        #TODO: Check content type before returning list
        user = get_user(email_address)
        queue = get_queue(user)
        # TODO: Add the URL of each queued item to the list
        if "application/json" in cherrypy.request.headers["Accept"]:
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return json.dumps([item.to_dict() for item in queue.all()])
        else:
            list_items = ["<li><a href='%s'>%s</li>" % (item.netflix_url, item.movie_title) for item in queue.all()]
            return "<html><body><h1>Queue</h1><ul>%s</ul></body></html>" % ("\n".join(list_items))

class QueueItemView(object):
    @allow_cross_origin
    @cherrypy.expose
    def add(self, email_address, movie_id, title=None):
        try:
            # Get the user
            user = get_user(email_address)
            # Make sure this movie isn't already in the queue
            if get_queue(user, movie_id).all():
                return json.dumps({"result":"ok"})
            item = QueueItem(movie_id, title, user)
            cherrypy.request.db.add(item)
            return json.dumps({"result":"ok"})
        except Exception, e:
            return json.dumps({"result":"error", "error_msg":str(e)})
            
    @allow_cross_origin
    @cherrypy.expose
    def delete(self, email_address, movie_id):
        print "Trying to delete %s" % movie_id
        try:
            # Get the user
            user = get_user(email_address)
            queued_items = get_queue(user, movie_id).all()
            if queued_items:
                for queued_item in queued_items:
                    cherrypy.request.db.delete(queued_item)
            return json.dumps({"result":"ok"})
        except Exception, e:
            return json.dumps({"result":"error", "error_msg":str(e)})
    
    @allow_cross_origin
    @cherrypy.expose
    def get(self, email_address, movie_id):
        try:
            user = get_user(email_address)
            print "user = %s" % user
            queued_items = get_queue(user, movie_id).all()
            if queued_items:
                return json.dumps(queued_items[0].to_dict())
            else:
                return json.dumps({"queued":False})
        except Exception, e:
            return json.dumps({"queued":False, "error_msg":str(e)})
     
    @allow_cross_origin
    @cherrypy.expose        
    def options(self, email_address, movie_id):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, PUT, DELETE'
        cherrypy.response.headers['Access-Control-Max-Age'] = 1000
        cherrypy.response.headers['Access-Control-Allow-Headers'] = '*'
        return ""

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
    d.connect('queue', '/users/:email_address/queue', QueueView(), action="index")
    d.connect('queueitem', '/users/:email_address/queue/:movie_id', QueueItemView(), conditions={'method':['POST']}, action="add")
    d.connect('queueitem', '/users/:email_address/queue/:movie_id', QueueItemView(), conditions={'method':['DELETE']}, action="delete")
    d.connect('queueitem', '/users/:email_address/queue/:movie_id', QueueItemView(), conditions={'method':['GET']}, action="get")
    d.connect('queueitem', '/users/:email_address/queue/:movie_id', QueueItemView(), conditions={'method':['OPTIONS']}, action="options")
    d.connect('main', '/', Root())
    return d
    
def main(argv):
    # Start the web server
    db_path = os.path.abspath(os.path.join(os.curdir, 'queues.db'))
    url = 'sqlite:///%s' % db_path
    
    framework.SAEnginePlugin(cherrypy.engine, url).subscribe()
    cherrypy.tools.db = framework.SATool()
    cherrypy.tree.mount(None, config={'/': {'tools.db.on': True, 'request.dispatch':setup_routes()}})
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__=="__main__":
    sys.exit(main(sys.argv))