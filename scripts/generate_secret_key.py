import secrets


def get_random_secret_key():
    """Returns 50 character random string usable as Django SECRET_KEY value.
    
    Equivalent to django.core.management.utils.get_random_secret_key but
    excludes $ character to avoid possible bash variable interpolation.
    """

    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))


if __name__ == '__main__':
    print(get_random_secret_key())
