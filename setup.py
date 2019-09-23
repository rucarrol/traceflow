import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="traceflow.py",
    version="0.1",
    scripts=["traceflow.py"],
    author="Ruairi Carroll",
    author_email="ruairi.carroll@gmail.com",
    description="Python version of traceroute which is path aware",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="bernese",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        'BSD 3-Clause "New" or "Revised" License',
        "Operating System :: OS Independent",
    ],
)
