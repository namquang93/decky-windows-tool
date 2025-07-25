"""Base class for communicating with a 32-bit library from 64-bit Python.

[Server32][] is used in combination with [Client64][] to communicate with
a 32-bit library from 64-bit Python.
"""

from __future__ import annotations

import importlib
import inspect
import io
import json
import os
import pickle
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import warnings
from http2.client import CannotSendRequest, HTTPConnection
from pathlib import Path
from typing import TYPE_CHECKING, cast

from ._constants import IS_WINDOWS, server_filename
from .exceptions import ConnectionTimeoutError, ResponseTimeoutError, Server32Error
from .server32 import METADATA, OK, SHUTDOWN, Server32
from .utils import get_available_port, wait_for_server

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import IO, Any, TypeVar

    from ._types import PathLike, Server32Subclass

    # the Self type was added in Python 3.11 (PEP 673)
    # using TypeVar is equivalent for < 3.11
    Self = TypeVar("Self", bound="Client64")


class Client64:
    """Base class for communicating with a 32-bit library from 64-bit Python."""

    def __init__(  # noqa: PLR0913
        self,
        module32: PathLike,
        *,
        add_dll_directory: PathLike | Iterable[PathLike] | None = None,
        append_environ_path: PathLike | Iterable[PathLike] | None = None,
        append_sys_path: PathLike | Iterable[PathLike] | None = None,
        host: str | None = "127.0.0.1",
        port: int = 0,
        protocol: int = 5,
        rpc_timeout: float | None = None,
        server32_dir: PathLike | None = None,
        timeout: float = 10,
        **kwargs: Any,
    ) -> None:
        """Base class for communicating with a 32-bit library from 64-bit Python.

        Starts a 32-bit server, [Server32][], to host a Python class that is a wrapper
        around a 32-bit library. [Client64][] runs within a 64-bit Python interpreter
        and it sends requests to the server which calls the 32-bit library to execute
        the request. The server then sends the response back to the client.

        Args:
            module32: The name of, or the path to, a Python module that will be imported by the
                32-bit server. The module must contain a class that inherits from [Server32][].

            add_dll_directory: Add path(s) to the 32-bit server's DLL search path.
                See [os.add_dll_directory][]{:target="_blank"} for more details.
                Supported on Windows only.

                !!! note "Added in version 1.0"

            append_environ_path: Append path(s) to the 32-bit server's
                [os.environ["PATH"]][os.environ]{:target="_blank"} variable. This may be useful if
                the library that is being loaded requires additional libraries that
                must be available on `PATH`.

            append_sys_path: Append path(s) to the 32-bit server's [sys.path][]{:target="_blank"}
                variable. The value of [sys.path][]{:target="_blank"} from the 64-bit process is
                automatically included, i.e.,

                <code>path<sub>32</sub> = path<sub>64</sub> + append_sys_path</code>

            host: The hostname (IP address) of the 32-bit server. If `None` then the
                connection to the server is [mocked][faq-mock].

                !!! note "Changed in version 1.0"
                    A value of `None` is allowed.

            port: The port to open on the 32-bit server. If `0`, any available port will be used.

            protocol: The [pickle protocol][pickle-protocols]{:target="_blank"} to use.
                !!! note "Added in version 0.8"

            rpc_timeout: The maximum number of seconds to wait for a response from the 32-bit server.
                The [RPC](https://en.wikipedia.org/wiki/Remote_procedure_call){:target="_blank"}
                timeout value is used for *all* requests from the server. If you want different
                requests to have different timeout values, you will need to implement custom
                timeout handling for each method on the server. Default is `None`, which will
                call [socket.getdefaulttimeout][]{:target="_blank"} to get the timeout value.

                !!! note "Added in version 0.6"

            server32_dir: The directory where the 32-bit server is located.
                Specifying this value may be useful if you created a [custom server][refreeze].

                !!! note "Added in version 0.10"

            timeout: The maximum number of seconds to wait to establish a connection
                with the 32-bit server.

            kwargs: All additional keyword arguments are passed to the [Server32][] subclass.
                The data type of each value is not preserved. It will be of type [str][]
                at the constructor of the [Server32][] subclass.

        Raises:
            OSError: If the 32-bit server cannot be found.
            ConnectionTimeoutError: If the connection to the 32-bit server cannot be established.

        !!! note
            If `module32` is not located in the current working directory then you
            must either specify the full path to `module32` **or** you can
            specify the folder where `module32` is located by passing a value to the
            `append_sys_path` parameter. Using the `append_sys_path` option also allows
            for any other modules that `module32` may depend on to also be included
            in [sys.path][]{:target="_blank"} so that those modules can be imported when `module32`
            is imported.
        """
        self._client: _MockClient | _HTTPClient
        if host is None:
            self._client = _MockClient(
                os.fsdecode(module32),
                add_dll_directory=add_dll_directory,
                append_environ_path=append_environ_path,
                append_sys_path=append_sys_path,
                **kwargs,
            )
        else:
            self._client = _HTTPClient(
                os.fsdecode(module32),
                add_dll_directory=add_dll_directory,
                append_environ_path=append_environ_path,
                append_sys_path=append_sys_path,
                host=host,
                port=port,
                protocol=protocol,
                rpc_timeout=rpc_timeout,
                server32_dir=server32_dir,
                timeout=timeout,
                **kwargs,
            )

    def __del__(self) -> None:
        """Call the cleanup() method from the client."""
        try:  # noqa: SIM105
            self._client.cleanup()
        except AttributeError:
            pass

    def __enter__(self: Self) -> Self:  # noqa: PYI019
        """Enter the context manager."""
        return self

    def __exit__(self, *ignored: object) -> None:
        """Exit the context manager."""
        try:  # noqa: SIM105
            self._client.cleanup()
        except AttributeError:
            pass

    def __repr__(self) -> str:
        """Returns the string representation."""
        lib = Path(self._client.lib32_path).name
        if self._client.host is None:
            return f"<{self.__class__.__name__} lib={lib} address=None (mocked)>"

        if self._client.connection is None:
            return f"<{self.__class__.__name__} lib={lib} address=None (closed)>"

        return f"<{self.__class__.__name__} lib={lib} address={self._client.host}:{self._client.port}>"

    @property
    def host(self) -> str | None:
        """[str][] | `None` &mdash; The host address of the 32-bit server.

        The value is `None` for a [mocked][faq-mock] connection.
        """
        return self._client.host

    @property
    def port(self) -> int:
        """[int][] &mdash; The port number of the 32-bit server.

        The value is `-1` for a [mocked][faq-mock] connection.
        """
        return self._client.port

    @property
    def connection(self) -> HTTPConnection | None:
        """[HTTPConnection][http2.client.HTTPConnection] | `None` &mdash; The connection to the 32-bit server.

        The value is `None` for a [mocked][faq-mock] connection or if the connection has been closed.
        """
        return self._client.connection

    @property
    def lib32_path(self) -> str:
        """[str][] &mdash; The path to the 32-bit library file."""
        return self._client.lib32_path

    def request32(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Send a request to the 32-bit server.

        Args:
            name: The name of a method, property or attribute of the [Server32][] subclass.
            args: The arguments that the method of the [Server32][] subclass requires.
            kwargs: The keyword arguments that the method of the [Server32][] subclass requires.

        Returns:
            Whatever is returned by calling `name`.

        Raises:
            Server32Error: If there was an error processing the request on the 32-bit server.
            ResponseTimeoutError: If a timeout occurs while waiting for the response from the 32-bit server.
        """
        return self._client.request32(name, *args, **kwargs)

    def shutdown_server32(self, kill_timeout: float = 10) -> tuple[IO[bytes], IO[bytes]]:
        """Shut down the 32-bit server.

        This method shuts down the 32-bit server, closes the client connection, and deletes
        the temporary file that was used to store the serialized [pickle][]{:target="_blank"}d data.

        Args:
            kill_timeout: If the 32-bit server is still running after `kill_timeout`
                seconds, the server will be killed using brute force. A warning will be
                issued if the server is killed in this manner.

                !!! note "Added in version 0.6"

        Returns:
            The `(stdout, stderr)` streams from the 32-bit server.

                Limit the total number of characters that are written to either `stdout`
                or `stderr` on the 32-bit server to be &lt; 4096. This will avoid potential
                blocking when reading the `stdout` and `stderr` PIPE buffers.

                !!! note "Changed in version 0.8"
                    Prior to version 0.8 this method returned `None`

        !!! tip
            This method gets called automatically when the reference count to the
            [Client64][] instance reaches zero (see [`object.__del__`][]{:target="_blank"}).
        """
        return self._client.shutdown_server32(kill_timeout=kill_timeout)


class _HTTPClient:
    def __init__(  # noqa: C901, PLR0912, PLR0913, PLR0915
        self,
        module32: str,
        *,
        add_dll_directory: PathLike | Iterable[PathLike] | None = None,
        append_environ_path: PathLike | Iterable[PathLike] | None = None,
        append_sys_path: PathLike | Iterable[PathLike] | None = None,
        host: str = "127.0.0.1",
        port: int = 0,
        protocol: int = 5,
        rpc_timeout: float | None = None,
        server32_dir: PathLike | None = None,
        timeout: float = 10,
        **kwargs: Any,
    ) -> None:
        """Start a server and connect to it."""
        self._meta32: dict[str, str | int] = {}
        self._conn: HTTPConnection | None = None

        if port == 0:
            port = get_available_port()

        # Temporary files to exchange client-server information
        f = Path(tempfile.gettempdir()) / f"msl-loadlib-{host}-{port}"
        self._pickle_path: str = f"{f}.pickle"
        self._meta_path: str = f"{f}.txt"
        self._pickle_protocol: int = protocol

        # Find the 32-bit server executable.
        # Check a few locations in case msl-loadlib is frozen.
        dirs = [Path(__file__).parent] if server32_dir is None else [Path(os.fsdecode(server32_dir))]
        if getattr(sys, "frozen", False):
            # PyInstaller location for data files
            if hasattr(sys, "_MEIPASS"):
                dirs.append(Path(sys._MEIPASS))  # pyright: ignore[reportAttributeAccessIssue,reportUnknownArgumentType,reportUnknownMemberType] # noqa: SLF001

            # cx_Freeze location for data files
            dirs.append(Path(sys.executable).parent)

            # Current working directory
            dirs.append(Path.cwd())

        server_exe: str | None = None
        for directory in dirs:
            exe = directory / server_filename
            if exe.is_file():
                server_exe = str(exe)
                break

        if server_exe is None:
            if len(dirs) == 1:
                msg = f"Cannot find {dirs[0] / server_filename}"
                raise OSError(msg)

            directories = "\n  ".join(sorted(str(d) for d in set(dirs)))
            msg = f"Cannot find {server_filename!r} in any of the following directories:\n  {directories}"
            raise OSError(msg)

        # Build the subprocess command
        cmd = [
            server_exe,
            "--module",
            module32,
            "--host",
            host,
            "--port",
            str(port),
        ]

        # Include paths to the 32-bit server's sys.path
        sys_path = list(sys.path)
        sys_path.extend(_build_paths(append_sys_path, ignore=sys_path))
        cmd.extend(["--append-sys-path", ";".join(sys_path)])

        # Include paths to the 32-bit server's os.environ['PATH']
        env_path = [str(Path.cwd())]
        env_path.extend(_build_paths(append_environ_path, ignore=env_path))
        cmd.extend(["--append-environ-path", ";".join(env_path)])

        # Include paths to the 32-bit server's os.add_dll_directory()
        dll_dirs = _build_paths(add_dll_directory)
        if dll_dirs:
            cmd.extend(["--add-dll-directory", ";".join(dll_dirs)])

        # Include user-defined keyword arguments
        if kwargs:
            kw_str = ";".join(f"{k}={v}" for k, v in kwargs.items())
            cmd.extend(["--kwargs", kw_str])

        # Start the 32-bit server and wait for it to be running
        flags = 0x08000000 if IS_WINDOWS else 0  # fixes issue 31, CREATE_NO_WINDOW = 0x08000000
        self._proc: subprocess.Popen[bytes] = subprocess.Popen(  # noqa: S603
            cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=flags
        )
        try:
            wait_for_server(host, port, timeout)
        except ConnectionTimeoutError as err:
            self._wait(timeout=0, stacklevel=5)
            # if the subprocess was killed then self._wait sets returncode to -2
            if self._proc.returncode == -2:  # noqa: PLR2004
                self._cleanup_zombie_and_files()
                assert self._proc.stdout is not None  # noqa: S101
                stdout = self._proc.stdout.read()
                if not stdout:
                    err.reason = (
                        f"If you add print() statements to {module32!r}\n"
                        f"the statements that are executed will be displayed here.\n"
                        f"Limit the total number of characters that are written to stdout to be < 4096\n"
                        f"to avoid potential blocking when reading the stdout PIPE buffer."
                    )
                else:
                    err.reason = f"stdout from {module32!r} is:\n{stdout.decode()}"
            else:
                assert self._proc.stderr is not None  # noqa: S101
                err.reason = self._proc.stderr.read().decode(errors="ignore")
            raise

        # Connect to the server
        self._rpc_timeout: float | None = socket.getdefaulttimeout() if rpc_timeout is None else rpc_timeout
        self._conn = HTTPConnection(host, port=port, timeout=self._rpc_timeout)
        self._host: str = self._conn.host
        self._port: int = self._conn.port

        # Let the server know the info to use for pickling
        self._conn.request("POST", f"protocol={self._pickle_protocol}&path={self._pickle_path}")
        response = self._conn.getresponse()
        if response.status != OK:
            _ = self.shutdown_server32()
            value = "Cannot set pickle info"
            raise Server32Error(value)

        try:
            self._meta32 = self.request32(METADATA)
        except ValueError:  # could happen if the pickle-protocol value is invalid for the client
            _ = self.shutdown_server32()
            raise

        self._lib32_path: str = str(self._meta32["path"])

    @property
    def host(self) -> str:
        """The host address of the 32-bit server."""
        return self._host

    @property
    def port(self) -> int:
        """The port number of the 32-bit server."""
        return self._port

    @property
    def connection(self) -> HTTPConnection | None:
        """The connection to the 32-bit server."""
        return self._conn

    @property
    def lib32_path(self) -> str:
        """The path to the 32-bit library file."""
        return self._lib32_path

    def cleanup(self) -> None:
        """Shutdown the server and remove files."""
        try:
            out, err = self.shutdown_server32()
            out.close()
            err.close()
        except AttributeError:
            pass

        try:  # noqa: SIM105
            self._cleanup_zombie_and_files()
        except AttributeError:
            pass

    def request32(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Send a request to the 32-bit server."""
        if self._conn is None:
            value = "The connection to the 32-bit server is closed"
            raise Server32Error(value)

        with open(self._pickle_path, mode="wb") as f:  # noqa: PTH123
            pickle.dump(args, f, protocol=self._pickle_protocol)
            pickle.dump(kwargs, f, protocol=self._pickle_protocol)

        self._conn.request("GET", name)

        try:
            response = self._conn.getresponse()
        except socket.timeout:
            msg = f"Waiting for the response from the {name!r} request timed out after {self._rpc_timeout} second(s)"
            raise ResponseTimeoutError(msg) from None

        if response.status == OK:
            with open(self._pickle_path, mode="rb") as f:  # noqa: PTH123
                return pickle.load(f)  # noqa: S301

        raise Server32Error(**json.loads(response.read().decode()))

    def shutdown_server32(self, kill_timeout: float = 10) -> tuple[IO[bytes], IO[bytes]]:
        """Shutdown the 32-bit server."""
        assert self._proc.stdout is not None  # noqa: S101
        assert self._proc.stderr is not None  # noqa: S101

        if self._conn is None:
            return self._proc.stdout, self._proc.stderr

        # send the shutdown request
        try:
            self._conn.request("POST", SHUTDOWN)
        except CannotSendRequest:
            # can occur if the previous request raised ResponseTimeoutError
            # send the shutdown request again
            self._conn.close()
            self._conn = HTTPConnection(self.host, port=self.port)
            self._conn.request("POST", SHUTDOWN)

        # give the frozen 32-bit server a chance to shut down gracefully
        self._wait(timeout=kill_timeout, stacklevel=4)

        self._cleanup_zombie_and_files()

        _ = self._conn.sock.shutdown(socket.SHUT_RDWR)
        self._conn.close()
        self._conn = None
        return self._proc.stdout, self._proc.stderr

    def _wait(self, timeout: float = 10, stacklevel: int = 4) -> None:
        # give the 32-bit server a chance to shut down gracefully
        t0 = time.time()
        while self._proc.poll() is None:
            try:  # noqa: SIM105
                time.sleep(0.1)
            except OSError:
                # could be raised while Python is shutting down
                #   OSError: [WinError 6] The handle is invalid
                pass

            if time.time() - t0 > timeout:
                self._proc.terminate()
                self._proc.returncode = -2
                warnings.warn("killed the 32-bit server using brute force", stacklevel=stacklevel)
                break

    def _cleanup_zombie_and_files(self) -> None:
        Path(self._pickle_path).unlink(missing_ok=True)

        if self._meta32:
            pid = int(self._meta32["pid"])
            unfrozen_dir = str(self._meta32["unfrozen_dir"])
        else:
            try:
                lines = Path(self._meta_path).read_text().splitlines()
            except (OSError, NameError):
                return
            else:
                pid, unfrozen_dir = int(lines[0]), lines[1]

        try:  # noqa: SIM105
            os.kill(pid, 9)  # <signal.SIGKILL 9> constant is not available on Windows
        except OSError:
            pass

        # cleans up PyInstaller issue #2379 if the server was killed
        shutil.rmtree(unfrozen_dir, ignore_errors=True)

        Path(self._meta_path).unlink(missing_ok=True)


class _MockClient:
    _PORT: int = -1

    def __init__(
        self,
        module32: str,
        *,
        add_dll_directory: PathLike | Iterable[PathLike] | None = None,
        append_environ_path: PathLike | Iterable[PathLike] | None = None,
        append_sys_path: PathLike | Iterable[PathLike] | None = None,
        **kwargs: Any,
    ) -> None:
        """Mocks the HTTP connection to the server."""
        self._added_dll_directories: list[Any] = []
        for path in _build_paths(add_dll_directory):
            self._added_dll_directories.append(os.add_dll_directory(path))

        if append_environ_path is not None:
            ignore = os.environ["PATH"].split(os.pathsep)
            new_env_paths = _build_paths(append_environ_path, ignore=ignore)
            if new_env_paths:
                os.environ["PATH"] += os.pathsep + os.pathsep.join(new_env_paths)

        # module32 may be a path to a Python file
        directory, module_name = os.path.split(module32)

        # must append specified paths to sys.path before importing module32
        if directory and directory not in sys.path:
            sys.path.append(directory)
        if append_sys_path is not None:
            sys.path.extend(_build_paths(append_sys_path, ignore=sys.path))

        # get the Server32 subclass in the module
        cls: type[Server32Subclass] | None = None
        if module_name.endswith(".py"):
            mod = importlib.import_module(module_name[:-3])
        else:
            mod = importlib.import_module(module_name)
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if name != "Server32" and issubclass(obj, Server32):
                cls = cast("type[Server32Subclass]", obj)
                break

        if cls is None:
            msg = f"Module {module32!r} does not contain a class that is a subclass of Server32"
            raise AttributeError(msg)

        # Server32 subclass expects the values for all kwargs to be of type string
        kw = {key: str(value) for key, value in kwargs.items()}
        self.server: Server32Subclass = cls(None, _MockClient._PORT, **kw)

    def cleanup(self) -> None:
        """Close the socket (which was never bound and activated)."""
        self.server.socket.close()

        for directory in self._added_dll_directories:
            if directory.path:
                directory.close()
        self._added_dll_directories.clear()

    @property
    def connection(self) -> None:
        """The connection to the mocked server."""
        return None

    @property
    def host(self) -> None:
        """The host address of the mocked server."""
        return None

    @property
    def lib32_path(self) -> str:
        """The path to the library file."""
        return self.server.path

    @property
    def port(self) -> int:
        """The port number of the mocked server."""
        return _MockClient._PORT

    def request32(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Send a request to the mocked server."""
        try:
            attr = getattr(self.server, name)
            if callable(attr):
                return attr(*args, **kwargs)
        except Exception as e:
            exception = {
                "name": e.__class__.__name__,
                "value": f"The mocked connection to the server raised:\n{e}\n(see above for more details)",
            }
            raise Server32Error(**exception) from e
        else:
            return attr

    def shutdown_server32(self, **_: object) -> tuple[IO[bytes], IO[bytes]]:
        """Shutdown the mocked server."""
        self.cleanup()
        return io.BytesIO(), io.BytesIO()


def _build_paths(paths: PathLike | Iterable[PathLike] | None, *, ignore: list[str] | None = None) -> list[str]:
    """Build a list of absolute paths."""
    if paths is None:
        return []

    if ignore is None:
        ignore = []

    if isinstance(paths, (str, bytes, os.PathLike)):
        paths = [paths]

    out: list[str] = []
    for p in paths:
        path = os.path.abspath(os.fsdecode(p))  # noqa: PTH100
        if path not in ignore:
            out.append(path)
    return out
