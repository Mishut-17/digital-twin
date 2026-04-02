"""Input validation for configuration parameters."""


def validate_config(data: dict) -> tuple:
    """
    Validate configuration parameters.
    Returns (is_valid, errors) tuple.
    """
    errors = []

    life_scale = data.get("life_weight_scale", 5)
    if not isinstance(life_scale, int) or not 1 <= life_scale <= 10:
        errors.append("life_weight_scale must be an integer between 1 and 10")

    slope_scale = data.get("slope_weight_scale", 5)
    if not isinstance(slope_scale, int) or not 1 <= slope_scale <= 10:
        errors.append("slope_weight_scale must be an integer between 1 and 10")

    age = data.get("bearing_age_hours", 0)
    if not isinstance(age, (int, float)) or age < 0:
        errors.append("bearing_age_hours must be a non-negative number")

    life = data.get("bearing_total_life_hours", 1500)
    if not isinstance(life, (int, float)) or life < 100:
        errors.append("bearing_total_life_hours must be at least 100")

    if age > life:
        errors.append("bearing_age_hours cannot exceed bearing_total_life_hours")

    return (len(errors) == 0, errors)
