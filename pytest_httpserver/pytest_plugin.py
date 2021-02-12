import os
import warnings

import pytest

from .httpserver import HTTPServer


class Plugin:
    SERVER = None


class PluginHTTPServerDeprecation(type):
    def __init__(cls, name, bases, clsdict):
        if len(cls.mro()) > 3:
            warnings.warn(f"{name}: Class deprecated. Use HTTPServer instead.", DeprecationWarning)

        super(PluginHTTPServerDeprecation, cls).__init__(name, bases, clsdict)


class PluginHTTPServer(HTTPServer, metaclass=PluginHTTPServerDeprecation):
    def start(self):
        super().start()
        Plugin.SERVER = self

    def stop(self):
        super().stop()
        Plugin.SERVER = None


def get_httpserver_listen_address():
    listen_host = os.environ.get("PYTEST_HTTPSERVER_HOST")
    listen_port = os.environ.get("PYTEST_HTTPSERVER_PORT")
    if listen_port:
        listen_port = int(listen_port)

    return (listen_host, listen_port)


@pytest.fixture
def httpserver_listen_address():
    return get_httpserver_listen_address()


@pytest.fixture
def httpserver(httpserver_listen_address):
    if Plugin.SERVER:
        Plugin.SERVER.clear()
        yield Plugin.SERVER
        return

    host, port = httpserver_listen_address
    if not host:
        host = HTTPServer.DEFAULT_LISTEN_HOST
    if not port:
        port = HTTPServer.DEFAULT_LISTEN_PORT

    server = PluginHTTPServer(host=host, port=port)
    server.start()
    yield server


def pytest_sessionfinish(session, exitstatus):  # pylint: disable=unused-argument
    if Plugin.SERVER is not None:
        Plugin.SERVER.clear()
        if Plugin.SERVER.is_running():
            Plugin.SERVER.stop()


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):  # pylint: disable=unused-argument
    if fixturedef.argname == 'httpserver_listen_address' and fixturedef.scope != 'session':
        warnings.warn("httpserver_listen_address must be scoped with session.", DeprecationWarning)
        yield
    else:
        yield
