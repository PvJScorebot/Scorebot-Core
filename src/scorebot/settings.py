#!/usr/bin/false
# Django Settings & Constants
# Scorebot v4 - The Scorebot Project
#
# Copyright (C) 2020 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from os.path import dirname, abspath, join

DEBUG = True
USE_TZ = True
USE_I18N = True
USE_L10N = True
TIME_ZONE = 'UTC'
ALLOWED_HOSTS = ['*']
STATIC_URL = '/static/'
LANGUAGE_CODE = 'en-us'
ROOT_URLCONF = 'scorebot_api.urls'
WSGI_APPLICATION = 'scorebot.wsgi.application'
BASE_DIR = dirname(dirname(abspath(__file__)))
SECRET_KEY = 'p8lh!%&0n_@&a%iz!7@9h_x_s3p5*iu-)4i&pzjfe)ksvfy+v#'
TEMPLATES = [{
    'DIRS': [],
    'APP_DIRS': True,
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug', 'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages'
        ]
    }
}]
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'scorebot_db', 'scorebot_api'
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': join(dirname(BASE_DIR), 'db', 'scorebot.sqlite3')
    },
    #    'mysql': {
    #        'ENGINE': 'django.db.backends.mysql',
    #        'NAME': 'scorebot_db',
    #        'HOST': 'localhost',
    #        'USER': 'scorebot_user',
    #        'PASSWORD': 'Scorebot123!'
    #    }
}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}
]
