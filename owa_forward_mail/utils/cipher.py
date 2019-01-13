from cryptography.fernet import Fernet, InvalidToken


class Cipher():
    def __init__(self, key):
        self.fernet = Fernet(key)

    def encrypt(self, plane):
        return self.fernet.encrypt(plane.encode('utf8')).decode('utf8')

    def decrypt(self, encrypted):
        try:
            return self.fernet.decrypt(encrypted.encode('utf8')).decode('utf8')
        except InvalidToken:
            return ''
