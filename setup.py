"""Tiktalik Cloud Computing Platform SDK for Python"""
from distutils.core import setup

setup(
    name="tiktalik",
    version="1.6.3.1",
    python_requires=">=3.5",
    description="Python SDK for the Tiktalik Computing service.",
    author="Techstorage sp. z o.o",
    author_email="kontakt@tiktalik.com",
    url="http://www.tiktalik.com",
    license="MIT",
    keywords = ['SDK', 'Tiktalik', 'VPS']
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers"
    ],
    packages=["tiktalik", "tiktalik.computing", "tiktalik.loadbalancer"],
)
