#!/usr/bin/env python3
"""
Database seeding script for Nettelhorst AQI Backend

This script seeds the database with initial data including AQI location information.

Usage:
    python seed_database.py

Requirements:
    - Database must be created and migrations applied
    - Virtual environment must be activated
    - Environment variables must be set (DATABASE_URL)
"""

import sys
import os
import logging

# Add the app directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.logging import setup_logging
from app.db.seed import seed_database, get_location_exists


def main():
    """Main seeding function"""
    # Setup logging
    logger = setup_logging()
    
    try:
        logger.info("=" * 50)
        logger.info("NETTELHORST AQI DATABASE SEEDING")
        logger.info("=" * 50)
        
        # Check current state before seeding
        nettelhorst_exists = get_location_exists(80146)
        logger.info(f"Nettelhorst location exists: {nettelhorst_exists}")
        
        # Run seeding
        seed_database()
        
        logger.info("=" * 50)
        logger.info("SEEDING COMPLETED")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Seeding failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()