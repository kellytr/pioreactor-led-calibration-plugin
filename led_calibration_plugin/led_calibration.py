# -*- coding: utf-8 -*-
from __future__ import annotations

import click
from msgspec.json import decode
from msgspec.json import encode
from pioreactor import structs
from pioreactor import types as pt
from pioreactor.actions.led_intensity import led_intensity
from pioreactor.pubsub import publish
from pioreactor.utils import is_pio_job_running
from pioreactor.utils import local_persistant_storage
from pioreactor.utils import publish_ready_to_disconnected_state
from pioreactor.utils.timing import current_utc_timestamp
from pioreactor.whoami import get_latest_testing_experiment_name
from pioreactor.whoami import get_unit_name
from pioreactor.whoami import UNIVERSAL_EXPERIMENT


class LEDCalibration(structs.Calibration):
    timestamp: str
    name: str
    max_intensity: float
    min_intensity: float
    min_lightprobe_readings: float
    max_lightprobe_readings: float
    curve_data_: list[float]
    curve_type: str
    lightprobe_readings: list[float]
    led_intensities: list[float]
    channel: pt.LedChannel


def introduction():
    click.clear()
    click.echo(
        """This routine will calibrate the LEDs on your current Pioreactor using an external lightprobe. You'll need:
    1. A Pioreactor
    2. At least 10mL of your media
    3. A sperical light probe (type of photometer)
"""
    )


def get_metadata_from_user():
    with local_persistant_storage("led_calibrations") as cache:
        while True:
            name = click.prompt("Provide a name for this calibration", type=str).strip()
            if name not in cache:
                break
            else:
                if click.confirm("❗️ Name already exists. Do you wish to overwrite?"):
                    break

    channel = click.prompt("Which channel is being used?", type=click.Choice(["A", "B", "C", "D"]))

    click.confirm(
        f"Confirm using channel {channel} with X2 or X3 pocket positions in the Pioreactor",
        abort=True,
        default=True,
    )

    return name, channel


def setup_probe_instructions():
    click.clear()
    click.echo(
        """ Setting up:
    1. Add 10ml of your media into the glass vial.
    2. Place into Pioreactor.
    3. Hold your light probe in place within the vial, submerged in your media.
"""
    )


def plot_data(x, y, title, x_min=None, x_max=None, interpolation_curve=None, highlight_recent_point=True):
    import plotext as plt

    plt.clf()

    if interpolation_curve:
        plt.plot(x, [interpolation_curve(x_) for x_ in x], color=204)

    plt.scatter(x, y)

    if highlight_recent_point:
        plt.scatter([x[-1]], [y[-1]], color=204)

    plt.theme("pro")
    plt.title(title)
    plt.plot_size(105, 22)
    plt.xlim(x_min, x_max)
    plt.show()


def start_recording(channel, min_intensity, max_intensity):
    led_intensity(
        desired_state={"A": 0, "B": 0, "C": 0, "D": 0},
        unit=get_unit_name(),
        experiment=get_latest_testing_experiment_name(),
        verbose=False,
    )

    lightprobe_readings: list[float] = []
    led_intensities_to_test = [
        min_intensity,
        min_intensity * 5.0,
        min_intensity * 10.0,
        min_intensity * 15.0,
    ] + [max_intensity * 0.85, max_intensity * 0.90, max_intensity * 0.95, max_intensity]

    for i, intensity in enumerate(led_intensities_to_test):
        if i != 0:
            plot_data(
                led_intensities_to_test[:i],
                lightprobe_readings,
                title="LED Calibration (ongoing)",
                x_min=min_intensity,
                x_max=max_intensity,
            )

        click.echo(click.style(f"Changing the LED intensity to {intensity}%", fg="green"))
        click.echo("Record the light intensity reading from your light probe.")

        led_intensity(
            desired_state={channel: intensity},
            unit=get_unit_name(),
            experiment=get_latest_testing_experiment_name(),
        )

        r = click.prompt(
            click.style("Enter reading on light probe", fg="green"),
            confirmation_prompt=click.style("Repeat for confirmation", fg="green"),
            type=float,
        )

        lightprobe_readings.append(r)
        click.clear()
        click.echo()

    led_intensity(
        desired_state={"A": 0, "B": 0, "C": 0, "D": 0},
        unit=get_unit_name(),
        experiment=get_latest_testing_experiment_name(),
        verbose=False,
    )

    return lightprobe_readings, led_intensities_to_test


def calculate_curve_of_best_fit(lightprobe_readings, led_intensities, degree):
    import numpy as np

    try:
        coefs = np.polyfit(led_intensities, lightprobe_readings, deg=degree).tolist()
    except Exception:
        click.echo("Unable to fit.")
        coefs = np.zeros(degree)

    return coefs, "poly"


def show_results_and_confirm_with_user(curve, curve_type, lightprobe_readings, led_intensities):
    click.clear()

    if curve_type == "poly":
        import numpy as np

        def curve_callable(x):
            return np.polyval(curve, x)

    else:
        curve_callable = None

    plot_data(
        led_intensities,
        lightprobe_readings,
        title="LED calibration with line of best fit",
        interpolation_curve=curve_callable,
        highlight_recent_point=False,
    )

    click.confirm("Confirm and save to disk?", abort=True, default=True)


