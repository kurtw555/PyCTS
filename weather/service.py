from datetime import datetime, timezone
import os
from pathlib import Path

from .cache import WeatherCache
from .clients import GeocodingClient, NWSClient
from .models import ForecastData, ForecastPeriod, WeatherBundle
from .transport import HttpTransport


class WeatherService:
    def __init__(
        self,
        user_agent: str | None = None,
        cache_path: str | None = None,
    ):
        resolved_agent = user_agent or os.getenv(
            "PYCTS_WEATHER_USER_AGENT",
            "PyCTSWeatherApp/1.0 (contact: set-PYCTS_WEATHER_USER_AGENT)",
        )
        self.user_agent = resolved_agent

        default_cache = Path.home() / ".pycts" / "weather_cache.sqlite3"
        self.cache_path = cache_path or str(default_cache)

        self.transport = HttpTransport(user_agent=resolved_agent)
        self.nws_client = NWSClient(self.transport)
        self.geocoder = GeocodingClient(self.transport)
        self.cache = WeatherCache(self.cache_path, ttl_minutes=15)

    def get_weather_for_place(self, query: str, units: str = "us") -> WeatherBundle:
        latitude, longitude = self.geocoder.geocode(query)
        return self.get_weather_for_coordinates(latitude, longitude, units=units)

    def get_weather_for_coordinates(self, latitude: float, longitude: float, units: str = "us") -> WeatherBundle:
        latitude = round(latitude, 4)
        longitude = round(longitude, 4)

        cached_point = self.cache.get_point(latitude, longitude)
        point = cached_point or self.nws_client.get_point_metadata(latitude, longitude)
        if not cached_point:
            self.cache.set_point(point)

        daily_key = f"daily::{point.forecast_url}::{units}"
        hourly_key = f"hourly::{point.forecast_hourly_url}::{units}"

        try:
            daily = self.nws_client.get_forecast(point.forecast_url, units)
            hourly = self.nws_client.get_forecast(point.forecast_hourly_url, units)

            self.cache.set_forecast(daily_key, self._forecast_to_payload(daily))
            self.cache.set_forecast(hourly_key, self._forecast_to_payload(hourly))

            return WeatherBundle(
                latitude=latitude,
                longitude=longitude,
                point_metadata=point,
                daily=daily,
                hourly=hourly,
                source="live_api",
                stale=False,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception:
            daily_cached = self.cache.get_forecast(daily_key, allow_stale=True)
            hourly_cached = self.cache.get_forecast(hourly_key, allow_stale=True)
            if daily_cached and hourly_cached:
                return WeatherBundle(
                    latitude=latitude,
                    longitude=longitude,
                    point_metadata=point,
                    daily=self._payload_to_forecast(daily_cached),
                    hourly=self._payload_to_forecast(hourly_cached),
                    source="cache",
                    stale=True,
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                )
            return WeatherBundle.empty(latitude, longitude, source="unavailable")

    def _forecast_to_payload(self, forecast: ForecastData) -> dict:
        return {
            "updated": forecast.updated,
            "units": forecast.units,
            "periods": [period.__dict__ for period in forecast.periods],
        }

    def _payload_to_forecast(self, payload: dict) -> ForecastData:
        periods = payload.get("periods", [])
        return ForecastData(
            updated=payload.get("updated", ""),
            units=payload.get("units", "us"),
            periods=[ForecastPeriod(**p) for p in periods],
        )
