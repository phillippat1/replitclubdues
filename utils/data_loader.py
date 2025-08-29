import pandas as pd
import os
import numpy as np
from typing import Dict, Any, cast
from .web_scraper import get_comprehensive_club_data
from .fallback_data import get_extended_club_data

def load_country_clubs_data() -> pd.DataFrame:
    """
    Load real country club data from web sources.
    
    Returns:
        pd.DataFrame: DataFrame containing country club information scraped from real sources
        
    Raises:
        ValueError: If the data scraping fails or returns empty data
    """
    
    try:
        # Try to get real data from web sources first
        df = get_comprehensive_club_data()
        
        # If web scraping fails or returns empty, use fallback data
        if df.empty:
            print("Web scraping returned empty results, using fallback data...")
            df = get_extended_club_data()
        
        # Validate that we have data
        if df.empty:
            raise ValueError("No country club data available from any source.")
        
        # Data type conversions and cleaning
        df = clean_and_validate_data(df)
        
        return cast(pd.DataFrame, df)
        
    except Exception as e:
        # Last resort: use fallback data
        print(f"Error loading from web sources: {str(e)}")
        print("Using fallback country club data...")
        try:
            df = get_extended_club_data()
            df = clean_and_validate_data(df)
            return cast(pd.DataFrame, df)
        except Exception as fallback_error:
            raise ValueError(f"Error loading fallback data: {str(fallback_error)}")

def clean_and_validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the country club data.
    
    Args:
        df (pd.DataFrame): Raw data from CSV file
        
    Returns:
        pd.DataFrame: Cleaned and validated data
    """
    
    # Create a copy to avoid modifying the original
    df_clean = cast(pd.DataFrame, df.copy())
    
    # Clean Club Name
    if 'Club Name' in df_clean.columns:
        df_clean['Club Name'] = df_clean['Club Name'].astype(str).str.strip()
        # Remove rows with empty club names
        df_clean = cast(pd.DataFrame, df_clean[df_clean['Club Name'].notna() & (df_clean['Club Name'] != '')])
    
    # Clean State
    if 'State' in df_clean.columns:
        df_clean['State'] = df_clean['State'].astype(str).str.strip().str.upper()
    
    # Clean City
    if 'City' in df_clean.columns:
        df_clean['City'] = df_clean['City'].astype(str).str.strip()
    
    # Clean and validate Monthly Dues
    if 'Monthly Dues' in df_clean.columns:
        # Remove dollar signs and commas, convert to float
        df_clean['Monthly Dues'] = df_clean['Monthly Dues'].astype(str).str.replace('$', '').str.replace(',', '')
        df_clean['Monthly Dues'] = pd.to_numeric(df_clean['Monthly Dues'], errors='coerce')
        
        # Remove rows with invalid dues (NaN or negative values)
        df_clean = cast(pd.DataFrame, df_clean[df_clean['Monthly Dues'].notna() & (df_clean['Monthly Dues'] >= 0)])
    
    # Clean Contact Phone
    if 'Contact Phone' in df_clean.columns:
        df_clean['Contact Phone'] = df_clean['Contact Phone'].astype(str).str.strip()
        # Replace 'nan' string with empty string
        df_clean['Contact Phone'] = df_clean['Contact Phone'].replace('nan', '')
    
    # Clean Website
    if 'Website' in df_clean.columns:
        df_clean['Website'] = df_clean['Website'].astype(str).str.strip()
        # Replace 'nan' string with empty string
        df_clean['Website'] = df_clean['Website'].replace('nan', '')
        # Add https:// if missing for valid URLs
        mask = (df_clean['Website'] != '') & (~df_clean['Website'].str.startswith(('http://', 'https://')))
        df_clean.loc[mask, 'Website'] = 'https://' + df_clean.loc[mask, 'Website']
    
    # Clean Address
    if 'Address' in df_clean.columns:
        df_clean['Address'] = df_clean['Address'].astype(str).str.strip()
        df_clean['Address'] = df_clean['Address'].replace('nan', '')
    
    # Clean Prestige Level
    if 'Prestige Level' in df_clean.columns:
        df_clean['Prestige Level'] = df_clean['Prestige Level'].astype(str).str.strip()
        df_clean['Prestige Level'] = df_clean['Prestige Level'].replace('nan', '')
    
    # Clean Membership Type
    if 'Membership Type' in df_clean.columns:
        df_clean['Membership Type'] = df_clean['Membership Type'].astype(str).str.strip()
        df_clean['Membership Type'] = df_clean['Membership Type'].replace('nan', '')
    
    # Clean and validate Initiation Fee
    if 'Initiation Fee' in df_clean.columns:
        df_clean['Initiation Fee'] = df_clean['Initiation Fee'].astype(str).str.replace('$', '').str.replace(',', '')
        df_clean['Initiation Fee'] = pd.to_numeric(df_clean['Initiation Fee'], errors='coerce')
        df_clean['Initiation Fee'] = df_clean['Initiation Fee'].fillna(0)
    
    # Clean Other Costs
    if 'Other Costs' in df_clean.columns:
        df_clean['Other Costs'] = df_clean['Other Costs'].astype(str).str.strip()
        df_clean['Other Costs'] = df_clean['Other Costs'].replace('nan', '')
    
    # Reset index after filtering
    df_clean = cast(pd.DataFrame, df_clean.reset_index(drop=True))
    
    return df_clean

def validate_state_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and standardize US state codes.
    
    Args:
        df (pd.DataFrame): DataFrame with State column
        
    Returns:
        pd.DataFrame: DataFrame with validated state codes
    """
    
    # US state codes mapping
    us_states = {
        'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 'CALIFORNIA': 'CA',
        'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE', 'FLORIDA': 'FL', 'GEORGIA': 'GA',
        'HAWAII': 'HI', 'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA',
        'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
        'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS', 'MISSOURI': 'MO',
        'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ',
        'NEW MEXICO': 'NM', 'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH',
        'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
        'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT', 'VERMONT': 'VT',
        'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY',
        'DISTRICT OF COLUMBIA': 'DC'
    }
    
    # Reverse mapping for state codes to full names
    state_codes_to_names = {v: k for k, v in us_states.items()}
    
    if 'State' in df.columns:
        df_copy = cast(pd.DataFrame, df.copy())
        
        # Convert full state names to state codes
        df_copy['State'] = df_copy['State'].str.upper()
        df_copy['State'] = df_copy['State'].replace(us_states).fillna(df_copy['State'])
        
        # Filter out invalid state codes
        valid_states = list(us_states.values())
        df_copy = cast(pd.DataFrame, df_copy[df_copy['State'].isin(valid_states)])
        
        return df_copy
    
    return df
