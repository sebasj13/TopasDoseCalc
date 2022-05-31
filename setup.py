import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="topasdosecalc",
    version="1.0.1",
    author="Sebastian Schäfer",
    author_email="sebastian.schaefer@student.uni-halle.de",
    description="Merge and scale TOPAS DICOMS - calculate and compare DVHs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sebasj13/TopasDoseCalc",
    project_urls={"Bug Tracker": "https://github.com/sebasj13/TopasDoseCalc/issues",},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "numpy",
        "matplotlib",
        "topas2numpy",
        "pydicom",
        "dicompyler-core",
    ],
    packages=["topasdosecalc", "topasdosecalc.src"],
    scripts=["topasdosecalc/topasdosecalc.py"],
    entry_points={
        "console_scripts": ["topasdosecalc=topasdosecalc.topasdosecalc:topasdosecalc"],
    },
    keywords=["topas", "monte-carlo", "python", "simulation", "dvh", "dicom"],
    python_requires=">=3.8",
)
