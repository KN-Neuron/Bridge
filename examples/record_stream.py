import time

from bridge.eeg import EEGConnector, close, init
from bridge.eeg.recorder import EEGRecorder


def record_session() -> None:
    # 1. Inicjalizacja sterowników SDK
    init()

    try:
        # 2. Używamy Connectora, aby automatycznie znalazł urządzenie
        with EEGConnector() as connector:
            device = connector._eeg_device  # Pobieramy dostęp do instancji urządzenia
            if not device:
                print("Nie znaleziono urządzenia!")
                return

            print(f"Połączono z: {device.get_device_data().name}")

            # 3. Tworzymy rekorder (automatycznie zapisze do .npz przy wyjściu z context managera)
            # Plik trafi do folderu recordings/my_brain_data.npz
            with EEGRecorder(device, filename="my_brain_data.npz") as recorder:
                print("Rozpoczynam zbieranie danych (10 sekund)...")

                start_time = time.time()
                # recorder.stream() to generator, który pod spodem wywołuje device.stream()
                for chunk in recorder.stream():
                    print(f"Odebrano paczkę o kształcie: {chunk.shape}")

                    # Przerwij po 10 sekundach
                    if time.time() - start_time > 10:
                        break

                print("Zakończono zbieranie. Zapisywanie...")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")
    finally:
        # 4. Zwolnienie zasobów SDK
        close()


if __name__ == "__main__":
    record_session()
