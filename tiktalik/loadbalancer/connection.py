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

from .http import *
from ..connection import TiktalikAuthConnection

class HTTPBalancerConnection(TiktalikAuthConnection):
	def base_url(self):
		return "/api/v1/loadbalancer"

	def list_httpbalancers(self, history=False):
		response = self.request("GET", "/http", query_params=dict(history=history))
		return [HTTPBalancer(self, i) for i in response]

	def get_httpbalancer(self, uuid):
		response = self.request("GET", "/http/%s" % uuid)
		return HTTPBalancer(self, response)

	def create_httpbalancer(self, name, domains=None, backends=None):
		"""
		backends: list of (ip, port, weight)
		"""
		response = self.request("POST", "/http",
			{ "name": name, "domains[]": domains, "backends[]": ["%s:%i:%i" % b for b in backends]})
		return HTTPBalancer(self, response)
