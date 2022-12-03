from pathlib import Path

from setuptools import find_packages
from setuptools import setup

project_name = "GooseHDF5"

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name=project_name,
    license="MIT",
    author="Tom de Geus",
    author_email="tom@geus.me",
    description="Wrapper around h5py",
    long_description=long_description,
    keywords="HDF5, h5py",
    url=f"https://github.com/tdegeus/{project_name:s}",
    packages=find_packages(exclude=["tests"]),
    use_scm_version={"write_to": f"{project_name}/_version.py"},
    setup_requires=["setuptools_scm"],
    install_requires=["click", "h5py", "prettytable", "pyyaml", "termcolor"],
    entry_points={
        "console_scripts": [
            f"G5check = {project_name}.cli.G5check:main",
            f"G5compare = {project_name}:_G5compare_cli",
            f"G5list = {project_name}:_G5list_cli",
            f"G5modify = {project_name}:_G5modify_cli",
            f"G5print = {project_name}:_G5print_cli",
            f"G5repack = {project_name}.cli.G5repack:main",
            f"G5repair = {project_name}.cli.G5repair:main",
        ]
    },
)
