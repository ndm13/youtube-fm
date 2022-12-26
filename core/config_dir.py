# By default, load config from ../config/*
from os import getenv, path

config_dir = getenv('CONFIG_DIR', path.abspath(path.join(path.dirname(path.abspath(__file__)), "..", "config")))
