import streamlit as st
import pandas as pd
import numpy as np
from utils.data_loader import load_country_clubs_data
import os
import re
from typing import cast

def calculate_total_monthly_cost(row):
    """Calculate total monthly cost including monthly dues and any monthly fees from other costs"""
    monthly_dues = row.get('Monthly Dues', 0)
    other_costs = str(row.get('Other Costs', ''))
    
    # Extract monthly fees from other costs using regex
    monthly_fees = 0
    monthly_matches = re.findall(r'\$(\d{1,3}(?:,\d{3})*)/month', other_costs)
    for match in monthly_matches:
        # Remove commas and convert to int
        fee = int(match.replace(',', ''))
        monthly_fees += fee
    
    return monthly_dues + monthly_fees

# Set page configuration
st.set_page_config(
    page_title="Country Club Golf Directory",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("⛳ Country Club Golf Directory")
st.markdown("Browse and search monthly dues for country clubs across all US states")

# Load data
@st.cache_data
def get_data():
    """Load and cache the country club data"""
    try:
        return load_country_clubs_data()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Load the data
df = cast(pd.DataFrame, get_data())

if df.empty:
    st.warning("No country club data is currently available. Please ensure the data file is properly configured.")
    st.info("Expected data structure should include: Club Name, State, City, Monthly Dues, Contact Phone, Website, Address, Prestige Level, Membership Type, Initiation Fee, Other Costs")
    st.stop()

# Search functionality - at the top of sidebar
st.sidebar.header("🔍 Search")
search_term = st.sidebar.text_input(
    "Search by Club Name:",
    placeholder="Enter club name...",
    help="Search for specific country clubs by name"
)

# Sidebar filters
st.sidebar.header("📊 Filters")

# State filter
states = sorted(df['State'].unique()) if 'State' in df.columns else []
if states:
    selected_states = st.sidebar.multiselect(
        "Select States:",
        options=states,
        default=states,  # Show all states by default
        help="Choose one or more states to filter the results"
    )
else:
    selected_states = []

# Monthly dues range filter
if 'Monthly Dues' in df.columns:
    min_dues = float(df['Monthly Dues'].min())
    max_dues = float(df['Monthly Dues'].max())
    
    dues_range = st.sidebar.slider(
        "Monthly Dues Range ($):",
        min_value=min_dues,
        max_value=max_dues,
        value=(min_dues, max_dues),
        step=50.0,
        format="$%.0f"
    )
else:
    dues_range = (0, 10000)

# Prestige level filter
prestige_levels = sorted(df['Prestige Level'].unique()) if 'Prestige Level' in df.columns and not bool(df['Prestige Level'].isna().all()) else []
if len(prestige_levels) > 0:
    selected_prestige = st.sidebar.multiselect(
        "Select Prestige Levels:",
        options=prestige_levels,
        default=prestige_levels,
        help="Choose club prestige levels"
    )
else:
    selected_prestige = []

# Membership type filter
membership_types = sorted(df['Membership Type'].unique()) if 'Membership Type' in df.columns and not bool(df['Membership Type'].isna().all()) else []
if len(membership_types) > 0:
    selected_membership = st.sidebar.multiselect(
        "Select Membership Types:",
        options=membership_types,
        default=membership_types,
        help="Choose membership types"
    )
else:
    selected_membership = []

# Initiation fee range filter
if 'Initiation Fee' in df.columns:
    min_init = float(df['Initiation Fee'].min())
    max_init = float(df['Initiation Fee'].max())
    
    init_range = st.sidebar.slider(
        "Initiation Fee Range ($):",
        min_value=min_init,
        max_value=max_init,
        value=(min_init, max_init),
        step=5000.0,
        format="$%.0f"
    )
else:
    init_range = (0, 1000000)

# Apply filters
filtered_df = cast(pd.DataFrame, df.copy())

# Filter by selected states
if len(selected_states) > 0 and 'State' in df.columns:
    filtered_df = cast(pd.DataFrame, filtered_df[filtered_df['State'].isin(selected_states)])

# Filter by dues range
if 'Monthly Dues' in df.columns:
    filtered_df = cast(pd.DataFrame, filtered_df[
        (filtered_df['Monthly Dues'] >= dues_range[0]) & 
        (filtered_df['Monthly Dues'] <= dues_range[1])
    ])

# Filter by prestige level
if len(selected_prestige) > 0 and 'Prestige Level' in df.columns:
    filtered_df = cast(pd.DataFrame, filtered_df[filtered_df['Prestige Level'].isin(selected_prestige)])

# Filter by membership type
if len(selected_membership) > 0 and 'Membership Type' in df.columns:
    filtered_df = cast(pd.DataFrame, filtered_df[filtered_df['Membership Type'].isin(selected_membership)])

# Filter by initiation fee range
if 'Initiation Fee' in df.columns:
    filtered_df = cast(pd.DataFrame, filtered_df[
        (filtered_df['Initiation Fee'] >= init_range[0]) & 
        (filtered_df['Initiation Fee'] <= init_range[1])
    ])

# Filter by search term
if search_term and len(search_term) > 0 and 'Club Name' in df.columns:
    filtered_df = cast(pd.DataFrame, filtered_df[
        filtered_df['Club Name'].str.contains(search_term, case=False, na=False)
    ])

# Main content area
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Directory Results ({len(filtered_df)} clubs found)")

with col2:
    # Sort options
    if not filtered_df.empty:
        sort_options = list(filtered_df.columns)
        sort_by = st.selectbox(
            "Sort by:",
            options=sort_options,
            index=sort_options.index('Monthly Dues') if 'Monthly Dues' in sort_options else 0
        )
        
        sort_order = st.radio(
            "Order:",
            options=["Ascending", "Descending"],
            horizontal=True
        )
        
        # Apply sorting
        ascending = sort_order == "Ascending"
        filtered_df = cast(pd.DataFrame, filtered_df.sort_values(by=sort_by, ascending=ascending))

# Club Comparison Feature
st.subheader("🔄 Club Comparison")
if not filtered_df.empty:
    # Allow users to select clubs for comparison
    available_clubs = filtered_df['Club Name'].tolist()
    selected_clubs = st.multiselect(
        "Select clubs to compare (up to 4):",
        options=available_clubs,
        max_selections=4,
        help="Choose 2-4 clubs to see a detailed side-by-side comparison"
    )
    
    if len(selected_clubs) >= 2:
        comparison_df = pd.DataFrame(filtered_df[filtered_df['Club Name'].isin(selected_clubs)]).copy()
        
        # Create comparison table
        st.subheader(f"Comparison of {len(selected_clubs)} Selected Clubs")
        
        # Display key metrics comparison
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = ['Monthly Dues', 'Total Monthly Cost', 'Annual Cost']
        for i, club_name in enumerate(selected_clubs[:4]):
            club_mask = comparison_df['Club Name'] == club_name
            club_rows = comparison_df.loc[club_mask]
            if len(club_rows) > 0:
                club_data = club_rows.iloc[0]
                
                with [col1, col2, col3, col4][i]:
                    st.markdown(f"**{club_name}**")
                    for metric in metrics:
                        if metric in comparison_df.columns:
                            if metric == 'Monthly Dues' or metric == 'Initiation Fee':
                                value = club_data[metric]
                                if isinstance(value, (int, float)) and value > 0:
                                    st.metric(metric, f"${value:,.0f}")
                                else:
                                    st.metric(metric, str(value))
                            elif metric == 'Total Monthly Cost' or metric == 'Annual Cost':
                                value = club_data.get(metric, 0)
                                if isinstance(value, (int, float)):
                                    st.metric(metric, f"${value:,.0f}")
        
        # Detailed comparison table
        st.subheader("Detailed Comparison")
        
        # Create a properly formatted comparison display
        comparison_display_data = []
        
        important_fields = ['State', 'City', 'Monthly Dues', 'Total Monthly Cost', 'Annual Cost', 'Initiation Fee', 
                          'Prestige Level', 'Membership Type', 'Contact Phone', 'Other Costs']
        
        available_fields = [field for field in important_fields if field in comparison_df.columns]
        
        for field in available_fields:
            row_data = {'Field': field}
            for club_name in selected_clubs:
                club_mask = comparison_df['Club Name'] == club_name
                club_rows = comparison_df.loc[club_mask]
                if len(club_rows) > 0:
                    value = club_rows.iloc[0][field]
                    
                    # Format numeric values with commas
                    if field in ['Monthly Dues', 'Total Monthly Cost', 'Annual Cost', 'Initiation Fee'] and isinstance(value, (int, float)) and value > 0:
                        formatted_value = f"${value:,.0f}"
                    else:
                        formatted_value = str(value)
                    
                    row_data[club_name] = formatted_value
                else:
                    row_data[club_name] = "N/A"
            
            comparison_display_data.append(row_data)
        
        comparison_display_df = pd.DataFrame(comparison_display_data)
        
        st.dataframe(
            comparison_display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Download comparison
        if len(selected_clubs) >= 2:
            csv_comparison = comparison_df.to_csv(index=False)
            st.download_button(
                label="Download Comparison as CSV",
                data=csv_comparison,
                file_name=f"club_comparison_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    elif len(selected_clubs) == 1:
        st.info("Please select at least 2 clubs to compare.")
    else:
        st.info("Select clubs from the list above to start comparing.")

# Club Membership Cost Savings Calculator
st.subheader("💰 Membership Cost Savings Calculator")

if not filtered_df.empty:
    calculator_col1, calculator_col2 = st.columns(2)
    
    with calculator_col1:
        st.markdown("**Current Club**")
        current_clubs = ['Select a club...'] + filtered_df['Club Name'].tolist()
        current_club = st.selectbox(
            "Choose your current club:",
            options=current_clubs,
            key="current_club"
        )
        
        # Manual cost input for current club
        if current_club != 'Select a club...':
            current_club_data = filtered_df[filtered_df['Club Name'] == current_club]
            if len(current_club_data) > 0:
                club_data = current_club_data.iloc[0]
                default_monthly = club_data.get('Monthly Dues', 0) if isinstance(club_data.get('Monthly Dues', 0), (int, float)) else 0
                default_initiation = club_data.get('Initiation Fee', 0) if isinstance(club_data.get('Initiation Fee', 0), (int, float)) else 0
            else:
                default_monthly = 0
                default_initiation = 0
        else:
            default_monthly = 0
            default_initiation = 0
            
        current_monthly = st.number_input(
            "Current monthly dues ($):",
            min_value=0,
            value=int(default_monthly),
            step=50,
            key="current_monthly"
        )
        
        current_initiation = st.number_input(
            "Current initiation fee ($):",
            min_value=0,
            value=int(default_initiation),
            step=1000,
            key="current_initiation"
        )
        
        current_food_min = st.number_input(
            "Current monthly food minimum ($):",
            min_value=0,
            value=0,
            step=25,
            key="current_food"
        )
    
    with calculator_col2:
        st.markdown("**Target Club**")
        target_clubs = ['Select a club...'] + filtered_df['Club Name'].tolist()
        target_club = st.selectbox(
            "Choose target club:",
            options=target_clubs,
            key="target_club"
        )
        
        # Manual cost input for target club
        if target_club != 'Select a club...':
            target_club_data = filtered_df[filtered_df['Club Name'] == target_club]
            if len(target_club_data) > 0:
                club_data = target_club_data.iloc[0]
                default_target_monthly = club_data.get('Monthly Dues', 0) if isinstance(club_data.get('Monthly Dues', 0), (int, float)) else 0
                default_target_initiation = club_data.get('Initiation Fee', 0) if isinstance(club_data.get('Initiation Fee', 0), (int, float)) else 0
            else:
                default_target_monthly = 0
                default_target_initiation = 0
        else:
            default_target_monthly = 0
            default_target_initiation = 0
            
        target_monthly = st.number_input(
            "Target monthly dues ($):",
            min_value=0,
            value=int(default_target_monthly),
            step=50,
            key="target_monthly"
        )
        
        target_initiation = st.number_input(
            "Target initiation fee ($):",
            min_value=0,
            value=int(default_target_initiation),
            step=1000,
            key="target_initiation"
        )
        
        target_food_min = st.number_input(
            "Target monthly food minimum ($):",
            min_value=0,
            value=0,
            step=25,
            key="target_food"
        )
    
    # Calculation period
    st.markdown("**Calculation Period**")
    calc_col1, calc_col2 = st.columns(2)
    
    with calc_col1:
        time_period = st.selectbox(
            "Calculate savings over:",
            options=[1, 2, 3, 5, 10, 15, 20],
            index=2,  # Default to 3 years
            format_func=lambda x: f"{x} year{'s' if x > 1 else ''}"
        )
    
    with calc_col2:
        include_initiation = st.checkbox(
            "Include initiation fees in calculation",
            value=True,
            help="Uncheck if you're already a member of both clubs"
        )
    
    # Calculate and display results
    if current_club != 'Select a club...' and target_club != 'Select a club...':
        # Monthly calculations
        current_total_monthly = current_monthly + current_food_min
        target_total_monthly = target_monthly + target_food_min
        monthly_difference = current_total_monthly - target_total_monthly
        
        # Annual calculations
        annual_difference = monthly_difference * 12
        
        # Total period calculations
        total_period_difference = annual_difference * time_period
        
        # Include initiation fees if selected
        if include_initiation:
            initiation_difference = current_initiation - target_initiation
            total_period_difference += initiation_difference
        else:
            initiation_difference = 0
        
        # Display results
        st.markdown("---")
        st.subheader("💡 Cost Analysis Results")
        
        result_col1, result_col2, result_col3, result_col4 = st.columns(4)
        
        with result_col1:
            if monthly_difference >= 0:
                st.metric("Monthly Savings", f"${monthly_difference:,.0f}", delta=f"${monthly_difference:,.0f}")
            else:
                st.metric("Monthly Cost Increase", f"${abs(monthly_difference):,.0f}", delta=f"-${abs(monthly_difference):,.0f}")
        
        with result_col2:
            if annual_difference >= 0:
                st.metric("Annual Savings", f"${annual_difference:,.0f}", delta=f"${annual_difference:,.0f}")
            else:
                st.metric("Annual Cost Increase", f"${abs(annual_difference):,.0f}", delta=f"-${abs(annual_difference):,.0f}")
        
        with result_col3:
            if include_initiation and initiation_difference != 0:
                if initiation_difference >= 0:
                    st.metric("Initiation Fee Savings", f"${initiation_difference:,.0f}", delta=f"${initiation_difference:,.0f}")
                else:
                    st.metric("Initiation Fee Increase", f"${abs(initiation_difference):,.0f}", delta=f"-${abs(initiation_difference):,.0f}")
            else:
                st.metric("Initiation Impact", "$0", delta="$0")
        
        with result_col4:
            if total_period_difference >= 0:
                st.metric(f"{time_period}-Year Total Savings", f"${total_period_difference:,.0f}", delta=f"${total_period_difference:,.0f}")
            else:
                st.metric(f"{time_period}-Year Total Increase", f"${abs(total_period_difference):,.0f}", delta=f"-${abs(total_period_difference):,.0f}")
        
        # Detailed breakdown
        with st.expander("📊 Detailed Cost Breakdown"):
            breakdown_data = {
                'Cost Component': ['Monthly Dues', 'Food Minimum', 'Total Monthly', 'Annual Cost'],
                f'{current_club}': [
                    f"${current_monthly:,.0f}",
                    f"${current_food_min:,.0f}",
                    f"${current_total_monthly:,.0f}",
                    f"${current_total_monthly * 12:,.0f}"
                ],
                f'{target_club}': [
                    f"${target_monthly:,.0f}",
                    f"${target_food_min:,.0f}",
                    f"${target_total_monthly:,.0f}",
                    f"${target_total_monthly * 12:,.0f}"
                ],
                'Difference': [
                    f"${current_monthly - target_monthly:+,.0f}",
                    f"${current_food_min - target_food_min:+,.0f}",
                    f"${monthly_difference:+,.0f}",
                    f"${annual_difference:+,.0f}"
                ]
            }
            
            if include_initiation:
                breakdown_data['Cost Component'].append('Initiation Fee')
                breakdown_data[f'{current_club}'].append(f"${current_initiation:,.0f}")
                breakdown_data[f'{target_club}'].append(f"${target_initiation:,.0f}")
                breakdown_data['Difference'].append(f"${initiation_difference:+,.0f}")
            
            breakdown_df = pd.DataFrame(breakdown_data)
            st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
        
        # Break-even analysis
        if monthly_difference < 0 and include_initiation and initiation_difference > 0:
            # Calculate break-even point
            break_even_months = initiation_difference / abs(monthly_difference)
            if break_even_months > 0:
                st.info(f"💡 **Break-even Analysis:** Despite higher monthly costs, the lower initiation fee means you'll break even after {break_even_months:.1f} months ({break_even_months/12:.1f} years)")

# Display results
if filtered_df.empty:
    st.info("No country clubs match your current filters. Please try adjusting your search criteria.")
else:
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clubs", len(filtered_df))
    
    with col2:
        if 'Monthly Dues' in filtered_df.columns:
            avg_dues = filtered_df['Monthly Dues'].mean()
            st.metric("Average Monthly Dues", f"${avg_dues:,.0f}")
    
    with col3:
        if 'State' in filtered_df.columns:
            unique_states = int(filtered_df['State'].nunique())
            st.metric("States Represented", unique_states)
    
    with col4:
        if 'Monthly Dues' in filtered_df.columns:
            min_dues = filtered_df['Monthly Dues'].min()
            max_dues = filtered_df['Monthly Dues'].max()
            if min_dues == max_dues:
                st.metric("Dues Range", f"${min_dues:,.0f}")
            else:
                # Use shorter format for better display
                min_formatted = f"${min_dues/1000:.0f}K" if min_dues >= 1000 else f"${min_dues:.0f}"
                max_formatted = f"${max_dues/1000:.0f}K" if max_dues >= 1000 else f"${max_dues:.0f}"
                st.metric("Dues Range", f"{min_formatted} - {max_formatted}")

    # Data table with formatting
    display_df = cast(pd.DataFrame, filtered_df.copy())
    
    # Calculate Total Monthly Cost (Monthly Dues + Monthly Fees from Other Costs) before formatting
    if 'Monthly Dues' in display_df.columns:
        # Store the numeric values for comparison before formatting
        filtered_df['Total Monthly Cost'] = filtered_df.apply(lambda row: calculate_total_monthly_cost(row), axis=1)
        display_df['Total Monthly Cost'] = display_df.apply(lambda row: calculate_total_monthly_cost(row), axis=1)
        
        # Calculate Annual Cost (Total Monthly Cost * 12)
        filtered_df['Annual Cost'] = filtered_df['Total Monthly Cost'] * 12
        display_df['Annual Cost'] = display_df['Total Monthly Cost'] * 12
    
    # Format monthly dues as currency if column exists
    if 'Monthly Dues' in display_df.columns:
        display_df['Monthly Dues'] = display_df['Monthly Dues'].apply(
            lambda x: f"${x:,.0f}" if isinstance(x, (int, float)) and x > 0 else str(x)
        )
    
    # Format total monthly cost as currency if column exists
    if 'Total Monthly Cost' in display_df.columns:
        display_df['Total Monthly Cost'] = display_df['Total Monthly Cost'].apply(
            lambda x: f"${x:,.0f}" if isinstance(x, (int, float)) and x > 0 else str(x)
        )
    
    # Format initiation fees as currency if column exists
    if 'Initiation Fee' in display_df.columns:
        display_df['Initiation Fee'] = display_df['Initiation Fee'].apply(
            lambda x: f"${x:,.0f}" if isinstance(x, (int, float)) and x > 0 else "No Fee"
        )
    
    # Format Annual Cost as currency if column exists
    if 'Annual Cost' in display_df.columns:
        display_df['Annual Cost'] = display_df['Annual Cost'].apply(
            lambda x: f"${x:,.0f}" if isinstance(x, (int, float)) and x > 0 else str(x)
        )
    
    # Format phone numbers if column exists
    if 'Contact Phone' in display_df.columns:
        display_df['Contact Phone'] = display_df['Contact Phone'].astype(str)
    
    # Ensure website URLs are properly formatted for LinkColumn
    if 'Website' in display_df.columns:
        def format_url(url):
            if pd.isna(url) or not url or str(url).strip() == '':
                return None
            url_str = str(url).strip()
            if not url_str.startswith(('http://', 'https://')):
                url_str = 'https://' + url_str
            return url_str
        
        display_df['Website'] = display_df['Website'].apply(format_url)
    
    # Reorder columns to put Total Monthly Cost and Annual Cost right after Monthly Dues
    if 'Total Monthly Cost' in display_df.columns:
        columns = list(display_df.columns)
        # Remove Total Monthly Cost and Annual Cost from their current positions
        if 'Total Monthly Cost' in columns:
            columns.remove('Total Monthly Cost')
        if 'Annual Cost' in columns:
            columns.remove('Annual Cost')
        
        # Find Monthly Dues index and insert Total Monthly Cost and Annual Cost after it
        if 'Monthly Dues' in columns:
            monthly_dues_idx = columns.index('Monthly Dues')
            columns.insert(monthly_dues_idx + 1, 'Total Monthly Cost')
            columns.insert(monthly_dues_idx + 2, 'Annual Cost')
        display_df = display_df[columns]
    
    # Display the dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Website": st.column_config.LinkColumn("Website"),
            "Monthly Dues": st.column_config.TextColumn("Monthly Dues"),
            "Total Monthly Cost": st.column_config.TextColumn("Total Monthly Cost", help="Monthly dues + monthly fees"),
            "Annual Cost": st.column_config.TextColumn("Annual Cost", help="Total monthly cost × 12 months"),
            "Initiation Fee": st.column_config.TextColumn("Initiation Fee"),
            "Contact Phone": st.column_config.TextColumn("Contact Phone"),
            "Prestige Level": st.column_config.TextColumn("Prestige Level"),
            "Membership Type": st.column_config.TextColumn("Membership Type"),
            "Other Costs": st.column_config.TextColumn("Other Costs")
        }
    )

# Export functionality
if not filtered_df.empty:
    st.subheader("📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download as CSV
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv,
            file_name=f"country_clubs_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            help="Download data as Excel-compatible CSV file"
        )
    
    with col2:
        # Generate and download PDF
        def create_pdf_report():
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            import io
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), 
                                  rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            # Create story elements
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            story.append(Paragraph("Country Club Golf Directory", title_style))
            story.append(Spacer(1, 12))
            
            # Summary info
            summary_style = ParagraphStyle(
                'Summary',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=12
            )
            story.append(Paragraph(f"Report Generated: {pd.Timestamp.now().strftime('%B %d, %Y')}", summary_style))
            story.append(Paragraph(f"Total Clubs: {len(filtered_df)}", summary_style))
            story.append(Spacer(1, 12))
            
            # Prepare data for table
            export_df = filtered_df.copy()
            
            # Select key columns for PDF
            pdf_columns = ['Club Name', 'State', 'City', 'Monthly Dues', 'Total Monthly Cost', 
                          'Annual Cost', 'Initiation Fee', 'Prestige Level']
            available_columns = [col for col in pdf_columns if col in export_df.columns]
            
            # Format data for PDF
            pdf_data = []
            header_row = available_columns
            pdf_data.append(header_row)
            
            for _, row in export_df.iterrows():
                row_data = []
                for col in available_columns:
                    value = row[col]
                    if col in ['Monthly Dues', 'Total Monthly Cost', 'Annual Cost', 'Initiation Fee']:
                        if isinstance(value, (int, float)) and value > 0:
                            row_data.append(f"${value:,.0f}")
                        else:
                            row_data.append(str(value))
                    else:
                        row_data.append(str(value)[:30])  # Truncate long text
                pdf_data.append(row_data)
            
            # Create table
            table = Table(pdf_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        
        if st.button("📄 Generate PDF", help="Create a formatted PDF report"):
            try:
                pdf_data = create_pdf_report()
                st.download_button(
                    label="📄 Download PDF Report",
                    data=pdf_data,
                    file_name=f"country_clubs_report_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                st.success("PDF report generated successfully!")
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
    
    with col3:
        # Download as JSON
        json_data = filtered_df.to_json(orient='records', indent=2)
        if json_data:
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name=f"country_clubs_{pd.Timestamp.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                help="Download data in JSON format for API use"
            )

# Footer with information
st.markdown("---")
st.markdown(
    """
    **About this Directory:**
    This application provides a comprehensive directory of country club golf monthly dues across all US states. 
    Use the filters and search functionality to find clubs that match your criteria.
    """
)

# Display data source information if available
if not df.empty:
    st.caption(f"Data last updated: {pd.Timestamp.now().strftime('%B %d, %Y')}")
    st.caption(f"Total clubs in database: {len(df)}")

# Made by Patlabs tag
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: red; font-weight: bold; margin-top: 20px;">Made by Patlabs</p>', 
    unsafe_allow_html=True
)
