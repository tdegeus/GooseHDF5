from setuptools import find_packages
from setuptools import setup

project_name = "GooseHDF5"

setup(
    name=project_name,
    license="MIT",
    author="Tom de Geus",
    author_email="tom@geus.me",
    description="Wrapper around h5py",
    long_description="Wrapper around h5py",
    keywords="HDF5, h5py",
    url=f"https://github.com/tdegeus/{project_name:s}",
    packages=find_packages(),
    use_scm_version={"write_to": f"{project_name}/_version.py"},
    setup_requires=["setuptools_scm"],
    install_requires=["h5py", "click"],
    entry_points={
        "console_scripts": [
            f"G5check = {project_name}.cli.G5check:main",
            f"G5compare = {project_name}.cli.G5compare:main",
            f"G5list = {project_name}:_G5list_catch",
            f"G5print = {project_name}:_G5print_catch",
            f"G5repack = {project_name}.cli.G5repack:main",
            f"G5repair = {project_name}.cli.G5repair:main",
        ]
    },
)
