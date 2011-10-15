from logging import getLogger

from django import http
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from django import forms

from cannula.api import DuplicateObject, UnitDoesNotExist, BaseAPI
from cannula.conf import api
from cannula.utils import make_admin_form, format_exception, validate_python_package_name

log = getLogger('api')


class CreateGroup(forms.Form):
    name = forms.CharField(label="Long name", max_length=100, required=False,
        help_text="A free-form name for your project group, e.g."
                  " <strong>\"Web Team\"</strong>.")
    abbr = forms.CharField(label="Python package name", max_length=50,
        help_text=("Python package name for your project group, e.g."
                   " <strong>\"web\"</strong>."))
    description = forms.CharField(required=False, widget=forms.Textarea)
    admin = forms.CharField(label="Admin User", required=False,
        help_text="By default, the requesting user becomes the admin for the"
                  " group.  Enter an username here to override that.")

    def clean_abbr(self):
        """Ensure name is a valid Python package name."""
        abbr = self.cleaned_data['abbr']
        validate_python_package_name(abbr)
        try:
            api.groups.get(abbr)
            raise forms.ValidationError(u'Group already exists.')
        except UnitDoesNotExist:
            pass
        return abbr


class EditMember(forms.Form):
    """Auto generated form for changing permissions of a user.
    
    This form displays all the current permissions possible for this
    group. If the key word argument 'edit'=True is passed then the
    username field will be hidden. Otherwise this form doubles as the 
    'add' form as well.
    """
    username = forms.CharField()
    
    def __init__(self, *args, **kwargs):
        edit = kwargs.pop('edit', False)
        super(EditMember, self).__init__(*args, **kwargs)
        if edit:
            # if we are editing the 
            self.fields['username'].widget = forms.HiddenInput()
        # generate a list of perms 
        perms = api.permissions.list()
        for p in perms:
            self.fields[p.perm] = forms.BooleanField(initial=p.default, required=False)

