import time

from bridge.eeg import EEGConnector
from bridge.eeg.brainaccess import get_cap_from_model
from bridge.eeg.fif import FifRecorder


def record_session_fif() -> None:
    try:
        with EEGConnector() as connector:
            device = connector._eeg_device
            if not device:
                print("Nie znaleziono urządzenia!")
                return

            print(f"Połączono z: {device.get_device_data().name}")

            cap = get_cap_from_model("MAXI")

            with FifRecorder(
                device, filename="my_brain_data.fif", cap=cap, sfreq=250.0, connect_device=False
            ) as recorder:
                print("Rozpoczynam zbieranie danych (10 sekund)...")

                start_time = time.time()
                for chunk in recorder.stream():
                    print(f"Odebrano paczkę o kształcie: {chunk.shape}")

                    if time.time() - start_time > 10:
                        break

                print("Zakończono zbieranie. Zapisywanie do .fif...")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")


if __name__ == "__main__":
    record_session_fif()