def save_results_locally(
    curve_data_: list[float],
    curve_type: str,
    lightprobe_readings: list[float],
    led_intensities: list[float],
    name: str,
    max_intensity: float,
    min_intensity: float,
    channel,
) -> structs.LEDCalibration:
    data_blob = LEDCalibration(
        timestamp=current_utc_timestamp(),
        name=name,
        max_intensity=max_intensity,
        min_intensity=0,
        min_lightprobe_readings=min(lightprobe_readings),
        max_lightprobe_readings=max(lightprobe_readings),
        curve_data_=curve_data_,
        curve_type=curve_type,
        lightprobe_readings=lightprobe_readings,
        led_intensities=led_intensities,
        channel=channel,
    )

    with local_persistant_storage("led_calibrations") as cache:
        cache[name] = encode(data_blob)

    with local_persistant_storage("current_led_calibration") as cache:
        cache[channel] = encode(data_blob)

    # send to MQTT
    publish(f"pioreactor/{get_unit_name()}/{UNIVERSAL_EXPERIMENT}/calibrations", encode(data_blob))

    return data_blob


## general schematic of what's gonna happen
def led_calibration(min_intensity, max_intensity):
    unit = get_unit_name()
    experiment = get_latest_testing_experiment_name()

    if is_pio_job_running("stirring", "od_reading"):
        raise ValueError("Stirring and OD reading should be turned off.")

    with publish_ready_to_disconnected_state(unit, experiment, "led_calibration"):

        introduction()
        name, channel = get_metadata_from_user()
        setup_probe_instructions()

        # retrieve readings from the light probe and list of led intensities
        lightprobe_readings, led_intensities = start_recording(channel, min_intensity, max_intensity)

        curve, curve_type = calculate_curve_of_best_fit(lightprobe_readings, led_intensities, 1)
        show_results_and_confirm_with_user(curve, curve_type, lightprobe_readings, led_intensities)

        data_blob = save_results_locally(
            curve,
            curve_type,
            lightprobe_readings,
            led_intensities,
            name,
            max_intensity,
            min_intensity,
            channel,
        )
        click.echo(click.style(f"Data for {name}", underline=True, bold=True))
        click.echo(data_blob)
        click.echo(f"Finished calibration of {name} ✅")
        return


def display_current() -> None:
    from pprint import pprint

    with local_persistant_storage("current_led_calibration") as c:
        if c.keys():
            for channel in c.keys():
                data_blob = decode(c[channel])
                lightprobe_readings = data_blob["lightprobe_readings"]
                led_intensities = data_blob["led_intensities"]
                name, channel = data_blob["name"], data_blob["channel"]
                plot_data(
                    led_intensities,
                    lightprobe_readings,
                    title=f"{name}, channel {channel}",
                    highlight_recent_point=False,
                )  # TODO: add interpolation curve
                click.echo(click.style(f"Data for {name}", underline=True, bold=True))
                pprint(data_blob)
                click.echo()
                click.echo()
                click.echo()
        else:
            click.echo("No calibrations exist. Please calibrate and try again.")


def change_current(name) -> None:
    try:
        with local_persistant_storage("led_calibrations") as c:
            calibration = decode(c[name], type=LEDCalibration)

        channel = calibration.channel
        with local_persistant_storage("current_led_calibration") as c:
            name_being_bumped = decode(c[channel], type=LEDCalibration).name
            c[channel] = encode(calibration)
        click.echo(f"Swapped {name_being_bumped} for {name} ✅")
    except Exception:
        click.echo("Failed to swap.")
        raise click.Abort()


def list_():
    click.secho(
        f"{'Name':15s} {'Timestamp':35s} {'Channel':20s}",
        bold=True,
    )
    with local_persistant_storage("led_calibrations") as c:
        for name in c.keys():
            try:
                cal = decode(c[name], type=LEDCalibration)
                click.secho(
                    f"{cal.name:15s} {cal.timestamp:35s} {cal.channel:20s}",
                )
            except Exception as e:
                raise e


### This part displays the current led calibration
@click.group(invoke_without_command=True, name="led_calibration")
@click.pass_context
@click.option("--min-intensity", type=float)
@click.option("--max-intensity", type=float)
def click_led_calibration(ctx, min_intensity, max_intensity):
    """
    Calibrate LED intensity.
    """
    if ctx.invoked_subcommand is None:
        if min_intensity is None and max_intensity is None:
            min_intensity, max_intensity = 1.0, 100.0
        elif (min_intensity is not None) and (max_intensity is not None):
            assert min_intensity < max_intensity, "min_intensity >= max_intensity"
        else:
            raise ValueError("min_intensity and max_intensity must both be set.")

        led_calibration(min_intensity, max_intensity)


@click_led_calibration.command(name="display_current")
def click_display_current():
    display_current()


@click_led_calibration.command(name="change_current")
@click.argument("name", type=click.STRING)
def click_change_current(name):
    change_current(name)


@click_led_calibration.command(name="list")
def click_list():
    list_()


if __name__ == "__main__":
    click_led_calibration()
