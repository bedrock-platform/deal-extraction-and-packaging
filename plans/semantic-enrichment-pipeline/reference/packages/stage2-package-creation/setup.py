"""
Setup script for Package Creation package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="package-creation-package",
    version="1.0.0",
    author="Your Name",
    description="A standalone Python package for creating intelligent audience packages from enriched deals using semantic clustering and LLM-based grouping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "sentence-transformers>=2.0.0",
        "scikit-learn>=1.0.0",
        "langchain-google-genai>=1.0.0",
        "numpy>=1.20.0",
    ],
)
