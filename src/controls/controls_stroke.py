import logging
import re
import subprocess
from re import Pattern
from typing import AnyStr, IO, Optional

import config
from controls.controls_abstract import Controls
from controls.file_manipulator import FileManipulator
from controls.utils import encode_base64, decode_base64, encode_hex, decode_hex


class ControlsStroke(Controls, FileManipulator):
    line_pattern: Pattern[AnyStr]

    def __init__(self, file_pattern: str = config.SECRETS_PATTERN):
        FileManipulator.__init__(self, file_pattern)
        self.line_pattern = re.compile(r'^"fqdn:#([A-Za-z0-9]+)" : EAP 0s([A-Za-z0-9+/=]+)\n$')

    def add_user(self, user_id: int, username: str, password: str) -> int:
        line = '"fqdn:#%s" : EAP 0s%s\n' % (encode_hex(username), encode_base64(password))
        with self.open(user_id, mode='ab') as f:
            return self.append(f, line)

    def remove_all(self, user_id: int):
        self.open(user_id, mode='wb').close()

    def remove_user(self, user_id: int, position: int) -> Optional[int]:
        with self.open(user_id) as f:
            return self.remove_line(f, position)

    def set_password(self, user_id: int, position: int, password: str) -> Optional[int]:
        with self.open(user_id) as f:
            _position, _count = self.get_password_pos(f, position)
            return self.replace_by_position(f, _position, _count, encode_base64(password))

    def set_username(self, user_id: int, position: int, username: str) -> Optional[int]:
        with self.open(user_id) as f:
            _position, _count = self.get_username_pos(f, position)
            return self.replace_by_position(f, _position, _count, encode_hex(username))

    def get_account(self, user_id: int, position: int) -> Optional[tuple[str, str]]:
        with self.open(user_id, mode='r') as f:
            f.seek(position)
            matches = self.line_pattern.match(f.readline())
            if matches:
                return decode_hex(matches[1]), decode_base64(matches[2])
            return None

    def get_accounts(self, user_id: int, *positions: int) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = list()
        with self.open(user_id, mode='r') as f:
            for position in positions:
                f.seek(position)
                matches = self.line_pattern.match(f.readline())
                result.append((decode_hex(matches[1]), decode_base64(matches[2])))
        return result

    def update_hook(self):
        try:
            # Try direct execution first
            subprocess.run(['strongswan', 'stroke', 'rereadsecrets'])
        except FileNotFoundError:
            # If direct execution fails, try with sudo
            subprocess.run(['sudo', 'strongswan', 'stroke', 'rereadsecrets'])
        except Exception as e:
            logging.error(f"Failed to execute strongswan stroke command: {e}")
            raise

    @staticmethod
    def get_username_pos(f: IO, position: int):
        f.seek(position)
        line = f.readline().decode()
        start = line.find('"fqdn:#') + 7
        end = line.find('"', start)
        return position + start, end - start

    @staticmethod
    def get_password_pos(f: IO, position: int):
        f.seek(position)
        line = f.readline().decode()
        end = line.rfind('\n')
        start = line.rfind('0s', 0, end) + 2
        return position + start, end - start
