from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ApiProblem:
    type: str
    title: str
    status: int
    detail: str
    instance: str = ""
    correlation_id: str = ""


@dataclass
class PointMetadata:
    latitude: float
    longitude: float
    grid_id: str
    grid_x: int
    grid_y: int
    forecast_url: str
    forecast_hourly_url: str
    forecast_grid_data_url: str
    timezone: str


@dataclass
class ForecastPeriod:
    name: str
    start_time: str
    end_time: str
    is_daytime: bool
    temperature: Optional[float]
    temperature_unit: str
    wind_speed: str
    wind_direction: str
    short_forecast: str
    detailed_forecast: str

    @classmethod
    def from_api(cls, payload: dict) -> "ForecastPeriod":
        return cls(
            name=payload.get("name", ""),
            start_time=payload.get("startTime", ""),
            end_time=payload.get("endTime", ""),
            is_daytime=bool(payload.get("isDaytime", False)),
            temperature=payload.get("temperature"),
            temperature_unit=payload.get("temperatureUnit", ""),
            wind_speed=payload.get("windSpeed", ""),
            wind_direction=payload.get("windDirection", ""),
            short_forecast=payload.get("shortForecast", ""),
            detailed_forecast=payload.get("detailedForecast", ""),
        )


@dataclass
class ForecastData:
    updated: str
    units: str
    periods: list[ForecastPeriod]


@dataclass
class WeatherBundle:
    latitude: float
    longitude: float
    point_metadata: Optional[PointMetadata]
    daily: ForecastData
    hourly: ForecastData
    source: str
    stale: bool
    retrieved_at: str

    @staticmethod
    def empty(latitude: float, longitude: float, source: str = "unavailable") -> "WeatherBundle":
        empty_data = ForecastData(updated="", units="us", periods=[])
        return WeatherBundle(
            latitude=latitude,
            longitude=longitude,
            point_metadata=None,
            daily=empty_data,
            hourly=empty_data,
            source=source,
            stale=True,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )

    def summary_lines(self) -> list[str]:
        lines = []
        if self.hourly.periods:
            now = self.hourly.periods[0]
            temp = "n/a" if now.temperature is None else f"{now.temperature}{now.temperature_unit}"
            lines.append(f"Now: {temp}, {now.short_forecast}")
        if self.daily.periods:
            today = self.daily.periods[0]
            temp = "n/a" if today.temperature is None else f"{today.temperature}{today.temperature_unit}"
            lines.append(f"Today ({today.name}): {temp}, {today.short_forecast}")
        lines.append("Source: stale cache" if self.stale else "Source: live API")
        return lines
