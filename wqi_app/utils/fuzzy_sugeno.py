def calculate_sugeno_wqi(measurement):
    """
    Fuzzy Sugeno implementation for Water Quality Index calculation aligned with 
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
                # For normal parameters with single range
                if len(points) == 3:
                    a, b, c = points
                    membership_values[param][category] = trimf(value, a, b, c)

    # Define Sugeno output values - aligned with WQI categories
    output_values = {
        "poor": 25,        # 0-50 range midpoint
        "fair": 62.5,      # 50-75 range midpoint
        "good": 82.5,      # 75-90 range midpoint
        "excellent": 95    # 90-100 range midpoint
    }
    
    # Define parameter weights based on environmental significance
    parameter_weights = {
        "do": 3,           # Crucial for aquatic life
        "ph": 2,           # Important for chemical balance
        "bod": 3,          # Key indicator of organic pollution
        "cod": 3,          # Key indicator of chemical pollution
        "total_coliform": 4 # Critical for human health
    }
    
    total_param_weight = sum(parameter_weights.values())
    
    # For Sugeno inference:
    # 1. Evaluate all rules
    # 2. Multiply each rule output by its firing strength
    # 3. Sum all weighted outputs and divide by sum of weights
    
    # Initialize accumulators for weighted sum
    weighted_sum = 0
    weight_sum = 0
    
    # Apply rule evaluation with weighted average defuzzification
    categories = ["poor", "fair", "good", "excellent"]
    
    # Track rule firing for debugging and results
    rule_firings = []
    
    # For each possible category
    for category in categories:
        # Calculate minimum rule firing strength for each parameter
        category_strengths = {param: membership_values[param][category] for param in parameter_ranges.keys()}
        min_strength = min(category_strengths.values())
        
        # Calculate weighted rule strength
        weighted_strength = sum(strength * parameter_weights[param] 
                               for param, strength in category_strengths.items()) / total_param_weight
        
        # Use a combination of min and weighted approach for better results
        # This balances traditional fuzzy logic with weighted importance
        alpha = 0.6  # Weight for min operator (traditional fuzzy logic)
        beta = 0.4   # Weight for weighted average (parameter importance)
        rule_strength = (alpha * min_strength) + (beta * weighted_strength)
        
        if rule_strength > 0:
            # Save rule firing information
            rule_firings.append({
                "category": category,
                "strength": rule_strength,
                "output": output_values[category],
                "param_strengths": category_strengths
            })
            
            # Apply weight to output value and accumulate
            weighted_sum += rule_strength * output_values[category]
            weight_sum += rule_strength
    
    # Calculate final weighted average (Sugeno defuzzification)
    if weight_sum > 0:
        wqi_value = weighted_sum / weight_sum
    else:
        # Fallback if no rules fire significantly
        # Use a weighted average of parameter qualities
        wqi_value = 0
        
        for param in parameter_ranges.keys():
            param_value = getattr(measurement, param)
            param_quality = 0
            
            # Parameter-specific quality assessment as fallback
            if param == "do":
                # DO: 0 = poor, 4+ = excellent
                param_quality = min(100, max(0, param_value * 25))
            elif param == "ph":
                # pH: 7 is ideal (100%), deviation reduces quality
                param_quality = 100 - min(100, abs(param_value - 7) * 20)
            elif param == "bod":
                # BOD: 0 = excellent, 10+ = poor
                param_quality = max(0, 100 - param_value * 10)
            elif param == "cod":
                # COD: 0 = excellent, 100+ = poor
                param_quality = max(0, 100 - param_value)
            elif param == "total_coliform":
                # Total Coliform: 0 = excellent, 100000+ = poor
                param_quality = max(0, 100 - (param_value / 1000))
            
            wqi_value += param_quality * parameter_weights[param]
        
        wqi_value = wqi_value / total_param_weight
    
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
        "method": "Sugeno (PP No. 22/2021)",
        "membership_values": membership_values,  # Return for debugging
        "rule_firings": rule_firings           # Return for debugging
    }