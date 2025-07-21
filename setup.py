"""
Setup script for Aqueduct Automation System
"""

from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aqueduct-automation",
    version="1.0.0",
    author="Aqueduct Automation Team",
    author_email="",
    description="Advanced Path of Exile Aqueduct farming automation system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/aqueduct-automation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "full": [
            "PyAutoGUI>=0.9.54",
            "pynput>=1.7.6",
            "numpy>=1.21.0",
            "matplotlib>=3.5.0",
            "pillow>=9.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aqueduct-automation=aqueduct_automation.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "aqueduct_automation": ["configs/*.json"],
    },
    zip_safe=False,
) 