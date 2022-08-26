# -*- coding: utf-8 -*-
from __future__ import annotations

from setuptools import find_packages
from setuptools import setup


setup(
    name="led_calibration_plugin",
    version="1.0.0",
    license="MIT",
    description="Calibrate your LEDs using an external light probe.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author_email="kelly@pioreactor.com",
    author="Kelly Tran",
    url="https://github.com/kellytr/pioreactor-led-calibration-plugin",
    packages=find_packages(),
    include_package_data=True,
    entry_points={"pioreactor.plugins": "led_calibration_plugin = led_calibration_plugin"},
)
