import asyncio

from collections import OrderedDict


class ClientServerProtocol(asyncio.Protocol):
    storage = OrderedDict()

    def connection_made(self, transport) -> None:
        self.transport = transport

    def data_received(self, data: bytes):
        request = data.decode()
        message = request.split()
        self.send_response(message)

    def send_response(self, message):
        if len(message) < 2:
            self.send_error()
            return None

        if message[0] == 'get':
            if 1 < len(message) <= 2:
                self._do_get(message[1])
            else:
                self.send_error()
        elif message[0] == 'put':
            if len(message) != 4:
                self.send_error()
                return

            self._do_put(message[1], message[2], message[3])
        else:
            self.send_error()

    def _do_get(self, metric_name: str):
        """Get value of metric by name

        :param metric_name:
            Used to request metric value, can accept '*'
        :type
            metric_name: str
        :return:
            sting with values of metrics
        """
        response = 'ok\n'
        if metric_name == '*':
            response += self._get_all()
        else:
            if metric_name in self.storage.keys():
                for metrics in self.storage[metric_name]:
                    response += f'{metric_name} {metrics[1]} {metrics[0]}\n'

        response += '\n'
        self.transport.write(response.encode())

    def _get_all(self):
        response = ''
        for metric_name in self.storage.keys():
            for metrics in self.storage[metric_name]:
                response += f'{metric_name} {metrics[1]} {metrics[0]}\n'
        return response

    def _do_put(self, metric_name, metric_value, metric_timestamp):
        try:
            metric_timestamp, metric_value = int(metric_timestamp), float(metric_value)
            if metric_name != '*':
                if metric_name not in self.storage.keys():
                    self.storage[metric_name] = list()

                if (metric_timestamp, metric_value,) not in self.storage[metric_name]:
                    for item in self.storage[metric_name]:
                        if item[0] == metric_timestamp:
                            self.storage[metric_name].remove(item)
                    self.storage[metric_name].append((metric_timestamp, metric_value))
                    self.storage[metric_name].sort(key=lambda metric_tuple: metric_tuple[0])

                self.transport.write(b'ok\n\n')
            else:
                self.send_error()
        except ValueError as err:
            self.send_error()

    def send_error(self):
        self.transport.write(b'error\nwrong command\n\n')


def run_server(host: str, port: int):
    loop = asyncio.get_event_loop()
    # Each client connection will create a new protocol instance
    coro = loop.create_server(ClientServerProtocol, host, port)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    run_server('127.0.0.1', 8888)
