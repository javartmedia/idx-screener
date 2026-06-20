from setuptools import setup, find_packages

setup(
    name="idx-screener",
    version="1.0.0",
    description="IDX Intraday Stock Screener - Beli Pagi Jual Sore",
    author="IDX Screener",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.0",
        "rich>=13.0",
        "pandas>=2.0",
        "pandas-ta>=0.3.14b0",
        "requests>=2.31",
        "beautifulsoup4>=4.12",
        "python-telegram-bot>=20.0",
        "schedule>=1.2",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "idx-screener=cli:main",
        ],
    },
    python_requires=">=3.10",
)
