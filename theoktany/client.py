"""OKTA API Client"""
from datetime import datetime

import requests

from theoktany.conf import settings
from theoktany.exceptions import ApiException
from theoktany.serializers import deserialize

__all__ = ['ApiClient', ]


class ApiClient(object):
    """Client for making requests to OKTA API.
    When creating an ApiClient, you can pass any settings that you wish to override from the defaults. See the settings
    documentation for more information."""

    def __init__(self, **kwargs):
        self.settings = settings

        # any values passed in kwargs will be a setting
        for key, value in kwargs.items():
            self.settings.set(key, value)

    @property
    def _headers(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'SSWS ' + self.settings.get('API_TOKEN'),
        }

    @property
    def _base_url(self):
        return self.settings.get('BASE_URL')

    @staticmethod
    def _process_response(response):
        """Do things with the response from requests"""
        if response is None:
            return None, None
        response_dict = deserialize(response.content)
        return response_dict, response.status_code

    def get(self, path, params=None):
        try:
            response = requests.get(
                self._base_url+path, params=params, headers=self._headers,
                timeout=self.settings.get('REQUEST_CONNECTION_TIMEOUT'))
        except requests.ConnectionError:
            response = None
        return self._process_response(response)

    def post(self, path, data=None):
        try:
            response = requests.post(
                self._base_url+path, data=data, headers=self._headers,
                timeout=self.settings.get('REQUEST_CONNECTION_TIMEOUT'))
        except requests.ConnectionError:
            response = None
        return self._process_response(response)

    def delete(self, path, params=None):
        try:
            response = requests.delete(
                self._base_url+path, params=params, headers=self._headers,
                timeout=self.settings.get('REQUEST_CONNECTION_TIMEOUT'))
        except requests.ConnectionError:
            response = None
        return self._process_response(response)

    def check_status(self):
        route = '/api/v1/users?limit=1'
        response = requests.get(self._base_url + route, headers=self._headers)

        # noinspection PyShadowingNames
        def _format_response(is_available, calls_remaining, reset_time):
            return {
                'okta': {
                    'is_available': is_available,
                    'calls_remaining': int(calls_remaining),
                    'time_of_reset': datetime.utcfromtimestamp(int(reset_time)),
                }
            }

        is_available = response.status_code == 200
        calls_remaining = response.headers.get('X-Rate-Limit-Remaining', 0)
        reset_time = response.headers.get('X-Rate-Limit-Reset', 0)
        return _format_response(is_available, calls_remaining, reset_time)

    @staticmethod
    def check_api_response(response, status_code, acceptable_status_codes=None):
        if acceptable_status_codes is None:
            acceptable_status_codes = [200, ]

        if status_code not in acceptable_status_codes:
            if 'errorCauses' in response:
                if response['errorCauses']:
                    msg = response['errorCauses'][0]['errorSummary']
                else:
                    msg = response['errorSummary']
            else:
                msg = 'Okta returned {}.'.format(status_code)
            raise ApiException(msg)
