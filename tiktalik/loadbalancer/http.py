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

from ..error import TiktalikAPIError
from ..apiobject import APIObject

__all__ = ["HTTPBalancer", "HTTPBalancerBackend", "HTTPBalancerAction"]

class HTTPBalancer(APIObject):
	"""A HTTPBalancer instance. Contains a list of domains and backends,
	and optionally a history of operations performed on this instance.

	Gives access to all API calls that operate on the Tiktalik HTTPBalancer service.
	"""

	def __init__(self, conn, json_dict):
		super(HTTPBalancer, self).__init__(conn, json_dict)

		self.backends = [HTTPBalancerBackend(conn, i) for i in self.backends]
		self.history = [HTTPBalancerAction(conn, i) for i in self.history] if self.history else []

	def __str__(self):
		return "<HTTPBalancer:(%s) %s" % (self.uuid, self.name)

	@classmethod
	def list_all(cls, conn, history=False):
		"""
		:seealso: ComputingConnection.list_httpbalancers()
		"""

		return conn.list_httpbalancers(history=history)

	@classmethod
	def create(cls, conn, name, domains=None, backends=None):
		"""
		:seealso: ComputingConnection.create_httpbalancer()
		"""

		return conn.create_httpbalancer(name, domains, backends)

	@classmethod
	def get(cls, conn, uuid):
		"""
		:seealso: ComputingConnection.get_httpbalancer()
		"""

		return conn.get_httpbalancer(uuid)

	def enable(self):
		"""
		Enable this HTTPBalancer.
		"""

		return self.conn.request("POST", "/http/%s/enable" % self.uuid)

	def disable(self):
		"""
		Disable this HTTPBalancer. Its configuration is left intact, this
		operation only stops serving user requests.
		"""

		return self.conn.request("POST", "/http/%s/disable" % self.uuid)

	def rename(self, name):
		"""
		Rename the HTTPBalancer.

		:type name: string
		:param name: new name
		"""

		return self.conn.request("PUT", "/http/%s/name" % self.uuid,
			{"name": name})

	def delete(self):
		return self.conn.request("DELETE", "/http/%s" % self.uuid)

	def set_domains(self, domains):
		return self.conn.request("POST", "/http/%s/domain" % self.uuid,
			{"domains[]": domains})
	
	def add_domain(self, domain):
		return self.conn.request("PUT", "/http/%s/domain" % self.uuid,
			{"domain": domain})

	def remove_domain(self, domain):
		return self.conn.request("DELETE", "/http/%s/domain/%s" % (self.uuid, domain))

	def set_backends(self, backends):
		"""
		backends: list of (ip, port, weight)
		"""

		return self.conn.request("POST", "/http/%s/backend" % self.uuid,
			{"backends[]": ["%s:%i:%i" % b for b in backends]})

	def add_backend(self, ip, port, weight):
		return self.conn.request("PUT", "/http/%s/backend" % self.uuid,
			{"backend": "%s:%i:%i" % (ip, port, weight)})

	def remove_backend(self, backend_uuid):
		return self.conn.request("DELETE", "/http/%s/backend/%s" % (self.uuid, backend_uuid))

	def modify_backend(self, backend_uuid, ip=None, port=None, weight=None):
		params = {}
		if ip is not None: params["ip"] = ip
		if port is not None: params["port"] = port
		if weight is not None: params["weight"] = weight

		return self.conn.request("PUT", "/http/%s/backend/%s" % (self.uuid, backend_uuid), params)


class HTTPBalancerBackend(APIObject):
	pass


class HTTPBalancerAction(APIObject):
	pass
