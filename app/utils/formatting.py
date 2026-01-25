def format_european_currency(amount):
    """Format currency in European style: 1.234,56"""
    if amount is None:
        return "0,00"
    # Convert to string with 2 decimal places
    formatted = f"{amount:,.2f}"
    # Replace comma with dot for thousands separator, and dot with comma for decimal
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted

def get_display_amount(sponsoring):
    """Get the amount to display, using fallback logic.
    Add bedrag_kaarten and netto_bedrag_excl_btw together.
    If one is not filled in, use 0 for that amount.
    """
    netto = sponsoring.netto_bedrag_excl_btw or 0
    kaarten = sponsoring.bedrag_kaarten or 0
    
    return netto + kaarten
