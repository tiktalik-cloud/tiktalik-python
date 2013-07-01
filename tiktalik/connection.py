# Copyright (c) 2013 Techstorage sp. z o.o.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of 
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to 
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of 
# the Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# -*- coding: utf8 -*-

import time, httplib, hmac, base64, sha, urllib, md5, json, string
from .error import TiktalikAPIError

class TiktalikAuthConnection(object):
	"""
	Simple wrapper for HTTPConnection. Adds authentication information to requests.
	"""

	def __init__(self, api_key, api_secret_key, host="www.tiktalik.com", port=443,
			use_ssl=True):
		self.api_key = api_key
		self.api_secret_key = api_secret_key
		self.host = host
		self.port = port

		# backward compability: secret_key is known as a base64 string, but it's used
		# internally as a binary decoded string. A long time ago this function as input
		# needed secret key decoded to binary string, so now try to handle both input
		# forms: deprecated decoded one and "normal" encoded as base64.
		try:
			if len(self.api_secret_key.lstrip(string.letters + string.digits + '+/=')) == 0:
				self.api_secret_key = base64.standard_b64decode(self.api_secret_key)
		except TypeError:
			pass

		if use_ssl:
			self.conn_cls = httplib.HTTPSConnection
		else:
			self.conn_cls = httplib.HTTPConnection

		self.use_ssl = use_ssl

		self.timeout = 5
		self.conn = None

	def _encode_param(self, value):
		if isinstance(value, list):
			return map(self._encode_param, value)
		elif isinstance(value, basestring):
			return value.encode("utf8")

		return value


	def request(self, method, path, params=None, query_params=None):
		"""
		Send a request over HTTP. The inheriting class must override self.base_url().

		:type method: string
		:param method: HTTP method to use (GET, POST etc.)

		:type path: string
		:param path: path to be requested from server

		:type params: dict
		:param params: a dictionary of parameters sent in request body

		:type query_params: dict
		:param query_params: a dictionary of parameters sent in request path

		:rtype: dict, string or None
		:return: a JSON dict if the server replied with "application/json".
		         Raw data otherwise. None, if the reply was empty.
		"""

		response = self.make_request(method, self.base_url() + path, params=params, query_params=query_params)

		data = response.read()
		if response.getheader("Content-Type", "").startswith("application/json"):
			data = json.loads(data)

		if response.status != 200:
			raise TiktalikAPIError(response.status, data)

		return data

	def base_url(self):
		"""
		:rtype: string
		:return: base URL for API requests, eg. "/api/v1/computing". Must NOT include trailing slash.
		"""

		raise NotImplementedError()


	def make_request(self, method, path, headers=None, body=None, params=None, query_params=None):
		"""
		Sends request, returns httplib.HTTPResponse.

		If `params` is provided, it should be a dict that contains form parameters.
		Content-Type is forced to "application/x-www-form-urlencoded" in this case.
		"""

		if params and body:
			raise ValueError("Both `body` and `params` can't be provided.")

		headers = headers or {}

		if params:
			params = dict((k.encode("utf8"), self._encode_param(v)) for (k, v) in params.iteritems())
			body = urllib.urlencode(params, True)
			headers["content-type"] = "application/x-www-form-urlencoded"

		path = urllib.quote(path.encode("utf8"))

		if query_params:
			qp = {}
			for key, value in query_params.iteritems():
				if isinstance(value, bool):
					qp[key] = "true" if value else "false"
				else:
					#assert isinstance(value, (str, int))
					qp[key.encode("utf8")] = self._encode_param(value)

			qp = urllib.urlencode(qp, True)
			path = "%s?%s" % (path, qp)

		if body:
			m = md5.new(body)
			headers["content-md5"] = m.hexdigest()

		conn = self.conn_cls(self.host, self.port, timeout=self.timeout)
		# XXX: lowercase headers?
		headers = self._add_auth_header(method, path, headers or {})
		# conn.set_debuglevel(3)
		conn.request(method, path, body, headers)

		response = conn.getresponse()
		return response

	def _add_auth_header(self, method, path, headers):
		if "date" not in headers:
			headers["date"] = time.strftime("%a, %d %b %Y %X GMT", time.gmtime())

		S = self._canonical_string(method, path, headers)
		headers["Authorization"] = "TKAuth %s:%s" % (self.api_key, self._sign_string(S))

		return headers

	def _canonical_string(self, method, path, headers):
		S = "\n".join((method, headers.get("content-md5", ""),
			headers.get("content-type", ""), headers["date"], path))
		return S

	def _sign_string(self, S):
		digest = base64.b64encode(hmac.new(self.api_secret_key, S, sha).digest())
		return digest
