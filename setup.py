from setuptools import setup, find_packages
import os

# Read version from __init__.py file
def get_version():
    version = {}
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "whatsapp_calling", "__init__.py")) as fp:
        exec(fp.read(), version)
    return version["__version__"]

# Read requirements from file
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="whatsapp_calling",
    version="1.0.1",
    description="WebRTC voice calling integration with WhatsApp Business API for FrappeCRM",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="FrappeCRM",
    author_email="admin@frappecrm.com",
    url="https://github.com/chinmaybhatk/FCRM-Whatsapp",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Frappe",
    ],
    python_requires=">=3.8",
)