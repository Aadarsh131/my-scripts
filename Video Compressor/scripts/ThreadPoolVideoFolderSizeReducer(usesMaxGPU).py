import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import shutil  # Import shutil for file copying

# Use NVIDIA NVENC for GPU compression (H.264 encoder)
algo = 'h264_nvenc'  # NVIDIA H.264 encoder for efficient compression
res = 'scale=-1:720'  # Use NVIDIA Performance Primitives (NPP) for scaling on the GPU
cq = 45  # Constant Quantization level (lower is higher quality)
fps = 15

def compress_video(input_path, output_path):
    # Check if the input file exists
    if not os.path.exists(input_path):
        print(f"Input file '{input_path}' not found.")
        return

    # Run ffmpeg command for video compression using GPU
    command = [
        'ffmpeg',
        '-y',  # Overwrite output files
        '-hwaccel', 'cuda',  # Use CUDA for hardware acceleration
        '-hwaccel_device', '0',  # Use GPU 0 for acceleration
        '-i', input_path,
        '-c:v', algo,  # Use NVIDIA GPU for encoding (H.264 NVENC)
        '-vf', res,  # Video filter (scale using GPU with NPP)
        '-r', str(fps),  # Frame rate
        '-cq', str(cq),  # Constant Quantization for NVENC (H.264)
        #'-preset', 'llhq',  # Low Latency High Quality preset for faster encoding
        '-gpu', '0',  # Use GPU 0 or all GPUs if applicable
        #'-rc', 'constqp',  # Rate control mode to use constant QP for more load on GPU
        #'-surfaces', '32',  # Increase the number of encoding surfaces to 32
        #'-bf', '0',  # Disable B-frames to reduce CPU usage and increase GPU throughput
        '-c:a', 'copy',  # Copy audio stream without re-encoding
        output_path
    ]

    subprocess.run(command)

def copy_file(input_path, output_path):
    # Copy the non-video file to the output directory
    print(f"Copying '{input_path}' to '{output_path}'")
    shutil.copy2(input_path, output_path)

def compress_videos_in_folder(input_folder, max_workers=4):
    # Check if the input folder exists
    if not os.path.exists(input_folder):
        print(f"Input folder '{input_folder}' not found.")
        return

    # Create output folder with a name starting with "(compressed)"
    resolution = res.split(":")[1]
    output_folder = os.path.join(os.path.dirname(input_folder), f"(compressed_{algo},cq{cq},{resolution}p,{fps}fps)" + os.path.basename(os.path.normpath(input_folder)))
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Prepare a list of files to compress or copy
    files_to_process = []
    for file_name in os.listdir(input_folder):
        input_path = os.path.join(input_folder, file_name)
        output_path = os.path.join(output_folder, file_name)
        
        # If the file is a video, compress it
        if file_name.endswith(('.mp4', '.avi', '.mkv', '.mov')):
            output_video_path = os.path.join(output_folder, f"compressed_{os.path.splitext(file_name)[0]}.mp4")
            if not os.path.exists(output_video_path):
                files_to_process.append((compress_video, input_path, output_video_path))
        # If it's not a video, copy it
        else:
            if not os.path.exists(output_path):
                files_to_process.append((copy_file, input_path, output_path))

    # Process files in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for func, input_path, output_path in files_to_process:
            executor.submit(func, input_path, output_path)

if __name__ == "__main__":
    # Specify the input folder
    input_folder = 'path/to/folder'

    # Compress videos in the input folder with parallel processing
    compress_videos_in_folder(input_folder, max_workers=8)  # Adjust max_workers to control parallelism
