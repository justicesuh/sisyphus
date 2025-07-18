import secrets


def get_random_string(length, allowed_chars):
    return ''.join(secrets.choice(allowed_chars) for _ in range(length))


def get_random_secret_key():
    # equivalent to django.core.management.utils.get_random_secret_key
    # except replaces $ with S. A $ in the secret key can throw warning
    # if shell interprets them as variable substitutions
    return get_random_string(50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#S%^&*(-_=+)')


if __name__ == '__main__':
    print(get_random_secret_key())
