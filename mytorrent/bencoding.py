from collections import OrderedDict


from .tokens import Token


class Decoder:
    """
    Decodes a bencoded sequence of bytes.
    """
    def __init__(self, data: bytes):
        if not isinstance(data, bytes):
            raise TypeError('Argument "data" must be of type bytes')
        self._data = data
        self._index = 0

    def decode(self):
        """
        Decodes the bencoded data and return the matching python object.

        :return A python object representing the bencoded data
        """
        c = self._peek()
        match c:
            case None:
                raise EOFError('Unexpected end-of-file')
            case Token.TOKEN_INTEGER:
                self._consume()  # The token
                return self._decode_int()
            case Token.TOKEN_LIST:
                self._consume()  # The token
                return self._decode_list()
            case Token.TOKEN_DICT:
                self._consume()  # The token
                return self._decode_dict()
            case Token.TOKEN_END:
                return None
            case item if item in b'01234567899':
                return self._decode_string()
            case _:
                raise RuntimeError('Invalid token read at {0}'.format(
                    str(self._index)))

    def _peek(self):
        """
        Return the next character from the bencoded data or None
        """
        if self._index + 1 >= len(self._data):
            return None
        return self._data[self._index:self._index + 1]

    def _consume(self) -> bytes:
        """
        Read (and therefore consume) the next character from the data
        """
        self._index += 1

    def _read(self, length: int) -> bytes:
        """
        Read the `length` number of bytes from data and return the result
        """
        if self._index + length > len(self._data):
            raise IndexError('Cannot read {0} bytes from current position {1}'
                             .format(str(length), str(self._index)))
        res = self._data[self._index:self._index+length]
        self._index += length
        return res

    def _read_until(self, token: bytes) -> bytes:
        """
        Read from the bencoded data until the given token is found and return
        the characters read.
        """
        try:
            occurrence = self._data.index(token, self._index)
            result = self._data[self._index:occurrence]
            self._index = occurrence + 1
            return result
        except ValueError:
            raise RuntimeError('Unable to find token {0}'.format(
                str(token)))

    def _decode_int(self):
        return int(self._read_until(Token.TOKEN_END))

    def _decode_list(self):
        res = []
        # Recursive decode the content of the list
        while self._data[self._index: self._index + 1] != Token.TOKEN_END:
            res.append(self.decode())
        self._consume()  # The END token
        return res

    def _decode_dict(self):
        res = OrderedDict()
        while self._data[self._index: self._index + 1] != Token.TOKEN_END:
            key = self.decode()
            obj = self.decode()
            res[key] = obj
        self._consume()  # The END token
        return res

    def _decode_string(self):
        bytes_to_read = int(self._read_until(Token.TOKEN_STRING_SEPARATOR))
        data = self._read(bytes_to_read)
        return data


class Encoder:
    """
    Encodes a python object to a bencoded sequence of bytes.

    Supported python types is:
        - str
        - int
        - list
        - dict
        - bytes

    Any other type will simply be ignored.
    """
    def __init__(self, data: str | int | list | dict | OrderedDict | bytes) -> None:
        self._data = data

    def encode(self) -> bytes:
        """
        Encode a python object to a bencoded binary string

        :return The bencoded binary data
        """
        return self.encode_next(self._data)

    def encode_next(self, data: str | int | list | dict | OrderedDict | bytes) -> bytes:
        match data:
            case str():
                return self._encode_string(data)
            case int():
                return self._encode_int(data)
            case list():
                return self._encode_list(data)
            case dict() | OrderedDict():
                return self._encode_dict(data)
            case bytes():
                return self._encode_bytes(data)
            case _:
                error_msg = f"Cannot bencode {type(data)}"
                raise TypeError(error_msg)
                return None

    def _encode_int(self, value: int) -> bytes:
        return str.encode('i' + str(value) + 'e')

    def _encode_string(self, value: str) -> bytes:
        res = str(len(value)) + ':' + value
        return str.encode(res)

    def _encode_bytes(self, value: bytes) -> bytes:
        result = bytearray()
        result += str.encode(str(len(value)))
        result += b':'
        result += value
        return result

    def _encode_list(self,  data: list) -> bytes:
        result = bytearray('l', 'utf-8')
        result += b''.join([self.encode_next(item) for item in data])
        result += b'e'
        return result

    def _encode_dict(self, data: dict) -> bytes:
        result = bytearray('d', 'utf-8')
        for k, v in data.items():
            key = self.encode_next(k)
            value = self.encode_next(v)
            if key and value:
                result += key
                result += value
            else:
                msg = "Bad dict"
                raise RuntimeError(msg)
        result += b'e'
        return result