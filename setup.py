#!/usr/bin/env python3
"""
Setup script for Agentic Debugger
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agentic-debugger",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An intelligent incident analysis system using specialized AI agents",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agentic-debugger",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/agentic-debugger/issues",
        "Source": "https://github.com/yourusername/agentic-debugger",
        "Documentation": "https://github.com/yourusername/agentic-debugger#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agentic-debugger=debugger:main",
            "download-model=download_model:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "ai", "agents", "debugging", "incident-response", "root-cause-analysis",
        "monitoring", "reliability", "sre", "devops", "langchain", "llm"
    ],
)
