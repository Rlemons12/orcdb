"""
WIP Analytics Dashboard
Analyzes and visualizes WIP (Work In Progress) data
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json


class WIPAnalytics:
    """
    Analyzes WIP data and generates visualizations

    Expected columns:
    - WIP_ENTITY_NAME
    - CREATION_DATE
    - QA_CREATION_DATE
    - ASSET_ACTIVITY
    - MAINTENANCE_OP_SEQ
    - ASSET_NUMBER
    - ASSET_DESCRIPTION
    - QA_USER_CREATED_BY
    - QA_USER_LAST_UPDATED
    - Lot Number
    - Location
    - Reason
    - Adjustment
    - Description
    - DESCRIPTION
    """

    def __init__(self, file_path: str):
        """Load WIP data from Excel file"""
        self.df = pd.read_excel(file_path)
        self._clean_data()

    def _clean_data(self):
        """Clean and prepare data"""
        # Convert dates
        date_columns = ['CREATION_DATE', 'QA_CREATION_DATE']
        for col in date_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')

        # Fill NaN values
        self.df = self.df.fillna('')

    def get_summary_stats(self) -> dict:
        """Get summary statistics"""
        return {
            'total_records': len(self.df),
            'unique_entities': self.df['WIP_ENTITY_NAME'].nunique() if 'WIP_ENTITY_NAME' in self.df.columns else 0,
            'unique_assets': self.df['ASSET_NUMBER'].nunique() if 'ASSET_NUMBER' in self.df.columns else 0,
            'unique_locations': self.df['Location'].nunique() if 'Location' in self.df.columns else 0,
            'unique_users': self.df['QA_USER_CREATED_BY'].nunique() if 'QA_USER_CREATED_BY' in self.df.columns else 0,
            'date_range': self._get_date_range()
        }

    def _get_date_range(self) -> dict:
        """Get date range of data"""
        if 'CREATION_DATE' in self.df.columns:
            dates = self.df['CREATION_DATE'].dropna()
            if len(dates) > 0:
                return {
                    'start': dates.min().strftime('%Y-%m-%d'),
                    'end': dates.max().strftime('%Y-%m-%d')
                }
        return {'start': None, 'end': None}

    def get_entities_by_date(self) -> dict:
        """Count entities created per day"""
        if 'CREATION_DATE' not in self.df.columns:
            return {}

        daily_counts = self.df.groupby(
            self.df['CREATION_DATE'].dt.date
        ).size().to_dict()

        return {str(k): int(v) for k, v in daily_counts.items() if k}

    def get_top_locations(self, limit: int = 10) -> dict:
        """Get top locations by count"""
        if 'Location' not in self.df.columns:
            return {}

        location_counts = self.df['Location'].value_counts().head(limit)
        return location_counts.to_dict()

    def get_top_assets(self, limit: int = 10) -> dict:
        """Get top assets by activity count"""
        if 'ASSET_NUMBER' not in self.df.columns:
            return {}

        asset_counts = self.df['ASSET_NUMBER'].value_counts().head(limit)
        return asset_counts.to_dict()

    def get_activity_breakdown(self) -> dict:
        """Get breakdown by asset activity type"""
        if 'ASSET_ACTIVITY' not in self.df.columns:
            return {}

        activity_counts = self.df['ASSET_ACTIVITY'].value_counts()
        return activity_counts.to_dict()

    def get_user_activity(self, limit: int = 10) -> dict:
        """Get activity by user"""
        if 'QA_USER_CREATED_BY' not in self.df.columns:
            return {}

        user_counts = self.df['QA_USER_CREATED_BY'].value_counts().head(limit)
        return user_counts.to_dict()

    def get_reason_breakdown(self) -> dict:
        """Get breakdown by reason"""
        if 'Reason' not in self.df.columns:
            return {}

        reason_counts = self.df['Reason'].value_counts()
        return reason_counts.to_dict()

    def get_weekly_trend(self) -> dict:
        """Get weekly creation trend"""
        if 'CREATION_DATE' not in self.df.columns:
            return {}

        # Group by week
        weekly = self.df.groupby(
            self.df['CREATION_DATE'].dt.to_period('W')
        ).size()

        return {str(k): int(v) for k, v in weekly.items()}

    def get_monthly_trend(self) -> dict:
        """Get monthly creation trend"""
        if 'CREATION_DATE' not in self.df.columns:
            return {}

        # Group by month
        monthly = self.df.groupby(
            self.df['CREATION_DATE'].dt.to_period('M')
        ).size()

        return {str(k): int(v) for k, v in monthly.items()}

    def get_all_analytics(self) -> dict:
        """Get all analytics data for visualization"""
        return {
            'summary': self.get_summary_stats(),
            'daily_trend': self.get_entities_by_date(),
            'weekly_trend': self.get_weekly_trend(),
            'monthly_trend': self.get_monthly_trend(),
            'top_locations': self.get_top_locations(),
            'top_assets': self.get_top_assets(),
            'activity_breakdown': self.get_activity_breakdown(),
            'user_activity': self.get_user_activity(),
            'reason_breakdown': self.get_reason_breakdown()
        }

    def export_to_json(self, output_path: str):
        """Export analytics to JSON"""
        analytics = self.get_all_analytics()

        with open(output_path, 'w') as f:
            json.dump(analytics, f, indent=2, default=str)

        return output_path


# Example usage
if __name__ == "__main__":
    # Example: Analyze a WIP report
    analyzer = WIPAnalytics("path/to/wip_report.xlsx")

    # Get summary
    print("Summary Statistics:")
    print(analyzer.get_summary_stats())

    # Get all analytics
    analytics = analyzer.get_all_analytics()

    # Export to JSON
    analyzer.export_to_json("wip_analytics.json")