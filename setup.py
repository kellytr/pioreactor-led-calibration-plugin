# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(
    name="led_calibration_plugin",
    version="0.0.3",
    license="MIT",
    description="Calibrate your LEDs using an external light probe.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author_email="kelly@pioreactor.com",
    author="Kelly Tran",
    url="https://github.com/kellytr/led-calibration-plugin",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "pioreactor.plugins": "led_calibration_plugin = led_calibration_plugin"
    },
)