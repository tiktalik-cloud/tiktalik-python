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

from .error import TiktalikAPIError
from abc import ABC, abstractmethod


class TiktalikAuthConnection(ABC):
    """
    Simple wrapper for HTTPConnection. Adds authentication information to requests.
    """

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

    def _request(
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
            method, self._base_url() + path, params=params, query_params=query_params
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

    @abstractmethod
    def _base_url(self):
        pass

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
