"""Module tiktalik.connection"""
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
import time
import hmac
import base64
import typing
from typing import Optional
from urllib import parse
import string
from hashlib import sha1, md5

import httpx
from httpx import Headers, Response

from .objects import Instance, VPSImage, BlockDevice, VPSNetInterface, Network
from .error import TiktalikAPIError


class TiktalikAuthConnection:
    def __init__(
        self,
        api_key: str,
        api_secret_key: str,
        host="tiktalik.com",
        port=443,
        use_ssl=True,
        http_proxy: Optional[str] = None,
        https_proxy: Optional[str] = None,
    ):
        self.api_key = api_key
        self.api_secret_key = api_secret_key
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = 20

        self.__base_url = "/api/v1/computing"

        self.proxy_mounts: dict[str, Optional[httpx.BaseTransport]] = {}

        if http_proxy:
            self.proxy_mounts["http://"] = httpx.HTTPTransport(proxy=http_proxy)
        if https_proxy:
            self.proxy_mounts["https://"] = httpx.HTTPTransport(proxy=https_proxy)

        # Backwards compatibility: secret_key is known as a base64 string, but it's used
        # internally as a binary decoded string. A long time ago this function took as input
        # a secret key decoded to binary string, so now try to handle both input
        # forms: deprecated decoded one and "normal" encoded as base64.
        try:
            if (
                len(
                    self.api_secret_key.lstrip(
                        string.ascii_letters + string.digits + "+/="
                    )
                )
                == 0
            ):
                self.api_secret_key = base64.standard_b64decode(self.api_secret_key)
        except TypeError:
            pass

    def __encode_param(self, value):
        if isinstance(value, list):
            return list(map(self.__encode_param, value))
        elif isinstance(value, str):
            return value.encode("utf8")

        return value

    def __request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, str | list[str] | int]] = None,
        query_params: Optional[dict[str, str | bool]] = None,
    ) -> typing.Any:
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

        response = self.__make_request(
            method, self.__base_url + path, params=params, query_params=query_params
        )

        data = response.text

        content_type_header = response.headers.get("Content-Type", "")
        assert isinstance(content_type_header, str), (
            "Failed to get Content-Type header!"
        )
        if content_type_header.startswith("application/json"):
            data = response.json()

        if response.status_code != httpx.codes.OK:
            raise TiktalikAPIError(response.status_code, data)

        return data

    def __make_request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, str | list[str] | int]] = None,
        query_params: Optional[dict[str, str | bool]] = None,
    ) -> Response:
        """
        If `params` is provided, it should be a dict that contains form parameters.
        Content-Type is forced to "application/x-www-form-urlencoded" in this case.
        """

        original_path = path
        path = parse.quote(path.encode("utf8"))

        if query_params:
            qp = {}
            for key, value in query_params.items():
                if isinstance(value, bool):
                    qp[key] = "true" if value else "false"
                else:
                    qp[key.encode("utf8")] = self.__encode_param(value)

            qp = parse.urlencode(qp, True)
            path = "%s?%s" % (path, qp)

        scheme: str = ""

        if self.use_ssl:
            scheme = "https"
        else:
            scheme = "http"

        url = scheme + "://" + self.host + ":" + str(self.port) + original_path

        with httpx.Client(
            verify=self.use_ssl, timeout=self.timeout, mounts=self.proxy_mounts
        ) as client:
            request = client.build_request(
                method, url, data=params, params=query_params
            )

            if params:
                body_checksum = md5(parse.urlencode(params, True).encode("utf-8"))
                request.headers["Content-MD5"] = body_checksum.hexdigest()

            request.headers = self.__add_auth_header(method, path, request.headers)
            response = client.send(request)
            return response

    def __add_auth_header(self, method: str, path: str, headers: Headers) -> Headers:
        if "date" not in headers:
            headers["date"] = time.strftime("%a, %d %b %Y %X GMT", time.gmtime())

        canonical_string = TiktalikAuthConnection.__canonical_string(
            method, path, headers
        )
        headers["Authorization"] = "TKAuth %s:%s" % (
            self.api_key,
            self.__sign_string(canonical_string),
        )

        return headers

    @staticmethod
    def __canonical_string(method: str, path: str, headers) -> str:
        return "\n".join(
            (
                method,
                headers.get("content-md5", ""),
                headers.get("content-type", ""),
                headers["date"],
                path,
            )
        )

    def __sign_string(self, canonical_string: str) -> str:
        digest = base64.b64encode(
            hmac.new(
                self.api_secret_key, canonical_string.encode("utf-8"), sha1
            ).digest()
        )
        return digest.decode("utf-8")

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

        response = self.__request(
            "GET",
            "/instance",
            query_params={"actions": actions, "vpsimage": vpsimage, "cost": cost},
        )

        return [Instance(self, i) for i in response]

    def list_networks(self):
        """
        List all available networks.

        :rtype: list
        :return: list of Network objects
        """

        response = self.__request("GET", "/network")
        return [Network(self, i) for i in response]

    def create_network(self, name: str):
        """
        Create a new network.

        A new instance will be created server-side, using the specified image,
        attaching networks resolved by UUID. This call returns immediately,
        the instance is created asynchronously.

        :type name: string
        :param name: Network name - as part of local domain. Max 15
                     characters length (will be truncated), allowed
                     characters are lower letters and digits. Must not
                     starts with a digit.

        :rtype: Network
        :return: Network object
        """

        params = dict(name=name)
        response = self.__request("POST", "/network", params)
        return Network(self, response)

    def list_images(self):
        """
        List all available VPS Images.

        :rtype: list
        :return: list of VPSImage objects
        """

        response = self.__request("GET", "/image")
        return [VPSImage(self, i) for i in response]

    def list_instance_interfaces(self, uuid: str):
        """
        List all interfaces attached to an Instance

        :type uuid: string
        :param uuid: Instance UUID

        :rtype: list
        :return: list of VPSNetInterface objects
        """

        response = self.__request("GET", "/instance/%s/interface" % uuid)
        return [VPSNetInterface(self, i) for i in response]

    def get_instance(self, uuid: str, actions=False, vpsimage=False, cost=False):
        """
        Fetch an Instance object from the server

        :type uuid: string
        :param uuid: Instance UUID

        :seealso: `list_instances`

        :rtype: Instance
        :return: an Instance object that represents the instance specified by UUID
        """

        response = self.__request(
            "GET",
            "/instance/" + uuid,
            query_params={"actions": actions, "vpsimage": vpsimage, "cost": cost},
        )
        return Instance(self, response)

    def get_instance_block_devices(self, uuid: str):
        """Fetch an Instances block devices from the server

        :type uuid: string
        :param uuid: Instance UUID

        :rtype: List[BlockDevice]
        """

        response = self.__request("GET", "/instance/" + uuid + "/blockdevice")
        return [BlockDevice(self, b) for b in response]

    def get_image(self, image_uuid: str):
        """
        Fetch a VPSImage object from the server

        :type image_uuid: string
        :param image_uuid: VPSImage UUID

        :rtype: VPSImage
        :return: a VPSImage object that represents the image specified by UUID
        """

        response = self.__request("GET", "/image/" + image_uuid)
        return VPSImage(self, response)

    def create_instance(
        self,
        hostname: str,
        size: str,
        image_uuid: str,
        networks: list[str],
        ssh_key: Optional[str] = None,
        disk_size_gb: Optional[int] = None,
    ):
        """
        Create a new instance.

        A new instance will be created server-side, using the specified image,
        attaching networks resolved by UUID. This call returns immediately,
        the instance is created asynchronously.

        :type hostname: string
        :param hostname: hostname that will be used for the new instance

        :type size: string
        :param size: instance size (or type); use 0.25, 0.5, 1 to 15 for PRO instances,
                     or one of "cpuhog", "cpuhog4" for PRO-cpuhog instances,
                     or one of "1s", "2s", "4s" for standard instances.

        :type image_uuid: string
        :param image_uuid: UUID of a VPSImage to be installed

        :type networks: list
        :param networks: list of network UUIDs to be attached to the new instance

        :type disk_size_gb: int
        :param disk_size_gb: for standard instances must set disk size in GB
        """

        params: dict[str, str | list[str] | int] = {
            "hostname": hostname,
            "size": size,
            "image_uuid": image_uuid,
            "networks[]": networks,
        }

        if ssh_key and ssh_key != "":
            params["ssh_key"] = ssh_key

        if disk_size_gb and isinstance(disk_size_gb, int):
            params["disk_size_gb"] = disk_size_gb

        return self.__request("POST", "/instance", params)

    def delete_instance(self, uuid: str):
        """
        Delete Tiktalik Instance specified by UUID.

        :type uuid: string
        :param uuid: UUID of the instance to be deleted
        """
        self.__request("DELETE", "/instance/%s" % uuid)

    def delete_image(self, uuid: str):
        """
        Delete a VPSImage specified by UUID.

        :type uuid: string
        :param uuid: UUID of the image to be deleted
        """

        self.__request("DELETE", "/image/%s" % uuid)

    def add_network_interface(self, instance_uuid: str, network_uuid: str, seq: int):
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

        self.__request(
            "POST",
            "/instance/%s/interface" % instance_uuid,
            dict(network_uuid=network_uuid, seq=seq),
        )

    def remove_network_interface(self, instance_uuid: str, interface_uuid: str):
        """
        Detach a network interface from an Instance.

        :type instance_uuid: string
        :param instance_uuid: UUID of the Instance

        :type interface_uuid: string
        :param interface_uuid: UUID of the Interface to be removed
        """

        self.__request(
            "DELETE", "/instance/%s/interface/%s" % (instance_uuid, interface_uuid)
        )

    def rename_image(self, uuid: str, name: str):
        """
        Rename an image.

        :type uuid: string
        :param uuid: UUID of the image


        :type name: string
        :param name: New name for the image
        """

        params = dict(image_name=name)

        self.__request(
            "POST",
            "/image/%s/set_name" % uuid,
            params,
        )
