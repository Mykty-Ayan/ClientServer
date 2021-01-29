import socket
import re

from time import time
from typing import Dict


class ClientError(Exception):
    """Custom client exception"""
    pass


class Client(object):
    """Client for sending metrics to the server."""

    def __init__(self, host: str, port: int, timeout=None):
        self.address = (host, port)
        self.timeout = timeout
        try:
            self.__connection = socket.create_connection(
                address=self.address, timeout=self.timeout
            )
        except socket.error as error:
            raise ClientError(error)

    def get(self, metric_name: str) -> Dict:
        """Get value of metric by name

        :param metric_name:
            Used to request metric value, can accept '*'
        :type
            metric_name: str
        :raises
            ClientError
        :return:
            Dictionary with values of metrics
        """
        message = f'get {metric_name}\n'
        self.__connection.send(message.encode())
        response = self.__connection.recv(1024).decode()
        result = dict()

        if response == 'ok\n\n':
            return result

        if response[0:3] != 'ok\n' or response[-2:] != '\n\n':
            raise ClientError(response)

        # preprocess metrics and skip command
        data = [item for item in response.split('\n') if item][1:]
        try:
            for metrics in data:
                metric = metrics.split()
                if len(metric) < 3:
                    raise ClientError(response)
                # unpack values into variables
                metric_name, percent, timestamp = metric

                if metric_name not in result.keys():
                    result[metric_name] = list()

                result[metric_name].append((int(timestamp), float(percent)))
                result[metric_name].sort(key=lambda metric_tuple: metric_tuple[0])
        except ValueError:
            raise ClientError

        return result

    def put(self, metric_name: str, metric_value: float, timestamp=None) -> None:
        """Saves metric to the server

                :param metric_name:
                    Used to store as a key in server
                :param metric_value:
                    Loading value of element
                :param timestamp:
                    UNIX time when metric was measured
                :type
                    metric_name: str
                    metric_value: float
                :raises
                    ClientError
                :return:
                    None
                """
        timestamp = str(timestamp or int(time()))
        message = f'put {metric_name} {metric_value} {timestamp}\n'

        self.__connection.send(message.encode())

        response = self.__connection.recv(1024).decode()

        if response[:3] != 'ok\n':
            raise ClientError()

        if 'error\nwrong command\n\n' in response:
            raise ClientError()

    def close_connection(self) -> None:
        """Used to close connection"""
        self.__connection.close()


if __name__ == '__main__':
    client = Client('127.0.0.1', 8888, timeout=15)
