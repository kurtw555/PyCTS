import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from weather.cache import WeatherCache
from weather.models import PointMetadata
from weather.service import WeatherService


class WeatherCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "weather_cache.sqlite3")
        self.cache = WeatherCache(self.db_path, ttl_minutes=15)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_forecast_respects_ttl_and_allow_stale(self):
        payload = {
            "updated": "2026-01-01T00:00:00+00:00",
            "units": "us",
            "periods": [],
        }
        key = "daily::example"
        self.cache.set_forecast(key, payload)

        fresh = self.cache.get_forecast(key)
        self.assertIsNotNone(fresh)
        self.assertTrue(fresh["_cache_fresh"])

        stale_time = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "UPDATE forecast_cache SET created_at = ? WHERE key = ?",
                (stale_time, key),
            )
            conn.commit()
        finally:
            conn.close()

        stale_rejected = self.cache.get_forecast(key, allow_stale=False)
        self.assertIsNone(stale_rejected)

        stale_allowed = self.cache.get_forecast(key, allow_stale=True)
        self.assertIsNotNone(stale_allowed)
        self.assertFalse(stale_allowed["_cache_fresh"])


class WeatherServiceFallbackTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "weather_cache.sqlite3")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_service_uses_stale_cache_when_live_fetch_fails(self):
        service = WeatherService(cache_path=self.db_path, user_agent="TestAgent/1.0")

        point = PointMetadata(
            latitude=37.7749,
            longitude=-122.4194,
            grid_id="MTR",
            grid_x=84,
            grid_y=105,
            forecast_url="https://api.weather.gov/gridpoints/MTR/84,105/forecast",
            forecast_hourly_url="https://api.weather.gov/gridpoints/MTR/84,105/forecast/hourly",
            forecast_grid_data_url="https://api.weather.gov/gridpoints/MTR/84,105",
            timezone="America/Los_Angeles",
        )
        service.cache.set_point(point)

        period_payload = {
            "name": "Now",
            "start_time": "2026-01-01T00:00:00+00:00",
            "end_time": "2026-01-01T01:00:00+00:00",
            "is_daytime": True,
            "temperature": 65,
            "temperature_unit": "F",
            "wind_speed": "5 mph",
            "wind_direction": "NW",
            "short_forecast": "Clear",
            "detailed_forecast": "Clear skies",
        }
        forecast_payload = {
            "updated": "2026-01-01T00:00:00+00:00",
            "units": "us",
            "periods": [period_payload],
        }

        daily_key = f"daily::{point.forecast_url}::us"
        hourly_key = f"hourly::{point.forecast_hourly_url}::us"
        service.cache.set_forecast(daily_key, forecast_payload)
        service.cache.set_forecast(hourly_key, forecast_payload)

        def fail_forecast(*_args, **_kwargs):
            raise RuntimeError("network down")

        service.nws_client.get_point_metadata = lambda lat, lon: point
        service.nws_client.get_forecast = fail_forecast

        bundle = service.get_weather_for_coordinates(37.7749, -122.4194)

        self.assertEqual(bundle.source, "cache")
        self.assertTrue(bundle.stale)
        self.assertEqual(len(bundle.daily.periods), 1)
        self.assertEqual(bundle.daily.periods[0].short_forecast, "Clear")


if __name__ == "__main__":
    unittest.main()
