from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import append, upload_template

import sys
import time
import os
    
def live():
    env.hosts = ['ec2-184-72-160-76.compute-1.amazonaws.com']
    env.user = 'ubuntu'

def get_revision_hash(treeish="master"):
    return local("git rev-parse %s" % treeish, capture=True)    
    
def deploy_site(treeish="master"):
    # TODO: Allow for deploying a clean copy
    src_dir = "."
    
    revision_hash = get_revision_hash(treeish)
    deploy_dir = os.path.join("netflix", revision_hash)
    current_symlink = "netflix/current"
    sudo("apt-get install supervisor")
    sudo("pip install virtualenv")
    run("mkdir -p %s" % deploy_dir)
    put("site/", deploy_dir)
    put("deployment/requirements.txt", deploy_dir)
    
    # TODO: This may fail on the first install (since supervisord won't know anything about netflix yet)
    sudo("supervisorctl stop netflix")
    with cd(deploy_dir):
        run("virtualenv --no-site-packages env")
        run("pip install -E env -r requirements.txt")
    
    with cd(deploy_dir):
            abs_deploy_dir = run("pwd")
                
    upload_template("deployment/netflix.conf", 
                    os.path.join(deploy_dir, "netflix.conf"), 
                    {"deploy_dir":abs_deploy_dir})
    sudo("ln -sf %s /etc/apache2/sites-available/netflix" % os.path.join(abs_deploy_dir, "netflix.conf"))
    upload_template("deployment/netflix.supervisord", 
                    os.path.join("/tmp/", "netflix.conf"), 
                    {"deploy_dir":abs_deploy_dir})
    sudo("mv /tmp/netflix.conf /etc/supervisor/conf.d/")
    sudo("a2ensite netflix")
    sudo("a2enmod proxy")
    sudo("a2enmod proxy_http")
    run("rm -f %s && ln -sf %s %s" % (current_symlink, revision_hash, current_symlink))
    sudo("/etc/init.d/apache2 reload")
    sudo("supervisorctl start netflix")
    