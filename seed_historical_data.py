#!/usr/bin/env python3
"""
Historical data seeding script for Nettelhorst AQI Backend

This script seeds the database with historical AirGradient API data for the last 130 days.
It fetches data in batches to be efficient with API requests and memory usage.

Usage:
    python seed_historical_data.py [options]

Examples:
    # Seed with default settings (130 days)
    python seed_historical_data.py
    
    # Seed with custom parameters
    python seed_historical_data.py --days-back 90 --batch-size 14 --delay-requests 2.0
    
    # Skip API validation (faster start but riskier)
    python seed_historical_data.py --no-validate-api

Requirements:
    - Database must be created and migrations applied
    - Virtual environment must be activated
    - Environment variables must be set (DATABASE_URL, AIRGRADIENT_API_TOKEN)
    - Location data must be seeded first (run: python seed_database.py)
"""

import sys
import os
import logging
import argparse
from datetime import datetime

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.logging import setup_logging
from app.db.seed import seed_historical_data_sync, get_location_exists


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Seed database with historical AirGradient API data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Default: 130 days, 7-day batches
  %(prog)s --days-back 90           # Seed 90 days of data
  %(prog)s --batch-size 14          # Use 14-day batches
  %(prog)s --delay-requests 2.0     # 2-second delay between API requests
  %(prog)s --no-validate-api        # Skip API connectivity validation
  %(prog)s --verbose                # Enable debug logging
        """
    )
    
    parser.add_argument(
        '--days-back',
        type=int,
        default=130,
        help='Number of days back to fetch data (default: 130)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=7,
        help='Number of days to fetch per batch (default: 7)'
    )
    
    parser.add_argument(
        '--delay-requests',
        type=float,
        default=0.5,
        help='Delay between API requests in seconds (default: 0.5)'
    )
    
    parser.add_argument(
        '--delay-locations',
        type=float,
        default=1.0,
        help='Delay between processing locations in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--no-validate-api',
        action='store_true',
        help='Skip API connectivity validation before starting'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt and proceed with seeding'
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """Validate command line arguments"""
    errors = []
    
    if args.days_back <= 0:
        errors.append("--days-back must be greater than 0")
    
    if args.days_back > 365:
        errors.append("--days-back should not exceed 365 days for performance reasons")
    
    if args.batch_size <= 0:
        errors.append("--batch-size must be greater than 0")
    
    if args.batch_size > args.days_back:
        errors.append("--batch-size cannot be larger than --days-back")
    
    if args.delay_requests < 0:
        errors.append("--delay-requests cannot be negative")
    
    if args.delay_locations < 0:
        errors.append("--delay-locations cannot be negative")
    
    return errors


def estimate_operation_time(days_back: int, batch_size: int, delay_requests: float, delay_locations: float) -> str:
    """
    Estimate the total operation time
    
    Args:
        days_back: Number of days to fetch
        batch_size: Days per batch
        delay_requests: Delay between requests
        delay_locations: Delay between locations
        
    Returns:
        Formatted time estimate string
    """
    # Rough estimates based on typical API performance
    batches_per_location = (days_back + batch_size - 1) // batch_size  # Ceiling division
    api_time_per_batch = 2.0  # Rough estimate of API response time
    
    # Assume 1 location for now (can be updated when we check actual count)
    time_per_location = (batches_per_location * (api_time_per_batch + delay_requests)) + (batches_per_location - 1) * delay_requests
    
    # Add some buffer for processing time
    total_time = time_per_location * 1.2  # 20% buffer
    
    if total_time < 60:
        return f"{total_time:.1f} seconds"
    elif total_time < 3600:
        return f"{total_time/60:.1f} minutes"
    else:
        return f"{total_time/3600:.1f} hours"


def print_operation_summary(args):
    """Print a summary of the operation that will be performed"""
    print("=" * 70)
    print("HISTORICAL DATA SEEDING OPERATION")
    print("=" * 70)
    print(f"Date Range:           Last {args.days_back} days")
    print(f"Batch Size:           {args.batch_size} days per batch")
    print(f"Request Delay:        {args.delay_requests} seconds")
    print(f"Location Delay:       {args.delay_locations} seconds")
    print(f"API Validation:       {'Disabled' if args.no_validate_api else 'Enabled'}")
    
    batches = (args.days_back + args.batch_size - 1) // args.batch_size
    print(f"Estimated Batches:    {batches} per location")
    
    estimated_time = estimate_operation_time(
        args.days_back, args.batch_size, args.delay_requests, args.delay_locations
    )
    print(f"Estimated Duration:   {estimated_time} per location")
    print("=" * 70)


def main():
    """Main seeding function"""
    args = parse_arguments()
    
    # Validate arguments
    errors = validate_arguments(args)
    if errors:
        print("Error: Invalid arguments:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Setup logging
    if args.verbose:
        # Temporarily set DEBUG to True for verbose logging
        import os
        os.environ['DEBUG'] = 'True'
    
    logger = setup_logging()
    
    try:
        print_operation_summary(args)
        
        # Check if locations exist
        nettelhorst_exists = get_location_exists(80146)
        if not nettelhorst_exists:
            logger.error("Nettelhorst location not found in database!")
            logger.error("Please run 'python seed_database.py' first to seed location data.")
            sys.exit(1)
        
        logger.info(f"Nettelhorst location found in database")
        
        # Confirm operation with user (unless --yes flag is provided)
        if not args.yes:
            print("\nThis operation will fetch historical data from the AirGradient API.")
            print("It may take a significant amount of time depending on the parameters.")
            
            try:
                confirm = input("\nDo you want to continue? [y/N]: ").strip().lower()
                if confirm not in ['y', 'yes']:
                    print("Operation cancelled by user.")
                    sys.exit(0)
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                sys.exit(0)
        else:
            logger.info("Skipping confirmation prompt (--yes flag provided)")
        
        print("\nStarting historical data seeding...")
        logger.info("User confirmed operation. Starting historical data seeding.")
        
        # Run seeding
        start_time = datetime.now()
        result = seed_historical_data_sync(
            days_back=args.days_back,
            batch_size_days=args.batch_size,
            delay_between_requests=args.delay_requests,
            delay_between_locations=args.delay_locations,
            validate_api_first=not args.no_validate_api
        )
        
        # Print results
        print("\n" + "=" * 70)
        print("SEEDING OPERATION COMPLETED")
        print("=" * 70)
        
        if result['success']:
            print(f"✅ Success! Operation completed in {result.get('duration_formatted', 'unknown time')}")
            print(f"📍 Locations processed: {result['locations_processed']}/{result['total_locations']}")
            print(f"📥 Total data points fetched: {result['total_fetched']:,}")
            print(f"💾 Total records saved: {result['total_saved']:,}")
            print(f"📊 Overall success rate: {result['success_rate']:.1%}")
            
            if result['locations_failed'] > 0:
                print(f"⚠️  Failed locations: {result['locations_failed']}")
            
            # Show per-location breakdown if available
            if 'location_results' in result and result['location_results']:
                print("\nPer-location results:")
                for location_result in result['location_results']:
                    if 'error' not in location_result:
                        print(f"  Location {location_result['location_id']}: "
                              f"{location_result['total_saved']:,} records saved "
                              f"({location_result['success_rate']:.1%} success)")
                    else:
                        print(f"  Location {location_result['location_id']}: FAILED - {location_result['error']}")
        else:
            print(f"❌ Operation failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        print("=" * 70)
        logger.info("Historical data seeding script completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        print("\n\nOperation interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Historical data seeding script failed: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        print("Check the logs for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()