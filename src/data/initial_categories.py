"""
Initial data for damage categories and items in the settlement calculator.
"""

# Default damage categories with initial items
DEFAULT_CATEGORIES = [
    {
        "name": "Structure",
        "description": "Damage to the main structure and attached components",
        "items": [
            {"name": "Roof", "description": "Roof covering, decking, flashing", "default_depreciation_rate": 0.05},
            {"name": "Exterior Walls", "description": "Siding, stucco, brick, trim", "default_depreciation_rate": 0.03},
            {"name": "Windows", "description": "Glass, frames, screens", "default_depreciation_rate": 0.04},
            {"name": "Doors", "description": "Entry doors, sliding doors, garage doors", "default_depreciation_rate": 0.05},
            {"name": "Foundation", "description": "Concrete, footings, slabs", "default_depreciation_rate": 0.01},
            {"name": "Framing", "description": "Beams, joists, studs, trusses", "default_depreciation_rate": 0.02}
        ]
    },
    {
        "name": "Interior",
        "description": "Damage to interior components of the structure",
        "items": [
            {"name": "Drywall", "description": "Wall and ceiling drywall/sheetrock", "default_depreciation_rate": 0.02},
            {"name": "Flooring", "description": "Carpet, tile, hardwood, laminate", "default_depreciation_rate": 0.08},
            {"name": "Cabinets", "description": "Kitchen and bathroom cabinets", "default_depreciation_rate": 0.05},
            {"name": "Countertops", "description": "Kitchen and bathroom countertops", "default_depreciation_rate": 0.04},
            {"name": "Interior Doors", "description": "Interior doors and hardware", "default_depreciation_rate": 0.05},
            {"name": "Trim", "description": "Baseboards, crown molding, casings", "default_depreciation_rate": 0.03},
            {"name": "Paint", "description": "Interior paint and wallpaper", "default_depreciation_rate": 0.10}
        ]
    },
    {
        "name": "Systems",
        "description": "Damage to building systems",
        "items": [
            {"name": "Electrical", "description": "Wiring, outlets, switches, panels", "default_depreciation_rate": 0.03},
            {"name": "Plumbing", "description": "Pipes, fixtures, water heater", "default_depreciation_rate": 0.04},
            {"name": "HVAC", "description": "Heating, cooling, ventilation", "default_depreciation_rate": 0.06},
            {"name": "Insulation", "description": "Wall, ceiling, floor insulation", "default_depreciation_rate": 0.05}
        ]
    },
    {
        "name": "Contents",
        "description": "Damage to personal property/contents",
        "items": [
            {"name": "Furniture", "description": "Tables, chairs, sofas, beds", "default_depreciation_rate": 0.10},
            {"name": "Appliances", "description": "Refrigerator, stove, washer/dryer", "default_depreciation_rate": 0.08},
            {"name": "Electronics", "description": "TVs, computers, audio equipment", "default_depreciation_rate": 0.15},
            {"name": "Clothing", "description": "All clothing items", "default_depreciation_rate": 0.20},
            {"name": "Kitchenware", "description": "Pots, pans, dishes, utensils", "default_depreciation_rate": 0.10},
            {"name": "Decor", "description": "Art, decorations, curtains, rugs", "default_depreciation_rate": 0.12}
        ]
    },
    {
        "name": "Exterior Features",
        "description": "Damage to exterior features of the property",
        "items": [
            {"name": "Landscaping", "description": "Trees, shrubs, plants, lawn", "default_depreciation_rate": 0.15},
            {"name": "Fencing", "description": "All types of fencing", "default_depreciation_rate": 0.07},
            {"name": "Deck/Patio", "description": "Decks, patios, porches", "default_depreciation_rate": 0.05},
            {"name": "Driveway", "description": "Concrete, asphalt, pavers", "default_depreciation_rate": 0.03},
            {"name": "Detached Structures", "description": "Sheds, detached garages", "default_depreciation_rate": 0.04}
        ]
    },
    {
        "name": "Additional Expenses",
        "description": "Additional costs related to the claim",
        "items": [
            {"name": "Temporary Housing", "description": "Hotel, rental housing", "default_depreciation_rate": 0.0},
            {"name": "Storage", "description": "Content storage costs", "default_depreciation_rate": 0.0},
            {"name": "Debris Removal", "description": "Cleanup and debris removal", "default_depreciation_rate": 0.0},
            {"name": "Professional Services", "description": "Engineering, architect fees", "default_depreciation_rate": 0.0}
        ]
    }
] 