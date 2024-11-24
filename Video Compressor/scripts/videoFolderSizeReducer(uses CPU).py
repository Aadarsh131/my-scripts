import os
import subprocess

def compress_video(input_path, output_path, crf=23):
    # Check if the input file exists
    if not os.path.exists(input_path):
        print(f"Input file '{input_path}' not found.")
        return

    # Run ffmpeg command for video compression
    command = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libvpx-vp9',
        # '-c:v', 'libx265',
        # '-vf', 'scale=854:480', # Adjust the resolution as needed (854x480 for 480p)
        '-vf', 'scale=640:360', # Adjust the resolution as needed (640x360 for 360p)
        # '-vf', 'scale=1280:720',
        '-r','15', # Hardcoded fps value (15 frames per second)
        #'-b:v', '0',  # Use a constant quality mode instead of a specific bitrate
        '-crf', str(crf),
        #'-c:a', 'libvorbis',
        #'-q:a', '4',  # Set audio quality (0 to 10, 4 is a good default)
        #'-strict', 'experimental',  # Required for using libvorbis with AVI
        output_path
    ]

    subprocess.run(command)

def compress_videos_in_folder(input_folder, crf=40):
    # Check if the input folder exists
    if not os.path.exists(input_folder):
        print(f"Input folder '{input_folder}' not found.")
        return

    # Create output folder with a name starting with "(compressed)"
    output_folder = os.path.join(os.path.dirname(input_folder), "(compressed_libvpx-vp9,crf60,360p,fps15)" + os.path.basename(os.path.normpath(input_folder)))
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Loop through all files in the input folder
    for file_name in os.listdir(input_folder):
        if file_name.endswith(('.mp4', '.avi', '.mkv', '.mov')):
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, f"compressed_{os.path.splitext(file_name)[0]}.mp4")
               # Check if the compressed file already exists
            if os.path.exists(output_path):
                print(f"Skipping compression for '{input_path}' - compressed file already exists.")
            else:
                compress_video(input_path, output_path, crf)

if __name__ == "__main__":
    # Specify the input and output folders
    input_folder = 'path/to/folder'

    # Specify the Constant Rate Factor (CRF) for compression (default: 23)
    crf_value = 60

    # Compress videos in the input folder and save to the output folder
    compress_videos_in_folder(input_folder, crf_value)
