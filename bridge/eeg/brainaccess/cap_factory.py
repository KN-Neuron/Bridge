from .typing import Cap

DEVICE_TO_CAP: dict[str, Cap] = {
    "MAXI": {
        0: "P8",
        1: "O2",
        2: "P4",
        3: "C4",
        4: "F8",
        5: "F4",
        6: "Oz",
        7: "Cz",
        8: "Fz",
        9: "Pz",
        10: "F3",
        11: "O1",
        12: "P7",
        13: "C3",
        14: "P3",
        15: "F7",
        16: "T8",
        17: "FC6",
        18: "CP6",
        19: "CP2",
        20: "PO4",
        21: "FC2",
        22: "AF4",
        23: "POz",
        24: "AFz",
        25: "AF3",
        26: "FC1",
        27: "FC5",
        28: "T7",
        29: "CP1",
        30: "CP5",
        31: "PO3",
    },
    "HALO": {0: "O1", 1: "O2", 2: "Fp2", 3: "Fp1"},
}


# IM-032
def get_cap_from_model(device_model: str) -> Cap:
    try:
        return DEVICE_TO_CAP[device_model]
    except KeyError as e:
        raise NotImplementedError(f"Model {device_model} is not implemented yet") from e


# IM-032
def get_cap_from_name(device_name: str) -> Cap | None:
    upper_device_name = device_name.upper()
    for model, cap in DEVICE_TO_CAP.items():
        if upper_device_name.__contains__(model.upper()):
            return cap

    return None
