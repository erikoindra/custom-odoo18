# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import time
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Rate limiting settings
RATE_LIMIT = {}
RATE_LIMIT_INTERVAL = 60  # Time interval window (seconds)
RATE_LIMIT_MAX_REQUESTS = 5  # Maximum requests per interval

headers = [('Content-Type', 'application/json')]

class RestApi(http.Controller):
    """
        This is a controller which is used to generate responses based on the
        api requests
    """

    def _check_rate_limit(self, api_key):
        """ Check if the API key has exceeded the rate limit """
        current_time = time.time()

        if api_key in RATE_LIMIT:
            requests, first_request_time = RATE_LIMIT[api_key]

            if current_time - first_request_time < RATE_LIMIT_INTERVAL:
                if requests >= RATE_LIMIT_MAX_REQUESTS:
                    return False  # Rate limit exceeded
                RATE_LIMIT[api_key] = (requests + 1, first_request_time)
            else:
                RATE_LIMIT[api_key] = (1, current_time)  # Reset rate limit window
        else:
            RATE_LIMIT[api_key] = (1, current_time)

        return True

    def auth_api_key(self, api_key):
        """This function is used to authenticate the api-key when sending a
        request"""
        user_id = request.env['res.users'].sudo().search([('api_key', '=', api_key)])
        if api_key is not None and user_id:
            response = True
        elif not user_id:
            error = json.dumps({'error': 'Invalid API Key.'})
            return request.make_response(data=error, status=403, headers=headers)
        else:
            error = json.dumps({'error': 'No API Key Provided.'})
            return request.make_response(data=error, status=403, headers=headers)
        return response

    def generate_response(self, method, model, rec_id):
        """This function is used to generate the response based on the type
        of request and the parameters given"""
        option = request.env['connection.api'].search(
            [('model_id', '=', model)], limit=1)
        model_name = option.model_id.model
        if method != 'DELETE':
            data = json.loads(request.httprequest.data)
        else:
            data = {}
        fields = []
        if data:
            for field in data['fields']:
                fields.append(field)
        if not fields and method != 'DELETE':
            error = json.dumps({'error': 'No fields selected for the model.'})
            return request.make_response(data=error, status=403, headers=headers)
        if not option:
            error = json.dumps({'error': 'No Record Created for the model.'})
            return request.make_response(data=error, status=403, headers=headers)
        try:
            if method == 'GET':
                fields = []
                for field in data['fields']:
                    fields.append(field)
                if not option.is_get:
                    error = json.dumps({'error': 'Method Not Allowed.'})
                    return request.make_response(data=error, status=403, headers=headers)
                else:
                    datas = []
                    if rec_id != 0:
                        partner_records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', rec_id)],
                            fields=fields
                        )
                        data = json.dumps({
                            'records': partner_records
                        })
                        datas.append(data)
                        return request.make_response(data=datas, headers=headers)
                    else:
                        partner_records = request.env[
                            str(model_name)].search_read(
                            domain=[],
                            fields=fields
                        )
                        data = json.dumps({
                            'records': partner_records
                        })
                        datas.append(data)
                        return request.make_response(data=datas, headers=headers)
        except:
            error = json.dumps({'error': 'Invalid JSON Data.'})
            return request.make_response(data=error, status=403, headers=headers)
        if method == 'POST':
            if not option.is_post:
                error = json.dumps({'error': 'Method Not Allowed.'})
                return request.make_response(data=error, status=403, headers=headers)
            else:
                try:
                    data = json.loads(request.httprequest.data)
                    datas = []
                    new_resource = request.env[str(model_name)].create(
                        data['values'])
                    partner_records = request.env[
                        str(model_name)].search_read(
                        domain=[('id', '=', new_resource.id)],
                        fields=fields
                    )
                    new_data = json.dumps({'New resource': partner_records, })
                    datas.append(new_data)
                    return request.make_response(data=datas, headers=headers)
                except:
                    error = json.dumps({'error': 'Invalid JSON Data.'})
                    return request.make_response(data=error, status=403, headers=headers)
        if method == 'PUT':
            if not option.is_put:
                error = json.dumps({'error': 'Method Not Allowed.'})
                return request.make_response(data=error, status=403, headers=headers)
            else:
                if rec_id == 0:
                    error = json.dumps({'error': 'No ID Provided.'})
                    return request.make_response(data=error, status=403, headers=headers)
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        error = json.dumps({'error': 'Resource not found.'})
                        return request.make_response(data=error, status=403, headers=headers)
                    else:
                        try:
                            datas = []
                            data = json.loads(request.httprequest.data)
                            resource.write(data['values'])
                            partner_records = request.env[
                                str(model_name)].search_read(
                                domain=[('id', '=', resource.id)],
                                fields=fields
                            )
                            new_data = json.dumps(
                                {
                                    'Updated resource': partner_records,
                                }
                            )
                            datas.append(new_data)
                            return request.make_response(data=datas, headers=headers)

                        except:
                            error = json.dumps({'error': 'Invalid JSON Data.'})
                            return request.make_response(data=error, status=403, headers=headers)
        if method == 'DELETE':
            if not option.is_delete:
                error = json.dumps({'error': 'Method Not Allowed.'})
                return request.make_response(data=error, status=403, headers=headers)
            else:
                if rec_id == 0:
                    error = json.dumps({'error': 'No ID Provided.'})
                    return request.make_response(data=error, status=403, headers=headers)
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        error = json.dumps({'error': 'Resource not found.'})
                        return request.make_response(data=error, status=403, headers=headers)
                    else:

                        records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', resource.id)],
                            fields=['id', 'display_name']
                        )
                        remove = json.dumps(
                            {
                                "Resource deleted": records,
                            }
                        )
                        resource.unlink()
                        return request.make_response(data=remove, headers=headers)

    @http.route(['/send_request'], type='http',
                auth='none',
                methods=['GET', 'POST', 'PUT', 'DELETE'], csrf=False)
    def fetch_data(self, **kw):
        """This controller will be called when sending a request to the
        specified url, and it will authenticate the api-key and then will
        generate the result"""
        http_method = request.httprequest.method
        api_key = request.httprequest.headers.get('api-key')
        auth_api = self.auth_api_key(api_key)
        if not self._check_rate_limit(api_key):
            limit = json.dumps({'error': 'Rate limit exceeded.'})
            return request.make_response(data=limit, status=429, headers=headers)
        model = kw.get('model')
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        credential = {'login': username, 'password': password, 'type': 'password'}
        request.session.authenticate(request.session.db, credential)
        model_id = request.env['ir.model'].search(
            [('model', '=', model)])
        if not model_id:
            error = json.dumps({'error': 'Invalid model, check spelling or maybe the related module is not installed.'})
            return request.make_response(data=error, status=403, headers=headers)

        if auth_api == True:
            if not kw.get('Id'):
                rec_id = 0
            else:
                rec_id = int(kw.get('Id'))
            result = self.generate_response(http_method, model_id.id, rec_id)
            return result
        else:
            return auth_api

    @http.route(['/odoo_connect'], type="http", auth="none", csrf=False,
                methods=['GET'])
    def odoo_connect(self, **kw):
        """This is the controller which initializes the api transaction by
        generating the api-key for specific user and database"""
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        db = request.httprequest.headers.get('db')
        try:
            request.session.update(http.get_default_session(), db=db)
            credential = {
                'login': username, 
                'password': password,
                'type': 'password'
            }

            auth = request.session.authenticate(db, credential)
            user = request.env['res.users'].browse(auth['uid'])
            api_key = request.env.user.generate_api(username)
            datas = json.dumps({"Status": "auth successful",
                                "User": user.name,
                                "api-key": api_key})
            return request.make_response(data=datas, headers=headers)
        except:
            error = json.dumps({'error': 'Wrong Login Credentials.'})
            return request.make_response(data=error, status=403, headers=headers)
