# -*- coding: utf8 -*-

import time, httplib, hmac, base64, sha, urllib, md5

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

		if use_ssl:
			self.conn_cls = httplib.HTTPSConnection
		else:
			self.conn_cls = httplib.HTTPConnection

		self.use_ssl = use_ssl

		self.timeout = 5
		self.conn = None

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
			body = urllib.urlencode(params, True)
			headers["content-type"] = "application/x-www-form-urlencoded"

		if query_params:
			qp = {}
			for key, value in query_params.iteritems():
				if isinstance(value, bool):
					qp[key] = "true" if value else "false"
				else:
					#assert isinstance(value, (str, int))
					qp[key] = value

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
