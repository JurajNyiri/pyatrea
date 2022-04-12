import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyatrea",
    version="0.9.1",
    author="Juraj Nyíri",
    author_email="juraj.nyiri@gmail.com",
    description="Python library for communication with Atrea ventilation units",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JurajNyiri/pyatrea",
    packages=setuptools.find_packages(),
    install_requires=["requests", "demjson"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
