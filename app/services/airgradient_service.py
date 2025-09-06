import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class AirGradientService:
    """Service for interacting with AirGradient API"""
    
    def __init__(self):
        self.base_url = settings.AIRGRADIENT_API_BASE_URL
        self.api_token = settings.AIRGRADIENT_API_TOKEN
        self.timeout = 30.0
    
    def _get_date_range(self, hours_back: int = 1) -> tuple[str, str]:
        """
        Get date range in ISO 8601 format with UTC offset
        
        Args:
            hours_back: Number of hours back from now to start the range
            
        Returns:
            Tuple of (from_date_str, to_date_str)
        """
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=hours_back)
        
        from_date_str = start_time.strftime("%Y%m%dT%H%M%SZ")
        to_date_str = now.strftime("%Y%m%dT%H%M%SZ")
        
        return from_date_str, to_date_str
    
    def _get_last_hour_date_range(self) -> tuple[str, str]:
        """
        Get date range for the last hour in ISO 8601 format with UTC offset
        
        Returns:
            Tuple of (from_date_str, to_date_str)
        """
        return self._get_date_range(hours_back=1)
    
    def _get_historical_date_range(self, days_back: int = 130) -> tuple[str, str]:
        """
        Get historical date range in ISO 8601 format with UTC offset
        
        Args:
            days_back: Number of days back from now to start the range
            
        Returns:
            Tuple of (from_date_str, to_date_str)
        """
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=days_back)
        
        from_date_str = start_time.strftime("%Y%m%dT%H%M%SZ")
        to_date_str = now.strftime("%Y%m%dT%H%M%SZ")
        
        return from_date_str, to_date_str
    
    def _format_datetime_for_api(self, dt: datetime) -> str:
        """
        Format datetime object for AirGradient API
        
        Args:
            dt: Datetime object (should be timezone-aware)
            
        Returns:
            Formatted datetime string for API
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y%m%dT%H%M%SZ")
    
    async def fetch_location_data(self, location_id: int) -> List[Dict[str, Any]]:
        """
        Fetch air quality data for a specific location from AirGradient API
        
        Args:
            location_id: The location ID to fetch data for
            
        Returns:
            List of measurement data points
            
        Raises:
            httpx.HTTPError: If API request fails
            Exception: For other errors
        """
        try:
            from_date_str, to_date_str = self._get_last_hour_date_range()
            
            url = f"{self.base_url}/locations/{location_id}/measures/past"
            params = {
                "token": self.api_token,
                "from": from_date_str,
                "to": to_date_str
            }
            
            logger.info(f"Fetching data for location {location_id} from {from_date_str} to {to_date_str}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not isinstance(data, list):
                    logger.warning(f"Unexpected response format for location {location_id}: {type(data)}")
                    return []
                
                logger.info(f"Fetched {len(data)} data points for location {location_id}")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching data for location {location_id}: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error fetching data for location {location_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching data for location {location_id}: {str(e)}")
            raise
    
    async def fetch_multiple_locations_data(self, location_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        """
        Fetch air quality data for multiple locations
        
        Args:
            location_ids: List of location IDs to fetch data for
            
        Returns:
            Dictionary mapping location_id to list of measurement data points
        """
        results = {}
        
        for location_id in location_ids:
            try:
                data = await self.fetch_location_data(location_id)
                results[location_id] = data
            except Exception as e:
                logger.error(f"Failed to fetch data for location {location_id}: {str(e)}")
                results[location_id] = []
                
        return results
    
    async def fetch_location_data_range(
        self, 
        location_id: int, 
        from_date: datetime, 
        to_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch air quality data for a specific location and date range from AirGradient API
        
        Args:
            location_id: The location ID to fetch data for
            from_date: Start date for data range (timezone-aware)
            to_date: End date for data range (timezone-aware)
            
        Returns:
            List of measurement data points
            
        Raises:
            httpx.HTTPError: If API request fails
            Exception: For other errors
        """
        try:
            from_date_str = self._format_datetime_for_api(from_date)
            to_date_str = self._format_datetime_for_api(to_date)
            
            url = f"{self.base_url}/locations/{location_id}/measures/past"
            params = {
                "token": self.api_token,
                "from": from_date_str,
                "to": to_date_str
            }
            
            logger.info(f"Fetching data for location {location_id} from {from_date_str} to {to_date_str}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if not isinstance(data, list):
                    logger.warning(f"Unexpected response format for location {location_id}: {type(data)}")
                    return []
                
                logger.info(f"Fetched {len(data)} data points for location {location_id}")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching data for location {location_id}: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout error fetching data for location {location_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching data for location {location_id}: {str(e)}")
            raise
    
    async def fetch_multiple_locations_data_range(
        self, 
        location_ids: List[int], 
        from_date: datetime, 
        to_date: datetime
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Fetch air quality data for multiple locations within a date range
        
        Args:
            location_ids: List of location IDs to fetch data for
            from_date: Start date for data range (timezone-aware)
            to_date: End date for data range (timezone-aware)
            
        Returns:
            Dictionary mapping location_id to list of measurement data points
        """
        results = {}
        
        for location_id in location_ids:
            try:
                data = await self.fetch_location_data_range(location_id, from_date, to_date)
                results[location_id] = data
            except Exception as e:
                logger.error(f"Failed to fetch data for location {location_id}: {str(e)}")
                results[location_id] = []
                
        return results


airgradient_service = AirGradientService()