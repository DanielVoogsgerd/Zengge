from setuptools import setup

url = "https://github.com/DanielVoogsgerd/Zengge"
version = "0.0.1-devel"
readme = open('README.md').read()

setup(
    name="Zengge",
    packages=["zengge"],
    version=version,
    description="Providesm a clear interface for interacting with Zengge lightbulbs",
    long_description=readme,
    include_package_data=True,
    author="Daniel Voogsgerd",
    author_email="daniel@voogsgerd.nl",
    url=url,
    install_requires=[],
    # download_url="{}/tarball/{}".format(url, version),
    license="ISC"
)
