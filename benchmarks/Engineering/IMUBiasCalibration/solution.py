"""Weak valid baseline: trust factory calibration without taking measurements."""


def infer_imu(problem, measure):
    return {
        "bias_mps2": [0.0, 0.0, 0.0],
        "temperature_drift_mps2_per_c": [0.0, 0.0, 0.0],
        "calibration_matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "prediction_accel_mps2": [[problem["gravity_mps2"]*v for v in s["orientation"]]
                                   for s in problem["prediction_settings"]],
        "diagnosis": "supported",
        "fault_axis": None,
        "confidence": 1.0,
        "abstain": False,
        "evidence_ids": [],
    }
