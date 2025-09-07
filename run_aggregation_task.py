#!/usr/bin/env python3
"""
Manual runner for the 30-minute data aggregation task

Usage:
    python run_aggregation_task.py
    
This script will run the scheduled 30-minute data aggregation task once,
aggregating 5-minute AQI data into 30-minute averages for all locations.
"""

import asyncio
import sys
import logging
from datetime import datetime

# Configure logging for the script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print a nice banner for the task runner"""
    print("=" * 60)
    print("📊 30-Minute Data Aggregation Task Runner")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_footer(success: bool, duration: float):
    """Print completion banner"""
    print()
    print("=" * 60)
    if success:
        print("✅ Task completed successfully!")
    else:
        print("❌ Task failed!")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


async def main():
    """Main function to run the 30-minute data aggregation task"""
    start_time = datetime.now()
    success = False
    
    try:
        print_banner()
        
        # Import the task function
        logger.info("Importing task function...")
        from app.tasks.aggregation_task import aggregate_30_minute_data
        
        # Run the task
        logger.info("Starting 30-minute data aggregation task...")
        await aggregate_30_minute_data()
        
        success = True
        logger.info("Task completed successfully!")
        
    except ImportError as e:
        logger.error(f"Failed to import task function: {e}")
        logger.error("Make sure you're running from the project root directory")
        logger.error("and that the virtual environment is activated")
        
    except Exception as e:
        logger.error(f"Task failed with error: {e}", exc_info=True)
        
    finally:
        # Calculate duration and print footer
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print_footer(success, duration)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Task interrupted by user")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)