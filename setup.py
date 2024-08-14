from setuptools import setup, find_packages
import os

def parse_requirements(filename):
    with open(filename, 'r') as file:
        return file.read().splitlines()

# Function to read the version from the version file
def get_version():
    version_file = os.path.join('starcompute', '__version__.py')
    version_vars = {}
    with open(version_file) as f:
        exec(f.read(), version_vars)
    return version_vars['__version__']


setup(
    name="starcompute",  # The main package name
    version=get_version(),  # Replace with your project's version
    description="Enables remote execution of tasks in a star topology.",  # Replace with a brief description
    author="Shah Rukh Qasim",  # Replace with your name
    author_email="shah.rukh.qasim@cern.ch",  # Replace with your email
    url="https://github.com/shahrukhqasim/StarCompute",  # Replace with your project's URL
    packages=find_packages(),  # Automatically finds all packages inside starcompute/
    install_requires=parse_requirements('requirements.txt'),  # Read dependencies from requirements.txt
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
