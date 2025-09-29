"""Module tiktalik.loadbalancer.connection"""

from typing import Literal, Optional

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

from .objects import LoadBalancer
from ..connection import TiktalikAuthConnection


class LoadBalancerConnection(TiktalikAuthConnection):
    def _base_url(self):
        return "/api/v1/loadbalancer"

    def list_loadbalancers(self, history=False):
        response = self._request("GET", "", query_params=dict(history=history))
        return [LoadBalancer(self, i) for i in response]

    def get_loadbalancer(self, uuid: str):
        response = self._request("GET", "/%s" % uuid)
        return LoadBalancer(self, response)

    def create_loadbalancer(
        self,
        name: str,
        proto: Literal["TCP"] | Literal["HTTP"] | Literal["HTTPS"],
        address: Optional[str] = None,
        port: Optional[int] = None,
        backends: Optional[list[tuple[str, int, int]]] = None,
        domains: Optional[list[str]] = None,
    ):
        """
        Create new load balancer instance

        :type name: string
        :param name:

        :type proto: string
        :param proto: load balancing protocol, one of 'TCP', 'HTTP' or 'HTTPS'

        :type address: string
        :param address: optional entry point to use, if None then new entry point will be created

        :type port: int
        :param port: listen port, only for TCP proto balancing

        :type backends: list
        :param backends: list of (ip, port, weight) tuples

        :type domains: list
        :param domains: list of domains, only for HTTP proto balancing
        """

        params: dict[str, str | int | list[str]] = {
            "name": name,
            "type": proto,
        }
        if isinstance(backends, list):
            params["backends[]"] = ["%s:%i:%i" % b for b in backends]
        else:
            params["backends[]"] = []
        if address:
            params["address"] = address
        if port:
            params["port"] = port
        if domains:
            params["domains[]"] = domains

        response = self._request("POST", "", params)
        return LoadBalancer(self, response)
