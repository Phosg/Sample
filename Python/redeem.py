import re, hashlib
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from ....apis.platform import auth

class RedeemCode(object):

    def __init__(self, request):
        """ NOTE: This set of views make a number of calls to 'auth',
            which is a proprietary, internal class that forwards
            requests to our platform services.  Calls will return a
            boolean or a dict as determined by that class. """

        self.request = request
        self.response = request.response
        self.response.messages = {}
        self.response.errors = {}
        self.settings = request.registry.settings

    @view_config(route_name='redeem.code',
                 renderer='pages/redeem/redeem.tpl',
                 http_cache=0)
    def redeem_code_index(self):
        """ The view loaded by the user at main page, returning
            status to vars used by the page """
        code = self.request.GET.get("code") or None

        if (code):
            code_parsed = re.sub(r'\W+', '', code)
            check = auth.call('redeem', code_parsed)
        else:
            return {'result': 'empty'}

        if (code_parsed and check):
            return {'result': 'valid', 'code': code_parsed}
        else:
            return {'result': 'invalid'}


    @view_config(route_name='user.redeem.code',
                 xhr=True,
                 renderer='json',
                 http_cache=0)
    def redeem_code(self):
        """ AJAX call to verify if reg code is valid """
        code = self.request.POST.get("code") or None
        check = auth.call('redeem', code)

        if (check):
            return {'status': 'success'}
        else:
            return {'status': 'failure'}

    @view_config(route_name='user.redeem.create',
                 xhr=True,
                 renderer='json',
                 http_cache=0)
    def create_account(self):
        """ AJAX call to create new account """
        code = self.request.POST.get("code") or None
        username = self.request.POST.get("username") or None
        email = self.request.POST.get("email") or None
        password = self.request.POST.get("password") or None
        language = self.request.POST.get("language").upper() or 'EN'
        newsletter = self.request.POST.get("newsletter") or False
        eula = self.request.POST.get("eula") or False
        ip = self.request.client_addr
        beta_create = None

        if (code and email and password):
            beta_create = auth.call('beta_create', code, username, email,
                                    password, language, newsletter, eula,
                                    ip)
        else:
            return {'status': 'failure', 'reason': 'incomplete'}
        
        if (beta_create['result'] == 'ok'):
            auth_data = str(beta_create['uid'])+"|"+\
                        str(beta_create['token']+"|0|0")
            headers = remember(self.request, auth_data)
            self.request.response.headerlist.extend(headers)
            return {'status': 'success'}
        else:
            return {'status': 'failure', 'reason': beta_create['message']}

    @view_config(route_name='user.redeem.merge',
                 xhr=True,
                 renderer='json',
                 http_cache=0)
    def merge_account(self):
        """ AJAX call to merge instead with a 3rd party token """
        access_token = self.request.POST.get("access_token") or None
        code = self.request.POST.get("code") or None
        token_type = 'internal'
        email = self.request.POST.get("email_address") or None
        password = self.request.POST.get("password") or None
        language = self.request.POST.get("language").upper() or 'EN'

        if (self.request.user and 'token' in self.request.user):
            token = self.request.user['token']
        else:
            token = self.request.POST.get("token") or None

        if (self.request.user and 'uid' in self.request.user):
            uid = int(self.request.user['uid'])
        else:
            uid = int(self.request.POST.get("uid")) or None

        if (access_token and token and uid and email):
            token_add = auth.call('token_add', access_token, token,
                                  token_type, uid, email, password[:16],
                                  language, code)
        else:
            return {'status': 'failure', 'reason': 'incomplete'}
        
        if (token_add):
            return {'status': 'success', 'username': token_add['message']}
        else:
            return {'status': 'failure', 'reason': 'server'}
