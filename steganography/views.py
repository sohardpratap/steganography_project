from django.shortcuts import render, HttpResponse
from PIL import Image, UnidentifiedImageError
import io

DELIMITER = '###'
BITS_PER_CHAR = 8

# Home view
def home(request):
    return render(request, 'home.html')

# Encryption view
def encrypt(request):
    context = {}
    if request.method == 'POST':
        image_file = request.FILES.get('file')
        message = request.POST.get('message')

        if not image_file:
            context['error'] = "Please select an image file."
            return render(request, 'encrypt.html', context)
        
        if not message:
            context['error'] = "Please enter a message to hide."
            return render(request, 'encrypt.html', context)

        try:
            image = Image.open(image_file)
            image = image.convert('RGB') # Convert to RGB before encoding
        except UnidentifiedImageError:
            context['error'] = "Invalid image file. Please select a valid image."
            return render(request, 'encrypt.html', context)
        except Exception as e:
            context['error'] = f"An error occurred while opening the image: {str(e)}"
            return render(request, 'encrypt.html', context)

        try:
            encoded_image = encode_message_in_image(image, message)
        except ValueError as e: # Specifically for "Message too large"
            context['error'] = str(e)
            return render(request, 'encrypt.html', context)
        except Exception as e: # Other unexpected errors during encoding
            context['error'] = f"An error occurred during encoding: {str(e)}"
            return render(request, 'encrypt.html', context)

        # Save the encoded image to a byte stream
        byte_stream = io.BytesIO()
        encoded_image.save(byte_stream, format='PNG')
        byte_stream.seek(0)

        # Return the modified image as a response
        response = HttpResponse(byte_stream, content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename="encoded_image.png"'
        return response

    return render(request, 'encrypt.html', context)

# Decryption view
def decrypt(request):
    context = {}
    if request.method == 'POST':
        image_file = request.FILES.get('file')

        if not image_file:
            context['error'] = "Please select an image file to decrypt."
            return render(request, 'decrypt.html', context)

        try:
            image = Image.open(image_file)
            image = image.convert('RGB') # Convert to RGB before decoding
        except UnidentifiedImageError:
            context['error'] = "Invalid image file. Please select a valid image."
            return render(request, 'decrypt.html', context)
        except Exception as e:
            context['error'] = f"An error occurred while opening the image: {str(e)}"
            return render(request, 'decrypt.html', context)

        try:
            hidden_message = decode_message_from_image(image)
            context['message'] = hidden_message
            if hidden_message == "No hidden message found or delimiter missing.": # Check specific message
                 context['warning'] = hidden_message # Use warning for non-critical "errors"
                 del context['message'] # Don't show it as a success message too
        except Exception as e:
            context['error'] = f"An error occurred during decoding: {str(e)}"
            # Potentially log e for server-side diagnosis
            return render(request, 'decrypt.html', context)


        return render(request, 'decrypt.html', context)

    return render(request, 'decrypt.html', context)


# Helper function to encode a message in an image
def encode_message_in_image(image, message):
    encoded_image = image.copy() # Operate on a copy
    width, height = encoded_image.size
    message_to_encode = message + DELIMITER

    # Convert message to binary
    binary_message = ''.join([format(ord(char), f'0{BITS_PER_CHAR}b') for char in message_to_encode])
    
    required_pixels = len(binary_message)
    available_pixels = width * height * 3 # Each pixel (RGB) can store 3 bits

    if required_pixels > available_pixels:
        raise ValueError(f"Message is too large for the image. Needs {required_pixels} bits, image has space for {available_pixels} bits.")

    binary_index = 0
    # Using putpixel for potentially better performance on some PIL versions, though getdata/putdata is also fine.
    # For simplicity and consistency with original, let's stick to getdata/putdata
    pixels_list = list(encoded_image.getdata())
    new_pixels = []

    for i in range(len(pixels_list)):
        pixel_rgb = list(pixels_list[i]) # Ensure it's a list for modification

        for j in range(3):  # Loop through RGB channels
            if binary_index < len(binary_message):
                # Modify the LSB of the color channel
                pixel_rgb[j] = (pixel_rgb[j] & ~1) | int(binary_message[binary_index])
                binary_index += 1
            # No else needed; if message is shorter, remaining bits are unchanged.
        new_pixels.append(tuple(pixel_rgb))

    encoded_image.putdata(new_pixels)
    return encoded_image


# Helper function to decode a message from an image
def decode_message_from_image(image):
    all_lsb_bits = []

    pixels = image.getdata()
    
    # Extract all LSBs from the image
    for pixel_rgb in pixels:
        for color_value in pixel_rgb[:3]: # Iterate over R, G, B components
            all_lsb_bits.append(str(color_value & 1))

    binary_payload = "".join(all_lsb_bits)
    decoded_message = ""

    # Process chunks of bits to form characters
    i = 0
    while i <= len(binary_payload) - BITS_PER_CHAR:
        char_bits = binary_payload[i : i + BITS_PER_CHAR]
        try:
            char = chr(int(char_bits, 2))
            decoded_message += char
        except ValueError:
            # This part of the image does not contain valid character data,
            # or we've hit noise after the actual message.
            # Append a placeholder to maintain position, or log.
            # This helps in cases where corruption might otherwise shift the delimiter.
            decoded_message += '?' # Placeholder for unreadable character
            # print(f"Warning: ValueError for bits {char_bits}, replaced with '?'")

        # Check for the delimiter
        # Using find() is more robust to message content than endswith() in a tight loop
        delimiter_index = decoded_message.find(DELIMITER)
        if delimiter_index != -1:
            return decoded_message[:delimiter_index]

        i += BITS_PER_CHAR

    # If loop finishes and delimiter was not found
    return "No hidden message found or delimiter missing."

def learn(request):
    return render(request, 'learn.html')

