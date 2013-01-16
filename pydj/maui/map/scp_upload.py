#!/usr/bin/env python
#
# pylibssh2 - python bindings for libssh2 library
#
# Copyright (C) 2010 Wallix Inc.
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
import socket, sys

import libssh2

usage = """Do a SCP send <file> with username@hostname:/remote_path/
Usage: scp.py <hostname> <username> <password> <file>"""

class MySCPClient:
    def __init__(self, hostname, username, password, port=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self._prepare_sock()

    def _prepare_sock(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.hostname, self.port))
            self.sock.setblocking(1)
        except Exception, e:
            print "SockError: Can't connect socket to %s:%d" % (self.hostname, self.port)
            print e

        try:
            self.session = libssh2.Session()
            self.session.set_banner()
            self.session.startup(self.sock)
            self.session.userauth_password(self.username, self.password)
        except Exception, e:
            print "SSHError: Can't startup session"
            print e

    def send(self,datas, remote_path, mode=0644):
        file_size = len(datas)
        try:
          channel = self.session.scp_send(remote_path, mode, file_size)
          channel.write(datas)
          channel.close()
        except Exception, e:
            print "SSHError: Can't startup session"
            print e

    def recv(self,remote_path):
			try:
				channel = self.session.scp_recv(remote_path)
				#TODO all data read once, hangs with buffer
				data = channel.read()
				channel.close()
				return data	
			except Exception, e:
				print "SSHError: REceive"
				print e

    def __del__(self):
        self.session.close()
        self.sock.close()

