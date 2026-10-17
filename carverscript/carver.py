import os

# Define file paths
INPUT_FILE = "/home/macaw/Documents/output/4531.ithmb"
OUTPUT_DIR = "/home/macaw/Documents/output/extracted_images"

# File signatures (Magic Bytes)
SIGNATURES = {
    'jpeg': {
        'start': b'\xff\xd8\xff',
        'end': b'\xff\xd9'
    },
    'png': {
        'start': b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a',
        'end': b'\x49\x45\x4e\x44\xae\x42\x60\x82'
    }
}

def carve_images():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    try:
        with open(INPUT_FILE, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: The file {INPUT_FILE} was not found.")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print(f"Scanning {INPUT_FILE} ({len(data)} bytes)...")

    for img_type, magic in SIGNATURES.items():
        start_bytes = magic['start']
        end_bytes = magic['end']
        
        start_idx = 0
        count = 0

        while True:
            # Find the start of the image
            start_idx = data.find(start_bytes, start_idx)
            if start_idx == -1:
                break

            # Find the corresponding end of the image
            end_idx = data.find(end_bytes, start_idx)
            if end_idx == -1:
                # If no end header is found, skip or carve to the end of the file
                start_idx += len(start_bytes)
                continue

            # Calculate actual end index including the end bytes themselves
            end_idx += len(end_bytes)

            # Extract the image data
            image_data = data[start_idx:end_idx]
            
            # Save the file
            output_filename = f"carved_{img_type}_{count}.{img_type}"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            with open(output_path, "wb") as out_file:
                out_file.write(image_data)
            
            count += 1
            # Move the index past the current image to find the next one
            start_idx = end_idx

        print(f"Extracted {count} {img_type.upper()} files.")

if __name__ == "__main__":
    carve_images()
