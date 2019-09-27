#!/bin/sh
gunicorn itemhunt.wsgi:application --bind 0.0.0.0:5001
