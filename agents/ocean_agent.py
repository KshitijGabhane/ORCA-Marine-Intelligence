from typing import Dict, Any


class OceanAgent:

    def __init__(self):
        self.agent_name = "Ocean Agent"
        self.source = "INCOIS"

    def calculate_risk(
        self,
        wave_height_m=None,
        swell_height_m=None,
        swell_period_s=None,
        current_speed_ms=None
    ):

        score = 0
        reasons = []

        # Significant wave height
        if wave_height_m is not None:

            if wave_height_m >= 4:
                score += 4
                reasons.append(
                    "Very high significant wave height"
                )

            elif wave_height_m >= 3:
                score += 3
                reasons.append(
                    "High significant wave height"
                )

            elif wave_height_m >= 2:
                score += 2
                reasons.append(
                    "Moderate to high waves"
                )

            elif wave_height_m >= 1.5:
                score += 1
                reasons.append(
                    "Moderate waves"
                )

        # Swell
        if swell_height_m is not None:

            if swell_height_m >= 3:
                score += 3
                reasons.append(
                    "High swell"
                )

            elif swell_height_m >= 2:
                score += 2
                reasons.append(
                    "Moderate to high swell"
                )

        # Long-period swell / Kallakkadal indicator
        if (
            swell_period_s is not None
            and swell_height_m is not None
        ):

            if (
                swell_period_s >= 15
                and swell_height_m >= 2
            ):
                score += 3

                reasons.append(
                    "Long-period high-energy swell detected"
                )

        # Ocean current
        if current_speed_ms is not None:

            if current_speed_ms >= 2:
                score += 3
                reasons.append(
                    "Very strong surface current"
                )

            elif current_speed_ms >= 1:
                score += 1
                reasons.append(
                    "Strong surface current"
                )

        # Final risk
        if score >= 7:
            risk = "CRITICAL"

        elif score >= 5:
            risk = "HIGH"

        elif score >= 3:
            risk = "MEDIUM"

        else:
            risk = "LOW"

        return {
            "risk": risk,
            "score": score,
            "reasons": reasons
        }

    def analyze(
        self,
        latitude,
        longitude,
        ocean_data
    ):

        risk = self.calculate_risk(
            wave_height_m=ocean_data.get(
                "significant_wave_height"
            ),
            swell_height_m=ocean_data.get(
                "swell_height"
            ),
            swell_period_s=ocean_data.get(
                "swell_period"
            ),
            current_speed_ms=ocean_data.get(
                "current_speed"
            )
        )

        return {

            "agent": self.agent_name,

            "latitude": latitude,
            "longitude": longitude,

            "source": self.source,

            "ocean": ocean_data,

            "risk": risk["risk"],

            "risk_score": risk["score"],

            "risk_reasons": risk["reasons"]
        }


ocean_agent = OceanAgent()