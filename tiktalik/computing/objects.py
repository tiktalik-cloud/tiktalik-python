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

class Network(APIObject):
	"""
	A user- or system-owned network. Each Instance has zero or more networks
	attached, each networking interfaces is represented by a VPSNetInterface
	object.

	Attributes:
		uuid: string
		name: string,
		net: string
		owner: string,
		domainname: string,
		public: boolean

	"""

	def __str__(self):
		return "<Network:(%s): %s>" % (self.uuid, self.name)

	@classmethod
	def list_all(cls, conn):
		"""
		:seealso: ComputingConnection.list_networks()
		"""

		return conn.list_networks()

class VPSNetInterface(APIObject):
	"""
	A network interface attached to an Instance. Maps directly to a network interface
	visible from the operating system's point.

	Attributes:
		uuid: string
		network: Network,
		mac: string
		ip: string
		seq: int # interface sequence number: 0 for eth0, 1 for eth1, etc.
	"""

	def __init__(self, conn, json_dict):
		super(VPSNetInterface, self).__init__(conn, json_dict)

		self.network = Network(conn, self.network)

	def __str__(self):
		return "<VPSNetInterface:(%s) ip=%s>" % (self.uuid, self.ip)

class VPSImage(APIObject):
	"""
	Disk image that can be used to create a new instance, or restore one from backup.

	Attributes:
		uuid: string /* UID of this image */,
		name: string,
		owner: string,
		type: string = ['backup' or 'image' or 'install']
		is_public: boolean,
		description: string,
		create_time: Date
	"""

	def __str__(self):
		return "<VPSImage:(%s) %s>" % (self.uuid, self.name)

	@classmethod
	def list_all(cls, conn):
		"""
		:seealso: ComputingConnection.list_images()
		"""

		return conn.list_images()

	@classmethod
	def get(cls, conn, uuid):
		"""
		:seealso: ComputingConnection.get_image()
		"""

		return conn.get_image(uuid)

	def delete(self):
		"""
		:seealso: ComputingConnection.delete_image()
		"""

		self.conn.delete_image(self.uuid)

class Operation(APIObject):
	"""
	Description of an operation that was performed on an Instance.
	Used purely for informative purposes.
	"""

	def __str__(self):
		return "<Operation:(%s) start=%s, end=%s, %s>" % (self.uuid, self.start_time, self.end_time, self.description)

class Instance(APIObject):
	"""
	Represents a user's Instance. This object is used to perform mission-critical
	operations like stopping or starting an instance. Note that you should never
	construct this object yourself; use a ComputingConnection to fetch instances
	from the server.

	Attributes:
		uuid: string
		hostname: string,
		owner: string,
		vpsimage_uuid: string,
		state: int,
		running: boolean
		interfaces: List[VPSNetInterface]
		actions: List[Operation]
		vpsimage: VPSImage,
		default_password: string,
		service_name: string
		gross_cost_per_hour: float
	"""
	def __init__(self, conn, json_dict):
		defaults = {"actions":[], "vpsimage":None, "gross_cost_per_hour":None}

		super(Instance, self).__init__(conn, json_dict, defaults)

		self.interfaces = [VPSNetInterface(conn, i) for i in self.interfaces]
		self.actions = [Operation(conn, o) for o in self.actions]
		if self.vpsimage:
			self.vpsimage = VPSImage(conn, self.vpsimage)

	@classmethod
	def get_by_uuid(cls, conn, uuid, actions=False, vpsimage=False, cost=False):
		"""
		:seealso: ComputingConnection.get_instance()
		"""

		return conn.get_instance(uuid, actions, vpsimage, cost)

	@classmethod
	def get_by_hostname(cls, conn, hostname, actions=False, vpsimage=False, cost=False):
		"""
		Fetch a list of instances with matching hostname. Raise TiktalikAPIError when there is no match.

		:seealso: ComputingConnection.list_instances()

		:rtype: list
		:return: list of Instance objects
		"""

		hostname = hostname.lower()
		instances = [i for i in conn.list_instances(actions, vpsimage, cost) if i.hostname.lower() == hostname]
		if not instances:
			raise TiktalikAPIError(404)
		return instances

	@classmethod
	def list_all(cls, conn, actions=False, vpsimage=False, cost=False):
		"""
		:seealso: ComputingConnection.list_instances()
		"""

		return conn.list_instances(actions=actions, vpsimage=vpsimage, cost=cost)

	def start(self):
		"""
		Start the instance.
		"""

		self.conn.request("POST", "/instance/%s/start" % self.uuid)

	def stop(self):
		"""
		Perform a graceful shutdown of the instance. This is analogous
		to executing "shutdown".
		"""
		self.conn.request("POST", "/instance/%s/stop" % self.uuid)

	def force_stop(self):
		"""
		Perform a forced shutdown of the instance. This is analogous
		to pulling the electrical cord out of a machine.
		"""

		self.conn.request("POST", "/instance/%s/force_stop" % self.uuid)

	def backup(self):
		"""
		Start a backup operation. The instance must be stopped.
		"""
		self.conn.request("POST", "/instance/%s/backup" % self.uuid)

	def list_interfaces(self):
		"""
		Reload list of networks interfaces from the server.

		:rtype: list
		:return: list of VPSNetInterface objects
		"""

		self.interfaces = self.conn.list_instance_interfaces(self.uuid)
		return self.interfaces

	def add_interface(self, network_uuid, seq):
		"""
		:seealso: ComputingConnection.add_network_interface()
		"""

		self.conn.add_network_interface(self.uuid, network_uuid, seq)

	def remove_interface(self, seq):
		"""
		:seealso: ComputingConnection.remove_network_interface()
		"""
		raise NotImplementedError()

	def __str__(self):
		return "<Instance(%s): %s, state=%s, running=%s>" % (self.uuid, self.hostname, self.state, self.running)
