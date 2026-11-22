#!/usr/bin/env python3
"""🏃‍♂️ Comprehensive Garmin Connect API Demo.
==========================================

This is a comprehensive demonstration program showing ALL available API calls
and error handling patterns for python-garminconnect.

For a simple getting-started example, see example.py

Dependencies:
pip3 install requests readchar

Environment Variables (optional):
export GARMIN_EMAIL=<your garmin email address>
export GARMIN_PASSWORD=<your garmin password>
export GARMINTOKENS=<path to token storage>
"""

import argparse
import datetime
import json
import logging
import os
import sys
import zipfile
from contextlib import suppress
from datetime import timedelta
from getpass import getpass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

import readchar
import requests

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# Configure logging to reduce verbose error output from garminconnect library
# This prevents double error messages for known API issues
logging.getLogger("garminconnect").setLevel(logging.CRITICAL)

api: Garmin | None = None


def safe_readkey() -> str:
    """Safe wrapper around readchar.readkey() that handles non-TTY environments.

    This is particularly useful on macOS and in CI/CD environments where stdin
    might not be a TTY, which would cause readchar to fail with:
    termios.error: (25, 'Inappropriate ioctl for device')

    Returns:
        str: A single character input from the user

    """
    if not sys.stdin.isatty():
        print("WARNING: stdin is not a TTY. Falling back to input().")
        user_input = input("Enter a key (then press Enter): ")
        return user_input[0] if user_input else ""
    try:
        return readchar.readkey()
    except Exception as e:
        print(f"readkey() failed: {e}")
        user_input = input("Enter a key (then press Enter): ")
        return user_input[0] if user_input else ""


class Config:
    """Configuration class for the Garmin Connect API demo."""

    def __init__(self):
        # Load environment variables
        self.email = os.getenv("GARMIN_EMAIL") or os.getenv("EMAIL")
        self.password = os.getenv("GARMIN_PASSWORD") or os.getenv("PASSWORD")
        self.tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"

        # Date settings
        self.today = datetime.date.today()
        self.week_start = self.today - timedelta(days=7)
        self.month_start = self.today - timedelta(days=30)

        # API call settings
        self.default_limit = 100
        self.start = 0
        self.start_badge = 1  # Badge related calls start counting at 1

        # Activity settings
        self.activitytype = ""  # Possible values: cycling, running, swimming, multi_sport, fitness_equipment, hiking, walking, other
        self.activityfile = "test_data/*.gpx"  # Supported file types: .fit .gpx .tcx
        self.workoutfile = "test_data/sample_workout.json"  # Sample workout JSON file

        # Export settings
        self.export_dir = Path("your_data")
        self.export_dir.mkdir(exist_ok=True)


# Initialize configuration
config = Config()

# Organized menu categories
menu_categories = {
    "1": {
        "name": "👤 User & Profile",
        "options": {
            "1": {"desc": "Get full name", "key": "get_full_name"},
            "2": {"desc": "Get unit system", "key": "get_unit_system"},
            "3": {"desc": "Get user profile", "key": "get_user_profile"},
            "4": {
                "desc": "Get userprofile settings",
                "key": "get_userprofile_settings",
            },
        },
    },
    "2": {
        "name": "📊 Daily Health & Activity",
        "options": {
            "1": {
                "desc": f"Get activity data for '{config.today.isoformat()}'",
                "key": "get_stats",
            },
            "2": {
                "desc": f"Get user summary for '{config.today.isoformat()}'",
                "key": "get_user_summary",
            },
            "3": {
                "desc": f"Get stats and body composition for '{config.today.isoformat()}'",
                "key": "get_stats_and_body",
            },
            "4": {
                "desc": f"Get steps data for '{config.today.isoformat()}'",
                "key": "get_steps_data",
            },
            "5": {
                "desc": f"Get heart rate data for '{config.today.isoformat()}'",
                "key": "get_heart_rates",
            },
            "6": {
                "desc": f"Get resting heart rate for '{config.today.isoformat()}'",
                "key": "get_resting_heart_rate",
            },
            "7": {
                "desc": f"Get sleep data for '{config.today.isoformat()}'",
                "key": "get_sleep_data",
            },
            "8": {
                "desc": f"Get stress data for '{config.today.isoformat()}'",
                "key": "get_all_day_stress",
            },
            "9": {
                "desc": f"Get lifestyle logging data for '{config.today.isoformat()}'",
                "key": "get_lifestyle_logging_data",
            },
        },
    },
    "3": {
        "name": "🔬 Advanced Health Metrics",
        "options": {
            "1": {
                "desc": f"Get training readiness for '{config.today.isoformat()}'",
                "key": "get_training_readiness",
            },
            "2": {
                "desc": f"Get morning training readiness for '{config.today.isoformat()}'",
                "key": "get_morning_training_readiness",
            },
            "3": {
                "desc": f"Get training status for '{config.today.isoformat()}'",
                "key": "get_training_status",
            },
            "4": {
                "desc": f"Get respiration data for '{config.today.isoformat()}'",
                "key": "get_respiration_data",
            },
            "5": {
                "desc": f"Get SpO2 data for '{config.today.isoformat()}'",
                "key": "get_spo2_data",
            },
            "6": {
                "desc": f"Get max metrics (VO2, fitness age) for '{config.today.isoformat()}'",
                "key": "get_max_metrics",
            },
            "7": {
                "desc": f"Get Heart Rate Variability (HRV) for '{config.today.isoformat()}'",
                "key": "get_hrv_data",
            },
            "8": {
                "desc": f"Get Fitness Age data for '{config.today.isoformat()}'",
                "key": "get_fitnessage_data",
            },
            "9": {
                "desc": f"Get stress data for '{config.today.isoformat()}'",
                "key": "get_stress_data",
            },
            "0": {"desc": "Get lactate threshold data", "key": "get_lactate_threshold"},
            "a": {
                "desc": f"Get intensity minutes for '{config.today.isoformat()}'",
                "key": "get_intensity_minutes_data",
            },
            "b": {
                "desc": f"Get running tolerance from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_running_tolerance",
            },
        },
    },
    "4": {
        "name": "📈 Historical Data & Trends",
        "options": {
            "1": {
                "desc": f"Get daily steps from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_daily_steps",
            },
            "2": {
            },
            "3": {
                "desc": f"Get floors data for '{config.week_start.isoformat()}'",
                "key": "get_floors",
            },
            "4": {
                "desc": f"Get blood pressure from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_blood_pressure",
            },
            "5": {
                "desc": f"Get progress summary from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_progress_summary_between_dates",
            },
            "6": {
            },
            "7": {
                "desc": f"Get weekly steps (52 weeks ending '{config.today.isoformat()}')",
                "key": "get_weekly_steps",
            },
            "8": {
                "desc": f"Get weekly stress (52 weeks ending '{config.today.isoformat()}')",
                "key": "get_weekly_stress",
            },
            "9": {
                "desc": f"Get weekly intensity minutes from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_weekly_intensity_minutes",
            },
        },
    },
    "5": {
        "name": "🏃 Activities & Workouts",
        "options": {
            "1": {
                "desc": f"Get recent activities (limit {config.default_limit})",
                "key": "get_activities",
            },
            "2": {"desc": "Get last activity", "key": "get_last_activity"},
            "3": {
                "desc": f"Get activities for today '{config.today.isoformat()}'",
                "key": "get_activities_fordate",
            },
            "4": {
                "desc": f"Download activities by date range '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "download_activities",
            },
            "5": {
                "desc": "Get all activity types and statistics",
                "key": "get_activity_types",
            },
            "6": {
                "desc": f"Upload activity data from {config.activityfile}",
                "key": "upload_activity",
            },
            "7": {"desc": "Get workouts", "key": "get_workouts"},
            "8": {"desc": "Get activity splits (laps)", "key": "get_activity_splits"},
            "9": {
                "desc": "Get activity typed splits",
                "key": "get_activity_typed_splits",
            },
            "0": {
                "desc": "Get activity split summaries",
                "key": "get_activity_split_summaries",
            },
            "a": {"desc": "Get activity weather data", "key": "get_activity_weather"},
            "b": {
                "desc": "Get activity heart rate zones",
                "key": "get_activity_hr_in_timezones",
            },
            "c": {
                "desc": "Get activity power zones",
                "key": "get_activity_power_in_timezones",
            },
            "d": {
                "desc": "Get cycling FTP (Functional Threshold Power)",
                "key": "get_cycling_ftp",
            },
            "e": {
                "desc": "Get detailed activity information",
                "key": "get_activity_details",
            },
            "f": {"desc": "Get activity gear information", "key": "get_activity_gear"},
            "g": {"desc": "Get single activity data", "key": "get_activity"},
            "h": {
                "desc": "Get strength training exercise sets",
                "key": "get_activity_exercise_sets",
            },
            "i": {"desc": "Get workout by ID", "key": "get_workout_by_id"},
            "j": {"desc": "Download workout to .FIT file", "key": "download_workout"},
            "k": {
                "desc": f"Upload workout from {config.workoutfile}",
                "key": "upload_workout",
            },
            "l": {
                "desc": f"Get activities by date range '{config.today.isoformat()}'",
                "key": "get_activities_by_date",
            },
            "m": {"desc": "Set activity name", "key": "set_activity_name"},
            "n": {"desc": "Set activity type", "key": "set_activity_type"},
            "o": {"desc": "Create manual activity", "key": "create_manual_activity"},
            "p": {"desc": "Delete activity", "key": "delete_activity"},
            "q": {
                "desc": "Get scheduled workout by ID",
                "key": "get_scheduled_workout_by_id",
            },
            "r": {
                "desc": "Count activities for current user",
                "key": "count_activities",
            },
            "s": {
                "desc": "Schedule a workout on a date (interactive)",
                "key": "scheduled_workout",
            },
            "t": {
                "desc": f"Import activity (no Strava re-export) from {config.activityfile}",
                "key": "import_activity",
            },
            "v": {
                "desc": "Upload typed running workout (sample)",
                "key": "upload_running_workout",
            },
            "w": {
                "desc": "Upload typed cycling workout (sample)",
                "key": "upload_cycling_workout",
            },
            "x": {
                "desc": "Upload typed swimming workout (sample)",
                "key": "upload_swimming_workout",
            },
            "y": {
                "desc": "Upload typed walking workout (sample)",
                "key": "upload_walking_workout",
            },
            "z": {
                "desc": "Upload typed hiking workout (sample)",
                "key": "upload_hiking_workout",
            },
        },
    },
    "6": {
        "name": "⚖️  Body Composition & Weight",
        "options": {
            "1": {
                "desc": f"Get body composition for '{config.today.isoformat()}'",
                "key": "get_body_composition",
            },
            "2": {
                "desc": f"Get weigh-ins from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_weigh_ins",
            },
            "3": {
                "desc": f"Get daily weigh-ins for '{config.today.isoformat()}'",
                "key": "get_daily_weigh_ins",
            },
            "4": {"desc": "Add a weigh-in (interactive)", "key": "add_weigh_in"},
            "5": {
                "desc": f"Set body composition data for '{config.today.isoformat()}' (interactive)",
                "key": "set_body_composition",
            },
            "6": {
                "desc": f"Add body composition for '{config.today.isoformat()}' (interactive)",
                "key": "add_body_composition",
            },
            "7": {
                "desc": f"Delete all weigh-ins for '{config.today.isoformat()}'",
                "key": "delete_weigh_ins",
            },
            "8": {"desc": "Delete specific weigh-in", "key": "delete_weigh_in"},
        },
    },
    "7": {
        "name": "🏆 Goals & Achievements",
        "options": {
            "1": {"desc": "Get personal records", "key": "get_personal_records"},
            "2": {"desc": "Get earned badges", "key": "get_earned_badges"},
            "3": {"desc": "Get adhoc challenges", "key": "get_adhoc_challenges"},
            "4": {
                "desc": "Get available badge challenges",
                "key": "get_available_badge_challenges",
            },
            "5": {"desc": "Get active goals", "key": "get_active_goals"},
            "6": {"desc": "Get future goals", "key": "get_future_goals"},
            "7": {"desc": "Get past goals", "key": "get_past_goals"},
            "8": {"desc": "Get badge challenges", "key": "get_badge_challenges"},
            "9": {
                "desc": "Get non-completed badge challenges",
                "key": "get_non_completed_badge_challenges",
            },
            "0": {
                "desc": "Get virtual challenges in progress",
                "key": "get_inprogress_virtual_challenges",
            },
            "a": {"desc": "Get race predictions", "key": "get_race_predictions"},
            "b": {
                "desc": f"Get hill score from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_hill_score",
            },
            "c": {
                "desc": f"Get endurance score from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_endurance_score",
            },
            "d": {"desc": "Get available badges", "key": "get_available_badges"},
            "e": {"desc": "Get badges in progress", "key": "get_in_progress_badges"},
        },
    },
    "8": {
        "name": "⌚ Device & Technical",
        "options": {
            "1": {"desc": "Get all device information", "key": "get_devices"},
            "2": {"desc": "Get device alarms", "key": "get_device_alarms"},
            "3": {"desc": "Get solar data from your devices", "key": "get_solar_data"},
            "4": {
                "desc": f"Request data reload (epoch) for '{config.today.isoformat()}'",
                "key": "request_reload",
            },
            "5": {"desc": "Get device settings", "key": "get_device_settings"},
            "6": {"desc": "Get device last used", "key": "get_device_last_used"},
            "7": {
                "desc": "Get primary training device",
                "key": "get_primary_training_device",
            },
        },
    },
    "9": {
        "name": "🎽 Gear & Equipment",
        "options": {
            "1": {"desc": "Get user gear list", "key": "get_gear"},
            "2": {"desc": "Get gear defaults", "key": "get_gear_defaults"},
            "3": {"desc": "Get gear statistics", "key": "get_gear_stats"},
            "4": {"desc": "Get gear activities", "key": "get_gear_activities"},
            "5": {"desc": "Set gear default", "key": "set_gear_default"},
            "6": {
                "desc": "Track gear usage (total time used)",
                "key": "track_gear_usage",
            },
            "7": {
                "desc": "Add and remove gear to/from activity (interactive)",
                "key": "add_and_remove_gear_to_activity",
            },
        },
    },
    "0": {
        "name": "💧 Hydration & Wellness",
        "options": {
            "1": {
                "desc": f"Get hydration data for '{config.today.isoformat()}'",
                "key": "get_hydration_data",
            },
            "2": {"desc": "Add hydration data", "key": "add_hydration_data"},
            "3": {
                "desc": "Set blood pressure and pulse (interactive)",
                "key": "set_blood_pressure",
            },
            "4": {"desc": "Get pregnancy summary data", "key": "get_pregnancy_summary"},
            "5": {
                "desc": f"Get all day events for '{config.week_start.isoformat()}'",
                "key": "get_all_day_events",
            },
            "6": {
            },
            "7": {
                "desc": f"Get menstrual data for '{config.today.isoformat()}'",
                "key": "get_menstrual_data_for_date",
            },
            "8": {
                "desc": f"Get menstrual calendar from '{config.week_start.isoformat()}' to '{config.today.isoformat()}'",
                "key": "get_menstrual_calendar_data",
            },
            "9": {
                "desc": "Delete blood pressure entry",
                "key": "delete_blood_pressure",
            },
            "a": {
                "desc": f"Get nutrition daily food log for '{config.today.isoformat()}'",
                "key": "get_nutrition_daily_food_log",
            },
            "b": {
                "desc": f"Get nutrition daily meals for '{config.today.isoformat()}'",
                "key": "get_nutrition_daily_meals",
            },
            "c": {
                "desc": f"Get nutrition daily settings for '{config.today.isoformat()}'",
                "key": "get_nutrition_daily_settings",
            },
        },
    },
    "a": {
        "name": "🔧 System & Export",
        "options": {
            "1": {"desc": "Create sample health report", "key": "create_health_report"},
            "2": {
                "desc": "Remove stored login tokens (logout)",
                "key": "remove_tokens",
            },
            "3": {"desc": "Disconnect from Garmin Connect", "key": "disconnect"},
            "4": {"desc": "Execute GraphQL query", "key": "query_garmin_graphql"},
        },
    },
    "b": {
        "name": "📅 Training Plans",
        "options": {
            "1": {"desc": "Get training plans", "key": "get_training_plans"},
            "2": {"desc": "Get training plan by ID", "key": "get_training_plan_by_id"},
        },
    },
    "c": {
        "name": "⛳ Golf",
        "options": {
            "1": {"desc": "Get golf scorecard summary", "key": "get_golf_summary"},
            "2": {"desc": "Get golf scorecard by ID", "key": "get_golf_scorecard"},
            "3": {
                "desc": "Get golf shot data by scorecard ID",
                "key": "get_golf_shot_data",
            },
        },
    },
}

current_category = None


def print_main_menu():
    """Print the main category menu."""
    print("\n" + "=" * 50)
    print("🚴 Full-blown Garmin Connect API Demo - Main Menu")
    print("=" * 50)
    print("Select a category:")
    print()

    for key, category in menu_categories.items():
        print(f"  [{key}] {category['name']}")

    print()
    print("  [q] Exit program")
    print()
    print("Make your selection: ", end="", flush=True)


def print_category_menu(category_key: str):
    """Print options for a specific category."""
    if category_key not in menu_categories:
        return False

    category = menu_categories[category_key]
    print(f"\n📋 #{category_key} {category['name']} - Options")
    print("-" * 40)

    for key, option in category["options"].items():
        print(f"  [{key}] {option['desc']}")

    print()
    print("  [q] Back to main menu")
    print()
    print("Make your selection: ", end="", flush=True)
    return True


def get_mfa() -> str:
    """Get MFA token."""
    return input("MFA one-time code: ")


