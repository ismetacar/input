from src.helpers.crypto import FernetCrpyto


def decrypt_critial_fields(data, secret):
    data["password"] = FernetCrpyto.decrypt(secret, data["password"].encode()).decode()
    data["cms_password"] = FernetCrpyto.decrypt(secret, data["cms_password"].encode()).decode()

    return data


def encrypt_critial_fields(data, secret):
    data["password"] = FernetCrpyto.encrypt(secret, data["password"].encode()).decode()
    data["cms_password"] = FernetCrpyto.encrypt(secret, data["cms_password"].encode()).decode()

    return data
