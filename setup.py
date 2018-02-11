from setuptools import setup, find_packages
from setuptools_scm import get_version
my_version = get_version()

setup(
    name="pdftags",
    packages=find_packages(),
    use_scm_version=True,
    version=my_version,
    setup_requires=['setuptools_scm', ],
    install_requires=['appdirs',
                      'sqlalchemy',
                      'tqdm'],
    scripts=['pdftags'],

    author="Arun Persaud",
    author_email="arun@nubati.net",
    description="Make hierachical tagging of pdfs easy",
    license="GPL",
    keywords="pdf files tagging",
)
