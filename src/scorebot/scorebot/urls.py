#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from django.contrib import admin
from django.urls import path, re_path
from scorebot_utils.restful import Api

urlpatterns = [path("admin/", admin.site.urls), re_path(r"^api/([a-zA-Z0-9/-]+)$", Api)]
