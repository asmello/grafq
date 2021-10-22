#!/usr/bin/env python3

from distutils.core import setup

setup(
    name="grafq",
    version="0.0.1",
    packages=["grafq"],
    url="https://github.com/asmello/grafq",
    license="MIT",
    author="André Sá de Mello",
    author_email="asmello.br@gmail.com",
    description="A pythonic way to build GraphQL queries",
    install_requires=["requests"],
)
