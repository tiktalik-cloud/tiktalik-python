"""Tiktalik Cloud Computing Platform SDK for Python"""
from setuptools import setup

setup(
    name="tiktalik",
    version="1.6.3.1",
    python_requires=">=3.5",
    description="Python SDK for the Tiktalik Computing service.",
    author="Techstorage sp. z o.o",
    author_email="kontakt@tiktalik.com",
    url="http://www.tiktalik.com",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
    ],
    packages=["tiktalik", "tiktalik.computing", "tiktalik.loadbalancer"],
)
