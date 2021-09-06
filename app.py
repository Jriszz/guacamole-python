import gevent
import time
import sqlite3
from geventwebsocket import WebSocketApplication

from guacamole.client import GuacamoleClient, PROTOCOL_NAME


class GuacamoleApp(WebSocketApplication):

    def __init__(self, ws):
        self.client = None
        self._listener = None

        super(GuacamoleApp, self).__init__(ws)

    @classmethod
    def protocol_name(cls):
        """
        Return our protocol.
        """
        return PROTOCOL_NAME

    def on_open(self, *args, **kwargs):
        """
        New Web socket connection opened.
        """
        if self.client:
            # we have a running client?!
            self.client.close()

        # @TODO: get guacd host and port!
        self.client = GuacamoleClient('192.168.0.110', 8081)

        conn = sqlite3.connect("..\\..\\test.db")
        cursor = conn.cursor()
        sql = "select * from machine_info"
        table_data = cursor.execute(sql)
        data_tuple = table_data.fetchone()
        # c = __import__('local_settings')
        # @TODO: get Remote server connection properties
        self.client.handshake(protocol='rdp', hostname=data_tuple[0],
                              port=3389, username=data_tuple[1],
                              password=data_tuple[2], domain='',
                              security='', remote_app='', height=924, width=1684, disable_glyph_caching="true")

        self._start_listener()

    def on_message(self, message):
        """
        New message received on the websocket.
        """
        # send message to guacd server
        if message:
            self.client.send(message)

    def on_close(self, reason):
        """
        Websocket closed.
        """
        # @todo: consider reconnect from client. (network glitch?!)
        self._stop_listener()
        self.client.close()
        self.client = None

    def _start_listener(self):
        if self._listener:
            self._stop_listener()
        self._listener = gevent.spawn(self.guacd_listener)
        self._listener.start()

    def _stop_listener(self):
        if self._listener:
            self._listener.kill()
            self._listener = None

    def guacd_listener(self):
        """
        A listener that would handle any messages sent from Guacamole server
        and push directly to browser client (over websocket).
        """
        while True:
            instruction = self.client.receive()
            self.ws.send(instruction)
