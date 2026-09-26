class ConnectionBuffer:
    def __init__(self):
        self.buffer = b""

    def feed(self, data: bytes):
        self.buffer += data

        commands = []

        while True:
            # 1. Find the Header
            pos = self.buffer.find(b"\r\n")

            if pos == -1:
                break

            header = self.buffer[:pos]
            rest = self.buffer[pos + 2:]

            parts = header.split()

            # If the header is not complete
            if not parts:
                self.buffer = rest
                continue

            command = parts[0].lower()

            if command == b"set":
                # Set key flags ttl bytes
                if len(parts) != 5:
                    raise ValueError("Invalid set command format")

                value_length = int(parts[4])

                # Check value + \r\n
                required = value_length + 2

                if len(rest) < required:
                    break

                value = rest[:value_length]

                if rest[value_length:value_length + 2] != b"\r\n":
                    raise ValueError("Invalid set command value termination")

                raw_command = header + b"\r\n" + value + b"\r\n"

                commands.append(raw_command)
                self.buffer = rest[required:]

            else:
                # For other commands, just take the header
                raw_command = header + b"\r\n"
                commands.append(raw_command)
                self.buffer = rest

        return commands