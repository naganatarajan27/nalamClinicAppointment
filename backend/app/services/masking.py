def mask_phone_number(number: str) -> str:
    """Masks all but the country code and last 2 digits, e.g. +919876543210 -> +91*******10."""
    if len(number) <= 6:
        return "*" * len(number)
    visible_prefix = number[:3]
    visible_suffix = number[-2:]
    masked_len = len(number) - len(visible_prefix) - len(visible_suffix)
    return f"{visible_prefix}{'*' * masked_len}{visible_suffix}"
