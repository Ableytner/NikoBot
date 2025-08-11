"""A module containing the Color class"""

from __future__ import annotations

class Color:
    """Class representing a single color."""

    def __init__(self, r: int, g: int, b: int, a: int):
        self._r = r
        self._g = g
        self._b = b
        self._a = a

    @staticmethod
    def from_rgb(r: int, g: int, b: int) -> Color:
        """
        Construct a new Color object from rgb values.

        Red: between 0 and 255
        Green: between 0 and 255
        Blue: between 0 and 255
        """

        _ensure_bounds(r, 0, 255)
        _ensure_bounds(g, 0, 255)
        _ensure_bounds(b, 0, 255)

        return Color(r, g, b, 255)

    @staticmethod
    def from_rgba(r: int, g: int, b: int, a: int) -> Color:
        """
        Construct a new Color object from rgba values.

        Red: between 0 and 255
        Green: between 0 and 255
        Blue: between 0 and 255
        Alpha: between 0 and 255
        """

        _ensure_bounds(r, 0, 255)
        _ensure_bounds(g, 0, 255)
        _ensure_bounds(b, 0, 255)
        _ensure_bounds(a, 0, 255)

        return Color(r, g, b, a)

    def rgb(self) -> tuple[int, int, int]:
        """
        Return this color in rgb format.
        
        Red: between 0 and 255
        Green: between 0 and 255
        Blue: between 0 and 255
        """

        _ensure_bounds(self._r, 0, 255)
        _ensure_bounds(self._g, 0, 255)
        _ensure_bounds(self._b, 0, 255)

        return (self._r, self._g, self._b)

    def rgba(self) -> tuple[int, int, int, int]:
        """
        Return this color in rgba format.
        
        Red: between 0 and 255
        Green: between 0 and 255
        Blue: between 0 and 255
        Alpha: between 0 and 255
        """

        _ensure_bounds(self._r, 0, 255)
        _ensure_bounds(self._g, 0, 255)
        _ensure_bounds(self._b, 0, 255)
        _ensure_bounds(self._a, 0, 255)

        return (self._r, self._g, self._b, self._a)

    def hex(self) -> str:
        """Return this color in hexadecimal format."""

        return f"#{self._r//16:x}{self._r%16:x}{self._g//16:x}{self._g%16:x}{self._b//16:x}{self._b%16:x}"

    def hsv(self) -> tuple[float, float, float]:
        """
        Return this color in hsv format.
        
        Hue: between 0 and 360 (degrees °)
        Saturation: between 0 and 100 (percent %)
        Value: between 0 and 100 (percent %)
        """

        # algorithm from https://math.stackexchange.com/q/556341

        r = self._r / 255
        g = self._g / 255
        b = self._b / 255

        cmax = max(r, g, b)
        cmin = min(r, g, b)
        diff = cmax - cmin

        if diff == 0:
            hue = 0.0
        elif cmax == r:
            hue = 60 * (((g - b) / diff) % 6)
        elif cmax == g:
            hue = 60 * (((b - r) / diff) + 2)
        elif cmax == b:
            hue = 60 * (((r - g) / diff) + 4)
        else:
            raise RuntimeError()

        if cmax == 0:
            saturation = 0.0
        else:
            saturation = diff / cmax

        hue = round(hue, 2)
        saturation = round(saturation * 100, 2)
        value = round(cmax * 100, 2)

        _ensure_bounds(hue, 0, 360)
        _ensure_bounds(saturation, 0, 100)
        _ensure_bounds(value, 0, 100)

        return (hue, saturation, value)

def _ensure_bounds(value: int | float, lower: int | float, upper: int | float) -> None:
    if not value >= lower and value <= upper:
        raise ValueError(f"Violated bounds: {lower} <= {value} <= {upper}")
