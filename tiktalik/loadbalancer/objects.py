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

__all__ = ["LoadBalancer", "LoadBalancerBackend", "LoadBalancerAction"]

class LoadBalancer(APIObject):
	"""A LoadBalancer instance. Contains a list of domains and backends,
	and optionally a history of operations performed on this instance.

	Gives access to all API calls that operate on the Tiktalik LoadBalancer service.
	"""

	def __init__(self, conn, json_dict):
		super(LoadBalancer, self).__init__(conn, json_dict)

		self.backends = [LoadBalancerBackend(conn, i) for i in self.backends]
		self.monitor = LoadBalancerBackendMonitor(conn, self.monitor)
		self.history = [LoadBalancerAction(conn, i) for i in self.history] if self.history else []

	def __str__(self):
		return "<LoadBalancer:(%s) %s>" % (self.uuid, self.name)

	@classmethod
	def list_all(cls, conn, history=False):
		"""
		:seealso: ComputingConnection.list_loadbalancers()
		"""

		return conn.list_loadbalancers(history=history)

	@classmethod
	def create(cls, conn, *args, **kwargs):
		"""
		:seealso: ComputingConnection.create_loadbalancer()
		"""

		return conn.create_loadbalancer(*args, **kwargs)

	@classmethod
	def get(cls, conn, uuid):
		"""
		:seealso: ComputingConnection.get_loadbalancer()
		"""

		return conn.get_loadbalancer(uuid)

	def enable(self):
		"""
		Enable this LoadBalancer.
		"""

		return self.conn.request("POST", "/%s/enable" % self.uuid)

	def disable(self):
		"""
		Disable this LoadBalancer. Its configuration is left intact, this
		operation only stops serving user requests.
		"""

		return self.conn.request("POST", "/%s/disable" % self.uuid)

	def rename(self, name):
		"""
		Rename the LoadBalancer.

		:type name: string
		:param name: new name
		"""

		return self.conn.request("PUT", "/%s/name" % self.uuid,
			{"name": name})

	def delete(self):
		return self.conn.request("DELETE", "/%s" % self.uuid)

	def set_domains(self, domains):
		return self.conn.request("POST", "/%s/domain" % self.uuid,
			{"domains[]": domains})
	
	def add_domain(self, domain):
		return self.conn.request("PUT", "/%s/domain" % self.uuid,
			{"domain": domain})

	def remove_domain(self, domain):
		return self.conn.request("DELETE", "/%s/domain/%s" % (self.uuid, domain))

	def set_backends(self, backends):
		"""
		backends: list of (ip, port, weight)
		"""

		return self.conn.request("POST", "/%s/backend" % self.uuid,
			{"backends[]": ["%s:%i:%i" % b for b in backends]})

	def add_backend(self, ip, port, weight):
		return self.conn.request("PUT", "/%s/backend" % self.uuid,
			{"backend": "%s:%i:%i" % (ip, port, weight)})

	def remove_backend(self, backend_uuid):
		return self.conn.request("DELETE", "/%s/backend/%s" % (self.uuid, backend_uuid))

	def modify_backend(self, backend_uuid, ip=None, port=None, weight=None):
		params = {}
		if ip is not None: params["ip"] = ip
		if port is not None: params["port"] = port
		if weight is not None: params["weight"] = weight

		return self.conn.request("PUT", "/%s/backend/%s" % (self.uuid, backend_uuid), params)


class LoadBalancerBackend(APIObject):
	pass


class LoadBalancerAction(APIObject):
	pass

class LoadBalancerBackendMonitor(APIObject):
	pass
