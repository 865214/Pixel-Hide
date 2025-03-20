import streamlit as st
import numpy as np
from io import BytesIO
from PIL import Image

try:
    from stegano.lsb import encode, decode
    USE_STEGANO = True
except ImportError:
    USE_STEGANO = False
    
def resize_image(image, max_size=(300, 200)):
    aspect_ratio = image.width / image.height
    new_width = min(max_size[0], image.width)
    new_height = int(new_width / aspect_ratio)
    return image.resize((new_width, new_height), Image.LANCZOS)

def encode_lsb(image, message):
    pixels = np.array(image.convert("RGB"))
    binary_message = ''.join(format(ord(char), '08b') for char in message) + '00000000'
    binary_index = 0

    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            for k in range(3):
                if binary_index < len(binary_message):
                    pixels[i, j, k] = (pixels[i, j, k] & ~1) | int(binary_message[binary_index])
                    binary_index += 1
                else:
                    break

    return Image.fromarray(pixels)

def decode_lsb(image):
    pixels = np.array(image.convert("RGB"))
    binary_message = ""
    
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            for k in range(3):
                binary_message += str(pixels[i, j, k] & 1)
                if binary_message[-8:] == "00000000":
                    return ''.join(chr(int(binary_message[i:i+8], 2)) for i in range(0, len(binary_message)-8, 8))

    return "No hidden message found."

def main():
    st.title("Image Steganography")
    
    option = st.radio("Choose an option:", ("Encode Text into Image", "Decode Text from Image"))
    
    if option == "Encode Text into Image":
        uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            resized_image = resize_image(image)
            st.image(resized_image, use_column_width=False)
            
            secret_message = st.text_area("Enter the secret message")
            
            if st.button("Encode Message"):
                if secret_message:
                    if USE_STEGANO:
                        encoded_image = encode(image, secret_message)  
                    else:
                        encoded_image = encode_lsb(image, secret_message)  
                    
                    buf = BytesIO()
                    encoded_image.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.success("Message encoded successfully!")
                    st.download_button(label="Download Encoded Image",
                                       data=byte_im,
                                       file_name="encoded_image.png",
                                       mime="image/png")
                else:
                    st.error("Please enter a message to encode.")
    
    elif option == "Decode Text from Image":
        uploaded_file = st.file_uploader("Upload an encoded image", type=["png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Encoded Image", use_column_width=False)
            
            if st.button("Decode Message"):
                try:
                    extracted_message = decode(image) if USE_STEGANO else decode_lsb(image)
                    if extracted_message:
                        st.success("Extracted Message: ")
                        st.write(extracted_message)
                    else:
                        st.warning("No hidden message found!")
                except Exception as e:
                    st.error(f"Error decoding the image: {e}")

if __name__ == "__main__":
    main()
