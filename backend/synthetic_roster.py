"""Reviewable synthetic roster used only by the first shift planning prototype."""

WORKERS = [
    {"id": "SYN-001", "departments": ["Passenger Services", "Ramp Operations"], "days": [0, 1, 2, 3, 4], "shifts": ["Morning", "Afternoon"], "weekly_cap": 32},
    {"id": "SYN-002", "departments": ["Passenger Services", "Fuel Services"], "days": [0, 1, 2, 3, 4, 5], "shifts": ["Morning", "Afternoon"], "weekly_cap": 32},
    {"id": "SYN-003", "departments": ["Ramp Operations", "Fuel Services"], "days": [1, 2, 3, 4, 5, 6], "shifts": ["Afternoon", "Overnight"], "weekly_cap": 32},
    {"id": "SYN-004", "departments": ["Passenger Services"], "days": [0, 1, 2, 3, 4, 5, 6], "shifts": ["Morning", "Afternoon", "Overnight"], "weekly_cap": 24},
    {"id": "SYN-005", "departments": ["Ramp Operations"], "days": [0, 1, 2, 3, 4, 5, 6], "shifts": ["Morning", "Afternoon", "Overnight"], "weekly_cap": 24},
    {"id": "SYN-006", "departments": ["Fuel Services"], "days": [0, 1, 2, 3, 4, 5, 6], "shifts": ["Morning", "Afternoon", "Overnight"], "weekly_cap": 24},
    {"id": "SYN-007", "departments": ["Passenger Services", "Fuel Services"], "days": [0, 1, 2, 3, 4, 5, 6], "shifts": ["Morning", "Afternoon"], "weekly_cap": 32},
    {"id": "SYN-008", "departments": ["Ramp Operations", "Passenger Services"], "days": [0, 1, 2, 3, 4, 5, 6], "shifts": ["Morning", "Overnight"], "weekly_cap": 32},
]
