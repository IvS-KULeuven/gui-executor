from enum import IntEnum
from pathlib import Path

from gui_executor.exec import exec_task, FileName, Directory
from gui_executor.utypes import FixedList


@exec_task()
def capture_image(camera, exposure_time, aperture, filename, location):
    ...  # here the actual capturing of the image is done
    image = "Captured image not shown for privacy reasons..."
    ...  # here any further processing of the image can be done

    return image


@exec_task()
def capture_image_with_type_hints(
        camera: str, exposure_time: float, aperture: int,
        filename: str, location: str = "~/data/images"
):
    ...  # here the actual capturing of the image is done
    image = f"Captured image from camera '{camera}' with {exposure_time=} and {aperture=}."
    ...  # here any further processing of the image can be done

    return image


@exec_task(capture_response='new_image')
def capture_image_file_type_hints(
        camera: str, exposure_time: float, aperture: int,
        filename: FileName, location: Directory = Path("~/data/images")
):
    ...  # here the actual capturing of the image is done

    image = (
        f"Captured image from camera '{camera}' with {exposure_time=} and {aperture=}, "
        f"saving it as {filename=} at {location=}."
    )

    ...  # here any further processing of the image can be done

    return image

class CameraName(IntEnum):
    FRONT_DOOR = 1
    BACK_DOOR = 2
    GARDEN = 3
    GARDEN_HOUSE = 4
    BIRD_HOUSE_1 = 5
    BIRD_HOUSE_2 = 6

@exec_task(capture_response='new_image')
def capture_image_camera_name(
        camera: CameraName, exposure_time: float, aperture: int,
        filename: FileName, location: Directory = Path("~/data/images")
):
    ...  # here the actual capturing of the image is done

    image = (
        f"Captured image from camera '{camera.name}' with {exposure_time=} and {aperture=}, "
        f"saving it as {filename=} at {location=}."
    )

    ...  # here any further processing of the image can be done

    return image


@exec_task()
def save_observation(
        coordinates: FixedList([float, float], name="lat, long"),
        time: str,
        bird_name: str,
):
    """
    Saves the observation into the database.

    Args:
        coordinates (list): the longitude and latitude coordinates of the observation (decimal degrees)
        time (str): the time of the observation [YYYY/MM/DD HH:MM:SS]
        bird_name (str): the name of the bird

    """
    print(f"A {bird_name} was spotted at [{coordinates[0]:.6f}, {coordinates[1]:.6f}]")
