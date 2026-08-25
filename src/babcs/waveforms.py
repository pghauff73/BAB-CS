from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol


class Waveform(Protocol):
    def value(self, time: float) -> float: ...

    def breakpoints(self, start: float, end: float) -> list[float]: ...


def _inside(time: float, start: float, end: float) -> bool:
    tolerance = 32.0 * math.ulp(max(abs(time), abs(start), abs(end), 1.0))
    return time > start + tolerance and time <= end + tolerance


@dataclass(frozen=True)
class Constant:
    level: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.level):
            raise ValueError("constant waveform level must be finite")

    def value(self, time: float) -> float:
        del time
        return self.level

    def breakpoints(self, start: float, end: float) -> list[float]:
        del start, end
        return []


@dataclass(frozen=True)
class Sine:
    offset: float
    amplitude: float
    frequency: float
    phase_radians: float = 0.0
    delay: float = 0.0

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value)
            for value in (self.offset, self.amplitude, self.frequency, self.phase_radians, self.delay)
        ):
            raise ValueError("sine waveform parameters must be finite")

    def value(self, time: float) -> float:
        if time < self.delay:
            return self.offset
        angle = 2.0 * math.pi * self.frequency * (time - self.delay) + self.phase_radians
        return self.offset + self.amplitude * math.sin(angle)

    def breakpoints(self, start: float, end: float) -> list[float]:
        return [self.delay] if _inside(self.delay, start, end) else []


@dataclass(frozen=True)
class PiecewiseLinear:
    points: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if not self.points:
            raise ValueError("piecewise-linear waveform requires at least one point")
        if any(not math.isfinite(value) for point in self.points for value in point):
            raise ValueError("piecewise-linear points must be finite")
        if any(right[0] <= left[0] for left, right in zip(self.points, self.points[1:])):
            raise ValueError("piecewise-linear times must be strictly increasing")

    def value(self, time: float) -> float:
        if time <= self.points[0][0]:
            return self.points[0][1]
        for left, right in zip(self.points, self.points[1:]):
            if time <= right[0]:
                fraction = (time - left[0]) / (right[0] - left[0])
                return left[1] + fraction * (right[1] - left[1])
        return self.points[-1][1]

    def breakpoints(self, start: float, end: float) -> list[float]:
        return [time for time, _ in self.points if _inside(time, start, end)]


@dataclass(frozen=True)
class Pulse:
    low: float
    high: float
    delay: float
    rise: float
    width: float
    fall: float
    period: float = 0.0

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value)
            for value in (self.low, self.high, self.delay, self.rise, self.width, self.fall, self.period)
        ):
            raise ValueError("pulse parameters must be finite")
        if min(self.delay, self.rise, self.width, self.fall, self.period) < 0.0:
            raise ValueError("pulse times must be non-negative")
        if self.period and self.period < self.rise + self.width + self.fall:
            raise ValueError("pulse period is shorter than its active interval")

    def value(self, time: float) -> float:
        if time < self.delay:
            return self.low
        local = time - self.delay
        if self.period > 0.0:
            local %= self.period
        active_end = self.rise + self.width + self.fall
        if self.period == 0.0 and local > active_end:
            return self.low
        if self.rise > 0.0 and local < self.rise:
            return self.low + (self.high - self.low) * local / self.rise
        if local < self.rise + self.width:
            return self.high
        if self.fall > 0.0 and local < active_end:
            fraction = (local - self.rise - self.width) / self.fall
            return self.high + (self.low - self.high) * fraction
        return self.low

    def breakpoints(self, start: float, end: float) -> list[float]:
        offsets = (0.0, self.rise, self.rise + self.width, self.rise + self.width + self.fall)
        points: list[float] = []
        if self.period <= 0.0:
            for offset in offsets:
                point = self.delay + offset
                if _inside(point, start, end):
                    points.append(point)
            return sorted(set(points))

        first_cycle = max(0, math.floor((start - self.delay) / self.period) - 1)
        last_cycle = max(first_cycle, math.ceil((end - self.delay) / self.period) + 1)
        for cycle in range(first_cycle, last_cycle + 1):
            base = self.delay + cycle * self.period
            for offset in offsets:
                point = base + offset
                if _inside(point, start, end):
                    points.append(point)
        return sorted(set(points))


def _breakpoint_schedule_key(waveform: Waveform) -> tuple[object, ...] | None:
    if type(waveform) is Constant:
        return (Constant,)
    if type(waveform) is Sine:
        return (Sine, waveform.delay)
    if type(waveform) is PiecewiseLinear:
        return (PiecewiseLinear, *(time for time, _ in waveform.points))
    if type(waveform) is Pulse:
        return (
            Pulse,
            waveform.delay,
            waveform.rise,
            waveform.width,
            waveform.fall,
            waveform.period,
        )
    return None


def waveform_from_data(data: float | int | dict[str, object]) -> Waveform:
    if isinstance(data, (int, float)):
        return Constant(float(data))
    kind = str(data.get("type", "constant")).lower()
    if kind == "constant":
        return Constant(float(data["value"]))
    if kind == "sine":
        return Sine(
            offset=float(data.get("offset", 0.0)),
            amplitude=float(data["amplitude"]),
            frequency=float(data["frequency"]),
            phase_radians=float(data.get("phase_radians", 0.0)),
            delay=float(data.get("delay", 0.0)),
        )
    if kind in {"pwl", "piecewise_linear"}:
        raw_points = data["points"]
        if not isinstance(raw_points, list):
            raise ValueError("piecewise-linear points must be a list")
        points = tuple((float(point[0]), float(point[1])) for point in raw_points)
        return PiecewiseLinear(points)
    if kind == "pulse":
        return Pulse(
            low=float(data.get("low", 0.0)),
            high=float(data["high"]),
            delay=float(data.get("delay", 0.0)),
            rise=float(data.get("rise", 0.0)),
            width=float(data["width"]),
            fall=float(data.get("fall", 0.0)),
            period=float(data.get("period", 0.0)),
        )
    raise ValueError(f"unknown waveform type: {kind}")
