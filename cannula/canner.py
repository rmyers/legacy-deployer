from functools import wraps
import logging

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify
from flask.views import MethodView

from cannula.conf import api
from cannula.api.exceptions import UnitDoesNotExist, DuplicateObject,\
    PermissionError

app = Flask('cannula')
#app.config.from_object(__name__)

def login_required(f):
    """Redirect users to login page who are not logged in."""
    @wraps(f)
    def wrapper(*args, **kwds):
        if session.get('logged_in'):
            return f(*args, **kwds)   
        return redirect(url_for('login'))
    return wrapper

def api_view(f):
    """Require login, raise 401 error. TODO: other stuff?"""
    @wraps(f)
    def wrapper(*args, **kwds):
        if session.get('logged_in'):
            return f(*args, **kwds)   
        abort(401)
    return wrapper

class CannulaView(MethodView):
    
    def default_context(self, extra_ctx=None):
        ctx = {'user': None}
        if session.get('logged_in'):
            user = api.users.get(session['user'])
            ctx['user'] = user
        # TODO: other stuff here too?
        if extra_ctx is not None:
            ctx.update(extra_ctx)
        return ctx

class Index(CannulaView):

    def get(self):
        ctx = self.default_context()
        return render_template('flask/index.html', **ctx)

class Login(CannulaView):
    
    def get(self):
        ctx = self.default_context()
        return render_template('flask/login.html', **ctx)
    
    def post(self):
        _next = request.args.get('next', '/')
        user = request.form.get('username')
        password = request.form.get('password')
        if not (user or password):
            abort(400)
        
        user = api.users.get(user)
        if user.check_password(password):
            session['logged_in'] = True
            session['user'] = user.name
            flash('You were logged in')
            return redirect(_next)
        
        ctx = self.default_context({'error': "Invalid user or password"})
        return render_template('flask/login.html', **ctx)

class Logout(CannulaView):
    
    def get(self):
        session['logged_in'] = False
        session['user'] = ''
        return redirect('/')

class Group(CannulaView):
    
    def get(self, group):
        try:
            group = api.groups.get(group)
        except UnitDoesNotExist:
            abort(404)
        
        ctx = self.default_context({'group': group, 'title': unicode(group)})
        return render_template('flask/group.html', **ctx)

class GroupAPI(CannulaView):
    
    @api_view
    def get(self, group=None):
        if group is not None:
            try:
                group = api.groups.get(group)
            except UnitDoesNotExist:
                abort(404)
            return jsonify(**group.to_dict())
        
        groups = [g.to_dict() for g in api.groups.list(user=session['user'])]
        
        return jsonify(objects=groups)
    
    @api_view
    def post(self):
        name = request.form.get('name')
        description = request.form.get('description')
        if not name:
            return jsonify(errorMsg="Name Required")
        
        try:
            group = api.groups.create(name, user=session['user'], description=description)
        except DuplicateObject:
            return jsonify(errorMsg="A group by that name exists.")
        except:
            return jsonify(error="Unknown Error")
        
        return jsonify(**group.to_dict())
    
    @api_view
    def delete(self, group):
        try:
            group = api.groups.get(group)
            api.groups.delete(group, user=session['user'])
        except UnitDoesNotExist:
            abort(404)
        except PermissionError:
            abort(403)
        
        return jsonify(message="Group deleted")
        
class ProjectAPI(CannulaView):
    
    @api_view
    def get(self, project=None):
        group = self.request.args.get('group', None)
        if group is not None:
            try:
                projects = [p.to_dict() for p in api.groups.list_projects(group, fetch=True)]
            except UnitDoesNotExist:
                abort(404)
        elif project is not None:
            return jsonify(project=api.projects.get(project).to_dict())
        else:
            projects = [p.to_dict() for p in api.projects.list_all(fetch=True)]
        
        return jsonify(objects=projects)
    
    @api_view
    def post(self):
        name = request.form.get('name')
        description = request.form.get('description')
        if not name:
            return jsonify(errorMsg="Name Required")
        
        try:
            group = api.groups.create(name, user=session['user'], description=description)
        except DuplicateObject:
            return jsonify(errorMsg="A group by that name exists.")
        except:
            return jsonify(error="Unknown Error")
        
        return jsonify(**group.to_dict())
    
    @api_view
    def delete(self, group):
        try:
            group = api.groups.get(group)
            api.groups.delete(group, user=session['user'])
        except UnitDoesNotExist:
            abort(404)
        except PermissionError:
            abort(403)
        
        return jsonify(message="Group deleted")        
        
app.add_url_rule('/', view_func=Index.as_view('index'))
app.add_url_rule('/login/', view_func=Login.as_view('login'))
app.add_url_rule('/logout/', view_func=Logout.as_view('logout'))

# Group API
group_view = GroupAPI.as_view('group_api')
app.add_url_rule('/api/groups/', defaults={'group': None},
                 view_func=group_view, methods=['GET',])
app.add_url_rule('/api/groups/', view_func=group_view, methods=['POST',])
app.add_url_rule('/api/groups/<group>', view_func=group_view,
                 methods=['GET', 'PUT', 'DELETE'])

# Project API
project_view = ProjectAPI.as_view('project_api')
app.add_url_rule('/api/projects/', defaults={'project': None},
                 view_func=project_view, methods=['GET',])
app.add_url_rule('/api/projects/', view_func=project_view, methods=['POST',])
app.add_url_rule('/api/projects/<project>', view_func=project_view,
                 methods=['GET', 'PUT', 'DELETE'])

# Greedy Urls
app.add_url_rule('/<group>/', view_func=Group.as_view('group'))

if __name__ == '__main__':
    #logging.basicConfig()
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.debug = True
    app.run()