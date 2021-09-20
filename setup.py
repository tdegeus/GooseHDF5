from setuptools import find_packages
from setuptools import setup

setup(
    name="GooseHDF5",
    license="MIT",
    author="Tom de Geus",
    author_email="tom@geus.me",
    description="Wrapper around h5py",
    long_description="Wrapper around h5py",
    keywords="HDF5, h5py",
    url="https://github.com/tdegeus/GooseHDF5",
    packages=find_packages(),
    use_scm_version={"write_to": "GooseHDF5/_version.py"},
    setup_requires=["setuptools_scm"],
    install_requires=["h5py", "click"],
    entry_points={
        "console_scripts": [
            "G5check = GooseHDF5.cli.G5check:main",
            "G5compare = GooseHDF5.cli.G5compare:main",
            "G5list = GooseHDF5.cli.G5list:main",
            "G5print = GooseHDF5.cli.G5print:main",
            "G5repack = GooseHDF5.cli.G5repack:main",
            "G5repair = GooseHDF5.cli.G5repair:main",
        ]
    },
)
