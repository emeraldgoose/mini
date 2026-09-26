from dataclasses import dataclass

@dataclass
class GetCommand:
    key: str

@dataclass
class SetCommand:
    key: str
    value: bytes
    flags: int
    ttl: int

@dataclass
class DeleteCommand:
    key: str

class ProtocolError(Exception):
    """Custom exception for protocol errors."""
    pass

class ProtocolParser:
    """
        A simple parser for the mini_memcached protocol.
        It can parse GET, SET, and DELETE commands from strings.
    """
    
    def parse(self, command_str: bytes):
        parts = command_str.split(b"\r\n")
        
        if not parts:
            raise ProtocolError("Empty request")

        command = parts[0].split()

        if not command:
            raise ProtocolError("Empty command")

        cmd = command[0].lower()

        if cmd == b"get":
            return self._parse_get(command)

        elif cmd == b"delete":
            return self._parse_delete(command)

        elif cmd == b"set":
            return self._parse_set(command, parts)

        else:
            raise ProtocolError(f"Unknown command: {cmd}")

    def _parse_get(self, command):
        if len(command) != 2:
            raise ProtocolError("GET command requires exactly one key")
        
        return GetCommand(key=command[1].decode())

    def _parse_delete(self, command):
        if len(command) != 2:
            raise ProtocolError("DELETE command requires exactly one key")
        
        return DeleteCommand(key=command[1].decode())

    def _parse_set(self, command, parts):
        if len(command) < 4:
            raise ProtocolError("SET command requires at least key, flags, and value")
        
        key = command[1].decode()
        flags = int(command[2])
        ttl = int(command[3]) if len(command) > 4 else 0
        size = int(command[4])

        if len(parts) < 2:
            raise ProtocolError("Missing value")

        value = parts[1]
        if size != len(value):
            raise ProtocolError("Invalid value size")
        
        return SetCommand(key=key, value=value, flags=flags, ttl=ttl)

class ResponseBuilder:
    """
        A simple builder for responses in the mini_memcached protocol.
    """
    def get_response(self, key, item):
        if item is None:
            return b"END\r\n"

        return (
            f"VALUE {key} {item.flags} {len(item.value)}\r\n"
            .encode()
            + item.value
            + b"\r\n"
            + b"END\r\n"
        )

    def set_response(self, success):
        if success:
            return b"STORED\r\n"

        return b"NOT_STORED\r\n"

    def delete_response(self, success):
        if success:
            return b"DELETED\r\n"

        return b"NOT_FOUND\r\n"