class DataExporter:
    """Utilities for exporting data in various formats."""

    @staticmethod
    def save_json(data: Any, filename: str, pretty: bool = True) -> str:
        """Save data as JSON file."""
        filepath = config.export_dir / f"{filename}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, indent=4, default=str, ensure_ascii=False)
            else:
                json.dump(data, f, default=str, ensure_ascii=False)
        return str(filepath)

    @staticmethod
    def create_health_report(api_instance: Garmin) -> str:
        """Create a comprehensive health report in JSON and HTML formats."""
        report_data = {
            "generated_at": datetime.datetime.now().isoformat(),
            "user_info": {"full_name": "N/A", "unit_system": "N/A"},
            "today_summary": {},
            "recent_activities": [],
            "health_metrics": {},
            "weekly_data": [],
            "device_info": [],
        }

        try:
            # Basic user info
            report_data["user_info"]["full_name"] = (
                api_instance.get_full_name() or "N/A"
            )
            report_data["user_info"]["unit_system"] = (
                api_instance.get_unit_system() or "N/A"
            )

            # Today's summary
            today_str = config.today.isoformat()
            report_data["today_summary"] = api_instance.get_user_summary(today_str)

            # Recent activities
            recent_activities = api_instance.get_activities(0, 10)
            report_data["recent_activities"] = recent_activities or []

            # Weekly data for trends
            for i in range(7):
                date = config.today - datetime.timedelta(days=i)
                try:
                    daily_data = api_instance.get_user_summary(date.isoformat())
                    if daily_data:
                        daily_data["date"] = date.isoformat()
                        report_data["weekly_data"].append(daily_data)
                except Exception as e:
                    print(
                        f"Skipping data for {date.isoformat()}: {e}"
                    )  # Skip if data not available

            # Health metrics for today
            health_metrics = {}
            metrics_to_fetch = [
                ("heart_rate", lambda: api_instance.get_heart_rates(today_str)),
                ("steps", lambda: api_instance.get_steps_data(today_str)),
                ("sleep", lambda: api_instance.get_sleep_data(today_str)),
                ("stress", lambda: api_instance.get_all_day_stress(today_str)),
                (
                ),
            ]

            for metric_name, fetch_func in metrics_to_fetch:
                try:
                    health_metrics[metric_name] = fetch_func()
                except Exception:
                    health_metrics[metric_name] = None

            report_data["health_metrics"] = health_metrics

            # Device information
            try:
                report_data["device_info"] = api_instance.get_devices()
            except Exception:
                report_data["device_info"] = []

        except Exception as e:
            print(f"Error creating health report: {e}")

        # Create HTML version
        html_filepath = DataExporter.create_readable_health_report(report_data)

        print(f"📊 Report created: {html_filepath}")

        return html_filepath

    @staticmethod
    def create_readable_health_report(report_data: dict) -> str:
        """Create a readable HTML report from comprehensive health data."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"health_report_{timestamp}.html"

        # Extract key information
        user_name = report_data.get("user_info", {}).get("full_name", "Unknown User")
        generated_at = report_data.get("generated_at", "Unknown")

        # Create HTML content with complete styling
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Garmin Health Report - {user_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007ACC;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007ACC;
            margin: 0;
            font-size: 2.5em;
        }}
        .meta-info {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #007ACC;
            border-bottom: 2px solid #007ACC;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007ACC;
        }}
        .metric-card h4 {{
            margin: 0 0 10px 0;
            color: #007ACC;
            font-size: 1.1em;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}
        .metric-unit {{
            color: #666;
            font-size: 0.9em;
        }}
        .activity-item {{
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }}
        .activity-item h4 {{
            margin: 0 0 10px 0;
            color: #28a745;
        }}
        .activity-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            font-size: 0.9em;
        }}
        .no-data {{
            color: #666;
            font-style: italic;
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏃 Garmin Health Report</h1>
            <p><strong>{user_name}</strong></p>
        </div>

        <div class="meta-info">
            <p><strong>Generated:</strong> {generated_at}</p>
            <p><strong>Date:</strong> {config.today.isoformat()}</p>
        </div>
"""

        # Today's Summary Section
        today_summary = report_data.get("today_summary", {})
        if today_summary:
            steps = today_summary.get("totalSteps", 0)
            calories = today_summary.get("totalKilocalories", 0)
            distance = (
                round(today_summary.get("totalDistanceMeters", 0) / 1000, 2)
                if today_summary.get("totalDistanceMeters")
                else 0
            )
            active_calories = today_summary.get("activeKilocalories", 0)

            html_content += f"""
        <div class="section">
            <h2>📈 Today's Activity Summary</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <h4>👟 Steps</h4>
                    <div class="metric-value">{steps:,} <span class="metric-unit">steps</span></div>
                </div>
                <div class="metric-card">
                    <h4>🔥 Calories</h4>
                    <div class="metric-value">{calories:,} <span class="metric-unit">total</span></div>
                    <div style="margin-top: 10px;">{active_calories:,} active</div>
                </div>
                <div class="metric-card">
                    <h4>📏 Distance</h4>
                    <div class="metric-value">{distance} <span class="metric-unit">km</span></div>
                </div>
            </div>
        </div>
"""
        else:
            html_content += """
        <div class="section">
            <h2>📈 Today's Activity Summary</h2>
            <div class="no-data">No activity data available for today</div>
        </div>
"""

        # Health Metrics Section
        health_metrics = report_data.get("health_metrics", {})
        if health_metrics and any(health_metrics.values()):
            html_content += """
        <div class="section">
            <h2>❤️ Health Metrics</h2>
            <div class="metric-grid">
"""

            # Heart Rate
            heart_rate = health_metrics.get("heart_rate", {})
            if heart_rate and isinstance(heart_rate, dict):
                resting_hr = heart_rate.get("restingHeartRate", "N/A")
                max_hr = heart_rate.get("maxHeartRate", "N/A")
                html_content += f"""
                <div class="metric-card">
                    <h4>💓 Heart Rate</h4>
                    <div class="metric-value">{resting_hr} <span class="metric-unit">bpm (resting)</span></div>
                    <div style="margin-top: 10px;">Max: {max_hr} bpm</div>
                </div>
"""

            # Sleep Data
            sleep_data = health_metrics.get("sleep", {})
            if (
                sleep_data
                and isinstance(sleep_data, dict)
                and "dailySleepDTO" in sleep_data
            ):
                sleep_seconds = sleep_data["dailySleepDTO"].get("sleepTimeSeconds", 0)
                sleep_hours = round(sleep_seconds / 3600, 1) if sleep_seconds else 0
                deep_sleep = sleep_data["dailySleepDTO"].get("deepSleepSeconds", 0)
                deep_hours = round(deep_sleep / 3600, 1) if deep_sleep else 0

                html_content += f"""
                <div class="metric-card">
                    <h4>😴 Sleep</h4>
                    <div class="metric-value">{sleep_hours} <span class="metric-unit">hours</span></div>
                    <div style="margin-top: 10px;">Deep Sleep: {deep_hours} hours</div>
                </div>
"""

            # Steps
            steps_data = health_metrics.get("steps", {})
            if steps_data and isinstance(steps_data, dict):
                total_steps = steps_data.get("totalSteps", 0)
                goal = steps_data.get("dailyStepGoal", 10000)
                html_content += f"""
                <div class="metric-card">
                    <h4>🎯 Step Goal</h4>
                    <div class="metric-value">{total_steps:,} <span class="metric-unit">of {goal:,}</span></div>
                    <div style="margin-top: 10px;">Goal: {round((total_steps / goal) * 100) if goal else 0}%</div>
                </div>
"""

            # Stress Data
            stress_data = health_metrics.get("stress", {})
            if stress_data and isinstance(stress_data, dict):
                avg_stress = stress_data.get("avgStressLevel", "N/A")
                max_stress = stress_data.get("maxStressLevel", "N/A")
                html_content += f"""
                <div class="metric-card">
                    <h4>😰 Stress Level</h4>
                    <div class="metric-value">{avg_stress} <span class="metric-unit">avg</span></div>
                    <div style="margin-top: 10px;">Max: {max_stress}</div>
                </div>
"""

            html_content += "            </div>\n        </div>\n"
        else:
            html_content += """
        <div class="section">
            <h2>❤️ Health Metrics</h2>
            <div class="no-data">No health metrics data available</div>
        </div>
"""

        # Weekly Trends Section
        weekly_data = report_data.get("weekly_data", [])
        if weekly_data:
            html_content += """
        <div class="section">
            <h2>📊 Weekly Trends (Last 7 Days)</h2>
            <div class="metric-grid">
"""
            for daily in weekly_data[:7]:  # Show last 7 days
                date = daily.get("date", "Unknown")
                steps = daily.get("totalSteps", 0)
                calories = daily.get("totalKilocalories", 0)
                distance = (
                    round(daily.get("totalDistanceMeters", 0) / 1000, 2)
                    if daily.get("totalDistanceMeters")
                    else 0
                )

                html_content += f"""
                <div class="metric-card">
                    <h4>📅 {date}</h4>
                    <div class="metric-value">{steps:,} <span class="metric-unit">steps</span></div>
                    <div style="margin-top: 10px;">
                        <div>{calories:,} kcal</div>
                        <div>{distance} km</div>
                    </div>
                </div>
"""
            html_content += "            </div>\n        </div>\n"

        # Recent Activities Section
        activities = report_data.get("recent_activities", [])
        if activities:
            html_content += """
        <div class="section">
            <h2>🏃 Recent Activities</h2>
"""
            for activity in activities[:5]:  # Show last 5 activities
                name = activity.get("activityName", "Unknown Activity")
                activity_type = activity.get("activityType", {}).get(
                    "typeKey", "Unknown"
                )
                date = (
                    activity.get("startTimeLocal", "").split("T")[0]
                    if activity.get("startTimeLocal")
                    else "Unknown"
                )
                duration = activity.get("duration", 0)
                duration_min = round(duration / 60, 1) if duration else 0
                distance = (
                    round(activity.get("distance", 0) / 1000, 2)
                    if activity.get("distance")
                    else 0
                )
                calories = activity.get("calories", 0)
                avg_hr = activity.get("avgHR", 0)

                html_content += f"""
                <div class="activity-item">
                    <h4>{name} ({activity_type})</h4>
                    <div class="activity-details">
                        <div><strong>Date:</strong> {date}</div>
                        <div><strong>Duration:</strong> {duration_min} min</div>
                        <div><strong>Distance:</strong> {distance} km</div>
                        <div><strong>Calories:</strong> {calories}</div>
                        <div><strong>Avg HR:</strong> {avg_hr} bpm</div>
                    </div>
                </div>
"""
            html_content += "        </div>\n"
        else:
            html_content += """
        <div class="section">
            <h2>🏃 Recent Activities</h2>
            <div class="no-data">No recent activities found</div>
        </div>
"""

        # Device Information
        device_info = report_data.get("device_info", [])
        if device_info:
            html_content += """
        <div class="section">
            <h2>⌚ Device Information</h2>
            <div class="metric-grid">
"""
            for device in device_info:
                device_name = device.get("displayName", "Unknown Device")
                model = device.get("productDisplayName", "Unknown Model")
                version = device.get("softwareVersion", "Unknown")

                html_content += f"""
                <div class="metric-card">
                    <h4>{device_name}</h4>
                    <div><strong>Model:</strong> {model}</div>
                    <div><strong>Software:</strong> {version}</div>
                </div>
"""
            html_content += "            </div>\n        </div>\n"

        # Footer
        html_content += f"""
        <div class="footer">
            <p>Generated by Garmin Connect API Demo on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>This report is for informational purposes only. Consult healthcare professionals for medical advice.</p>
        </div>
    </div>
</body>
</html>
"""

        # Save HTML file
        html_filepath = config.export_dir / html_filename
        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(html_filepath)


def safe_api_call(api_method, *args, method_name: str | None = None, **kwargs):
    """Centralized API call wrapper with comprehensive error handling.

    This function provides unified error handling for all Garmin Connect API calls.
    It handles common HTTP errors (400, 401, 403, 404, 429, 500, 503) with
    user-friendly messages and provides consistent error reporting.

    Usage:
        success, result, error_msg = safe_api_call(api.get_user_summary)

    Args:
        api_method: The API method to call
        *args: Positional arguments for the API method
        method_name: Human-readable name for the API method (optional)
        **kwargs: Keyword arguments for the API method

    Returns:
        tuple: (success: bool, result: Any, error_message: str|None)

    """
    if method_name is None:
        method_name = getattr(api_method, "__name__", str(api_method))

    try:
        result = api_method(*args, **kwargs)
        return True, result, None

    except GarminConnectConnectionError as e:
        # Handle specific HTTP errors more gracefully
        error_str = str(e)

        # Extract status code more reliably
        status_code = None
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            status_code = e.response.status_code

        # Handle specific status codes
        if status_code == 400 or ("400" in error_str and "Bad Request" in error_str):
            error_msg = "Endpoint not available (400 Bad Request) - This feature may not be enabled for your account or region"
            # Don't print for 400 errors as they're often expected for unavailable features
        elif status_code == 401 or "401" in error_str:
            error_msg = (
                "Authentication required (401 Unauthorized) - Please re-authenticate"
            )
            print(f"⚠️ {method_name} failed: {error_msg}")
        elif status_code == 403 or "403" in error_str:
            error_msg = "Access denied (403 Forbidden) - Your account may not have permission for this feature"
            print(f"⚠️ {method_name} failed: {error_msg}")
        elif status_code == 404 or "404" in error_str:
            error_msg = (
                "Endpoint not found (404) - This feature may have been moved or removed"
            )
            print(f"⚠️ {method_name} failed: {error_msg}")
        elif status_code == 410 or "410" in error_str:
            error_msg = "Resource no longer available (410 Gone) - This data does not exist or the endpoint has been retired"
            print(f"⚠️ {method_name} failed: {error_msg}")
        elif status_code == 429 or "429" in error_str:
            error_msg = (
                "Rate limit exceeded (429) - Please wait before making more requests"
            )
            print(f"⚠️ {method_name} failed: {error_msg}")
        elif status_code == 500 or "500" in error_str:
            error_msg = "Server error (500) - Garmin's servers are experiencing issues"
            print(f"⚠️ {method_name} failed: {error_msg}")
        elif status_code == 503 or "503" in error_str:
            error_msg = "Service unavailable (503) - Garmin's servers are temporarily unavailable"
            print(f"⚠️ {method_name} failed: {error_msg}")
        else:
            error_msg = f"HTTP error: {e}"

        print(f"⚠️ {method_name} failed: {error_msg}")
        return False, None, error_msg

    except GarminConnectAuthenticationError as e:
        error_msg = f"Authentication issue: {e}"
        print(f"⚠️ {method_name} failed: {error_msg}")
        return False, None, error_msg

    except GarminConnectConnectionError as e:  # noqa: B025
        error_str = str(e)
        # Extract a clean message by detecting common HTTP status codes
        if "410" in error_str:
            error_msg = "Resource no longer available (410 Gone) - This data does not exist or the endpoint has been retired"
        elif "403" in error_str:
            error_msg = "Access denied (403 Forbidden) - Your account may not have permission for this feature"
        elif "404" in error_str:
            error_msg = (
                "Endpoint not found (404) - This feature may have been moved or removed"
            )
        else:
            error_msg = f"Connection issue: {e}"
        print(f"⚠️ {method_name} failed: {error_msg}")
        return False, None, error_msg

    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"⚠️ {method_name} failed: {error_msg}")
        return False, None, error_msg


def call_and_display(
    api_method=None,
    *args,
    method_name: str | None = None,
    api_call_desc: str | None = None,
    group_name: str | None = None,
    api_responses: list | None = None,
    **kwargs,
):
    """Unified wrapper that calls API methods safely and displays results.
    Can handle both single API calls and grouped API responses.

    For single API calls:
        call_and_display(api.get_user_summary, "2024-01-01")

    For grouped responses:
        call_and_display(group_name="User Data", api_responses=[("api.get_user", data)])

    Args:
        api_method: The API method to call (for single calls)
        *args: Positional arguments for the API method
        method_name: Human-readable name for the API method (optional)
        api_call_desc: Description for display purposes (optional)
        group_name: Name for grouped display (when displaying multiple responses)
        api_responses: List of (api_call_desc, result) tuples for grouped display
        **kwargs: Keyword arguments for the API method

    Returns:
        For single calls: tuple: (success: bool, result: Any)
        For grouped calls: None

    """
    # Handle grouped display mode
    if group_name is not None and api_responses is not None:
        return _display_group(group_name, api_responses)

    # Handle single API call mode
    if api_method is None:
        raise ValueError(
            "Either api_method or (group_name + api_responses) must be provided"
        )

    if method_name is None:
        method_name = getattr(api_method, "__name__", str(api_method))

    if api_call_desc is None:
        # Try to construct a reasonable description
        args_str = ", ".join(str(arg) for arg in args)
        kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        api_call_desc = f"{method_name}({all_args})"

    success, result, error_msg = safe_api_call(
        api_method, *args, method_name=method_name, **kwargs
    )

    if success:
        _display_single(api_call_desc, result)
        return True, result
    # Display error in a consistent format
    _display_single(f"{api_call_desc} [ERROR]", {"error": error_msg})
    return False, None


def _display_single(api_call: str, output: Any):
    """Internal function to display single API response."""
    print(f"\n📡 API Call: {api_call}")
    print("-" * 50)

    if output is None:
        print("No data returned")
        # Save empty JSON to response.json in the export directory
        response_file = config.export_dir / "response.json"
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(f"{'-' * 20} {api_call} {'-' * 20}\n{{}}\n{'-' * 77}\n")
        return

    try:
        # Format the output
        if isinstance(output, int | str | dict | list):
            formatted_output = json.dumps(output, indent=2, default=str)
        else:
            formatted_output = str(output)

        # Save to response.json in the export directory
        response_content = (
            f"{'-' * 20} {api_call} {'-' * 20}\n{formatted_output}\n{'-' * 77}\n"
        )

        response_file = config.export_dir / "response.json"
        with open(response_file, "w", encoding="utf-8") as f:
            f.write(response_content)

        print(formatted_output)
        print("-" * 77)

    except Exception as e:
        print(f"Error formatting output: {e}")
        print(output)


def _display_group(group_name: str, api_responses: list[tuple[str, Any]]):
    """Internal function to display grouped API responses."""
    print(f"\n📡 API Group: {group_name}")

    # Collect all responses for saving
    all_responses = {}
    response_content_parts = []

    for api_call, output in api_responses:
        print(f"\n📋 {api_call}")
        print("-" * 50)

        if output is None:
            print("No data returned")
            formatted_output = "{}"
        else:
            try:
                if isinstance(output, int | str | dict | list):
                    formatted_output = json.dumps(output, indent=2, default=str)
                else:
                    formatted_output = str(output)
                print(formatted_output)
            except Exception as e:
                print(f"Error formatting output: {e}")
                formatted_output = str(output)
                print(output)

        # Store for grouped response file
        all_responses[api_call] = output
        response_content_parts.append(
            f"{'-' * 20} {api_call} {'-' * 20}\n{formatted_output}"
        )
        print("-" * 50)

    # Save grouped responses to file
    try:
        response_file = config.export_dir / "response.json"
        header = "=" * 20 + f" {group_name} " + "=" * 20
        footer = "=" * 77
        content_lines = [header, *response_content_parts, footer, ""]
        grouped_content = "\n".join(content_lines)
        with response_file.open("w", encoding="utf-8") as f:
            f.write(grouped_content)

        print(f"\n✅ Grouped responses saved to: {response_file}")
        print("=" * 77)

    except Exception as e:
        print(f"Error saving grouped responses: {e}")


def format_timedelta(td):
    minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}"


def safe_call_for_group(
    api_method,
    *args,
    method_name: str | None = None,
    api_call_desc: str | None = None,
    **kwargs,
):
    """Safe API call wrapper that returns result suitable for grouped display.

    Args:
        api_method: The API method to call
        *args: Positional arguments for the API method
        method_name: Human-readable name for the API method (optional)
        api_call_desc: Description for display purposes (optional)
        **kwargs: Keyword arguments for the API method

    Returns:
        tuple: (api_call_description: str, result: Any) - suitable for grouped display

    """
    if method_name is None:
        method_name = getattr(api_method, "__name__", str(api_method))

    if api_call_desc is None:
        # Try to construct a reasonable description
        args_str = ", ".join(str(arg) for arg in args)
        kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        api_call_desc = f"{method_name}({all_args})"

    success, result, error_msg = safe_api_call(
        api_method, *args, method_name=method_name, **kwargs
    )

    if success:
        return api_call_desc, result
    return f"{api_call_desc} [ERROR]", {"error": error_msg}


