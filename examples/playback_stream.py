from bridge.eeg.file import FileDevice


def playback_session() -> None:
    # Ścieżka do pliku utworzonego przez poprzedni skrypt
    file_path = "recordings/my_brain_data.npz"

    try:
        # 1. Inicjalizujemy emulator pliku (sfreq=250 to standard dla BrainAccess)
        device = FileDevice(file_path=file_path, sfreq=250.0)

        print(f"Otwieranie pliku: {file_path}")

        # 2. Łączymy się (wczytanie danych do pamięci)
        with device:
            info = device.get_device_data()
            print(f"Symulacja urządzenia: {info.manufacturer} (Źródło: {info.name})")

            print("Rozpoczynam odtwarzanie strumienia...")

            # 3. Ta pętla działa identycznie jak przy prawdziwym czepku
            # FileDevice sam zadba o odpowiednie odstępy czasowe (timing), żeby symulować 250Hz.
            for i, chunk in enumerate(device.stream()):
                avg_signal = chunk.mean()
                print(f"Ramka {i:03} | Średnie napięcie: {avg_signal:.2f} uV")

    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {file_path}. Najpierw uruchom record_stream.py")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")


if __name__ == "__main__":
    playback_session()
