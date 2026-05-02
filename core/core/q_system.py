def calculate_q_prime(
    rqd: float,
    jn: float,
    jr: float,
    ja: float,
) -> float:
    """
    Calculate modified Q value for Mathews stability graph method.

    Q' = (RQD / Jn) * (Jr / Ja)

    Jw and SRF are assumed to be equal to 1.
    """
    if rqd <= 0:
        raise ValueError("RQD must be greater than zero.")
    if jn <= 0:
        raise ValueError("Jn must be greater than zero.")
    if jr <= 0:
        raise ValueError("Jr must be greater than zero.")
    if ja <= 0:
        raise ValueError("Ja must be greater than zero.")

    return (rqd / jn) * (jr / ja)

