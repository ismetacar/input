from cryptography.fernet import Fernet


class FernetCrpyto:

    @staticmethod
    def encrypt(k, v):
        f = Fernet(k)
        return f.encrypt(v)

    @staticmethod
    def decrypt(k, v):
        f = Fernet(k)
        return f.decrypt(v)