def get_solar_data(api: Garmin) -> None:
    """Get solar data from all Garmin devices using centralized error handling."""
    print("☀️ Getting solar data from devices...")

    # Collect all API responses for grouped display
    api_responses = []

    # Get all devices using centralized wrapper
    api_responses.append(
        safe_call_for_group(
            api.get_devices,
            method_name="get_devices",
            api_call_desc="api.get_devices()",
        )
    )

    # Get device last used using centralized wrapper
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get the device list to process solar data
    devices_success, devices, _ = safe_api_call(
        api.get_devices, method_name="get_devices"
    )

    # Get solar data for each device
    if devices_success and devices:
        for device in devices:
            device_id = device.get("deviceId")
            if device_id:
                device_name = device.get("displayName", f"Device {device_id}")
                print(
                    f"\n☀️ Getting solar data for device: {device_name} (ID: {device_id})"
                )

                # Use centralized wrapper for each device's solar data
                api_responses.append(
                    safe_call_for_group(
                        api.get_device_solar_data,
                        device_id,
                        config.today.isoformat(),
                        method_name="get_device_solar_data",
                        api_call_desc=f"api.get_device_solar_data({device_id}, '{config.today.isoformat()}')",
                    )
                )
    else:
        print("ℹ️ No devices found or error retrieving devices")

    # Display all responses as a group
    call_and_display(group_name="Solar Data Collection", api_responses=api_responses)


def import_activity_file(api: Garmin) -> None:
    """Import activity data from file (not re-exported to Strava)."""
    import glob

    try:
        activity_files = glob.glob(config.activityfile)
        if not activity_files:
            print("❌ No activity files found in test_data directory.")
            print("ℹ️ Please add FIT/GPX/TCX files to test_data before importing.")
            return

        print("Select a file to import (will NOT be re-exported to Strava):")
        for idx, fname in enumerate(activity_files, 1):
            print(f"  {idx}. {fname}")

        while True:
            try:
                choice = int(input(f"Enter number (1-{len(activity_files)}): "))
                if 1 <= choice <= len(activity_files):
                    selected_file = activity_files[choice - 1]
                    break
                print("Invalid selection. Try again.")
            except ValueError:
                print("Please enter a valid number.")

        print(f"📥 Importing activity from file: {selected_file}")

        call_and_display(
            api.import_activity,
            selected_file,
            method_name="import_activity",
            api_call_desc=f"api.import_activity({selected_file})",
        )

    except FileNotFoundError:
        print(f"❌ File not found: {selected_file}")
    except Exception as e:
        if "409" in str(e) or "duplicate" in str(e).lower():
            print("⚠️ Activity already exists (duplicate)")
        else:
            print(f"❌ Import failed: {e}")


def upload_activity_file(api: Garmin) -> None:
    """Upload activity data from file."""
    import glob

    try:
        # List all .gpx files in test_data
        gpx_files = glob.glob(config.activityfile)
        if not gpx_files:
            print("❌ No .gpx files found in test_data directory.")
            print("ℹ️ Please add GPX files to test_data before uploading.")
            return

        print("Select a GPX file to upload:")
        for idx, fname in enumerate(gpx_files, 1):
            print(f"  {idx}. {fname}")

        while True:
            try:
                choice = int(input(f"Enter number (1-{len(gpx_files)}): "))
                if 1 <= choice <= len(gpx_files):
                    selected_file = gpx_files[choice - 1]
                    break
                print("Invalid selection. Try again.")
            except ValueError:
                print("Please enter a valid number.")

        print(f"📤 Uploading activity from file: {selected_file}")

        call_and_display(
            api.upload_activity,
            selected_file,
            method_name="upload_activity",
            api_call_desc=f"api.upload_activity({selected_file})",
        )

    except FileNotFoundError:
        print(f"❌ File not found: {selected_file}")
        print("ℹ️ Please ensure the activity file exists in the current directory")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            print(
                "⚠️ Activity already exists: This activity has already been uploaded to Garmin Connect"
            )
            print("ℹ️ Garmin Connect prevents duplicate activities from being uploaded")
            print(
                "💡 Try modifying the activity timestamps or creating a new activity file"
            )
        elif e.response.status_code == 413:
            print(
                "❌ File too large: The activity file exceeds Garmin Connect's size limit"
            )
            print("💡 Try compressing the file or reducing the number of data points")
        elif e.response.status_code == 422:
            print(
                "❌ Invalid file format: The activity file format is not supported or corrupted"
            )
            print("ℹ️ Supported formats: FIT, GPX, TCX")
            print("💡 Try converting to a different format or check file integrity")
        elif e.response.status_code == 400:
            print("❌ Bad request: Invalid activity data or malformed file")
            print(
                "💡 Check if the activity file contains valid GPS coordinates and timestamps"
            )
        elif e.response.status_code == 401:
            print("❌ Authentication failed: Please login again")
            print("💡 Your session may have expired")
        elif e.response.status_code == 429:
            print("❌ Rate limit exceeded: Too many upload requests")
            print("💡 Please wait a few minutes before trying again")
        else:
            print(f"❌ HTTP Error {e.response.status_code}: {e}")
    except GarminConnectAuthenticationError as e:
        print(f"❌ Authentication error: {e}")
        print("💡 Please check your login credentials and try again")
    except GarminConnectConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Please check your internet connection and try again")
    except GarminConnectTooManyRequestsError as e:
        print(f"❌ Too many requests: {e}")
        print("💡 Please wait a few minutes before trying again")
    except Exception as e:
        error_str = str(e)
        if "409 Client Error: Conflict" in error_str:
            print(
                "⚠️ Activity already exists: This activity has already been uploaded to Garmin Connect"
            )
            print("ℹ️ Garmin Connect prevents duplicate activities from being uploaded")
            print(
                "💡 Try modifying the activity timestamps or creating a new activity file"
            )
        elif "413" in error_str and "Request Entity Too Large" in error_str:
            print(
                "❌ File too large: The activity file exceeds Garmin Connect's size limit"
            )
            print("💡 Try compressing the file or reducing the number of data points")
        elif "422" in error_str and "Unprocessable Entity" in error_str:
            print(
                "❌ Invalid file format: The activity file format is not supported or corrupted"
            )
            print("ℹ️ Supported formats: FIT, GPX, TCX")
            print("💡 Try converting to a different format or check file integrity")
        elif "400" in error_str and "Bad Request" in error_str:
            print("❌ Bad request: Invalid activity data or malformed file")
            print(
                "💡 Check if the activity file contains valid GPS coordinates and timestamps"
            )
        elif "401" in error_str and "Unauthorized" in error_str:
            print("❌ Authentication failed: Please login again")
            print("💡 Your session may have expired")
        elif "429" in error_str and "Too Many Requests" in error_str:
            print("❌ Rate limit exceeded: Too many upload requests")
            print("💡 Please wait a few minutes before trying again")
        else:
            print(f"❌ Unexpected error uploading activity: {e}")
            print("💡 Please check the file format and try again")


def download_activities_by_date(api: Garmin) -> None:
    """Download activities by date range in multiple formats."""
    try:
        print(
            f"📥 Downloading activities by date range ({config.week_start.isoformat()} to {config.today.isoformat()})..."
        )

        # Get activities for the date range (last 7 days as default)
        activities = api.get_activities_by_date(
            config.week_start.isoformat(), config.today.isoformat()
        )

        if not activities:
            print("ℹ️ No activities found in the specified date range")
            return

        print(f"📊 Found {len(activities)} activities to download")

        # Download each activity in multiple formats
        for activity in activities:
            activity_id = activity.get("activityId")
            activity_name = activity.get("activityName", "Unknown")
            start_time = activity.get("startTimeLocal", "").replace(":", "-")

            if not activity_id:
                continue

            print(f"📥 Downloading: {activity_name} (ID: {activity_id})")

            # Download formats: GPX, TCX, ORIGINAL, CSV
            formats = ["GPX", "TCX", "ORIGINAL", "CSV"]

            for fmt in formats:
                try:
                    filename = f"{start_time}_{activity_id}_ACTIVITY.{fmt.lower()}"
                    if fmt == "ORIGINAL":
                        filename = f"{start_time}_{activity_id}_ACTIVITY.zip"

                    filepath = config.export_dir / filename

                    if fmt == "CSV":
                        # Get activity details for CSV export
                        activity_details = api.get_activity_details(activity_id)
                        with open(filepath, "w", encoding="utf-8") as f:
                            import json

                            json.dump(activity_details, f, indent=2, ensure_ascii=False)
                        print(f"  ✅ {fmt}: {filename}")
                    else:
                        # Download the file from Garmin using proper enum values
                        format_mapping = {
                            "GPX": api.ActivityDownloadFormat.GPX,
                            "TCX": api.ActivityDownloadFormat.TCX,
                            "ORIGINAL": api.ActivityDownloadFormat.ORIGINAL,
                        }

                        dl_fmt = format_mapping[fmt]
                        content = api.download_activity(activity_id, dl_fmt=dl_fmt)

                        if content:
                            with open(filepath, "wb") as f:
                                f.write(content)
                            print(f"  ✅ {fmt}: {filename}")
                        else:
                            print(f"  ❌ {fmt}: No content available")

                except Exception as e:
                    print(f"  ❌ {fmt}: Error downloading - {e}")

        print(f"✅ Activity downloads completed! Files saved to: {config.export_dir}")

    except Exception as e:
        print(f"❌ Error downloading activities: {e}")


def add_weigh_in_data(api: Garmin) -> None:
    """Add a weigh-in with timestamps."""
    try:
        # Get weight input from user
        print("⚖️ Adding weigh-in entry")
        print("-" * 30)

        # Weight input with validation
        while True:
            try:
                weight_str = input("Enter weight (30-300, default: 85.1): ").strip()
                if not weight_str:
                    weight = 85.1
                    break
                weight = float(weight_str)
                if 30 <= weight <= 300:
                    break
                print("❌ Weight must be between 30 and 300")
            except ValueError:
                print("❌ Please enter a valid number")

        # Unit selection
        while True:
            unit_input = input("Enter unit (kg/lbs, default: kg): ").strip().lower()
            if not unit_input:
                weight_unit = "kg"
                break
            if unit_input in ["kg", "lbs"]:
                weight_unit = unit_input
                break
            print("❌ Please enter 'kg' or 'lbs'")

        print(f"⚖️ Adding weigh-in: {weight} {weight_unit}")

        # Collect all API responses for grouped display
        api_responses = []

        # Add a simple weigh-in
        result1 = api.add_weigh_in(weight=weight, unitKey=weight_unit)
        api_responses.append(
            (f"api.add_weigh_in(weight={weight}, unitKey={weight_unit})", result1)
        )

        # Add a weigh-in with timestamps for yesterday
        import datetime
        from datetime import timezone

        yesterday = config.today - datetime.timedelta(days=1)  # Get yesterday's date
        weigh_in_date = datetime.datetime.strptime(yesterday.isoformat(), "%Y-%m-%d")
        local_timestamp = weigh_in_date.strftime("%Y-%m-%dT%H:%M:%S")
        gmt_timestamp = weigh_in_date.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )

        result2 = api.add_weigh_in_with_timestamps(
            weight=weight,
            unitKey=weight_unit,
            dateTimestamp=local_timestamp,
            gmtTimestamp=gmt_timestamp,
        )
        api_responses.append(
            (
                f"api.add_weigh_in_with_timestamps(weight={weight}, unitKey={weight_unit}, dateTimestamp={local_timestamp}, gmtTimestamp={gmt_timestamp})",
                result2,
            )
        )

        # Display all responses as a group
        call_and_display(group_name="Weigh-in Data Entry", api_responses=api_responses)

        print("✅ Weigh-in data added successfully!")

    except Exception as e:
        print(f"❌ Error adding weigh-in: {e}")


# Helper functions for the new API methods
def get_lactate_threshold_data(api: Garmin) -> None:
    """Get lactate threshold data."""
    try:
        # Collect all API responses for grouped display
        api_responses = []

        # Get latest lactate threshold
        latest = api.get_lactate_threshold(latest=True)
        api_responses.append(("api.get_lactate_threshold(latest=True)", latest))

        # Get historical lactate threshold for past four weeks
        four_weeks_ago = config.today - datetime.timedelta(days=28)
        historical = api.get_lactate_threshold(
            latest=False,
            start_date=four_weeks_ago.isoformat(),
            end_date=config.today.isoformat(),
            aggregation="daily",
        )
        api_responses.append(
            (
                f"api.get_lactate_threshold(latest=False, start_date='{four_weeks_ago.isoformat()}', end_date='{config.today.isoformat()}', aggregation='daily')",
                historical,
            )
        )

        # Display all responses as a group
        call_and_display(
            group_name="Lactate Threshold Data", api_responses=api_responses
        )

    except Exception as e:
        print(f"❌ Error getting lactate threshold data: {e}")


def get_activity_splits_data(api: Garmin) -> None:
    """Get activity splits for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_splits,
                activity_id,
                method_name="get_activity_splits",
                api_call_desc=f"api.get_activity_splits({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity splits: {e}")


def get_activity_typed_splits_data(api: Garmin) -> None:
    """Get activity typed splits for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_typed_splits,
                activity_id,
                method_name="get_activity_typed_splits",
                api_call_desc=f"api.get_activity_typed_splits({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity typed splits: {e}")


def get_activity_split_summaries_data(api: Garmin) -> None:
    """Get activity split summaries for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_split_summaries,
                activity_id,
                method_name="get_activity_split_summaries",
                api_call_desc=f"api.get_activity_split_summaries({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity split summaries: {e}")


def get_activity_weather_data(api: Garmin) -> None:
    """Get activity weather data for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_weather,
                activity_id,
                method_name="get_activity_weather",
                api_call_desc=f"api.get_activity_weather({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity weather: {e}")


def get_activity_hr_timezones_data(api: Garmin) -> None:
    """Get activity heart rate timezones for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_hr_in_timezones,
                activity_id,
                method_name="get_activity_hr_in_timezones",
                api_call_desc=f"api.get_activity_hr_in_timezones({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity HR timezones: {e}")


def get_activity_power_timezones_data(api: Garmin) -> None:
    """Get activity power timezones for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_power_in_timezones,
                activity_id,
                method_name="get_activity_power_in_timezones",
                api_call_desc=f"api.get_activity_power_in_timezones({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity power timezones: {e}")


def get_cycling_ftp_data(api: Garmin) -> None:
    """Get cycling Functional Threshold Power (FTP) information."""
    call_and_display(
        api.get_cycling_ftp,
        method_name="get_cycling_ftp",
        api_call_desc="api.get_cycling_ftp()",
    )


def get_activity_details_data(api: Garmin) -> None:
    """Get detailed activity information for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_details,
                activity_id,
                method_name="get_activity_details",
                api_call_desc=f"api.get_activity_details({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity details: {e}")


def get_activity_gear_data(api: Garmin) -> None:
    """Get activity gear information for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity_gear,
                activity_id,
                method_name="get_activity_gear",
                api_call_desc=f"api.get_activity_gear({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting activity gear: {e}")


