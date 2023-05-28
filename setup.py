from setuptools import setup

setup(
    name="idr-client",
    version="1.0.0",
    packages=["app"],
    include_package_data=True,
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "idr-client = app.runtime.__main__:main",
        ],
    },
)
