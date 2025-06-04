def calculate_mamdani_wqi(measurement):
    """
    Fuzzy Mamdani implementation for Water Quality Index calculation aligned with 
    PP No. 22 Tahun 2021 water standards and STORET calculation methodology.
    
    Parameters:
        measurement: Object containing water quality parameters (do, ph, bod, cod, total_coliform)
    
    Returns:
        Dictionary containing WQI score, category, and detailed calculation information
    """
    def trimf(x, a, b, c):
        """
        Triangular membership function
        
        Parameters:
            x: The input value
            a, b, c: Parameters of triangular function where b is the peak
        
        Returns:
            Membership value between 0 and 1
        """
        if x <= a or x >= c:
            return 0
        elif a < x <= b:
            return (x - a) / (b - a) if (b - a) != 0 else 1
        else:  # b < x < c
            return (c - x) / (c - b) if (c - b) != 0 else 1

    # Parameter ranges based on PP No. 22/2021 standards
    parameter_ranges = {
        # DO: Higher is better (>= 4 is good)
        "do": {
            "poor": (0, 0, 2),          # Severely depleted oxygen
            "fair": (0, 2, 4),          # Below regulation minimum
            "good": (2, 4, 6),          # Meeting regulation minimum
            "excellent": (4, 6, 100)    # Well oxygenated
        },
        # pH: Should be between 6-9 (medium is ideal)
        "ph": {
            "poor": [(0, 0, 4), (11, 14, 14)],  # Far from neutral (very acidic or alkaline)
            "fair": [(3, 5, 6), (9, 10, 12)],   # Slightly outside regulation range
            "good": [(5, 6, 7), (8, 9, 10)],    # Near neutral, within regulation
            "excellent": [(6.5, 7, 8.5)]        # Ideal pH range for aquatic life
        },
        # BOD: Lower is better (<= 3 is good)
        "bod": {
            "poor": (6, 10, 100),       # Severely polluted
            "fair": (3, 6, 10),         # Moderately polluted
            "good": (1, 3, 6),          # Slightly polluted
            "excellent": (0, 0, 3)      # Clean water
        },
        # COD: Lower is better (<= 25 is good)
        "cod": {
            "poor": (50, 100, 1000),    # Severely polluted
            "fair": (25, 50, 100),      # Moderately polluted
            "good": (10, 25, 50),       # Slightly polluted
            "excellent": (0, 0, 25)     # Clean water
        },
        # Total Coliform: Lower is better (<= 5000 is good)
        "total_coliform": {
            "poor": (10000, 50000, 10000000),  # Heavy contamination
            "fair": (5000, 10000, 50000),      # Moderate contamination
            "good": (1000, 5000, 10000),       # Low contamination
            "excellent": (0, 0, 1000)          # Very low contamination
        }
    }

    # Check if all required parameters are present in measurement
    required_params = ["do", "ph", "bod", "cod", "total_coliform"]
    for param in required_params:
        if not hasattr(measurement, param):
            raise ValueError(f"Missing required parameter: {param}")

    # Calculate membership values for each parameter
    membership_values = {}
    for param, ranges in parameter_ranges.items():
        value = getattr(measurement, param)
        membership_values[param] = {}
        
        # Handle special case for pH which has a non-monotonic ideal range
        if param == "ph":
            for category, range_list in ranges.items():
                max_membership = 0
                for points in range_list:
                    if len(points) == 3:
                        a, b, c = points
                        membership = trimf(value, a, b, c)
                        max_membership = max(max_membership, membership)
                membership_values[param][category] = max_membership
        else:
            for category, points in ranges.items():
                # For normal parameters
                if len(points) == 3:
                    a, b, c = points
                    membership_values[param][category] = trimf(value, a, b, c)

    # Define WQI output ranges for defuzzification
    wqi_ranges = {
        "poor": (0, 25, 50),
        "fair": (25, 50, 75),
        "good": (50, 75, 90),
        "excellent": (75, 90, 100)
    }

    # Parameter weights based on their environmental significance
    parameter_weights = {
        "do": 3,            # Crucial for aquatic life
        "ph": 2,            # Important for chemical balance
        "bod": 3,           # Key indicator of organic pollution
        "cod": 3,           # Key indicator of chemical pollution
        "total_coliform": 4 # Critical for human health
    }
    
    # Rule evaluation and aggregation
    # We'll use a modified approach for rule firing
    total_weight = sum(parameter_weights.values())
    rule_strengths = {category: 0 for category in ["poor", "fair", "good", "excellent"]}
    
    # Calculate weighted rule strengths for each category
    for category in rule_strengths.keys():
        weighted_sum = 0
        for param in parameter_ranges.keys():
            # Apply weight to each parameter's membership value
            weighted_membership = membership_values[param][category] * parameter_weights[param]
            weighted_sum += weighted_membership
        
        # Normalize by total weight to get final rule strength
        rule_strengths[category] = weighted_sum / total_weight
    
    # Create discretized universe for defuzzification
    universe_points = list(range(0, 101))
    
    # Aggregate outputs using maximum combination method
    # For each point in the universe, find the maximum membership from all fired rules
    aggregated_output = [0] * len(universe_points)
    
    for i, x in enumerate(universe_points):
        for category, strength in rule_strengths.items():
            if strength > 0:  # Only consider rules with non-zero firing strength
                # Calculate output membership for this point
                a, b, c = wqi_ranges[category]
                category_membership = trimf(x, a, b, c)
                
                # Apply rule strength (min operator in Mamdani)
                clipped_membership = min(strength, category_membership)
                
                # Aggregate using max operator
                aggregated_output[i] = max(aggregated_output[i], clipped_membership)
    
    # Defuzzify using center of gravity (centroid) method
    numerator = sum(x * mu for x, mu in zip(universe_points, aggregated_output))
    denominator = sum(aggregated_output)
    
    # Handle division by zero
    if denominator > 0:
        wqi_value = numerator / denominator
    else:
        # If no rules fire significantly, use weighted average of rule strengths
        category_values = {"poor": 25, "fair": 50, "good": 75, "excellent": 90}
        wqi_value = sum(strength * category_values[cat] for cat, strength in rule_strengths.items())
        
        # Ensure there's at least some value
        if wqi_value == 0:
            wqi_value = 50  # Default to middle value as last resort
    
    # Ensure WQI is within valid range
    wqi_value = max(1, min(100, wqi_value))
    
    # Determine final category based on defuzzified value
    if wqi_value >= 90:
        category = "excellent"
    elif wqi_value >= 75:
        category = "good"
    elif wqi_value >= 50:
        category = "fair"
    else:
        category = "poor"

    return {
        "wqi_value": round(wqi_value, 2),
        "wqi_category": category,
        "method": "Mamdani (PP No. 22/2021)",
        "membership_values": membership_values,  # Return these for debugging
        "rule_strengths": rule_strengths,         # Return these for debugging
        "aggregated_output": aggregated_output   # Return for visualization if needed
    }