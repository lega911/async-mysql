import os
from distutils.core import setup

version = '0.1.0'

setup(
    name="async_mysql",
    version=version,
    keywords=["mysql", "tornado", "async_mysql"],
    long_description=open(os.path.join(os.path.dirname(__file__),"README.md"), "r").read(),
    description="Asynchronous library for accessing mysql built upon the tornado IOLoop.",
    author="Oleg Nechaev",
    author_email="lega911@gmail.com",
    url="http://github.com/lega911/async-mysql",
    license="Apache Software License",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
    ],
    packages=['async_mysql'],
    install_requires=['MySQLdb>=1.2.3', 'tornado'],
    requires=['MySQLdb (>=1.2.3)', 'tornado']
)