def get_single_activity_data(api: Garmin) -> None:
    """Get single activity data for the last activity."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            call_and_display(
                api.get_activity,
                activity_id,
                method_name="get_activity",
                api_call_desc=f"api.get_activity({activity_id})",
            )
        else:
            print("ℹ️ No activities found")
    except Exception as e:
        print(f"❌ Error getting single activity: {e}")


def get_activity_exercise_sets_data(api: Garmin) -> None:
    """Get exercise sets for strength training activities."""
    try:
        activities = api.get_activities(
            0, 20
        )  # Get more activities to find a strength training one
        strength_activity = None

        # Find strength training activities
        for activity in activities:
            activity_type = activity.get("activityType", {})
            type_key = activity_type.get("typeKey", "")
            if "strength" in type_key.lower() or "training" in type_key.lower():
                strength_activity = activity
                break

        if strength_activity:
            activity_id = strength_activity["activityId"]
            call_and_display(
                api.get_activity_exercise_sets,
                activity_id,
                method_name="get_activity_exercise_sets",
                api_call_desc=f"api.get_activity_exercise_sets({activity_id})",
            )
        else:
            # Return empty JSON response
            print("ℹ️ No strength training activities found")
    except Exception:
        print("ℹ️ No activity exercise sets available")


def get_golf_scorecard_data(api: Garmin) -> None:
    """Get golf scorecard detail by ID."""
    try:
        # First get summary to find valid IDs
        summary = api.get_golf_summary(limit=20)
        if not summary:
            print("❌ No golf scorecards found")
            return

        scorecards = (
            summary
            if isinstance(summary, list)
            else summary.get("scorecardList", summary.get("items", [summary]))
        )
        if isinstance(scorecards, list) and scorecards:
            print("\n⛳ Recent golf scorecards:")
            for i, sc in enumerate(scorecards[:10], 1):
                sc_id = sc.get("scorecardId", sc.get("id", "?"))
                course = sc.get("courseName", sc.get("golfCourseName", "Unknown"))
                sc_date = sc.get("startTime", sc.get("date", "?"))
                print(f"  [{i}] ID={sc_id} - {course} ({sc_date})")

        scorecard_id = input("\nEnter scorecard ID: ").strip()
        if not scorecard_id:
            print("❌ No scorecard ID provided")
            return

        call_and_display(
            api.get_golf_scorecard,
            int(scorecard_id),
            method_name="get_golf_scorecard",
            api_call_desc=f"api.get_golf_scorecard({scorecard_id})",
        )
    except Exception as e:
        print(f"❌ Error getting golf scorecard: {e}")


def get_golf_shot_data_entry(api: Garmin) -> None:
    """Get golf shot data by scorecard ID."""
    try:
        # First get summary to find valid IDs
        summary = api.get_golf_summary(limit=20)
        if not summary:
            print("❌ No golf scorecards found")
            return

        scorecards = (
            summary
            if isinstance(summary, list)
            else summary.get("scorecardList", summary.get("items", [summary]))
        )
        if isinstance(scorecards, list) and scorecards:
            print("\n⛳ Recent golf scorecards:")
            for i, sc in enumerate(scorecards[:10], 1):
                sc_id = sc.get("scorecardId", sc.get("id", "?"))
                course = sc.get("courseName", sc.get("golfCourseName", "Unknown"))
                print(f"  [{i}] ID={sc_id} - {course}")

        scorecard_id = input("\nEnter scorecard ID: ").strip()
        if not scorecard_id:
            print("❌ No scorecard ID provided")
            return

        holes = input(
            "Enter hole numbers (comma-separated, or Enter for all 18): "
        ).strip()
        if not holes:
            holes = "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18"

        call_and_display(
            api.get_golf_shot_data,
            int(scorecard_id),
            hole_numbers=holes,
            method_name="get_golf_shot_data",
            api_call_desc=f"api.get_golf_shot_data({scorecard_id}, hole_numbers='{holes}')",
        )
    except Exception as e:
        print(f"❌ Error getting golf shot data: {e}")


def get_training_plan_by_id_data(api: Garmin) -> None:
    """Get training plan details by ID (routes FBT_ADAPTIVE plans to the adaptive endpoint)."""
    resp = api.get_training_plans() or {}
    training_plans = resp.get("trainingPlanList") or []

    if not training_plans:
        print("ℹ️ No training plans found in your list")
        prompt_text = "Enter training plan ID: "
    else:
        prompt_text = "Enter training plan ID (press Enter for most recent): "

    user_input = input(prompt_text).strip()
    selected = None
    if user_input:
        try:
            wanted_id = int(user_input)
            selected = next(
                (
                    p
                    for p in training_plans
                    if int(p.get("trainingPlanId", 0)) == wanted_id
                ),
                None,
            )
            if not selected:
                print(
                    f"ℹ️ Plan ID {wanted_id} not found in your plans; attempting fetch anyway"
                )
                plan_id = wanted_id
                plan_name = f"Plan {wanted_id}"
                plan_category = None
            else:
                plan_id = int(selected["trainingPlanId"])
                plan_name = selected.get("name", str(plan_id))
                plan_category = selected.get("trainingPlanCategory")
        except ValueError:
            print("❌ Invalid plan ID")
            return
    else:
        if not training_plans:
            print("❌ No training plans available and no ID provided")
            return
        selected = training_plans[-1]
        plan_id = int(selected["trainingPlanId"])
        plan_name = selected.get("name", str(plan_id))
        plan_category = selected.get("trainingPlanCategory")

    if plan_category == "FBT_ADAPTIVE":
        call_and_display(
            api.get_adaptive_training_plan_by_id,
            plan_id,
            method_name="get_adaptive_training_plan_by_id",
            api_call_desc=f"api.get_adaptive_training_plan_by_id({plan_id}) - {plan_name}",
        )
    else:
        call_and_display(
            api.get_training_plan_by_id,
            plan_id,
            method_name="get_training_plan_by_id",
            api_call_desc=f"api.get_training_plan_by_id({plan_id}) - {plan_name}",
        )


def get_workout_by_id_data(api: Garmin) -> None:
    """Get workout by ID for the last workout."""
    try:
        workouts = api.get_workouts()
        if workouts:
            workout_id = workouts[-1]["workoutId"]
            workout_name = workouts[-1]["workoutName"]
            call_and_display(
                api.get_workout_by_id,
                workout_id,
                method_name="get_workout_by_id",
                api_call_desc=f"api.get_workout_by_id({workout_id}) - {workout_name}",
            )
        else:
            print("ℹ️ No workouts found")
    except Exception as e:
        print(f"❌ Error getting workout by ID: {e}")


def download_workout_data(api: Garmin) -> None:
    """Download workout to .FIT file."""
    try:
        workouts = api.get_workouts()
        if workouts:
            workout_id = workouts[-1]["workoutId"]
            workout_name = workouts[-1]["workoutName"]

            print(f"📥 Downloading workout: {workout_name}")
            workout_data = api.download_workout(workout_id)

            if workout_data:
                output_file = config.export_dir / f"{workout_name}_{workout_id}.fit"
                with open(output_file, "wb") as f:
                    f.write(workout_data)
                print(f"✅ Workout downloaded to: {output_file}")
            else:
                print("❌ No workout data available")
        else:
            print("ℹ️ No workouts found")
    except Exception as e:
        print(f"❌ Error downloading workout: {e}")


def upload_workout_data(api: Garmin) -> None:
    """Upload workout from JSON file."""
    try:
        print(f"📤 Uploading workout from file: {config.workoutfile}")

        # Check if file exists
        if not os.path.exists(config.workoutfile):
            print(f"❌ File not found: {config.workoutfile}")
            print(
                "ℹ️ Please ensure the workout JSON file exists in the test_data directory"
            )
            return

        # Load the workout JSON data
        import json

        with open(config.workoutfile, encoding="utf-8") as f:
            workout_data = json.load(f)

        # Get current timestamp in Garmin format
        current_time = datetime.datetime.now()
        garmin_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%S.0")

        # Remove IDs that shouldn't be included when uploading a new workout
        fields_to_remove = ["workoutId", "ownerId", "updatedDate", "createdDate"]
        for field in fields_to_remove:
            if field in workout_data:
                del workout_data[field]

        # Add current timestamps
        workout_data["createdDate"] = garmin_timestamp
        workout_data["updatedDate"] = garmin_timestamp

        # Remove step IDs to ensure new ones are generated
        def clean_step_ids(workout_segments):
            """Recursively remove step IDs from workout structure."""
            if isinstance(workout_segments, list):
                for segment in workout_segments:
                    clean_step_ids(segment)
            elif isinstance(workout_segments, dict):
                # Remove stepId if present
                if "stepId" in workout_segments:
                    del workout_segments["stepId"]

                # Recursively clean nested structures
                if "workoutSteps" in workout_segments:
                    clean_step_ids(workout_segments["workoutSteps"])

                # Handle any other nested lists or dicts
                for value in workout_segments.values():
                    if isinstance(value, list | dict):
                        clean_step_ids(value)

        # Clean step IDs from workout segments
        if "workoutSegments" in workout_data:
            clean_step_ids(workout_data["workoutSegments"])

        # Update workout name to indicate it's uploaded with current timestamp
        original_name = workout_data.get("workoutName", "Workout")
        workout_data["workoutName"] = (
            f"Uploaded {original_name} - {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        print(f"📤 Uploading workout: {workout_data['workoutName']}")

        # Upload the workout
        result = api.upload_workout(workout_data)

        if result:
            print("✅ Workout uploaded successfully!")
            call_and_display(
                lambda: result,  # Use a lambda to pass the result
                method_name="upload_workout",
                api_call_desc="api.upload_workout(workout_data)",
            )
        else:
            print(f"❌ Failed to upload workout from {config.workoutfile}")

    except FileNotFoundError:
        print(f"❌ File not found: {config.workoutfile}")
        print("ℹ️ Please ensure the workout JSON file exists in the test_data directory")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format in {config.workoutfile}: {e}")
        print("ℹ️ Please check the JSON file format")
    except Exception as e:
        print(f"❌ Error uploading workout: {e}")
        # Check for common upload errors
        error_str = str(e)
        if "400" in error_str:
            print("💡 The workout data may be invalid or malformed")
        elif "401" in error_str:
            print("💡 Authentication failed - please login again")
        elif "403" in error_str:
            print("💡 Permission denied - check account permissions")
        elif "409" in error_str:
            print("💡 Workout may already exist")
        elif "422" in error_str:
            print("💡 Workout data validation failed")


def upload_running_workout_data(api: Garmin) -> None:
    """Upload a typed running workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_running_workout import create_sample_running_workout

        print("🏃 Creating and uploading running workout...")
        workout = create_sample_running_workout()
        print(f"📤 Uploading workout: {workout.workoutName}")

        result = api.upload_running_workout(workout)

        if result:
            print("✅ Running workout uploaded successfully!")
            call_and_display(
                lambda: result,
                method_name="upload_running_workout",
                api_call_desc="api.upload_running_workout(workout)",
            )
        else:
            print("❌ Failed to upload running workout")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print(
            "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
        )
    except Exception as e:
        print(f"❌ Error uploading running workout: {e}")


def upload_cycling_workout_data(api: Garmin) -> None:
    """Upload a typed cycling workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_cycling_workout import create_sample_cycling_workout

        print("🚴 Creating and uploading cycling workout...")
        workout = create_sample_cycling_workout()
        print(f"📤 Uploading workout: {workout.workoutName}")

        result = api.upload_cycling_workout(workout)

        if result:
            print("✅ Cycling workout uploaded successfully!")
            call_and_display(
                lambda: result,
                method_name="upload_cycling_workout",
                api_call_desc="api.upload_cycling_workout(workout)",
            )
        else:
            print("❌ Failed to upload cycling workout")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print(
            "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
        )
    except Exception as e:
        print(f"❌ Error uploading cycling workout: {e}")


def upload_swimming_workout_data(api: Garmin) -> None:
    """Upload a typed swimming workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_swimming_workout import create_sample_swimming_workout

        print("🏊 Creating and uploading swimming workout...")
        workout = create_sample_swimming_workout()
        print(f"📤 Uploading workout: {workout.workoutName}")

        result = api.upload_swimming_workout(workout)

        if result:
            print("✅ Swimming workout uploaded successfully!")
            call_and_display(
                lambda: result,
                method_name="upload_swimming_workout",
                api_call_desc="api.upload_swimming_workout(workout)",
            )
        else:
            print("❌ Failed to upload swimming workout")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print(
            "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
        )
    except Exception as e:
        print(f"❌ Error uploading swimming workout: {e}")


def upload_walking_workout_data(api: Garmin) -> None:
    """Upload a typed walking workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_walking_workout import create_sample_walking_workout

        print("🚶 Creating and uploading walking workout...")
        workout = create_sample_walking_workout()
        print(f"📤 Uploading workout: {workout.workoutName}")

        result = api.upload_walking_workout(workout)

        if result:
            print("✅ Walking workout uploaded successfully!")
            call_and_display(
                lambda: result,
                method_name="upload_walking_workout",
                api_call_desc="api.upload_walking_workout(workout)",
            )
        else:
            print("❌ Failed to upload walking workout")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print(
            "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
        )
    except Exception as e:
        print(f"❌ Error uploading walking workout: {e}")


def upload_hiking_workout_data(api: Garmin) -> None:
    """Upload a typed hiking workout."""
    try:
        import sys
        from pathlib import Path

        # Add test_data to path for imports
        test_data_path = Path(__file__).parent / "test_data"
        if str(test_data_path) not in sys.path:
            sys.path.insert(0, str(test_data_path))

        from sample_hiking_workout import create_sample_hiking_workout

        print("🥾 Creating and uploading hiking workout...")
        workout = create_sample_hiking_workout()
        print(f"📤 Uploading workout: {workout.workoutName}")

        result = api.upload_hiking_workout(workout)

        if result:
            print("✅ Hiking workout uploaded successfully!")
            call_and_display(
                lambda: result,
                method_name="upload_hiking_workout",
                api_call_desc="api.upload_hiking_workout(workout)",
            )
        else:
            print("❌ Failed to upload hiking workout")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print(
            "💡 Install pydantic with: pip install pydantic or pip install garminconnect[workout]"
        )
    except Exception as e:
        print(f"❌ Error uploading hiking workout: {e}")


def schedule_workout_data(api: Garmin) -> None:
    """Schedule a workout on a specific date."""
    try:
        workouts = api.get_workouts()
        if not workouts:
            print("ℹ️ No workouts found")
            return

        print("\nAvailable workouts (most recent):")
        for i, workout in enumerate(workouts[:10]):
            workout_id = workout.get("workoutId")
            workout_name = workout.get("workoutName", "Unknown")
            print(f"  [{i}] {workout_name} (ID: {workout_id})")

        try:
            index_input = input(
                f"\nEnter workout index (0-{min(9, len(workouts) - 1)}, or 'q' to cancel): "
            ).strip()

            if index_input.lower() == "q":
                print("❌ Cancelled")
                return

            workout_index = int(index_input)
            if not (0 <= workout_index < min(10, len(workouts))):
                print("❌ Invalid index")
                return

            selected_workout = workouts[workout_index]
            workout_id = selected_workout["workoutId"]
            workout_name = selected_workout.get("workoutName", "Unknown")

            date_input = input(
                f"Enter date to schedule '{workout_name}' (YYYY-MM-DD, default: today): "
            ).strip()
            schedule_date = date_input if date_input else config.today.isoformat()

            call_and_display(
                api.schedule_workout,
                workout_id,
                schedule_date,
                method_name="scheduled_workout",
                api_call_desc=f"api.scheduled_workout({workout_id}, '{schedule_date}') - {workout_name}",
            )

            print("✅ Workout scheduled successfully!")

        except ValueError:
            print("❌ Invalid input")

    except Exception as e:
        print(f"❌ Error scheduling workout: {e}")


def get_scheduled_workout_by_id_data(api: Garmin) -> None:
    """Get scheduled workout by ID."""
    try:
        scheduled_workout_id = input("Enter scheduled workout ID: ").strip()

        if not scheduled_workout_id:
            print("❌ Scheduled workout ID is required")
            return

        call_and_display(
            api.get_scheduled_workout_by_id,
            scheduled_workout_id,
            method_name="get_scheduled_workout_by_id",
            api_call_desc=f"api.get_scheduled_workout_by_id({scheduled_workout_id})",
        )
    except Exception as e:
        print(f"❌ Error getting scheduled workout by ID: {e}")


def delete_workout_data(api: Garmin) -> None:
    """Delete a workout template from the library."""
    try:
        workouts = api.get_workouts()
        if not workouts:
            print("ℹ️ No workouts found")
            return

        print("\nAvailable workouts (most recent):")
        for i, workout in enumerate(workouts[:10]):
            workout_id = workout.get("workoutId")
            workout_name = workout.get("workoutName", "Unknown")
            print(f"  [{i}] {workout_name} (ID: {workout_id})")

        try:
            index_input = input(
                f"\nEnter workout index to delete (0-{min(9, len(workouts) - 1)}, or 'q' to cancel): "
            ).strip()

            if index_input.lower() == "q":
                print("❌ Cancelled")
                return

            workout_index = int(index_input)
            if not (0 <= workout_index < min(10, len(workouts))):
                print("❌ Invalid index")
                return

            selected_workout = workouts[workout_index]
            workout_id = selected_workout["workoutId"]
            workout_name = selected_workout.get("workoutName", "Unknown")

            confirm = input(
                f"Delete '{workout_name}' (ID: {workout_id})? (y/N): "
            ).strip()
            if confirm.lower() != "y":
                print("❌ Cancelled")
                return

            call_and_display(
                api.delete_workout,
                workout_id,
                method_name="delete_workout",
                api_call_desc=f"api.delete_workout({workout_id}) - {workout_name}",
            )
            print("✅ Workout deleted successfully!")

        except ValueError:
            print("❌ Invalid input")

    except Exception as e:
        print(f"❌ Error deleting workout: {e}")


def unschedule_workout_data(api: Garmin) -> None:
    """Remove a scheduled workout from the calendar."""
    try:
        scheduled_id = input("Enter scheduled workout ID to unschedule: ").strip()

        if not scheduled_id:
            print("❌ Scheduled workout ID is required")
            return

        call_and_display(
            api.unschedule_workout,
            scheduled_id,
            method_name="unschedule_workout",
            api_call_desc=f"api.unschedule_workout({scheduled_id})",
        )
        print("✅ Workout unscheduled successfully!")

    except Exception as e:
        print(f"❌ Error unscheduling workout: {e}")


def set_body_composition_data(api: Garmin) -> None:
    """Set body composition data."""
    try:
        print(f"⚖️ Setting body composition data for {config.today.isoformat()}")
        print("-" * 50)

        # Get weight input from user
        while True:
            try:
                weight_str = input(
                    "Enter weight in kg (30-300, default: 85.1): "
                ).strip()
                if not weight_str:
                    weight = 85.1
                    break
                weight = float(weight_str)
                if 30 <= weight <= 300:
                    break
                print("❌ Weight must be between 30 and 300 kg")
            except ValueError:
                print("❌ Please enter a valid number")

        call_and_display(
            api.set_body_composition,
            timestamp=config.today.isoformat(),
            weight=weight,
            percent_fat=15.4,
            percent_hydration=54.8,
            bone_mass=2.9,
            muscle_mass=55.2,
            method_name="set_body_composition",
            api_call_desc=f"api.set_body_composition({config.today.isoformat()}, weight={weight}, ...)",
        )
        print("✅ Body composition data set successfully!")
    except Exception as e:
        print(f"❌ Error setting body composition: {e}")


def add_body_composition_data(api: Garmin) -> None:
    """Add body composition data."""
    try:
        print(f"⚖️ Adding body composition data for {config.today.isoformat()}")
        print("-" * 50)

        # Get weight input from user
        while True:
            try:
                weight_str = input(
                    "Enter weight in kg (30-300, default: 85.1): "
                ).strip()
                if not weight_str:
                    weight = 85.1
                    break
                weight = float(weight_str)
                if 30 <= weight <= 300:
                    break
                print("❌ Weight must be between 30 and 300 kg")
            except ValueError:
                print("❌ Please enter a valid number")

        call_and_display(
            api.add_body_composition,
            config.today.isoformat(),
            weight=weight,
            percent_fat=15.4,
            percent_hydration=54.8,
            visceral_fat_mass=10.8,
            bone_mass=2.9,
            muscle_mass=55.2,
            basal_met=1454.1,
            active_met=None,
            physique_rating=None,
            metabolic_age=33.0,
            visceral_fat_rating=None,
            bmi=22.2,
            method_name="add_body_composition",
            api_call_desc=f"api.add_body_composition({config.today.isoformat()}, weight={weight}, ...)",
        )
        print("✅ Body composition data added successfully!")
    except Exception as e:
        print(f"❌ Error adding body composition: {e}")


def delete_weigh_ins_data(api: Garmin) -> None:
    """Delete all weigh-ins for today."""
    try:
        call_and_display(
            api.delete_weigh_ins,
            config.today.isoformat(),
            delete_all=True,
            method_name="delete_weigh_ins",
            api_call_desc=f"api.delete_weigh_ins({config.today.isoformat()}, delete_all=True)",
        )
        print("✅ Weigh-ins deleted successfully!")
    except Exception as e:
        print(f"❌ Error deleting weigh-ins: {e}")


def delete_weigh_in_data(api: Garmin) -> None:
    """Delete a specific weigh-in."""
    try:
        all_weigh_ins = []

        # Find weigh-ins
        print(f"🔍 Checking daily weigh-ins for today ({config.today.isoformat()})...")
        try:
            daily_weigh_ins = api.get_daily_weigh_ins(config.today.isoformat())

            if daily_weigh_ins and "dateWeightList" in daily_weigh_ins:
                weight_list = daily_weigh_ins["dateWeightList"]
                for weigh_in in weight_list:
                    if isinstance(weigh_in, dict):
                        all_weigh_ins.append(weigh_in)
                print(f"📊 Found {len(all_weigh_ins)} weigh-in(s) for today")
            else:
                print("📊 No weigh-in data found in response")
        except Exception as e:
            print(f"⚠️ Could not fetch daily weigh-ins: {e}")

        if not all_weigh_ins:
            print("ℹ️ No weigh-ins found for today")
            print("💡 You can add a test weigh-in using menu option [4]")
            return

        print(f"\n⚖️ Found {len(all_weigh_ins)} weigh-in(s) available for deletion:")
        print("-" * 70)

        # Display weigh-ins for user selection
        for i, weigh_in in enumerate(all_weigh_ins):
            # Extract weight data - Garmin API uses different field names
            weight = weigh_in.get("weight")
            if weight is None:
                weight = weigh_in.get("weightValue", "Unknown")

            # Convert weight from grams to kg if it's a number
            if isinstance(weight, int | float) and weight > 1000:
                weight = weight / 1000  # Convert from grams to kg
                weight = round(weight, 1)  # Round to 1 decimal place

            unit = weigh_in.get("unitKey", "kg")
            date = weigh_in.get("calendarDate", config.today.isoformat())

            # Try different timestamp fields
            timestamp = (
                weigh_in.get("timestampGMT")
                or weigh_in.get("timestamp")
                or weigh_in.get("date")
            )

            # Format timestamp for display
            if timestamp:
                try:
                    import datetime as dt

                    if isinstance(timestamp, str):
                        # Handle ISO format strings
                        datetime_obj = dt.datetime.fromisoformat(
                            timestamp.replace("Z", "+00:00")
                        )
                    else:
                        # Handle millisecond timestamps
                        datetime_obj = dt.datetime.fromtimestamp(timestamp / 1000)
                    time_str = datetime_obj.strftime("%H:%M:%S")
                except Exception:
                    time_str = "Unknown time"
            else:
                time_str = "Unknown time"

            print(f"  [{i}] {weight} {unit} on {date} at {time_str}")

        print()
        try:
            selection = input(
                "Enter the index of the weigh-in to delete (or 'q' to cancel): "
            ).strip()

            if selection.lower() == "q":
                print("❌ Delete cancelled")
                return

            weigh_in_index = int(selection)
            if 0 <= weigh_in_index < len(all_weigh_ins):
                selected_weigh_in = all_weigh_ins[weigh_in_index]

                # Get the weigh-in ID (Garmin uses 'samplePk' as the primary key)
                weigh_in_id = (
                    selected_weigh_in.get("samplePk")
                    or selected_weigh_in.get("id")
                    or selected_weigh_in.get("weightPk")
                    or selected_weigh_in.get("pk")
                    or selected_weigh_in.get("weightId")
                    or selected_weigh_in.get("uuid")
                )

                if weigh_in_id:
                    weight = selected_weigh_in.get("weight", "Unknown")

                    # Convert weight from grams to kg if it's a number
                    if isinstance(weight, int | float) and weight > 1000:
                        weight = weight / 1000  # Convert from grams to kg
                        weight = round(weight, 1)  # Round to 1 decimal place

                    unit = selected_weigh_in.get("unitKey", "kg")
                    date = selected_weigh_in.get(
                        "calendarDate", config.today.isoformat()
                    )

                    # Confirm deletion
                    confirm = input(
                        f"Delete weigh-in {weight} {unit} from {date}? (yes/no): "
                    ).lower()
                    if confirm == "yes":
                        call_and_display(
                            api.delete_weigh_in,
                            weigh_in_id,
                            config.today.isoformat(),
                            method_name="delete_weigh_in",
                            api_call_desc=f"api.delete_weigh_in({weigh_in_id}, {config.today.isoformat()})",
                        )
                        print("✅ Weigh-in deleted successfully!")
                    else:
                        print("❌ Delete cancelled")
                else:
                    print("❌ No weigh-in ID found for selected entry")
            else:
                print("❌ Invalid selection")

        except ValueError:
            print("❌ Invalid input - please enter a number")

    except Exception as e:
        print(f"❌ Error deleting weigh-in: {e}")


def get_device_settings_data(api: Garmin) -> None:
    """Get device settings for all devices."""
    try:
        devices = api.get_devices()
        if devices:
            for device in devices:
                device_id = device["deviceId"]
                device_name = device.get("displayName", f"Device {device_id}")
                try:
                    call_and_display(
                        api.get_device_settings,
                        device_id,
                        method_name="get_device_settings",
                        api_call_desc=f"api.get_device_settings({device_id}) - {device_name}",
                    )
                except Exception as e:
                    print(f"❌ Error getting settings for device {device_name}: {e}")
        else:
            print("ℹ️ No devices found")
    except Exception as e:
        print(f"❌ Error getting device settings: {e}")


def get_gear_data(api: Garmin) -> None:
    """Get user gear list."""
    print("🔄 Fetching user gear list...")

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number from the first call
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            api_responses.append(
                safe_call_for_group(
                    api.get_gear,
                    user_profile_number,
                    method_name="get_gear",
                    api_call_desc=f"api.get_gear({user_profile_number})",
                )
            )
        else:
            print("❌ Could not get user profile number")

    call_and_display(group_name="User Gear List", api_responses=api_responses)


def get_gear_defaults_data(api: Garmin) -> None:
    """Get gear defaults."""
    print("🔄 Fetching gear defaults...")

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number from the first call
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            api_responses.append(
                safe_call_for_group(
                    api.get_gear_defaults,
                    user_profile_number,
                    method_name="get_gear_defaults",
                    api_call_desc=f"api.get_gear_defaults({user_profile_number})",
                )
            )
        else:
            print("❌ Could not get user profile number")

    call_and_display(group_name="Gear Defaults", api_responses=api_responses)


def get_gear_stats_data(api: Garmin) -> None:
    """Get gear statistics."""
    print("🔄 Fetching comprehensive gear statistics...")

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number and gear list
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            # Get gear list
            api_responses.append(
                safe_call_for_group(
                    api.get_gear,
                    user_profile_number,
                    method_name="get_gear",
                    api_call_desc=f"api.get_gear({user_profile_number})",
                )
            )

            # Get gear data to extract UUIDs for stats
            gear_success, gear_data, _ = safe_api_call(
                api.get_gear, user_profile_number, method_name="get_gear"
            )

            if gear_success and gear_data:
                # Get stats for each gear item (limit to first 3)
                for gear_item in gear_data[:3]:
                    gear_uuid = gear_item.get("uuid")
                    gear_name = gear_item.get("displayName", "Unknown")
                    if gear_uuid:
                        api_responses.append(
                            safe_call_for_group(
                                api.get_gear_stats,
                                gear_uuid,
                                method_name="get_gear_stats",
                                api_call_desc=f"api.get_gear_stats('{gear_uuid}') - {gear_name}",
                            )
                        )
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")

    call_and_display(group_name="Gear Statistics", api_responses=api_responses)


def get_gear_activities_data(api: Garmin) -> None:
    """Get gear activities."""
    print("🔄 Fetching gear activities...")

    api_responses = []

    # Get device info first
    api_responses.append(
        safe_call_for_group(
            api.get_device_last_used,
            method_name="get_device_last_used",
            api_call_desc="api.get_device_last_used()",
        )
    )

    # Get user profile number and gear list
    device_success, device_data, _ = safe_api_call(
        api.get_device_last_used, method_name="get_device_last_used"
    )

    if device_success and device_data:
        user_profile_number = device_data.get("userProfileNumber")
        if user_profile_number:
            # Get gear list
            api_responses.append(
                safe_call_for_group(
                    api.get_gear,
                    user_profile_number,
                    method_name="get_gear",
                    api_call_desc=f"api.get_gear({user_profile_number})",
                )
            )

            # Get gear data to extract UUID for activities
            gear_success, gear_data, _ = safe_api_call(
                api.get_gear, user_profile_number, method_name="get_gear"
            )

            if gear_success and gear_data and len(gear_data) > 0:
                # Get activities for the first gear item
                gear_uuid = gear_data[0].get("uuid")
                gear_name = gear_data[0].get("displayName", "Unknown")

                if gear_uuid:
                    api_responses.append(
                        safe_call_for_group(
                            api.get_gear_activities,
                            gear_uuid,
                            method_name="get_gear_activities",
                            api_call_desc=f"api.get_gear_activities('{gear_uuid}') - {gear_name}",
                        )
                    )
                else:
                    print("❌ No gear UUID found")
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")

    call_and_display(group_name="Gear Activities", api_responses=api_responses)


def set_gear_default_data(api: Garmin) -> None:
    """Set gear default."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear = api.get_gear(user_profile_number)
            if gear:
                gear_uuid = gear[0].get("uuid")
                gear_name = gear[0].get("displayName", "Unknown")
                if gear_uuid:
                    # Set as default for running (activity type ID 1)
                    # Correct method signature: set_gear_default(activityType, gearUUID, defaultGear=True)
                    activity_type = 1  # Running
                    call_and_display(
                        api.set_gear_default,
                        activity_type,
                        gear_uuid,
                        True,
                        method_name="set_gear_default",
                        api_call_desc=f"api.set_gear_default({activity_type}, '{gear_uuid}', True) - {gear_name} for running",
                    )
                    print("✅ Gear default set successfully!")
                else:
                    print("❌ No gear UUID found")
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error setting gear default: {e}")


