from setuptools import setup, find_packages

setup(
    name="ChatStream",
    version="0.1.1",
    author="Tom Misawa",
    author_email="riversun.org@gmail.com",
    description="Streaming chat server building blocks for FastAPI/Starlette",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/riversun/ChatStream",
    packages=find_packages(exclude=["tests.*", "tests", "examples.*", "examples"]),
    tests_require=["pytest", "httpx"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch",
        "transformers"
        "fastapi",
        "fastsession",
        "tokflow"
    ]
)
