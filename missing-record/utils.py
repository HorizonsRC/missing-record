"""General utilities."""

import matplotlib
import pandas as pd


def get_hex_colour(normval, cmap="jet", invert=False, baw=False):
    """Return a hex colour from a matplotlib named cmap.

    Parameters
    ----------
    normval : float
        The normalised value between 0 and 1 to convert to a colour.
    cmap : str, optional
        The name of the matplotlib colormap to use, by default "jet".
    invert : bool, optional
        Invert the color, by default False.
    baw : bool, optional
        Use black and white color scheme, by default False.

    Returns
    -------
    str
        A hex colour string
    """
    # Return white if the value is NaN
    if pd.isna(normval):
        return "#ffffff"
    if normval <= 0:
        return "#ffffff"
    # Convert the value to a color
    colormap = matplotlib.colormaps.get(cmap)
    rgb_color = colormap(normval)

    hex_color = matplotlib.colors.rgb2hex(rgb_color)
    if invert:
        hex_color = invert_colour(hex_color, baw=baw)
    return hex_color

def invert_colour(hex_color, hsv=False, baw=False):
    """Invert a color from its hex code.

    Parameters
    ----------
    hex_color : str
        A hex colour code.
    hsv : bool, optional
        Use HSV color inversion, by default False.
    baw : bool, optional
        Use black and white color scheme, by default False.

    Returns
    -------
    str
        The inverted hex colour string
    """
    # Remove the '#' character from the hex code
    if hex_color[0] == "#":
        hex_color = hex_color[1:]
    else:
        raise ValueError("Invalid hex color code")

    # Convert 3-digit hex color to 6-digit hex color
    if len(hex_color) == 3:
        hex_color = "".join([char * 2 for char in hex_color])

    if len(hex_color) != 6:
        raise ValueError("Invalid hex color code")

    # Convert the hex color to RGB
    r = int(hex_color[:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:], 16)

    if hsv:
        # Convert the RGB to HSV
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        h, s, v = matplotlib.colors.rgb_to_hsv((r, g, b))
        h = (h + 0.5) % 1

        # Invert the hsv components
        i_h = 1 - h
        i_s = 1 - s
        i_v = 1 - v

        i_r, i_g, i_b = matplotlib.colors.hsv_to_rgb((i_h, i_s, i_v))

        i_r_hex = hex(int(i_r * 255))[2:].zfill(2)
        i_g_hex = hex(int(i_g * 255))[2:].zfill(2)
        i_b_hex = hex(int(i_b * 255))[2:].zfill(2)

        return f"#{i_r_hex}{i_g_hex}{i_b_hex}"

    # if black and white color scheme is selected (baw)
    if baw:
        # // https://stackoverflow.com/a/3943023/112731
        return (r * 0.299 + g * 0.587 + b * 0.114) > 186 and "#000000" or "#ffffff"

    # convert the RGB to inverted RGB, then to hex, padded with zeros
    i_r = hex(255 - r)[2:].zfill(2)
    i_g = hex(255 - g)[2:].zfill(2)
    i_b = hex(255 - b)[2:].zfill(2)

    return f"#{i_r}{i_g}{i_b}"
