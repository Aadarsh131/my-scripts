import os
import re
from pytube import Playlist, YouTube

def download_playlist(playlist_url):
    playlist = Playlist(playlist_url)
    playlist_name = re.sub(r'\W+', '-', playlist.title)

    if not os.path.exists(playlist_name):
        os.mkdir(playlist_name)

    for index, video in enumerate(playlist.videos, start=1):
        print(f"\nProcessing video {index}: {video.title}")
        yt = YouTube(video.watch_url, use_oauth=True)

        # Get all available combined streams (video + audio)
        combined_streams = yt.streams.filter(progressive=True).order_by('resolution').desc()
        if combined_streams:
            print("\nAvailable resolutions with combined streams:")
            for i, stream in enumerate(combined_streams, start=1):
                print(f"{i}. {stream.resolution}")
        else:
            print("\nNo combined streams available for this video.")

        # Prompt user for resolution choice
        resolution_choice = input(
            "Enter the resolution to download (e.g., 720p), or type 'separate' to use separate video and audio streams: "
        )

        # Check if the chosen resolution is available as a combined stream
        selected_stream = combined_streams.filter(res=resolution_choice).first() if resolution_choice != "separate" else None

        # Generate unique filenames
        video_filename = f"{index}. {yt.title.replace(' ', '_')}.mp4"
        video_path = os.path.join(playlist_name, video_filename)

        if os.path.exists(video_path):
            print(f"{video_filename} already exists, skipping download.")
            continue

        if selected_stream:
            print(f"Downloading {video_filename} in {resolution_choice}.")
            selected_stream.download(output_path=playlist_name, filename=video_filename)
        else:
            print("Downloading separate video and audio streams.")
            video_stream = yt.streams.filter(res=resolution_choice, only_video=True).first() or yt.streams.get_highest_resolution()
            audio_stream = yt.streams.get_audio_only()

            if not video_stream or not audio_stream:
                print("Error: Unable to fetch video or audio streams. Skipping video.")
                continue

            # Temporary filenames based on original stream filenames
            temp_video_filename = f"{video_stream.default_filename.replace(' ', '_')}.mp4"
            temp_audio_filename = f"{audio_stream.default_filename.replace(' ', '_')}.mp4"

            # Download temporary files
            video_stream.download(filename=temp_video_filename)
            audio_stream.download(filename=temp_audio_filename)

            # Merge video and audio using ffmpeg
            os.system(
                f"ffmpeg -y -i \"{temp_video_filename}\" -i \"{temp_audio_filename}\" -c:v copy -c:a aac \"{video_path}\" -loglevel quiet -stats"
            )

            # Clean up temporary files
            os.remove(temp_video_filename)
            os.remove(temp_audio_filename)

        print("----------------------------------")


if __name__ == "__main__":
    playlist_url = input("Enter the playlist URL: ")
    download_playlist(playlist_url)
