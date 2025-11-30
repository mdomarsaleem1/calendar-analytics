"""Setup configuration for calendar-analytics package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="calendar-analytics",
    version="1.0.0",
    author="Calendar Analytics Team",
    description="A comprehensive analytics platform for Outlook 365 calendar data with HRIS integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/calendar-analytics",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.10",
    install_requires=[
        # No external dependencies required - uses only standard library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "viz": [
            "matplotlib>=3.7.0",
            "pandas>=2.0.0",
            "plotly>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "calendar-analytics=calendar_analytics.cli:main",
        ],
    },
)
