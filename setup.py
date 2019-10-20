import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="traceflow",
    version="0.3",
    author="Ruairi Carroll",
    author_email="ruairi.carroll@gmail.com",
    description="Python version of traceroute which is path aware",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rucarrol/traceflow",
    python_requires=">=3.5",
    packages=["traceflow"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    package_data={"": ["var/*.html"]},
    entry_points={"console_scripts": ["traceflow=traceflow.__main__:main"]},
)
