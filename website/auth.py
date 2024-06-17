import os
import base64
from flask import Blueprint, render_template, request, session, flash
from .structure_view import main1, check_syntax
from .detail_view import main2
from PIL import Image, ImageEnhance

auth = Blueprint('auth', __name__)

def enhance_image(image_path):
    # Open the image
    img = Image.open(image_path)
    img = img.convert("RGBA")

    # Enhance the image (adjust brightness and contrast)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.5)  # Decrease brightness by 50%
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)   # Increase contrast by 50%

    # Save the modified image to a temporary path
    modified_image_path = "modified_" + os.path.basename(image_path)
    img.save(modified_image_path, "PNG")

    return modified_image_path

def remove_background(image_path):
    # Open the image
    img = Image.open(image_path)
    img = img.convert("RGBA")
    
    # Get the data of the image
    datas = img.getdata()
    
    # Define the background color (white in this case, you may need to adjust this)
    background_color = (255, 255, 255, 255)
    
    new_data = []
    for item in datas:
        # Change all white (also shades of whites)
        # to transparent
        if item[:3] == background_color[:3]:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    
    # Update image data
    img.putdata(new_data)
    
    # Save the modified image to a temporary path
    modified_image_path = "modified_" + os.path.basename(image_path)
    img.save(modified_image_path, "PNG")
    
    return modified_image_path

@auth.route('/SQLViz', methods=['GET', 'POST'])
def SQLViz():
    if request.method == 'POST':
        query1 = request.form.get('query', '')
        query2 = query1
        #if check_syntax(query1, 0):
         #   print('error')
         #   flash("SQL Syntax Error:", "error")
         #   return render_template("SQLViz.html")
        if query1 and query2:
            # Generate the visualization
            image_path1 = main1(query1)
            image_path2 = main2(query2)
            if image_path1 and os.path.exists(image_path1) and image_path2 and os.path.exists(image_path2):

                # Remove the background from the image
                modified_image_path1 = remove_background(image_path1)
                modified_image_path2 = remove_background(image_path2)
                
                # Enhance the content of the image
                modified_image_path1 = enhance_image(modified_image_path1)
                modified_image_path2 = enhance_image(modified_image_path2)

                # Encode the modified image to base64
                with open(modified_image_path1, 'rb') as image_file:
                    img_data1 = base64.b64encode(image_file.read()).decode('utf-8')
                with open(modified_image_path2, 'rb') as image_file:
                    img_data2 = base64.b64encode(image_file.read()).decode('utf-8')
                
                # Remove the original and modified image files after encoding
                os.remove(image_path1)
                os.remove(image_path2)
                os.remove(modified_image_path1)
                os.remove(modified_image_path2)
                return render_template("SQLViz.html", query = query1, encoded_image1=img_data1, encoded_image2=img_data2)
    
    return render_template("SQLViz.html")
