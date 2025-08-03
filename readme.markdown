# Trip Planner

Welcome to the **Truck Trip Planner**! This application helps you plan long-haul truck trips, automates route calculations, and simulates U.S. FMCSA Hours of Service (HOS) log sheets, including detecting regulation violations for over-the-road truck drivers.

## Table of Contents

- [Features](#features)
- [Setup](#setup)
- [Models](#models)
- [API Overview](#api-overview)
- [Core Logic Explanation](#core-logic-explanation)
- [How Routing & HOS Work](#how-routing--hos-work)
- [Example Workflow](#example-workflow)
- [Error Handling](#error-handling)
- [Notes](#notes)

## Features

- **Trip Storage**: Stores trip details including current location, pickup location, dropoff location, and hours driven in the current 70hr/8day cycle
- **Route Integration**: Integrates with OpenRouteService for address geocoding and route calculation
- **Trip Estimation**: Estimates total distance and simulates truck trip timeframes, including stops and rest periods
- **HOS Log Generation**: Generates detailed simulated HOS daily log sheets
- **Violation Detection**: Detects HOS rule violations and highlights where regulations would be broken
- **Trip Visualization**: Visualizes trip segments and fuel stop coordinates

## Setup

### Clone the Repo & Install Dependencies

Python 3.8+ and Django/DRF required:

```bash
pip install -r requirements.txt
```

### Add API Keys

Place your OpenRouteService API key in your `.env` file or settings as `ORS_API_KEY`.

### Migrate Database

```bash
python manage.py migrate
```

### Run Server

```bash
python manage.py runserver
```

## Models

```python
class Trip(models.Model):
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_hours = models.FloatField(
        help_text="Total on-duty hours used in the current 70hr/8day cycle"
    )
    created_at = models.DateTimeField(auto_now_add=True)
```

## API Overview

**Endpoint**: `/api/trip/` (POST)  
**Serializer**: `TripInputSerializer`

### Fields

- `current_location`: Starting city/address
- `pickup_location`: Where to pickup load
- `dropoff_location`: Delivery location
- `current_cycle_hours`: Hours used in current 70hr/8day cycle

### Sample POST Payload

```json
{
  "current_location": "Denver, CO",
  "pickup_location": "Chicago, IL",
  "dropoff_location": "Boston, MA",
  "current_cycle_hours": 40.5
}
```

## Core Logic Explanation

### Geocoding & Routing

- `geocode_place(place)`: Gets longitude/latitude for a place using OpenRouteService
- `get_route_distance(start, end)`:
  - Geocodes both addresses
  - Fetches route distance/polyline geometry
  - Decodes route for mapping and calculations

### Trip Calculation

- Calculates two segments: current → pickup, and pickup → dropoff
- Total route and encoded geometry are merged
- **Fuel stops**: Estimated as 1 stop every 1,000 miles

### HOS Log Sheet Simulation

#### Driving Rules Implemented

- **Max 11 driving hours** per 14 hour day
- **Max 14 hours on-duty** per 24h
- **70-hour max** in 8-day cycle; built-in logic for automatic 34-hour reset simulation if needed
- Generates a daily log for the trip, marking rest, resets, and violations

#### HOS Violation Detection

- Warns if the driver starts above 70 hours, or trip would push over limit
- Detects daily violations (excess driving/duty), incomplete logging

### Fuel Stop Coordinates

- Interpolates route geometry to generate lat/lon of each planned stop

## How Routing & HOS Work

The application follows U.S. FMCSA Hours of Service regulations:

1. **Daily Limits**: 11 hours driving within a 14-hour on-duty window
2. **Weekly Limits**: 70 hours on-duty in 8 consecutive days
3. **Rest Requirements**: 10 consecutive hours off-duty between driving periods
4. **34-Hour Reset**: Automatically simulated when cycle hours are exhausted

## Example Workflow

1. Send trip details to `/api/trip/`
2. Response will contain:
   - Distance, estimated driving days, and log sheet
   - HOS warnings if any rule would be broken
   - Route/fuel stop coordinates for mapping

## Error Handling

The application fails gracefully if:
- Locations can't be geocoded
- Route can't be calculated
- Log can't be fit due to cycle limits

## Notes

- Assumes fixed driving speed (50mph) and fixed times for pickup/dropoff/fueling
- Obeys basic U.S. HOS logic but is **only for simulation & testing**, not legal compliance advice
- Polyline route geometry can be visualized using any polyline mapping tool
- Easily extendable for additional trip features, reporting, or vehicle constraints