def add_and_remove_gear_to_activity(api: Garmin) -> None:
    """Add gear to most recent activity, then remove."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear_list = api.get_gear(user_profile_number)
            if gear_list:
                activities = api.get_activities(0, 1)
                if activities:
                    activity_id = activities[0].get("activityId")
                    activity_name = activities[0].get("activityName")
                    for gear in gear_list:
                        if gear["gearStatusName"] == "active":
                            break
                    gear_uuid = gear.get("uuid")
                    gear_name = gear.get("displayName", "Unknown")
                    if gear_uuid:
                        # Add gear to an activity
                        # Correct method signature: add_gear_to_activity(gearUUID, activity_id)
                        call_and_display(
                            api.add_gear_to_activity,
                            gear_uuid,
                            activity_id,
                            method_name="add_gear_to_activity",
                            api_call_desc=f"api.add_gear_to_activity('{gear_uuid}', {activity_id}) - Add {gear_name} to {activity_name}",
                        )
                        print("✅ Gear added successfully!")

                        # Wait for user to check gear, then continue
                        input(
                            "Go check Garmin to confirm, then press Enter to continue"
                        )

                        # Remove gear from an activity
                        # Correct method signature: remove_gear_from_activity(gearUUID, activity_id)
                        call_and_display(
                            api.remove_gear_from_activity,
                            gear_uuid,
                            activity_id,
                            method_name="remove_gear_from_activity",
                            api_call_desc=f"api.remove_gear_from_activity('{gear_uuid}', {activity_id}) - Remove {gear_name} from {activity_name}",
                        )
                        print("✅ Gear removed successfully!")
                    else:
                        print("❌ No activities found")
                else:
                    print("❌ No gear UUID found")
            else:
                print("ℹ️ No gear found")
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error adding gear: {e}")


def set_activity_name_data(api: Garmin) -> None:
    """Set activity name."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            print(f"Current name of fetched activity: {activities[0]['activityName']}")
            new_name = input("Enter new activity name: (or 'q' to cancel): ").strip()

            if new_name.lower() == "q":
                print("❌ Rename cancelled")
                return

            if new_name:
                call_and_display(
                    api.set_activity_name,
                    activity_id,
                    new_name,
                    method_name="set_activity_name",
                    api_call_desc=f"api.set_activity_name({activity_id}, '{new_name}')",
                )
                print("✅ Activity name updated!")
            else:
                print("❌ No name provided")
        else:
            print("❌ No activities found")
    except Exception as e:
        print(f"❌ Error setting activity name: {e}")


def set_activity_type_data(api: Garmin) -> None:
    """Set activity type."""
    try:
        activities = api.get_activities(0, 1)
        if activities:
            activity_id = activities[0]["activityId"]
            activity_types = api.get_activity_types()

            # Show available types
            print("\nAvailable activity types: (limit=10)")
            for i, activity_type in enumerate(activity_types[:10]):  # Show first 10
                print(
                    f"{i}: {activity_type.get('typeKey', 'Unknown')} - {activity_type.get('display', 'No description')}"
                )

            try:
                print(
                    f"Current type of fetched activity '{activities[0]['activityName']}': {activities[0]['activityType']['typeKey']}"
                )
                type_index = input(
                    "Enter activity type index: (or 'q' to cancel): "
                ).strip()

                if type_index.lower() == "q":
                    print("❌ Type change cancelled")
                    return

                type_index = int(type_index)
                if 0 <= type_index < len(activity_types):
                    selected_type = activity_types[type_index]
                    type_id = selected_type["typeId"]
                    type_key = selected_type["typeKey"]
                    parent_type_id = selected_type.get(
                        "parentTypeId", selected_type["typeId"]
                    )

                    call_and_display(
                        api.set_activity_type,
                        activity_id,
                        type_id,
                        type_key,
                        parent_type_id,
                        method_name="set_activity_type",
                        api_call_desc=f"api.set_activity_type({activity_id}, {type_id}, '{type_key}', {parent_type_id})",
                    )
                    print("✅ Activity type updated!")
                else:
                    print("❌ Invalid index")
            except ValueError:
                print("❌ Invalid input")
        else:
            print("❌ No activities found")
    except Exception as e:
        print(f"❌ Error setting activity type: {e}")


def create_manual_activity_data(api: Garmin) -> None:
    """Create manual activity."""
    try:
        print("Creating manual activity...")
        print("Enter activity details (press Enter for defaults):")

        activity_name = (
            input("Activity name [Manual Activity]: ").strip() or "Manual Activity"
        )
        type_key = input("Activity type key [running]: ").strip() or "running"
        duration_min = input("Duration in minutes [60]: ").strip() or "60"
        distance_km = input("Distance in kilometers [5]: ").strip() or "5"
        timezone = input("Timezone [UTC]: ").strip() or "UTC"

        try:
            duration_min = float(duration_min)
            distance_km = float(distance_km)

            # Use the current time as start time
            import datetime

            start_datetime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.00")

            call_and_display(
                api.create_manual_activity,
                start_datetime=start_datetime,
                time_zone=timezone,
                type_key=type_key,
                distance_km=distance_km,
                duration_min=duration_min,
                activity_name=activity_name,
                method_name="create_manual_activity",
                api_call_desc=f"api.create_manual_activity(start_datetime='{start_datetime}', time_zone='{timezone}', type_key='{type_key}', distance_km={distance_km}, duration_min={duration_min}, activity_name='{activity_name}')",
            )
            print("✅ Manual activity created!")
        except ValueError:
            print("❌ Invalid numeric input")
    except Exception as e:
        print(f"❌ Error creating manual activity: {e}")


def delete_activity_data(api: Garmin) -> None:
    """Delete activity."""
    try:
        activities = api.get_activities(0, 5)
        if activities:
            print("\nRecent activities:")
            for i, activity in enumerate(activities):
                activity_name = activity.get("activityName", "Unnamed")
                activity_id = activity.get("activityId")
                start_time = activity.get("startTimeLocal", "Unknown time")
                print(f"{i}: {activity_name} ({activity_id}) - {start_time}")

            try:
                activity_index = input(
                    "Enter activity index to delete: (or 'q' to cancel): "
                ).strip()

                if activity_index.lower() == "q":
                    print("❌ Delete cancelled")
                    return
                activity_index = int(activity_index)
                if 0 <= activity_index < len(activities):
                    activity_id = activities[activity_index]["activityId"]
                    activity_name = activities[activity_index].get(
                        "activityName", "Unnamed"
                    )

                    confirm = input(f"Delete '{activity_name}'? (yes/no): ").lower()
                    if confirm == "yes":
                        call_and_display(
                            api.delete_activity,
                            activity_id,
                            method_name="delete_activity",
                            api_call_desc=f"api.delete_activity({activity_id})",
                        )
                        print("✅ Activity deleted!")
                    else:
                        print("❌ Delete cancelled")
                else:
                    print("❌ Invalid index")
            except ValueError:
                print("❌ Invalid input")
        else:
            print("❌ No activities found")
    except Exception as e:
        print(f"❌ Error deleting activity: {e}")


def delete_blood_pressure_data(api: Garmin) -> None:
    """Delete blood pressure entry."""
    try:
        # Get recent blood pressure entries
        bp_data = api.get_blood_pressure(
            config.week_start.isoformat(), config.today.isoformat()
        )
        entry_list = []

        # Parse the actual blood pressure data structure
        if bp_data and bp_data.get("measurementSummaries"):
            for summary in bp_data["measurementSummaries"]:
                if summary.get("measurements"):
                    for measurement in summary["measurements"]:
                        # Use 'version' as the identifier (this is what Garmin uses)
                        entry_id = measurement.get("version")
                        systolic = measurement.get("systolic")
                        diastolic = measurement.get("diastolic")
                        pulse = measurement.get("pulse")
                        timestamp = measurement.get("measurementTimestampLocal")
                        notes = measurement.get("notes", "")

                        # Extract date for deletion API (format: YYYY-MM-DD)
                        measurement_date = None
                        if timestamp:
                            try:
                                measurement_date = timestamp.split("T")[
                                    0
                                ]  # Get just the date part
                            except Exception:
                                measurement_date = summary.get(
                                    "startDate"
                                )  # Fallback to summary date
                        else:
                            measurement_date = summary.get(
                                "startDate"
                            )  # Fallback to summary date

                        if entry_id and systolic and diastolic and measurement_date:
                            # Format display text with more details
                            display_parts = [f"{systolic}/{diastolic}"]
                            if pulse:
                                display_parts.append(f"pulse {pulse}")
                            if timestamp:
                                display_parts.append(f"at {timestamp}")
                            if notes:
                                display_parts.append(f"({notes})")

                            display_text = " ".join(display_parts)
                            # Store both entry_id and measurement_date for deletion
                            entry_list.append(
                                (entry_id, display_text, measurement_date)
                            )

        if entry_list:
            print(f"\n📊 Found {len(entry_list)} blood pressure entries:")
            print("-" * 70)
            for i, (entry_id, display_text, _measurement_date) in enumerate(entry_list):
                print(f"  [{i}] {display_text} (ID: {entry_id})")

            try:
                entry_index = input(
                    "\nEnter entry index to delete: (or 'q' to cancel): "
                ).strip()

                if entry_index.lower() == "q":
                    print("❌ Entry deletion cancelled")
                    return

                entry_index = int(entry_index)
                if 0 <= entry_index < len(entry_list):
                    entry_id, display_text, measurement_date = entry_list[entry_index]
                    confirm = input(
                        f"Delete entry '{display_text}'? (yes/no): "
                    ).lower()
                    if confirm == "yes":
                        call_and_display(
                            api.delete_blood_pressure,
                            entry_id,
                            measurement_date,
                            method_name="delete_blood_pressure",
                            api_call_desc=f"api.delete_blood_pressure('{entry_id}', '{measurement_date}')",
                        )
                        print("✅ Blood pressure entry deleted!")
                    else:
                        print("❌ Delete cancelled")
                else:
                    print("❌ Invalid index")
            except ValueError:
                print("❌ Invalid input")
        else:
            print("❌ No blood pressure entries found for past week")
            print("💡 You can add a test measurement using menu option [3]")

    except Exception as e:
        print(f"❌ Error deleting blood pressure: {e}")