class GroupAPIBase(BaseAPI):
    
    create_template = 'cannula/form.html'
    details_template = 'cannula/group_details.html'
    list_template = 'cannula/groups.html'
    mod_member_template = 'cannula/form.html'
    
    create_form = CreateGroup
    member_form = EditMember
    
    def _get(self, groupname):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    
    def get(self, groupname):
        try:
            return self._get(groupname)
        except:
            raise UnitDoesNotExist("Group does not exist")
    
    
    def _create(self, abbr, name, description, **kwargs):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    
    def create(self, abbr, name='', description='', request_user=None, **kwargs):
        req_user = api.users.get(request_user)
        try:
            self.get(abbr)
            raise DuplicateObject()
        except UnitDoesNotExist:
            # create group
            if not name:
                name = abbr
            group = self._create(abbr, name, description, **kwargs)
            msg = 'Creating new group: %s' % abbr
            log.info(msg)
            api.log.create(message=msg, user=req_user, group=group)
            return group
    
    
    def _list(self, user=None, perm=None, **kwargs):
        """Subclasses should define this."""
        raise NotImplementedError()
        
    
    
    def list(self, user=None, perm=None, **kwargs):
        """
        Return a list of all groups.

        If user is given, then filter the list of groups to only those that
        the user has membership too (any permission).

        If perm is given, then filter the list of groups to only
        those that the user has the given permission to.
        """
        if user:
            user = api.users.get(user)
        return self._list(user=user, perm=perm, **kwargs)

    
    def members(self, groupname):
        log.debug("Looking up users in group: %s" % groupname)
        group = self.get(groupname)
        return group.members_list

    
    def check_members(self, groupname, req_user):
        """
        Check all group members to make sure they are active before attempting to
        add a project.  All members found to be inactive are removed from the
        group.
        """
        group = self.get(groupname)
        req_user = api.users.get(req_user)

        log.debug("Checking %s for active user status." % groupname)
        group_users = set()

        for user in self.members(group):
            # let the auth backend handle checking the user status.
            log.debug("Checking user: %s" % user)
            api.users.update(user)
            group_users.add(user)

        for user in group_users:
            if not user.is_active:
                # Revoke  permissions and admin and user roles.
                log.warn("Removing %s from group: %s" % (user, group.name))
                self.revoke_group_permissions(user, group, req_user=req_user)
    
    def _edit_user_forms(self, group):
        """Creates a list of users with edit permission forms for each."""
        forms = []
        members = self.members(group)
        perms = api.permissions.list()
        for member in members:
            initial = {'username': member.username}
            for p in perms:
                initial[p.perm] = member.has_perm(p.perm, group)
            form = self.member_form(initial=initial, edit=True)
            forms.append({'user': member, 'form': form})
    
        return forms

    @method_decorator(login_required)
    def list_view(self, request):
        """
        Display a list of development groups with their name and admin contact.
        """
        context = {
            'title': "Project Groups",
            'groups': api.groups.list(),
        }
        return self.respond(request, self.list_template, context)

   
    @method_decorator(login_required)
    @method_decorator(require_GET)
    @transaction.commit_on_success
    def details_view(self, request, group):
        """
        Handle form action for project group member management.
        """
        group = api.groups.get_or_404(group)
        if not request.user.has_perm('admin', group):
            return http.HttpResponseForbidden("<h1>Forbidden</h1>")
    
        addform = self.member_form()
    
        context = {
           'title': 'Details for group: %s' % group,
           'group': group,
           'addform': make_admin_form(addform),
           'errors': [],
           'editforms': self._edit_user_forms(group)
           }
        return self.respond(request, self.details_template, context)

    
    @method_decorator(login_required)
    @transaction.commit_on_success
    def create_view(self, request):
        """
        Display/process the create group form.
        """
        errors = False
        if request.method == "POST":
            form = self.create_form(data=request.POST)
            if form.is_valid():
                self.create(request_user=request.user, **form.cleaned_data)
                request.session['message'] = "Group successfully created."
                return http.HttpResponseRedirect(reverse('cannula-index'))
            errors = True
        else:
            form = self.create_form()
        context = {
            'title': "Create Group",
            'form': form,
            'cancel_url': reverse('cannula-index'),
            'errors': errors,
            'add': True,
        }
        return self.respond(request, self.create_template, context)


    @method_decorator(login_required)
    @transaction.commit_on_success
    def mod_member_view(self, request, group, action):
        """
        Handle form action for project group member management.
        """
        group = api.groups.get_or_404(group)
        if not request.user.has_perm('admin', group):
            return http.HttpResponseForbidden(
                "You don't have access to manage this group.")
    
        addform = self.member_form()
        url = reverse('group-details', args=[group.abbr])
        
        msg = ""
        errors = []
        if request.method == 'POST':
            addform = self.member_form(data=request.POST)
            if addform.is_valid():
                cd = addform.cleaned_data.copy()
                username = cd.pop('username')
                log.info("Modifying %s in group: %s" % (username, group))
                # List all the existing perms and check which ones need to be removed.
                existing_perms = set(api.permissions.list(user=username, group=group))
                perms = set([perm for perm, selected in cd.iteritems() if selected])
                revoke_perms = existing_perms.difference(perms)
                api.permissions.revoke(username, revoke_perms, group=group, 
                                       req_user=request.user)
                try:
                    api.permissions.grant(username, perms, group=group, 
                                          req_user=request.user)
                    msg = u"User: %s modified in group" % username
                except Exception:
                    msg = "Error changing member %s in group: %s" % (username, group)
                    log.exception(msg)
                    errors.append(msg)
                if not errors:
                    request.session['message'] = msg
                    return http.HttpResponseRedirect(url)
        context = {
           'title': 'Details for group: %s' % group,
           'group': group,
           'form': addform,
           'errors': errors,
           }
        return self.respond(request, self.mod_member_template, context)
