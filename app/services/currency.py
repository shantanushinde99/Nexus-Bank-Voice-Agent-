"""Indian currency formatting utilities for voice-friendly output."""


def format_inr_spoken(amount: float) -> str:
    """Convert a number to Indian spoken words format.
    Example: 125430.50 -> '1 lakh 25 thousand 430 rupees and 50 paise'
    """
    rupees = int(amount)
    paise = round((amount - rupees) * 100)

    if rupees == 0:
        spoken = "zero rupees"
    else:
        parts = []
        # Crores (1,00,00,000+)
        if rupees >= 10000000:
            crores = rupees // 10000000
            rupees %= 10000000
            parts.append(f"{crores} crore" if crores == 1 else f"{crores} crores")

        # Lakhs (1,00,000+)
        if rupees >= 100000:
            lakhs = rupees // 100000
            rupees %= 100000
            parts.append(f"{lakhs} lakh" if lakhs == 1 else f"{lakhs} lakhs")

        # Thousands (1,000+)
        if rupees >= 1000:
            thousands = rupees // 1000
            rupees %= 1000
            parts.append(f"{thousands} thousand")

        # Hundreds
        if rupees >= 100:
            hundreds = rupees // 100
            rupees %= 100
            parts.append(f"{hundreds} hundred")

        # Remaining
        if rupees > 0:
            parts.append(str(rupees))

        spoken = " ".join(parts) + " rupees"

    if paise > 0:
        spoken += f" and {paise} paise"

    return spoken


def format_inr_display(amount: float) -> str:
    """Format number in Indian comma grouping for display.
    Example: 125430.50 -> '₹1,25,430.50'
    """
    rupees = int(amount)
    paise = round((amount - rupees) * 100)

    # Indian grouping: last 3 digits, then groups of 2
    s = str(rupees)
    if len(s) <= 3:
        formatted = s
    else:
        last_three = s[-3:]
        remaining = s[:-3]
        # Group remaining digits in pairs from right
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted = ",".join(groups) + "," + last_three

    if paise > 0:
        return f"₹{formatted}.{paise:02d}"
    return f"₹{formatted}"