def query_garmin_graphql_data(api: Garmin) -> None:
    """Execute GraphQL query with a menu of available queries."""
    try:
        print("Available GraphQL queries:")
        print("  [1] Activities (recent activities with details)")
        print("  [2] Health Snapshot (comprehensive health data)")
        print("  [3] Weight Data (weight measurements)")
        print("  [4] Blood Pressure (blood pressure data)")
        print("  [5] Sleep Summaries (sleep analysis)")
        print("  [6] Heart Rate Variability (HRV data)")
        print("  [7] User Daily Summary (comprehensive daily stats)")
        print("  [8] Training Readiness (training readiness metrics)")
        print("  [9] Training Status (training status data)")
        print("  [10] Activity Stats (aggregated activity statistics)")
        print("  [11] VO2 Max (VO2 max data)")
        print("  [12] Endurance Score (endurance scoring)")
        print("  [13] User Goals (current goals)")
        print("  [14] Stress Data (epoch chart with stress)")
        print("  [15] Badge Challenges (available challenges)")
        print("  [16] Adhoc Challenges (adhoc challenges)")
        print("  [c] Custom query")

        choice = input("\nEnter choice (1-16, c): ").strip()

        # Use today's date and date range for queries that need them
        today = config.today.isoformat()
        week_start = config.week_start.isoformat()
        start_datetime = f"{today}T00:00:00.00"
        end_datetime = f"{today}T23:59:59.999"

        if choice == "1":
            query = f'query{{activitiesScalar(displayName:"{api.display_name}", startTimestampLocal:"{start_datetime}", endTimestampLocal:"{end_datetime}", limit:10)}}'
        elif choice == "2":
            query = f'query{{healthSnapshotScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "3":
            query = (
                f'query{{weightScalar(startDate:"{week_start}", endDate:"{today}")}}'
            )
        elif choice == "4":
            query = f'query{{bloodPressureScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "5":
            query = f'query{{sleepSummariesScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "6":
            query = f'query{{heartRateVariabilityScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "7":
            query = f'query{{userDailySummaryV2Scalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "8":
            query = f'query{{trainingReadinessRangeScalar(startDate:"{week_start}", endDate:"{today}")}}'
        elif choice == "9":
            query = f'query{{trainingStatusDailyScalar(calendarDate:"{today}")}}'
        elif choice == "10":
            query = f'query{{activityStatsScalar(aggregation:"daily", startDate:"{week_start}", endDate:"{today}", metrics:["duration", "distance"], groupByParentActivityType:true, standardizedUnits:true)}}'
        elif choice == "11":
            query = (
                f'query{{vo2MaxScalar(startDate:"{week_start}", endDate:"{today}")}}'
            )
        elif choice == "12":
            query = f'query{{enduranceScoreScalar(startDate:"{week_start}", endDate:"{today}", aggregation:"weekly")}}'
        elif choice == "13":
            query = "query{userGoalsScalar}"
        elif choice == "14":
            query = f'query{{epochChartScalar(date:"{today}", include:["stress"])}}'
        elif choice == "15":
            query = "query{badgeChallengesScalar}"
        elif choice == "16":
            query = "query{adhocChallengesScalar}"
        elif choice.lower() == "c":
            print("\nEnter your custom GraphQL query:")
            print("Example: query{userGoalsScalar}")
            query = input("Query: ").strip()
        else:
            print("❌ Invalid choice")
            return

        if query:
            # GraphQL API expects a dictionary with the query as a string value
            graphql_payload = {"query": query}
            call_and_display(
                api.query_garmin_graphql,
                graphql_payload,
                method_name="query_garmin_graphql",
                api_call_desc=f"api.query_garmin_graphql({graphql_payload})",
            )
        else:
            print("❌ No query provided")
    except Exception as e:
        print(f"❌ Error executing GraphQL query: {e}")


def get_virtual_challenges_data(api: Garmin) -> None:
    """Get virtual challenges data with centralized error handling."""
    print("🏆 Attempting to get virtual challenges data...")

    # Try in-progress virtual challenges - this endpoint often returns 400 for accounts
    # that don't have virtual challenges enabled, so handle it quietly
    try:
        challenges = api.get_inprogress_virtual_challenges(
            config.start_badge, config.default_limit
        )
        if challenges:
            print("✅ Virtual challenges data retrieved successfully")
            call_and_display(
                api.get_inprogress_virtual_challenges,
                config.start_badge,
                config.default_limit,
                method_name="get_inprogress_virtual_challenges",
                api_call_desc=f"api.get_inprogress_virtual_challenges({config.start_badge}, {config.default_limit})",
            )
            return
        print("ℹ️ No in-progress virtual challenges found")
        return
    except GarminConnectConnectionError as e:
        # Handle the common 400 error case quietly - this is expected for many accounts
        error_str = str(e)
        if "400" in error_str and (
            "Bad Request" in error_str or "API client error" in error_str
        ):
            print("ℹ️ Virtual challenges are not available for your account")
        else:
            # For unexpected connection errors, show them
            print(f"⚠️ Connection error accessing virtual challenges: {error_str}")
    except Exception as e:
        print(f"⚠️ Unexpected error accessing virtual challenges: {e}")

    # Since virtual challenges failed or returned no data, suggest alternatives
    print("💡 You can try other challenge-related endpoints instead:")
    print("   - Badge challenges (menu option 7-8)")
    print("   - Available badge challenges (menu option 7-4)")
    print("   - Adhoc challenges (menu option 7-3)")


def add_hydration_data_entry(api: Garmin) -> None:
    """Add hydration data entry."""
    try:
        import datetime

        value_in_ml = 240
        raw_date = config.today
        cdate = str(raw_date)
        raw_ts = datetime.datetime.now()
        timestamp = datetime.datetime.strftime(raw_ts, "%Y-%m-%dT%H:%M:%S.%f")

        call_and_display(
            api.add_hydration_data,
            value_in_ml=value_in_ml,
            cdate=cdate,
            timestamp=timestamp,
            method_name="add_hydration_data",
            api_call_desc=f"api.add_hydration_data(value_in_ml={value_in_ml}, cdate='{cdate}', timestamp='{timestamp}')",
        )
        print("✅ Hydration data added successfully!")
    except Exception as e:
        print(f"❌ Error adding hydration data: {e}")


def set_blood_pressure_data(api: Garmin) -> None:
    """Set blood pressure (and pulse) data."""
    try:
        print("🩸 Adding blood pressure (and pulse) measurement")
        print("Enter blood pressure values (press Enter for defaults):")

        # Get systolic pressure
        systolic_input = input("Systolic pressure [120]: ").strip()
        systolic = int(systolic_input) if systolic_input else 120

        # Get diastolic pressure
        diastolic_input = input("Diastolic pressure [80]: ").strip()
        diastolic = int(diastolic_input) if diastolic_input else 80

        # Get pulse
        pulse_input = input("Pulse rate [60]: ").strip()
        pulse = int(pulse_input) if pulse_input else 60

        # Get notes (optional)
        notes = input("Notes (optional): ").strip() or "Added via demo.py"

        # Validate ranges
        if not (50 <= systolic <= 300):
            print("❌ Invalid systolic pressure (should be between 50-300)")
            return
        if not (30 <= diastolic <= 200):
            print("❌ Invalid diastolic pressure (should be between 30-200)")
            return
        if not (30 <= pulse <= 250):
            print("❌ Invalid pulse rate (should be between 30-250)")
            return

        print(f"📊 Recording: {systolic}/{diastolic} mmHg, pulse {pulse} bpm")

        call_and_display(
            api.set_blood_pressure,
            systolic,
            diastolic,
            pulse,
            notes=notes,
            method_name="set_blood_pressure",
            api_call_desc=f"api.set_blood_pressure({systolic}, {diastolic}, {pulse}, notes='{notes}')",
        )
        print("✅ Blood pressure data set successfully!")

    except ValueError:
        print("❌ Invalid input - please enter numeric values")
    except Exception as e:
        print(f"❌ Error setting blood pressure: {e}")


def track_gear_usage_data(api: Garmin) -> None:
    """Calculate total time of use of a piece of gear by going through all activities where said gear has been used."""
    try:
        device_last_used = api.get_device_last_used()
        user_profile_number = device_last_used.get("userProfileNumber")
        if user_profile_number:
            gear_list = api.get_gear(user_profile_number)
            # call_and_display(api.get_gear, user_profile_number, method_name="get_gear", api_call_desc=f"api.get_gear({user_profile_number})")
            if gear_list and isinstance(gear_list, list):
                first_gear = gear_list[0]
                gear_uuid = first_gear.get("uuid")
                gear_name = first_gear.get("displayName", "Unknown")
                print(f"Tracking usage for gear: {gear_name} (UUID: {gear_uuid})")
                activityList = api.get_gear_activities(gear_uuid)
                if len(activityList) == 0:
                    print("No activities found for the given gear uuid.")
                else:
                    print("Found " + str(len(activityList)) + " activities.")

                D = 0
                for a in activityList:
                    print(
                        "Activity: "
                        + a["startTimeLocal"]
                        + (" | " + a["activityName"] if a["activityName"] else "")
                    )
                    print(
                        "  Duration: "
                        + format_timedelta(datetime.timedelta(seconds=a["duration"]))
                    )
                    D += a["duration"]
                print("")
                print(
                    "Total Duration: " + format_timedelta(datetime.timedelta(seconds=D))
                )
                print("")
            else:
                print("No gear found for this user.")
        else:
            print("❌ Could not get user profile number")
    except Exception as e:
        print(f"❌ Error getting gear for track_gear_usage_data: {e}")


