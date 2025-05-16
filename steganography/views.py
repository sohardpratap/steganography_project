from django.shortcuts import render,HttpResponse
from PIL import Image
import io

# Home view
def home(request):
    return render(request, 'home.html')

# Encryption view
def encrypt(request):
    if request.method == 'POST' and request.FILES['file'] and request.POST['message']:
        image_file = request.FILES['file']
        message = request.POST['message']
        
        # Open the image
        image = Image.open(image_file)
        encoded_image = encode_message_in_image(image, message)

        # Save the encoded image to a byte stream
        byte_stream = io.BytesIO()
        encoded_image.save(byte_stream, format='PNG')
        byte_stream.seek(0)

        # Return the modified image as a response
        response = HttpResponse(byte_stream, content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename="encoded_image.png"'
        return response

    return render(request, 'encrypt.html')

# Decryption view
def decrypt(request):
    if request.method == 'POST' and request.FILES['file']:
        image_file = request.FILES['file']

        # Open the image
        image = Image.open(image_file)
        hidden_message = decode_message_from_image(image)

        return render(request, 'decrypt.html', {'message': hidden_message})

    return render(request, 'decrypt.html')


# Helper function to encode a message in an image
def encode_message_in_image(image, message):
    encoded = image.copy()
    width, height = image.size
    message += '###'  # End of message delimiter

    # Convert message to binary
    binary_message = ''.join([format(ord(char), '08b') for char in message])
    
    # Make sure the image has enough space to hold the message
    if len(binary_message) > width * height * 3:
        raise ValueError("Message is too large for the image.")

    binary_index = 0
    pixels = list(encoded.getdata())

    for i in range(len(pixels)):
        pixel = list(pixels[i])

        for j in range(3):  # Loop through RGB channels
            if binary_index < len(binary_message):
                pixel[j] = pixel[j] & ~1 | int(binary_message[binary_index])
                binary_index += 1

        pixels[i] = tuple(pixel)

    encoded.putdata(pixels)
    return encoded


# Helper function to decode a message from an image
def decode_message_from_image(image):
    binary_message = ''
    pixels = list(image.getdata())

    for pixel in pixels:
        for color_value in pixel[:3]:  # Check RGB channels
            binary_message += str(color_value & 1)

    # Convert binary message back to a string
    message = ''.join([chr(int(binary_message[i:i+8], 2)) for i in range(0, len(binary_message), 8)])

    # Look for end of message delimiter '###'
    end_index = message.find('###')
    if end_index != -1:
        return message[:end_index]
    else:
        return "No hidden message found."
    
def learn(request):
    return render(request, 'learn.html')

