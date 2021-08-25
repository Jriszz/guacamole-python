from __future__ import print_function

__author__ = 'ght'

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

# ---------------------------------
# Client

from twisted.application import reactors

reactors.installReactor('qt4')

#reactors.installReactor('kqueue')

from twisted.python import log

import sys

log.startLogging(sys.stdout)

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor


# noinspection PyClassHasNoInit
class EchoClientDatagramProtocol(DatagramProtocol):
    long_string = "-" * 1000

    def __init__(self):
        self.sendflag = True

    def stop_sending(self):
        self.sendflag = False

    def startProtocol(self):
        #log.msg("client start protocol")
        self.transport.connect('127.0.0.1', self.useport)
        self.senddatagram()

    def senddatagram(self):
        #log.msg("client send datagram")
        datagram = self.long_string
        self.transport.write(datagram)

    def datagramReceived(self, datagram, host):
        #log.msg("client datagram received")
        #log.msg('Datagram received: ', repr(datagram))
        if self.sendflag:
            reactor.callLater(0.001, self.senddatagram)


def build_client(port):
    protocol = EchoClientDatagramProtocol()
    protocol.useport = port
    reactor.listenUDP(0, protocol)
    return protocol


#------------------------------------------
# Server


# noinspection PyClassHasNoInit
class EchoUDP(DatagramProtocol):
    def datagramReceived(self, datagram, address):
        #log.msg("server received: ", repr(datagram), repr(address))
        self.transport.write(datagram, address)

def trap_me():
    log.msg("trapped")

begin_port = 5010

def main():
    for port in xrange(begin_port, begin_port + 50):
        reactor.listenUDP(port, EchoUDP())
        protocol = build_client(port)
        reactor.callLater(12.0, protocol.stop_sending)

    reactor.callLater(10, trap_me)
    reactor.callLater(15, reactor.stop)
    reactor.run()


if __name__ == '__main__':
    main()