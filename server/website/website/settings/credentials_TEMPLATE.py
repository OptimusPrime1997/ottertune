#
# OtterTune - credentials_TEMPLATE.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#
"""
Private/custom Django settings for the OtterTune project.

"""
# pylint: disable=invalid-name

# ==============================================
# SECRET KEY CONFIGURATION
# ==============================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ADD ME!!'

# ==============================================
# DATABASE CONFIGURATION
# ==============================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ottertune_ddpg',
        'USER': 'dbuser',
        'PASSWORD': 'test123',
        'HOST': 'localhost',
        'PORT': '8081',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES',innodb_strict_mode=1",
        },
    }
}

# ==============================================
# DEBUG CONFIGURATION
# ==============================================

# Can override the DEBUG setting here
# DEBUG = False
DEBUG = True

# ==============================================
# MANAGER CONFIGURATION
# ==============================================

# Admin and managers for this project. These people receive private
# site alerts.
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

# ==============================================
# GENERAL CONFIGURATION
# ==============================================

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*', '0.0.0.0', '10.0.2.41', '10.0.2.33',
                 '127.0.0.1', '192.168.122.77',
                 '192.168.122.1', '10.0.3.177',
                 '*.*.*.*',
                 '10.0.14.35',
                 '10.0.*.*']
