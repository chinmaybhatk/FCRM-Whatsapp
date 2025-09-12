from setuptools import setup, find_packages

# get version from __version__ variable in whatsapp_calling/__init__.py
from whatsapp_calling import __version__ as version

setup(
    name="whatsapp_calling",
    version=version,
    description="WebRTC voice calling integration with WhatsApp Business API for FrappeCRM",
    author="FrappeCRM",
    author_email="admin@frappecrm.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        "requests>=2.28.0",
        "PyJWT>=2.4.0",
    ]
)