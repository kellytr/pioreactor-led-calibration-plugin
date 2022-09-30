# -*- coding: utf-8 -*-
from __future__ import annotations

import time

import pytest
from msgspec.json import encode
from pioreactor.background_jobs.led_control import LEDController
from pioreactor.exc import CalibrationError
from pioreactor.utils import local_intermittent_storage
from pioreactor.utils import local_persistant_storage
from pioreactor.utils.timing import current_utc_timestamp
from pioreactor.whoami import get_unit_name

from .led_calibration import LEDCalibration


def pause(n=1) -> None:
    # to avoid race conditions when updating state
    time.sleep(n * 0.5)


def test_led_fails_if_calibration_not_present():
    experiment = "test_led_fails_if_calibration_not_present"
    unit = get_unit_name()

    with local_persistant_storage("led_calibrations") as cache:
        del cache["C"]
        del cache["D"]

    with pytest.raises(CalibrationError):

        with LEDController(
            "calibrated_light_dark_cycle",
            duration=0.01,
            light_intensity=-1,
            light_duration_hours=16,
            dark_duration_hours=8,
            unit=unit,
            experiment=experiment,
        ):

            pause(8)


def test_set_intensity_au_above_max() -> None:
    experiment = "test_set_intensity_au_above_max"
    unit = get_unit_name()

    with local_persistant_storage("current_led_calibration") as cache:
        cache["C"] = encode(
            LEDCalibration(
                timestamp=current_utc_timestamp(),
                name=experiment,
                max_intensity=100,
                min_intensity=0,
                min_lightprobe_readings=0,
                max_lightprobe_readings=1000,
                curve_data_=[1, 0],
                curve_type="poly",
                lightprobe_readings=[],
                led_intensities=[],
                channel="C",
            )
        )

        cache["D"] = encode(
            LEDCalibration(
                timestamp=current_utc_timestamp(),
                name=experiment,
                max_intensity=100,
                min_intensity=0,
                min_lightprobe_readings=0,
                max_lightprobe_readings=1000,
                curve_data_=[1, 0],
                curve_type="poly",
                lightprobe_readings=[],
                led_intensities=[],
                channel="D",
            )
        )

    with LEDController(
        "calibrated_light_dark_cycle",
        duration=0.01,
        light_intensity=1500,
        light_duration_hours=16,
        dark_duration_hours=8,
        unit=unit,
        experiment=experiment,
    ) as lc:

        assert lc.automation_job.light_intensity == 1500  # test returns light_intensity (au)

        lc.automation_job.set_light_intensity(2000)

        assert lc.automation_job.light_intensity == 2000


def test_set_intensity_au_negative() -> None:
    experiment = "test_set_intensity_au_negative"
    unit = get_unit_name()

    with local_persistant_storage("current_led_calibration") as cache:
        cache["C"] = encode(
            LEDCalibration(
                timestamp=current_utc_timestamp(),
                name=experiment,
                max_intensity=100,
                min_intensity=0,
                min_lightprobe_readings=0,
                max_lightprobe_readings=1000,
                curve_data_=[1, 0],
                curve_type="poly",
                lightprobe_readings=[],
                led_intensities=[],
                channel="C",
            )
        )

        cache["D"] = encode(
            LEDCalibration(
                timestamp=current_utc_timestamp(),
                name=experiment,
                max_intensity=100,
                min_intensity=0,
                min_lightprobe_readings=0,
                max_lightprobe_readings=1000,
                curve_data_=[10, 0],
                curve_type="poly",
                lightprobe_readings=[],
                led_intensities=[],
                channel="D",
            )
        )

    with LEDController(
        "calibrated_light_dark_cycle",
        duration=0.01,
        light_intensity=-1,
        light_duration_hours=16,
        dark_duration_hours=8,
        unit=unit,
        experiment=experiment,
    ) as lc:

        assert lc.automation_job.light_intensity == -1
        pause(8)

        with local_intermittent_storage("leds") as led_cache:
            assert float(led_cache["C"]) == 0.0
            assert float(led_cache["D"]) == 0.0


def test_set_curve_data_negative() -> None:
    experiment = "test_set_curve_data_negative"
    unit = get_unit_name()

    with local_persistant_storage("current_led_calibration") as cache:
        cache["C"] = encode(
            LEDCalibration(
                timestamp=current_utc_timestamp(),
                name=experiment,
                max_intensity=100,
                min_intensity=0,
                min_lightprobe_readings=0,
                max_lightprobe_readings=1000,
                curve_data_=[1, -4],
                curve_type="poly",
                lightprobe_readings=[],
                led_intensities=[],
                channel="C",
            )
        )

    with local_persistant_storage("current_led_calibration") as cache:
        cache["D"] = encode(
            LEDCalibration(
                timestamp=current_utc_timestamp(),
                name=experiment,
                max_intensity=100,
                min_intensity=0,
                min_lightprobe_readings=0,
                max_lightprobe_readings=1000,
                curve_data_=[1, -4],
                curve_type="poly",
                lightprobe_readings=[],
                led_intensities=[],
                channel="D",
            )
        )

    with LEDController(
        "calibrated_light_dark_cycle",
        duration=60,
        light_intensity=1,
        light_duration_hours=16,
        dark_duration_hours=8,
        unit=unit,
        experiment=experiment,
    ) as lc:
        assert lc.automation_job.light_intensity == 1
        pause(8)

        with local_intermittent_storage("leds") as led_cache:
            assert float(led_cache["C"]) == 5.0
            assert float(led_cache["D"]) == 5.0

        lc.automation_job.set_light_intensity(150)

        with local_intermittent_storage("leds") as led_cache:
            assert float(led_cache["C"]) == 100
            assert float(led_cache["D"]) == 100

        lc.automation_job.set_light_intensity(-5)

        with local_intermittent_storage("leds") as led_cache:
            assert float(led_cache["C"]) == 0
            assert float(led_cache["D"]) == 0
