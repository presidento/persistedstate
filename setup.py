import setuptools

setuptools.setup(
    name="persistedstate",
    version="22.04",
    scripts=[],
    author="Máté Farkas",
    author_email="fm@farkas-mate.hu",
    description="Persist state in editable text file",
    long_description_content_type="text/markdown",
    url="https://github.com/presidento/persistedstate",
    packages=["persistedstate"],
    package_data={"persistedstate": ["py.typed"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Utilities",
        "Typing :: Typed",
    ]
)
