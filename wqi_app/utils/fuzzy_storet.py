def calculate_storet_score(measurement):
    """
    Perhitungan STORET berdasarkan 5 parameter sesuai PP No. 22 Tahun 2021
    
    Parameters:
        measurement: Object containing water quality parameters (do, ph, bod, cod, total_coliform)
    
    Returns:
        Dictionary containing WQI score, category, class, and detailed parameter scores
    """
    # Check if all required parameters are present in measurement
    required_params = ["do", "ph", "bod", "cod", "total_coliform"]
    for param in required_params:
        if not hasattr(measurement, param):
            raise ValueError(f"Missing required parameter: {param}")

    def get_score(value, param):
        """
        Calculate STORET score for individual parameter based on PP No. 22 Tahun 2021
        
        Parameters:
            value: Measured value of parameter
            param: Parameter name
            
        Returns:
            Score value (negative value indicates pollution level)
        """
        thresholds = {
            'ph': (6.0, 9.0),
            'do': 4.0,
            'bod': 3.0,
            'cod': 25.0,
            'total_coliform': 5000
        }

        if param == 'ph':
            if thresholds['ph'][0] <= value <= thresholds['ph'][1]:
                return 0
            elif value < thresholds['ph'][0] - 1 or value > thresholds['ph'][1] + 1:
                return -5  # Significant deviation from pH range
            else:
                return -3  # Minor deviation from pH range
        else:
            if param in thresholds:
                if param == 'do':
                    if value >= thresholds[param]:
                        return 0
                    elif value >= thresholds[param] * 0.8:  # Within 80% of threshold
                        return -1
                    elif value >= thresholds[param] * 0.6:  # Within 60% of threshold
                        return -3
                    else:
                        return -5  # Severe oxygen depletion
                else:  # For BOD, COD, Total Coliform (lower is better)
                    if value <= thresholds[param]:
                        return 0
                    elif value <= thresholds[param] * 1.5:
                        return -1
                    elif value <= thresholds[param] * 2:
                        return -3
                    else:
                        return -5
        
        return -5  # Default untuk nilai yang sangat jauh dari baku mutu

    # Calculate scores for each parameter
    scores = {
        'ph': get_score(measurement.ph, 'ph'),
        'do': get_score(measurement.do, 'do'),
        'bod': get_score(measurement.bod, 'bod'),
        'cod': get_score(measurement.cod, 'cod'),
        'total_coliform': get_score(measurement.total_coliform, 'total_coliform')
    }

    # Calculate total score
    total_score = sum(scores.values())
    
    # Convert STORET score to WQI value (0-100 scale)
    # Using a modified linear mapping that ensures:
    # - Score 0 maps to WQI 100
    # - Score -15 maps to WQI 50 (fair/moderate pollution)
    # - Score -30 or lower maps to WQI 0 (severe pollution)
    wqi_value = max(0, 100 + (total_score / 0.3))

    # Determine WQI category based on WQI value
    if wqi_value >= 90:
        category = "excellent"
    elif wqi_value >= 75:
        category = "good"
    elif wqi_value >= 50:
        category = "fair"
    else:
        category = "poor"

    return {
        'wqi_value': round(wqi_value, 2),
        'wqi_category': category,
        'method': 'STORET (PP No. 22/2021)',
        'storet_score': total_score,
        'storet_class': get_storet_class(total_score),
        'parameter_scores': scores
    }

def get_storet_class(score):
    """
    Menentukan kelas kualitas air berdasarkan skor STORET
    
    Parameters:
        score: STORET score value
        
    Returns:
        Class category and description
    """
    if score == 0:
        return "A (Memenuhi Baku Mutu)"
    elif -1 >= score > -11:
        return "B (Tercemar Ringan)"
    elif -11 >= score > -30:
        return "C (Tercemar Sedang)"
    else:
        return "D (Tercemar Berat)"