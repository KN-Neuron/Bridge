from bridge.eeg.fif import FifDevice


def playback_session_fif() -> None:
    file_path = "recordings/my_brain_data.fif"

    try:
        device = FifDevice(file_path=file_path, chunk_size=25)

        print(f"Otwieranie pliku: {file_path}")

        with device:
            info = device.get_device_data()
            print(f"Symulacja urządzenia: {info.manufacturer} (Źródło: {info.name})")
            print(f"Częstotliwość próbkowania: {info.sample_rate} Hz")

            print("Rozpoczynam odtwarzanie strumienia...")

            for i, chunk in enumerate(device.stream()):
                avg_signal = chunk.mean()
                print(f"Ramka {i:03} | Średnie napięcie: {avg_signal:.4f} uV")

    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {file_path}. Najpierw uruchom record_fif.py")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")


if __name__ == "__main__":
    playback_session_fif()
