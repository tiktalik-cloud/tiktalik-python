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

import json

from .objects import *
from ..error import TiktalikAPIError
from ..connection import TiktalikAuthConnection

class ComputingConnection(TiktalikAuthConnection):
	"""
	Performs API calls. All method raise TiktalikAPIError on errors.
	"""

	def base_url(self):
		return "/api/v1/computing"

	def list_instances(self, actions=False, vpsimage=False, cost=False):
		"""
		List all instances.

		:type actions: boolean
		:param actions: include recent actions in each Instance

		:type vpsimage: boolean
		:param vpsimage: include VPS Image details in each Instance

		:type cost: boolean
		:param cost: include cost per hour in each Instance

		:rtype: list
		:return: list of Instance objects
		"""

		response = self.request("GET", "/instance",
				query_params={"actions": actions, "vpsimage": vpsimage, "cost": cost})

		return [Instance(self, i) for i in response]

	def list_networks(self):
		"""
		List all available networks.

		:rtype: list
		:return: list of Network objects
		"""

		response = self.request("GET", "/network")
		return [Network(self, i) for i in response]

	def list_images(self):
		"""
		List all available VPS Images.

		:rtype: list
		:return: list of VPSImage objects
		"""

		response = self.request("GET", "/image")
		return [VPSImage(self, i) for i in response]

	def list_instance_interfaces(self, uuid):
		"""
		List all interfaces attached to an Instance

		:type uuid: string
		:param uuid: Instance UUID

		:rtype: list
		:return: list of VPSNetInterface objects
		"""

		response = self.request("GET", "/instance/%s/interface" % uuid)
		return [VPSNetInterface(self, i) for i in response]

	def get_instance(self, uuid, actions=False, vpsimage=False, cost=False):
		"""
		Fetch an Instance object from the server

		:type uuid: string
		:param uuid: Instance UUID

		:seealso: `list_instances`

		:rtype: Instance
		:return: an Instance object that represents the instance specified by UUID
		"""

		response = self.request("GET", "/instance/" + uuid,
				query_params={"actions": actions, "vpsimage": vpsimage, "cost": cost})
		return Instance(self, response)

	def get_image(self, image_uuid):
		"""
		Fetch a VPSImage object from the server

		:type image_uuid: string
		:param image_uuid: VPSImage UUID

		:rtype: VPSImage
		:return: a VPSImage object that represents the image specified by UUID
		"""

		response = self.request("GET", "/image/" + image_uuid)
		return VPSImage(self, response)

	def create_instance(self, hostname, size, image_uuid, networks, ssh_key = None):
		"""
		Create a new instance.

		A new instance will be created server-side, using the specified image,
		attaching networks resolved by UUID. This call returns immediately,
		the instance is created asynchronously.

		:type hostname: string
		:param hostname: hostname that will be used for the new instance

		:type size: string
		:param size: instance size; use 0.25, 0.5, 1 to 15, or one of: "cpuhog", "cpuhog4"

		:type image_uuid: string
		:param image_uuid: UUID of a VPSImage to be installed

		:type networks: list
		:param networks: list of network UUIDs to be attached to the new instance
		"""

		params = dict(hostname=hostname, size=size, image_uuid=image_uuid)
		params["networks[]"] = networks

		if ssh_key and ssh_key != '':
			params["ssh_key"] = ssh_key

		return self.request("POST", "/instance", params)

	def delete_instance(self, uuid):
		"""
		Delete Tiktalik Instance specified by UUID.

		:type uuid: string
		:param uuid: UUID of the instance to be deleted
		"""
		self.request("DELETE", "/instance/%s" % uuid)


	def delete_image(self, uuid):
		"""
		Delete a VPSImage specified by UUID.

		:type uuid: string
		:param uuid: UUID of the image to be deleted
		"""

		self.request("DELETE", "/image/%s" % uuid)

	def add_network_interface(self, instance_uuid, network_uuid, seq):
		"""
		Attach a new network interface to an Instance. The Instance doesn't
		have to be stopped to perform this action. This action is performed
		asynchronously.

		:type instance_uuid: string
		:param instance_uuid: UUID of the Instance

		:type network_uuid: string
		:param network_uuid: UUID of the Network to be attached

		:type seq: int
		:param seq: sequential number of the interface that will obtain an
		            address belonging to the Network. This will be reflected
		            by the operating system's configuration, eg. "3" maps to "eth3"
		"""

		self.request("POST", "/instance/%s/interface" % instance_uuid,
			dict(network_uuid=network_uuid, seq=seq))

