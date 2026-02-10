"""KernelSight - Setup configuration"""

from setuptools import setup, find_packages

setup(
    name="kernelsight",
    version="1.0.0",
    description="Lightweight container management with cgroups and namespaces",
    author="KernelSight Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "websockets>=11.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "kernelsight=kernelsight.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Systems Administration",
    ],
)
