import os
import subprocess
import mutagen
if __name__ == "__main__":
    print("Welcome to MixMagnetizer!")
    print("This tool helps you to dub digital music onto cassette tapes. \n It can automatically divide your playlist into sections the length of your tape's side, and play them back. \n Support for Pioneer CD Synchro deck control is planned.")

# Read the playlist file
def read_playlist(playlist_file):
    with open(playlist_file, 'r') as playlist:
        tracks = [line.strip() for line in playlist.readlines() if not line.startswith('#')]
    return tracks

def calculate_sections(tracks, break_time):
    sections = []
    current_section = []
    current_length = 0

    for track in tracks:
        audio_info = subprocess.run(["soxi", "-D", track], capture_output=True, text=True)
        track_duration = float(audio_info.stdout.strip())

        if track_duration > break_time:
            raise ValueError(f"Track '{track}' duration exceeds section length.")

        if current_length + track_duration <= break_time:
            if len(current_section) > 0 and (current_length + track_duration) > break_time:
                sections.append(current_section)
                current_section = [track]
                current_length = track_duration
            else:
                current_section.append(track)
                current_length += track_duration
        else:
            sections.append(current_section)
            current_section = [track]
            current_length = track_duration

    if current_section:
        sections.append(current_section)

    return sections

# Display track information
def display_track_info(tracks):
    print("Tracks in the playlist:")
    for i, track in enumerate(tracks):
        print(f"{i + 1}. {os.path.basename(track)}")

# Create a .m3u playlist file
def create_m3u_playlist(tracks, playlist_name):
    with open(playlist_name, 'w') as playlist_file:
        for track in tracks:
            playlist_file.write(f"{track}\n")

# Input time in MM:SS format
def time_input(prompt):
    while True:
        time_str = input(prompt)
        try:
            minutes, seconds = map(int, time_str.split(':'))
            return minutes * 60 + seconds
        except ValueError:
            print("Invalid input. Please enter time in MM:SS format.")

# Generate track information report
def create_track_info_report(section, section_number):
    report_name = f"section_{section_number}_info.txt"

    with open(report_name, 'w') as report_file:
        report_file.write(f"Tape {section_number + 1}, Side {'A' if section_number % 2 == 0 else 'B'}\n\n")
        for track in section:
            audio = mutagen.File(track)
            track_name = audio.get("title", "Unknown Title")
            album_name = audio.get("album", "Unknown Album")
            artist_name = audio.get("artist", "Unknown Artist")
            for i, track in enumerate(section, start=1):
                report_file.write(f"Playlist Number: {i}\n")
            report_file.write(f"File Path: {track}\n")
            report_file.write(f"Track Name: {track_name}\n")
            report_file.write(f"Album: {album_name}\n")
            report_file.write(f"Artist: {artist_name}\n\n")
    return report_name



# Play sections using sox
def play_sections(sections):
    for i, section in enumerate(sections):
        confirm = input(f"\nAre you ready to start playback for section {i + 1}? (y/n): ")
        if confirm.lower() != 'y':
            print("Playback stopped.")
            break

        print(f"\nPlaying section {i + 1}")
        create_m3u_playlist(section, f"section_{i}.m3u")
        subprocess.run(["play", f"section_{i}.m3u"])

        if i < len(sections) - 1:
            confirm_next = input(f"\nDo you want to play the next section? (y/n): ")
            if confirm_next.lower() != 'y':
                print("Playback stopped.")
                break
            subprocess.run(["rm", f"section_{i}.m3u"])
        else:
            subprocess.run(["rm", f"section_{i}.m3u"])
            print("Playback finished for all sections.")


if __name__ == "__main__":
    # Get the playlist
    playlist_file = input("Enter the path to the playlist file: ")
    tracks = read_playlist(playlist_file)

    # Get section length
    break_time = time_input("Enter the time limit for each tape side in MM:SS format. \n You should determine this through your deck's tape counter function rather than trusting the advertised length, \n be sure to account for a few seconds of head and tail leader. \n Side length (MM:SS):")
    sections = calculate_sections(tracks, break_time)

    # Display track information
    display_track_info(tracks)

    # Generate and play sections
    play_sections(sections)

    # Generate cassette labels and J-cards
    for i, section in enumerate(sections):
        print(f"\nGenerating section {i + 1} information report")
        track_info_report = create_track_info_report(section, i)