def execute_api_call(api: Garmin, key: str) -> None:
    """Execute an API call based on the key."""
    if not api:
        print("API not available")
        return

    try:
        # Map of keys to API methods - this can be extended as needed
        api_methods = {
            # User & Profile
            "get_full_name": lambda: call_and_display(
                api.get_full_name,
                method_name="get_full_name",
                api_call_desc="api.get_full_name()",
            ),
            "get_unit_system": lambda: call_and_display(
                api.get_unit_system,
                method_name="get_unit_system",
                api_call_desc="api.get_unit_system()",
            ),
            "get_user_profile": lambda: call_and_display(
                api.get_user_profile,
                method_name="get_user_profile",
                api_call_desc="api.get_user_profile()",
            ),
            "get_userprofile_settings": lambda: call_and_display(
                api.get_userprofile_settings,
                method_name="get_userprofile_settings",
                api_call_desc="api.get_userprofile_settings()",
            ),
            # Daily Health & Activity
            "get_stats": lambda: call_and_display(
                api.get_stats,
                config.today.isoformat(),
                method_name="get_stats",
                api_call_desc=f"api.get_stats('{config.today.isoformat()}')",
            ),
            "get_user_summary": lambda: call_and_display(
                api.get_user_summary,
                config.today.isoformat(),
                method_name="get_user_summary",
                api_call_desc=f"api.get_user_summary('{config.today.isoformat()}')",
            ),
            "get_stats_and_body": lambda: call_and_display(
                api.get_stats_and_body,
                config.today.isoformat(),
                method_name="get_stats_and_body",
                api_call_desc=f"api.get_stats_and_body('{config.today.isoformat()}')",
            ),
            "get_steps_data": lambda: call_and_display(
                api.get_steps_data,
                config.today.isoformat(),
                method_name="get_steps_data",
                api_call_desc=f"api.get_steps_data('{config.today.isoformat()}')",
            ),
            "get_heart_rates": lambda: call_and_display(
                api.get_heart_rates,
                config.today.isoformat(),
                method_name="get_heart_rates",
                api_call_desc=f"api.get_heart_rates('{config.today.isoformat()}')",
            ),
            "get_resting_heart_rate": lambda: call_and_display(
                api.get_rhr_day,
                config.today.isoformat(),
                method_name="get_rhr_day",
                api_call_desc=f"api.get_rhr_day('{config.today.isoformat()}')",
            ),
            "get_sleep_data": lambda: call_and_display(
                api.get_sleep_data,
                config.today.isoformat(),
                method_name="get_sleep_data",
                api_call_desc=f"api.get_sleep_data('{config.today.isoformat()}')",
            ),
            "get_all_day_stress": lambda: call_and_display(
                api.get_all_day_stress,
                config.today.isoformat(),
                method_name="get_all_day_stress",
                api_call_desc=f"api.get_all_day_stress('{config.today.isoformat()}')",
            ),
            # Advanced Health Metrics
            "get_running_tolerance": lambda: call_and_display(
                api.get_running_tolerance,
                config.week_start.isoformat(),
                config.today.isoformat(),
            ),
            "get_training_readiness": lambda: call_and_display(
                api.get_training_readiness,
                config.today.isoformat(),
                method_name="get_training_readiness",
                api_call_desc=f"api.get_training_readiness('{config.today.isoformat()}')",
            ),
            "get_morning_training_readiness": lambda: call_and_display(
                api.get_morning_training_readiness,
                config.today.isoformat(),
                method_name="get_morning_training_readiness",
                api_call_desc=f"api.get_morning_training_readiness('{config.today.isoformat()}')",
            ),
            "get_training_status": lambda: call_and_display(
                api.get_training_status,
                config.today.isoformat(),
                method_name="get_training_status",
                api_call_desc=f"api.get_training_status('{config.today.isoformat()}')",
            ),
            "get_respiration_data": lambda: call_and_display(
                api.get_respiration_data,
                config.today.isoformat(),
                method_name="get_respiration_data",
                api_call_desc=f"api.get_respiration_data('{config.today.isoformat()}')",
            ),
            "get_spo2_data": lambda: call_and_display(
                api.get_spo2_data,
                config.today.isoformat(),
                method_name="get_spo2_data",
                api_call_desc=f"api.get_spo2_data('{config.today.isoformat()}')",
            ),
            "get_max_metrics": lambda: call_and_display(
                api.get_max_metrics,
                config.today.isoformat(),
                method_name="get_max_metrics",
                api_call_desc=f"api.get_max_metrics('{config.today.isoformat()}')",
            ),
            "get_hrv_data": lambda: call_and_display(
                api.get_hrv_data,
                config.today.isoformat(),
                method_name="get_hrv_data",
                api_call_desc=f"api.get_hrv_data('{config.today.isoformat()}')",
            ),
            "get_fitnessage_data": lambda: call_and_display(
                api.get_fitnessage_data,
                config.today.isoformat(),
                method_name="get_fitnessage_data",
                api_call_desc=f"api.get_fitnessage_data('{config.today.isoformat()}')",
            ),
            "get_stress_data": lambda: call_and_display(
                api.get_stress_data,
                config.today.isoformat(),
                method_name="get_stress_data",
                api_call_desc=f"api.get_stress_data('{config.today.isoformat()}')",
            ),
            "get_lactate_threshold": lambda: get_lactate_threshold_data(api),
            "get_intensity_minutes_data": lambda: call_and_display(
                api.get_intensity_minutes_data,
                config.today.isoformat(),
                method_name="get_intensity_minutes_data",
                api_call_desc=f"api.get_intensity_minutes_data('{config.today.isoformat()}')",
            ),
            "get_lifestyle_logging_data": lambda: call_and_display(
                api.get_lifestyle_logging_data,
                config.today.isoformat(),
                method_name="get_lifestyle_logging_data",
                api_call_desc=f"api.get_lifestyle_logging_data('{config.today.isoformat()}')",
            ),
            # Historical Data & Trends
            "get_daily_steps": lambda: call_and_display(
                api.get_daily_steps,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_daily_steps",
                api_call_desc=f"api.get_daily_steps('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_floors": lambda: call_and_display(
                api.get_floors,
                config.week_start.isoformat(),
                method_name="get_floors",
                api_call_desc=f"api.get_floors('{config.week_start.isoformat()}')",
            ),
            "get_blood_pressure": lambda: call_and_display(
                api.get_blood_pressure,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_blood_pressure",
                api_call_desc=f"api.get_blood_pressure('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_progress_summary_between_dates": lambda: call_and_display(
                api.get_progress_summary_between_dates,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_progress_summary_between_dates",
                api_call_desc=f"api.get_progress_summary_between_dates('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_weekly_steps": lambda: call_and_display(
                api.get_weekly_steps,
                config.today.isoformat(),
                52,
                method_name="get_weekly_steps",
                api_call_desc=f"api.get_weekly_steps('{config.today.isoformat()}', 52)",
            ),
            "get_weekly_stress": lambda: call_and_display(
                api.get_weekly_stress,
                config.today.isoformat(),
                52,
                method_name="get_weekly_stress",
                api_call_desc=f"api.get_weekly_stress('{config.today.isoformat()}', 52)",
            ),
            "get_weekly_intensity_minutes": lambda: call_and_display(
                api.get_weekly_intensity_minutes,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_weekly_intensity_minutes",
                api_call_desc=f"api.get_weekly_intensity_minutes('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            # Activities & Workouts
            "get_activities": lambda: call_and_display(
                api.get_activities,
                config.start,
                config.default_limit,
                method_name="get_activities",
                api_call_desc=f"api.get_activities({config.start}, {config.default_limit})",
            ),
            "get_last_activity": lambda: call_and_display(
                api.get_last_activity,
                method_name="get_last_activity",
                api_call_desc="api.get_last_activity()",
            ),
            "get_activities_fordate": lambda: call_and_display(
                api.get_activities_fordate,
                config.today.isoformat(),
                method_name="get_activities_fordate",
                api_call_desc=f"api.get_activities_fordate('{config.today.isoformat()}')",
            ),
            "get_activity_types": lambda: call_and_display(
                api.get_activity_types,
                method_name="get_activity_types",
                api_call_desc="api.get_activity_types()",
            ),
            "get_workouts": lambda: call_and_display(
                api.get_workouts,
                method_name="get_workouts",
                api_call_desc="api.get_workouts()",
            ),
            "get_training_plan_by_id": lambda: get_training_plan_by_id_data(api),
            "get_training_plans": lambda: call_and_display(
                api.get_training_plans,
                method_name="get_training_plans",
                api_call_desc="api.get_training_plans()",
            ),
            # Golf
            "get_golf_summary": lambda: call_and_display(
                api.get_golf_summary,
                method_name="get_golf_summary",
                api_call_desc="api.get_golf_summary()",
            ),
            "get_golf_scorecard": lambda: get_golf_scorecard_data(api),
            "get_golf_shot_data": lambda: get_golf_shot_data_entry(api),
            "upload_activity": lambda: upload_activity_file(api),
            "import_activity": lambda: import_activity_file(api),
            "download_activities": lambda: download_activities_by_date(api),
            "get_activity_splits": lambda: get_activity_splits_data(api),
            "get_activity_typed_splits": lambda: get_activity_typed_splits_data(api),
            "get_activity_split_summaries": lambda: get_activity_split_summaries_data(
                api
            ),
            "get_activity_weather": lambda: get_activity_weather_data(api),
            "get_activity_hr_in_timezones": lambda: get_activity_hr_timezones_data(api),
            "get_activity_power_in_timezones": lambda: (
                get_activity_power_timezones_data(api)
            ),
            "get_cycling_ftp": lambda: get_cycling_ftp_data(api),
            "get_activity_details": lambda: get_activity_details_data(api),
            "get_activity_gear": lambda: get_activity_gear_data(api),
            "get_activity": lambda: get_single_activity_data(api),
            "get_activity_exercise_sets": lambda: get_activity_exercise_sets_data(api),
            "get_workout_by_id": lambda: get_workout_by_id_data(api),
            "download_workout": lambda: download_workout_data(api),
            "upload_workout": lambda: upload_workout_data(api),
            "upload_running_workout": lambda: upload_running_workout_data(api),
            "upload_cycling_workout": lambda: upload_cycling_workout_data(api),
            "upload_swimming_workout": lambda: upload_swimming_workout_data(api),
            "upload_walking_workout": lambda: upload_walking_workout_data(api),
            "upload_hiking_workout": lambda: upload_hiking_workout_data(api),
            "get_scheduled_workout_by_id": lambda: get_scheduled_workout_by_id_data(
                api
            ),
            "scheduled_workout": lambda: schedule_workout_data(api),
            "delete_workout": lambda: delete_workout_data(api),
            "unschedule_workout": lambda: unschedule_workout_data(api),
            "count_activities": lambda: call_and_display(
                api.count_activities,
                method_name="count_activities",
                api_call_desc="api.count_activities()",
            ),
            # Body Composition & Weight
            "get_body_composition": lambda: call_and_display(
                api.get_body_composition,
                config.today.isoformat(),
                method_name="get_body_composition",
                api_call_desc=f"api.get_body_composition('{config.today.isoformat()}')",
            ),
            "get_weigh_ins": lambda: call_and_display(
                api.get_weigh_ins,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_weigh_ins",
                api_call_desc=f"api.get_weigh_ins('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_daily_weigh_ins": lambda: call_and_display(
                api.get_daily_weigh_ins,
                config.today.isoformat(),
                method_name="get_daily_weigh_ins",
                api_call_desc=f"api.get_daily_weigh_ins('{config.today.isoformat()}')",
            ),
            "add_weigh_in": lambda: add_weigh_in_data(api),
            "set_body_composition": lambda: set_body_composition_data(api),
            "add_body_composition": lambda: add_body_composition_data(api),
            "delete_weigh_ins": lambda: delete_weigh_ins_data(api),
            "delete_weigh_in": lambda: delete_weigh_in_data(api),
            # Goals & Achievements
            "get_personal_records": lambda: call_and_display(
                api.get_personal_record,
                method_name="get_personal_record",
                api_call_desc="api.get_personal_record()",
            ),
            "get_earned_badges": lambda: call_and_display(
                api.get_earned_badges,
                method_name="get_earned_badges",
                api_call_desc="api.get_earned_badges()",
            ),
            "get_adhoc_challenges": lambda: call_and_display(
                api.get_adhoc_challenges,
                config.start,
                config.default_limit,
                method_name="get_adhoc_challenges",
                api_call_desc=f"api.get_adhoc_challenges({config.start}, {config.default_limit})",
            ),
            "get_available_badge_challenges": lambda: call_and_display(
                api.get_available_badge_challenges,
                config.start_badge,
                config.default_limit,
                method_name="get_available_badge_challenges",
                api_call_desc=f"api.get_available_badge_challenges({config.start_badge}, {config.default_limit})",
            ),
            "get_active_goals": lambda: call_and_display(
                api.get_goals,
                status="active",
                start=config.start,
                limit=config.default_limit,
                method_name="get_goals",
                api_call_desc=f"api.get_goals(status='active', start={config.start}, limit={config.default_limit})",
            ),
            "get_future_goals": lambda: call_and_display(
                api.get_goals,
                status="future",
                start=config.start,
                limit=config.default_limit,
                method_name="get_goals",
                api_call_desc=f"api.get_goals(status='future', start={config.start}, limit={config.default_limit})",
            ),
            "get_past_goals": lambda: call_and_display(
                api.get_goals,
                status="past",
                start=config.start,
                limit=config.default_limit,
                method_name="get_goals",
                api_call_desc=f"api.get_goals(status='past', start={config.start}, limit={config.default_limit})",
            ),
            "get_badge_challenges": lambda: call_and_display(
                api.get_badge_challenges,
                config.start_badge,
                config.default_limit,
                method_name="get_badge_challenges",
                api_call_desc=f"api.get_badge_challenges({config.start_badge}, {config.default_limit})",
            ),
            "get_non_completed_badge_challenges": lambda: call_and_display(
                api.get_non_completed_badge_challenges,
                config.start_badge,
                config.default_limit,
                method_name="get_non_completed_badge_challenges",
                api_call_desc=f"api.get_non_completed_badge_challenges({config.start_badge}, {config.default_limit})",
            ),
            "get_inprogress_virtual_challenges": lambda: get_virtual_challenges_data(
                api
            ),
            "get_race_predictions": lambda: call_and_display(
                api.get_race_predictions,
                method_name="get_race_predictions",
                api_call_desc="api.get_race_predictions()",
            ),
            "get_hill_score": lambda: call_and_display(
                api.get_hill_score,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_hill_score",
                api_call_desc=f"api.get_hill_score('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_endurance_score": lambda: call_and_display(
                api.get_endurance_score,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_endurance_score",
                api_call_desc=f"api.get_endurance_score('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            "get_available_badges": lambda: call_and_display(
                api.get_available_badges,
                method_name="get_available_badges",
                api_call_desc="api.get_available_badges()",
            ),
            "get_in_progress_badges": lambda: call_and_display(
                api.get_in_progress_badges,
                method_name="get_in_progress_badges",
                api_call_desc="api.get_in_progress_badges()",
            ),
            # Device & Technical
            "get_devices": lambda: call_and_display(
                api.get_devices,
                method_name="get_devices",
                api_call_desc="api.get_devices()",
            ),
            "get_device_alarms": lambda: call_and_display(
                api.get_device_alarms,
                method_name="get_device_alarms",
                api_call_desc="api.get_device_alarms()",
            ),
            "get_solar_data": lambda: get_solar_data(api),
            "request_reload": lambda: call_and_display(
                api.request_reload,
                config.today.isoformat(),
                method_name="request_reload",
                api_call_desc=f"api.request_reload('{config.today.isoformat()}')",
            ),
            "get_device_settings": lambda: get_device_settings_data(api),
            "get_device_last_used": lambda: call_and_display(
                api.get_device_last_used,
                method_name="get_device_last_used",
                api_call_desc="api.get_device_last_used()",
            ),
            "get_primary_training_device": lambda: call_and_display(
                api.get_primary_training_device,
                method_name="get_primary_training_device",
                api_call_desc="api.get_primary_training_device()",
            ),
            # Gear & Equipment
            "get_gear": lambda: get_gear_data(api),
            "get_gear_defaults": lambda: get_gear_defaults_data(api),
            "get_gear_stats": lambda: get_gear_stats_data(api),
            "get_gear_activities": lambda: get_gear_activities_data(api),
            "set_gear_default": lambda: set_gear_default_data(api),
            "track_gear_usage": lambda: track_gear_usage_data(api),
            "add_and_remove_gear_to_activity": lambda: add_and_remove_gear_to_activity(
                api
            ),
            # Hydration & Wellness
            "get_hydration_data": lambda: call_and_display(
                api.get_hydration_data,
                config.today.isoformat(),
                method_name="get_hydration_data",
                api_call_desc=f"api.get_hydration_data('{config.today.isoformat()}')",
            ),
            "get_pregnancy_summary": lambda: call_and_display(
                api.get_pregnancy_summary,
                method_name="get_pregnancy_summary",
                api_call_desc="api.get_pregnancy_summary()",
            ),
            "get_all_day_events": lambda: call_and_display(
                api.get_all_day_events,
                config.week_start.isoformat(),
                method_name="get_all_day_events",
                api_call_desc=f"api.get_all_day_events('{config.week_start.isoformat()}')",
            ),
            "add_hydration_data": lambda: add_hydration_data_entry(api),
            "set_blood_pressure": lambda: set_blood_pressure_data(api),
            "get_menstrual_data_for_date": lambda: call_and_display(
                api.get_menstrual_data_for_date,
                config.today.isoformat(),
                method_name="get_menstrual_data_for_date",
                api_call_desc=f"api.get_menstrual_data_for_date('{config.today.isoformat()}')",
            ),
            "get_menstrual_calendar_data": lambda: call_and_display(
                api.get_menstrual_calendar_data,
                config.week_start.isoformat(),
                config.today.isoformat(),
                method_name="get_menstrual_calendar_data",
                api_call_desc=f"api.get_menstrual_calendar_data('{config.week_start.isoformat()}', '{config.today.isoformat()}')",
            ),
            # Nutrition
            "get_nutrition_daily_food_log": lambda: call_and_display(
                api.get_nutrition_daily_food_log,
                config.today.isoformat(),
                method_name="get_nutrition_daily_food_log",
                api_call_desc=f"api.get_nutrition_daily_food_log('{config.today.isoformat()}')",
            ),
            "get_nutrition_daily_meals": lambda: call_and_display(
                api.get_nutrition_daily_meals,
                config.today.isoformat(),
                method_name="get_nutrition_daily_meals",
                api_call_desc=f"api.get_nutrition_daily_meals('{config.today.isoformat()}')",
            ),
            "get_nutrition_daily_settings": lambda: call_and_display(
                api.get_nutrition_daily_settings,
                config.today.isoformat(),
                method_name="get_nutrition_daily_settings",
                api_call_desc=f"api.get_nutrition_daily_settings('{config.today.isoformat()}')",
            ),
            # Blood Pressure Management
            "delete_blood_pressure": lambda: delete_blood_pressure_data(api),
            # Activity Management
            "set_activity_name": lambda: set_activity_name_data(api),
            "set_activity_type": lambda: set_activity_type_data(api),
            "create_manual_activity": lambda: create_manual_activity_data(api),
            "delete_activity": lambda: delete_activity_data(api),
            "get_activities_by_date": lambda: call_and_display(
                api.get_activities_by_date,
                config.today.isoformat(),
                config.today.isoformat(),
                method_name="get_activities_by_date",
                api_call_desc=f"api.get_activities_by_date('{config.today.isoformat()}', '{config.today.isoformat()}')",
            ),
            # System & Export
            "create_health_report": lambda: DataExporter.create_health_report(api),
            "remove_tokens": remove_stored_tokens,
            "disconnect": lambda: disconnect_api(api),
            # GraphQL Queries
            "query_garmin_graphql": lambda: query_garmin_graphql_data(api),
        }

        if key in api_methods:
            print(f"\n🔄 Executing: {key}")
            api_methods[key]()
        else:
            print(f"❌ API method '{key}' not implemented yet. You can add it later!")

    except Exception as e:
        print(f"❌ Error executing {key}: {e}")


def remove_stored_tokens():
    """Remove stored login tokens."""
    try:
        import os
        import shutil

        token_path = os.path.expanduser(config.tokenstore)
        if os.path.isdir(token_path):
            shutil.rmtree(token_path)
            print("✅ Stored login tokens directory removed")
        else:
            print("ℹ️ No stored login tokens found")
    except Exception as e:
        print(f"❌ Error removing stored login tokens: {e}")


def disconnect_api(api: Garmin):
    """Disconnect from Garmin Connect."""
    api.logout()
    print("✅ Disconnected from Garmin Connect")


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PIPELINE_WORKBOOK_COLUMNS: dict[str, list[str]] = {
    "Daily_Summary": [
        "calendarDate",
        "activeKilocalories",
        "totalSteps",
        "restingHeartRate",
        "restingHr",
        "minHeartRate",
        "maxHeartRate",
        "averageStressLevel",
        "maxStressLevel",
        "averageSpo2",
        "lowestSpo2",
        "avgWakingRespirationValue",
        "avgSleepRespirationValue",
        "moderateIntensityMinutes",
        "vigorousIntensityMinutes",
        "intensityMinutes",
    ],
    "Daily_Sleep": [
        "calendarDate",
        "sleepDate",
        "duration",
        "sleepDuration",
        "deepSleepSeconds",
        "lightSleepSeconds",
        "remSleepSeconds",
        "awakeSleepSeconds",
        "awakeSeconds",
        "averageSpo2",
        "lowestSpo2",
    ],
    "Daily_HRV": [
        "calendarDate",
        "date",
        "weeklyAvg",
        "lastNightAvg",
        "hrvStatus",
        "status",
        "baselineLowUpper",
        "baselineLow",
        "baselineUpper",
        "balancedLow",
        "balancedUpper",
    ],
    "Daily_RHR": [
        "calendarDate",
        "date",
        "restingHeartRate",
        "restingHr",
        "rhr",
        "averageRestingHeartRate",
        "baselineRestingHeartRate",
    ],
    "Daily_Stress": [
        "calendarDate",
        "date",
        "averageStressLevel",
        "avgStressLevel",
        "maxStressLevel",
        "stressLevel",
    ],
    "Daily_Respiration": [
        "calendarDate",
        "date",
        "avgSleepRespirationValue",
        "minRespirationValue",
        "avgWakingRespirationValue",
        "avgRespirationValue",
    ],
    "Daily_SpO2": [
        "calendarDate",
        "date",
        "averageSpo2",
        "avgSpo2",
        "avgSleepSpo2",
        "lowestSpo2",
        "sevenDayAvgSpo2",
    ],
    "Daily_Intensity_Minutes": [
        "calendarDate",
        "date",
        "moderateIntensityMinutes",
        "vigorousIntensityMinutes",
        "intensityMinutes",
        "totalIntensityMinutes",
    ],
    "Range_Daily_Steps": [
        "calendarDate",
        "date",
        "totalSteps",
        "steps",
        "distance",
        "stepGoal",
    ],
    "Activities": [
        "activityId",
        "activityName",
        "activityType",
        "startTimeLocal",
        "distance",
        "duration",
        "calories",
        "averageSpeed",
        "averageHR",
        "maxHR",
        "avgPower",
        "maxPower",
        "elevationGain",
        "elevationLoss",
        "hrTimeInZone1",
        "hrTimeInZone2",
        "hrTimeInZone3",
        "hrTimeInZone4",
        "hrTimeInZone5",
        "directWorkoutRpe",
        "directWorkoutFeel",
    ],
    "Range_Body_Composition": [
        "calendarDate",
        "date",
        "measurementDate",
        "weight",
        "bodyWeight",
    ],
}


def _pipeline_dates(start_date: datetime.date, end_date: datetime.date) -> list[datetime.date]:
    if end_date < start_date:
        raise ValueError("end-date must be greater than or equal to start-date")
    return [start_date + datetime.timedelta(days=offset) for offset in range((end_date - start_date).days + 1)]


def _deep_find(data: Any, *keys: str) -> Any:
    if data is None:
        return None
    wanted = set(keys)
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return value
        for key, value in data.items():
            if key in wanted and value not in (None, ""):
                return value
            nested = _deep_find(value, *keys)
            if nested not in (None, ""):
                return nested
    elif isinstance(data, list):
        for item in data:
            nested = _deep_find(item, *keys)
            if nested not in (None, ""):
                return nested
    return None


def _first_value(*sources: Any, keys: list[str]) -> Any:
    for source in sources:
        value = _deep_find(source, *keys)
        if value not in (None, ""):
            return value
    return None


def _safe_call(api_instance: Garmin, method_name: str, fetch_errors: list[dict[str, str]], *args: Any) -> Any:
    method = getattr(api_instance, method_name, None)
    if method is None:
        fetch_errors.append({"method": method_name, "error_type": "method_not_available"})
        return None
    try:
        return method(*args)
    except Exception as exc:
        fetch_errors.append(
            {
                "method": method_name,
                "error_type": type(exc).__name__,
                "message": str(exc)[:240],
            }
        )
        return None


def _safe_range_call_by_chunks(
    api_instance: Garmin,
    method_name: str,
    fetch_errors: list[dict[str, str]],
    start_date: datetime.date,
    end_date: datetime.date,
    chunk_days: int = 7,
) -> list[Any]:
    results: list[Any] = []
    current = start_date
    while current <= end_date:
        chunk_end = min(current + datetime.timedelta(days=chunk_days - 1), end_date)
        chunk = _safe_call(api_instance, method_name, fetch_errors, current.isoformat(), chunk_end.isoformat())
        if isinstance(chunk, list):
            results.extend(chunk)
        elif chunk:
            results.append(chunk)
        current = chunk_end + datetime.timedelta(days=1)
    return results


def _date_key(record: Any) -> str | None:
    value = _deep_find(record, "calendarDate", "date", "measurementDate", "startTimeLocal", "startTimeGMT", "startGMT")
    if value is None:
        return None
    text = str(value)
    return text[:10] if len(text) >= 10 else text


def _index_by_date(records: Any) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    if isinstance(records, dict):
        for candidate in (
            records.get("dailyStepDTOs"),
            records.get("dateWeightList"),
            records.get("bodyComps"),
            records.get("data"),
            records.get("items"),
        ):
            indexed.update(_index_by_date(candidate))
        key = _date_key(records)
        if key:
            indexed.setdefault(key, records)
    elif isinstance(records, list):
        for item in records:
            key = _date_key(item)
            if key:
                indexed.setdefault(key, item)
    return indexed


def _column_name(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _cell_xml(row_index: int, col_index: int, value: Any) -> str:
    ref = f"{_column_name(col_index)}{row_index}"
    if value is None:
        return f'<c r="{ref}"/>'
    if isinstance(value, bool):
        return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"><v>{value}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t>{xml_escape(str(value))}</t></is></c>'


def _write_pipeline_xlsx(output_path: Path, workbook_rows: dict[str, list[dict[str, Any]]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    worksheet_parts: list[str] = []
    workbook_sheets: list[str] = []
    rels: list[str] = []
    for sheet_index, (sheet_name, columns) in enumerate(PIPELINE_WORKBOOK_COLUMNS.items(), start=1):
        table_rows = [columns]
        for row in workbook_rows.get(sheet_name, []):
            table_rows.append([row.get(column) for column in columns])
        rows_xml: list[str] = []
        for row_index, row_values in enumerate(table_rows, start=1):
            cells = "".join(_cell_xml(row_index, col_index, value) for col_index, value in enumerate(row_values, start=1))
            rows_xml.append(f'<row r="{row_index}">{cells}</row>')
        worksheet_parts.append(
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetData>{"".join(rows_xml)}</sheetData></worksheet>'
        )
        workbook_sheets.append(f'<sheet name="{xml_escape(sheet_name)}" sheetId="{sheet_index}" r:id="rId{sheet_index}"/>')
        rels.append(
            f'<Relationship Id="rId{sheet_index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{sheet_index}.xml"/>'
        )
    content_types = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    ]
    for sheet_index in range(1, len(PIPELINE_WORKBOOK_COLUMNS) + 1):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{sheet_index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    content_types.append("</Types>")
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "".join(content_types))
        archive.writestr(
            "_rels/.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        archive.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheets>{"".join(workbook_sheets)}</sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'{"".join(rels)}</Relationships>',
        )
        for sheet_index, worksheet_xml in enumerate(worksheet_parts, start=1):
            archive.writestr(f"xl/worksheets/sheet{sheet_index}.xml", worksheet_xml)


def _build_pipeline_workbook_rows(api_instance: Garmin, start_date: datetime.date, end_date: datetime.date) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]]]:
    fetch_errors: list[dict[str, str]] = []
    dates = _pipeline_dates(start_date, end_date)
    start_text = start_date.isoformat()
    end_text = end_date.isoformat()
    daily_steps_by_date = _index_by_date(_safe_call(api_instance, "get_daily_steps", fetch_errors, start_text, end_text))
    body_comp_by_date = _index_by_date(_safe_call(api_instance, "get_body_composition", fetch_errors, start_text, end_text))
    activities = _safe_call(api_instance, "get_activities_by_date", fetch_errors, start_text, end_text) or []
    activity_details: dict[str, dict[str, Any]] = {}
    if isinstance(activities, list):
        for activity in activities:
            activity_id = _first_value(activity, keys=["activityId", "activityIdStr"])
            if activity_id in (None, ""):
                continue
            detail = _safe_call(api_instance, "get_activity", fetch_errors, str(activity_id))
            if isinstance(detail, dict):
                activity_details[str(activity_id)] = detail
    rows: dict[str, list[dict[str, Any]]] = {sheet_name: [] for sheet_name in PIPELINE_WORKBOOK_COLUMNS}
    for day in dates:
        date_text = day.isoformat()
        summary = _safe_call(api_instance, "get_user_summary", fetch_errors, date_text) or {}
        stats = _safe_call(api_instance, "get_stats", fetch_errors, date_text) or {}
        stats_body = _safe_call(api_instance, "get_stats_and_body", fetch_errors, date_text) or {}
        sleep = _safe_call(api_instance, "get_sleep_data", fetch_errors, date_text) or {}
        hrv = _safe_call(api_instance, "get_hrv_data", fetch_errors, date_text) or {}
        stress = _safe_call(api_instance, "get_stress_data", fetch_errors, date_text) or {}
        respiration = _safe_call(api_instance, "get_respiration_data", fetch_errors, date_text) or {}
        spo2 = _safe_call(api_instance, "get_spo2_data", fetch_errors, date_text) or {}
        sleep_spo2 = _first_value(
            spo2,
            sleep,
            keys=["avgSleepSpO2", "averageSpO2Value", "averageSPO2"],
        )
        lowest_sleep_spo2 = _first_value(
            sleep,
            spo2,
            keys=["lowestSpO2Value", "lowestSPO2", "lowestSpO2"],
        )
        daily_steps = daily_steps_by_date.get(date_text) or {}
        body_comp = body_comp_by_date.get(date_text) or {}
        active_kcal = _first_value(
            summary,
            stats,
            stats_body,
            keys=["activeKilocalories", "activeCalories", "activeKcal"],
        )
        if active_kcal is None:
            fetch_errors.append(
                {
                    "method": "pipeline_export_required_daily_summary",
                    "error_type": "required_value_missing",
                    "message": f"Skipped {date_text}: activeKilocalories was not available from Garmin.",
                }
            )
            continue
        rows["Daily_Summary"].append({
            "calendarDate": date_text,
            "activeKilocalories": active_kcal,
            "totalSteps": _first_value(summary, daily_steps, stats, keys=["totalSteps", "steps"]),
            "restingHeartRate": _first_value(summary, stats, stats_body, keys=["restingHeartRate", "restingHR", "rhr"]),
            "restingHr": _first_value(summary, stats, stats_body, keys=["restingHr", "restingHR", "rhr"]),
            "minHeartRate": _first_value(summary, stats, keys=["minHeartRate", "minHR"]),
            "maxHeartRate": _first_value(summary, stats, keys=["maxHeartRate", "maxHR"]),
            "averageStressLevel": _first_value(summary, stress, keys=["averageStressLevel", "avgStressLevel", "avgStress"]),
            "maxStressLevel": _first_value(summary, stress, keys=["maxStressLevel", "maxStress"]),
            "averageSpo2": _first_value(summary, spo2, sleep, keys=["averageSpo2", "averageSpO2", "avgSpo2"]),
            "lowestSpo2": _first_value(summary, spo2, sleep, keys=["lowestSpo2", "lowestSpO2", "minSpo2"]),
            "avgWakingRespirationValue": _first_value(summary, respiration, keys=["avgWakingRespirationValue", "avgRespirationValue"]),
            "avgSleepRespirationValue": _first_value(summary, respiration, keys=["avgSleepRespirationValue"]),
            "moderateIntensityMinutes": _first_value(summary, stats, keys=["moderateIntensityMinutes"]),
            "vigorousIntensityMinutes": _first_value(summary, stats, keys=["vigorousIntensityMinutes"]),
            "intensityMinutes": _first_value(summary, stats, keys=["intensityMinutes", "totalIntensityMinutes"]),
        })
        rows["Daily_Sleep"].append({
            "calendarDate": date_text,
            "sleepDate": _first_value(sleep, keys=["sleepDate", "calendarDate", "date"]) or date_text,
            "duration": _first_value(sleep, keys=["duration", "sleepTimeSeconds", "sleepTimeInSeconds", "totalSleepSeconds"]),
            "sleepDuration": _first_value(sleep, keys=["sleepDuration", "sleepTimeSeconds", "sleepTimeInSeconds", "totalSleepSeconds"]),
            "deepSleepSeconds": _first_value(sleep, keys=["deepSleepSeconds", "deepSleepTimeSeconds"]),
            "lightSleepSeconds": _first_value(sleep, keys=["lightSleepSeconds", "lightSleepTimeSeconds"]),
            "remSleepSeconds": _first_value(sleep, keys=["remSleepSeconds", "remSleepTimeSeconds"]),
            "awakeSleepSeconds": _first_value(sleep, keys=["awakeSleepSeconds", "awakeSleepTimeSeconds"]),
            "awakeSeconds": _first_value(sleep, keys=["awakeSeconds", "awakeSleepSeconds"]),
            "averageSpo2": sleep_spo2,
            "lowestSpo2": lowest_sleep_spo2,
        })
        rows["Daily_HRV"].append({
            "calendarDate": date_text,
            "date": date_text,
            "weeklyAvg": _first_value(hrv, keys=["weeklyAvg", "weeklyAverage", "hrvWeeklyAverage"]),
            "lastNightAvg": _first_value(hrv, keys=["lastNightAvg", "lastNightAverage", "hrvLastNightAverage"]),
            "hrvStatus": _first_value(hrv, keys=["hrvStatus", "status"]),
            "status": _first_value(hrv, keys=["status", "hrvStatus"]),
            "baselineLowUpper": _first_value(hrv, keys=["baselineLowUpper"]),
            "baselineLow": _first_value(hrv, keys=["baselineLow", "balancedLow"]),
            "baselineUpper": _first_value(hrv, keys=["baselineUpper", "balancedUpper"]),
            "balancedLow": _first_value(hrv, keys=["balancedLow", "baselineLow"]),
            "balancedUpper": _first_value(hrv, keys=["balancedUpper", "baselineUpper"]),
        })
        rows["Daily_RHR"].append({
            "calendarDate": date_text,
            "date": date_text,
            "restingHeartRate": _first_value(summary, stats, stats_body, keys=["restingHeartRate", "restingHR", "rhr"]),
            "restingHr": _first_value(summary, stats, stats_body, keys=["restingHr", "restingHR", "rhr"]),
            "rhr": _first_value(summary, stats, stats_body, keys=["rhr", "restingHeartRate", "restingHr"]),
            "averageRestingHeartRate": _first_value(stats_body, stats, keys=["averageRestingHeartRate", "avgRestingHeartRate"]),
            "baselineRestingHeartRate": _first_value(
                summary,
                stats_body,
                stats,
                keys=["lastSevenDaysAvgRestingHeartRate", "baselineRestingHeartRate"],
            ),
        })
        rows["Daily_Stress"].append({
            "calendarDate": date_text,
            "date": date_text,
            "averageStressLevel": _first_value(summary, stress, keys=["averageStressLevel", "avgStressLevel", "avgStress"]),
            "avgStressLevel": _first_value(summary, stress, keys=["avgStressLevel", "averageStressLevel", "avgStress"]),
            "maxStressLevel": _first_value(summary, stress, keys=["maxStressLevel", "maxStress"]),
            "stressLevel": _first_value(stress, summary, keys=["stressLevel"]),
        })
        rows["Daily_Respiration"].append({
            "calendarDate": date_text,
            "date": date_text,
            "avgSleepRespirationValue": _first_value(respiration, summary, keys=["avgSleepRespirationValue"]),
            "minRespirationValue": _first_value(respiration, summary, keys=["minRespirationValue", "lowestRespirationValue"]),
            "avgWakingRespirationValue": _first_value(respiration, summary, keys=["avgWakingRespirationValue"]),
            "avgRespirationValue": _first_value(respiration, summary, keys=["avgRespirationValue", "avgWakingRespirationValue"]),
        })
        rows["Daily_SpO2"].append({
            "calendarDate": date_text,
            "date": date_text,
            "averageSpo2": _first_value(spo2, summary, sleep, keys=["averageSpO2", "averageSpo2", "avgSpo2"]),
            "avgSpo2": _first_value(spo2, summary, sleep, keys=["averageSpO2", "avgSpo2", "averageSpo2"]),
            "avgSleepSpo2": sleep_spo2,
            "lowestSpo2": _first_value(spo2, summary, sleep, keys=["lowestSpO2", "lowestSpo2", "minSpo2"]),
            "sevenDayAvgSpo2": _first_value(spo2, keys=["lastSevenDaysAvgSpO2", "sevenDayAvgSpo2"]),
        })
        rows["Daily_Intensity_Minutes"].append({
            "calendarDate": date_text,
            "date": date_text,
            "moderateIntensityMinutes": _first_value(summary, stats, keys=["moderateIntensityMinutes"]),
            "vigorousIntensityMinutes": _first_value(summary, stats, keys=["vigorousIntensityMinutes"]),
            "intensityMinutes": _first_value(summary, stats, keys=["intensityMinutes", "totalIntensityMinutes"]),
            "totalIntensityMinutes": _first_value(summary, stats, keys=["totalIntensityMinutes", "intensityMinutes"]),
        })
        rows["Range_Daily_Steps"].append({
            "calendarDate": date_text,
            "date": date_text,
            "totalSteps": _first_value(daily_steps, summary, stats, keys=["totalSteps", "steps"]),
            "steps": _first_value(daily_steps, summary, stats, keys=["steps", "totalSteps"]),
            "distance": _first_value(daily_steps, summary, keys=["distance", "totalDistance"]),
            "stepGoal": _first_value(daily_steps, summary, keys=["stepGoal", "dailyStepGoal"]),
        })
        rows["Range_Body_Composition"].append({
            "calendarDate": date_text,
            "date": date_text,
            "measurementDate": _first_value(body_comp, stats_body, keys=["measurementDate", "date", "calendarDate"]) or date_text,
            "weight": _first_value(body_comp, stats_body, keys=["weight", "bodyWeight", "weightInGrams"]),
            "bodyWeight": _first_value(body_comp, stats_body, keys=["bodyWeight", "weight", "weightInGrams"]),
        })
    if isinstance(activities, list):
        for activity in activities:
            activity_id = _first_value(activity, keys=["activityId", "activityIdStr"])
            detail = activity_details.get(str(activity_id), {}) if activity_id not in (None, "") else {}
            start_time = _deep_find(activity, "startTimeLocal", "startTimeGMT", "startGMT")
            if start_time:
                activity_date = str(start_time)[:10]
                if activity_date < start_text or activity_date > end_text:
                    continue
            rows["Activities"].append({
                "activityId": activity_id,
                "activityName": _first_value(activity, keys=["activityName", "name"]),
                "activityType": _first_value(activity, keys=["activityType", "typeKey", "type"]),
                "startTimeLocal": start_time,
                "distance": _first_value(activity, keys=["distance"]),
                "duration": _first_value(activity, keys=["duration", "elapsedDuration"]),
                "calories": _first_value(activity, keys=["calories", "activeKilocalories"]),
                "averageSpeed": _first_value(activity, keys=["averageSpeed", "avgSpeed"]),
                "averageHR": _first_value(activity, keys=["averageHR", "averageHeartRate", "avgHR"]),
                "maxHR": _first_value(activity, keys=["maxHR", "maxHeartRate"]),
                "avgPower": _first_value(activity, keys=["avgPower", "averagePower"]),
                "maxPower": _first_value(activity, keys=["maxPower"]),
                "elevationGain": _first_value(activity, keys=["elevationGain", "totalElevationGain"]),
                "elevationLoss": _first_value(activity, keys=["elevationLoss", "totalElevationLoss"]),
                "hrTimeInZone1": _first_value(activity, keys=["hrTimeInZone1"]),
                "hrTimeInZone2": _first_value(activity, keys=["hrTimeInZone2"]),
                "hrTimeInZone3": _first_value(activity, keys=["hrTimeInZone3"]),
                "hrTimeInZone4": _first_value(activity, keys=["hrTimeInZone4"]),
                "hrTimeInZone5": _first_value(activity, keys=["hrTimeInZone5"]),
                "directWorkoutRpe": _first_value(detail, activity, keys=["directWorkoutRpe"]),
                "directWorkoutFeel": _first_value(detail, activity, keys=["directWorkoutFeel"]),
            })
    return rows, fetch_errors


def run_pipeline_workbook_export_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Garmin Connect data into the workbook shape expected by the local modular pipeline."
    )
    parser.add_argument("--pipeline-export", action="store_true", help="Enable pipeline workbook export mode.")
    parser.add_argument("--start-date", default=config.today.isoformat(), help="First date to fetch, YYYY-MM-DD.")
    parser.add_argument("--end-date", default=config.today.isoformat(), help="Last date to fetch, YYYY-MM-DD.")
    parser.add_argument("--output", default=None, help="Output .xlsx path. Defaults to data/input/garmin_export_api_<start>_<end>.xlsx.")
    args = parser.parse_args(argv)
    start_date = datetime.date.fromisoformat(args.start_date)
    end_date = datetime.date.fromisoformat(args.end_date)
    output_path = Path(args.output) if args.output else PROJECT_ROOT / "data" / "input" / f"garmin_export_api_{start_date.isoformat()}_{end_date.isoformat()}.xlsx"
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    api_instance = init_api(config.email, config.password)
    if api_instance is None:
        print("Unable to initialize Garmin API; no workbook was exported.")
        return 1
    rows, fetch_errors = _build_pipeline_workbook_rows(api_instance, start_date, end_date)
    _write_pipeline_xlsx(output_path, rows)
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    manifest = {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "output_workbook": str(output_path),
        "date_range": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "workbook_pattern_for_pipeline": "garmin_export_*.xlsx",
        "pipeline_expected_input_directory": "data/input",
        "sheets": {sheet_name: {"columns": columns, "rows_written": len(rows.get(sheet_name, []))} for sheet_name, columns in PIPELINE_WORKBOOK_COLUMNS.items()},
        "fetch_errors": fetch_errors,
        "privacy": {
            "tokens_written_to_workbook": False,
            "credentials_written_to_workbook": False,
            "raw_api_payloads_written": False,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Pipeline workbook exported: {output_path}")
    print(f"Export manifest written: {manifest_path}")
    if fetch_errors:
        print(f"Completed with {len(fetch_errors)} non-blocking fetch warning(s). See manifest for method names and error types.")
    return 0


def init_api(email: str | None = None, password: str | None = None) -> Garmin | None:
    """Initialize Garmin API with smart error handling and recovery."""
    # First try to login with stored tokens
    try:
        print(f"Attempting to login using stored tokens from: {config.tokenstore}")

        garmin = Garmin()
        garmin.login(config.tokenstore)
        print("Successfully logged in using stored tokens!")
        return garmin

    except GarminConnectTooManyRequestsError as err:
        print(f"\n❌ {err}")
        sys.exit(1)

    except (
        FileNotFoundError,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
    ):
        print("No valid tokens found. Requesting fresh login credentials.")

    # Loop for credential entry with retry on auth failure
    while True:
        try:
            # Get credentials if not provided
            if not email or not password:
                email = input("Email address: ").strip()
                password = getpass("Password: ")

            print("Logging in with credentials...")
            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()

            if result1 == "needs_mfa":
                print("Multi-factor authentication required")

                mfa_code = get_mfa()
                print("🔄 Submitting MFA code...")

                try:
                    garmin.resume_login(result2, mfa_code)
                    print("✅ MFA authentication successful!")

                except GarminConnectTooManyRequestsError:
                    print("❌ Too many MFA attempts")
                    print("💡 Please wait 30 minutes before trying again")
                    sys.exit(1)
                except GarminConnectAuthenticationError as mfa_error:
                    # Handle specific errors from MFA
                    error_str = str(mfa_error)
                    print(f"🔍 Debug: MFA error details: {error_str}")
                    if "401" in error_str or "403" in error_str:
                        print("❌ Invalid MFA code")
                        print("💡 Please verify your MFA code and try again")
                        continue
                    # Other HTTP errors - don't retry
                    print(f"❌ MFA authentication failed: {mfa_error}")
                    sys.exit(1)

            # Save tokens for future use
            garmin.client.dump(config.tokenstore)
            print(f"Login successful! Tokens saved to: {config.tokenstore}")

            return garmin

        except GarminConnectTooManyRequestsError as err:
            print(f"\n❌ {err}")
            sys.exit(1)

        except GarminConnectAuthenticationError as err:
            print(f"\n❌ {err}")
            print("💡 Please check your username and password and try again")
            # Clear the provided credentials to force re-entry
            email = None
            password = None
            continue

        except (
            FileNotFoundError,
            GarminConnectConnectionError,
            requests.exceptions.HTTPError,
        ) as err:
            print(f"❌ Connection error: {err}")
            print("💡 Please check your internet connection and try again")
            return None

        except KeyboardInterrupt:
            print("\nLogin cancelled by user")
            return None


def main():
    """Main program loop with funny health status in menu prompt."""
    if "--pipeline-export" in sys.argv:
        raise SystemExit(run_pipeline_workbook_export_cli(sys.argv[1:]))

    # Display export directory information on startup
    print(f"📁 Exported data will be saved to the directory: '{config.export_dir}'")
    print("📄 All API responses are written to: 'response.json'")

    api_instance = init_api(config.email, config.password)
    current_category = None

    while True:
        try:
            if api_instance:
                # Add health status in menu prompt
                try:
                    summary = api_instance.get_user_summary(config.today.isoformat())
                    hydration_data = None
                    with suppress(Exception):
                        hydration_data = api_instance.get_hydration_data(
                            config.today.isoformat()
                        )

                    if summary:
                        steps = summary.get("totalSteps") or 0
                        calories = summary.get("totalKilocalories") or 0

                        # Build stats string with hydration if available
                        stats_parts = [f"{steps:,} steps", f"{calories} kcal"]

                        if hydration_data and hydration_data.get("valueInML"):
                            hydration_ml = int(hydration_data.get("valueInML", 0))
                            hydration_cups = round(hydration_ml / 240, 1)
                            hydration_goal = hydration_data.get("goalInML", 0)

                            if hydration_goal > 0:
                                hydration_percent = round(
                                    (hydration_ml / hydration_goal) * 100
                                )
                                stats_parts.append(
                                    f"{hydration_ml}ml water ({hydration_percent}% of goal)"
                                )
                            else:
                                stats_parts.append(
                                    f"{hydration_ml}ml water ({hydration_cups} cups)"
                                )

                        stats_string = " | ".join(stats_parts)
                        print(f"\n📊 Your Stats Today: {stats_string}")

                        if steps < 5000:
                            print("🐌 Time to get those legs moving!")
                        elif steps > 15000:
                            print("🏃‍♂️ You're crushing it today!")
                        else:
                            print("👍 Nice progress! Keep it up!")
                except Exception as e:
                    print(
                        f"Unable to fetch stats for display: {e}"
                    )  # Silently skip if stats can't be fetched

            # Display appropriate menu
            if current_category is None:
                print_main_menu()
                option = safe_readkey()

                # Handle main menu options
                if option == "q":
                    print(
                        "Be active, generate some data to play with next time ;-) Bye!"
                    )
                    break
                if option in menu_categories:
                    current_category = option
                else:
                    print(
                        f"❌ Invalid selection. Use {', '.join(menu_categories.keys())} for categories or 'q' to quit"
                    )
            else:
                # In a category - show category menu
                print_category_menu(current_category)
                option = safe_readkey()

                # Handle category menu options
                if option == "q":
                    current_category = None  # Back to main menu
                elif option in "0123456789abcdefghijklmnopqrstuvwxyz":
                    try:
                        category_data = menu_categories[current_category]
                        category_options = category_data["options"]
                        if option in category_options:
                            api_key = category_options[option]["key"]
                            execute_api_call(api_instance, api_key)
                        else:
                            valid_keys = ", ".join(category_options.keys())
                            print(
                                f"❌ Invalid option selection. Valid options: {valid_keys}"
                            )
                    except Exception as e:
                        print(f"❌ Error processing option {option}: {e}")
                else:
                    print(
                        "❌ Invalid selection. Use numbers/letters for options or 'q' to go back/quit"
                    )

        except KeyboardInterrupt:
            print("\nInterrupted by user. Press q to quit.")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
