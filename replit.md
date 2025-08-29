# Country Club Golf Directory

## Overview

A Streamlit-based web application that provides a searchable directory of country clubs across the United States. The application allows users to browse and filter country club information including monthly dues, locations, and contact details. Built with Python and Streamlit, it features a clean interface with sidebar filtering capabilities and caching for optimal performance.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework for rapid prototyping and deployment
- **Layout**: Wide layout with expandable sidebar for filtering controls
- **Caching**: Streamlit's built-in caching decorator (@st.cache_data) for data loading optimization
- **State Management**: Session-based state management through Streamlit's native capabilities

### Data Architecture
- **Data Source**: CSV file-based storage located in `data/country_clubs.csv`
- **Data Loading**: Centralized data loading through utility module with error handling
- **Data Validation**: Schema validation ensuring required columns are present
- **Data Structure**: Structured data with columns for Club Name, State, City, Monthly Dues, Contact Phone, Website, and Address

### Application Structure
- **Main Application**: `app.py` serves as the entry point and UI controller
- **Utilities Module**: `utils/data_loader.py` handles data loading, validation, and cleaning
- **Error Handling**: Comprehensive error handling for missing files, empty datasets, and malformed data
- **User Experience**: Progressive disclosure with filters in sidebar and main content area for results

### Performance Considerations
- **Data Caching**: Automatic caching of loaded data to prevent repeated file reads
- **Lazy Loading**: Data is only loaded when the application starts and cached thereafter
- **Efficient Filtering**: Client-side filtering through Streamlit's built-in components

## External Dependencies

### Core Dependencies
- **Streamlit**: Web application framework for the user interface
- **Pandas**: Data manipulation and analysis library for handling CSV data
- **NumPy**: Numerical computing library for data processing support

### Data Dependencies
- **CSV Data Source**: Expects a structured CSV file at `data/country_clubs.csv`
- **File System**: Relies on local file system for data storage and retrieval

### Runtime Environment
- **Python**: Python runtime environment required for execution
- **Web Browser**: Client-side rendering through web browser interface
- **Port Access**: Requires available port for Streamlit server (typically 8501)