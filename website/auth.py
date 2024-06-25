import os
import base64
from flask import Blueprint, render_template, request, session, flash
from .structure_view import main1, check_syntax
from .detail_view import main2
from PIL import Image, ImageEnhance
from .SQL_parsing_module import sql_to_dict

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


def add_cte_table(dict_of_cte_table, query, query_num):
    new_dict = dict_of_cte_table
    query = query.replace('\n', ' ').replace(', ', ',').replace(',', ', ')
    i = 0
    parsed = query.split()
    while i < len(parsed):
        if parsed[i].upper() == 'CREATE':
            create_table_str = ''
            while parsed[i].upper() != 'TABLE':
                i += 1
            i += 1
            while parsed[i].upper() != 'AS':
                if parsed[i][-1] == ',':
                    create_table_str += parsed[i] + '\n'
                else:
                    create_table_str += parsed[i]
                i += 1
            dict_of_cte_table[create_table_str] = query_num
        i += 1

    return new_dict

@auth.route('/SQLViz', methods=['GET', 'POST'])
def SQLViz():
    dict_of_images = {}  # Initialize dict_of_images here
    query_input = ''

    if request.method == 'POST':
        query_input = request.form.get('query', '')
        query_dict = sql_to_dict(query_input)  # Parse multiple queries
        dict_of_table_created = {}

        if query_dict:
            for query_num, query in query_dict.items():
                #if check_syntax(query, 0):
                #    flash(f"SQL Syntax Error in Query {query_num}:", "error")
                #    continue
                dict_of_table_created = add_cte_table(dict_of_table_created, query, query_num)

                # Generate the visualization
                image_path1 = main1(query, dict_of_table_created)
                image_path2 = main2(query, dict_of_table_created)
                
                if image_path1 and os.path.exists(image_path1) and image_path2 and os.path.exists(image_path2):
                    # Process and encode images
                    modified_image_path1 = remove_background(image_path1)
                    modified_image_path2 = remove_background(image_path2)
                    
                    modified_image_path1 = enhance_image(modified_image_path1)
                    modified_image_path2 = enhance_image(modified_image_path2)

                    with open(modified_image_path1, 'rb') as image_file:
                        img_data1 = base64.b64encode(image_file.read()).decode('utf-8')
                    with open(modified_image_path2, 'rb') as image_file:
                        img_data2 = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    # Store encoded images in dict_of_images
                    dict_of_images[query_num] = {
                        'tables_view': img_data1,
                        'query_view': img_data2
                    }
                    
                    # Remove temporary files
                    os.remove(image_path1)
                    os.remove(image_path2)
                    os.remove(modified_image_path1)
                    os.remove(modified_image_path2)
                else:
                    flash(f"Failed to generate visualization for Query {query_num}", "error")
        print(dict_of_table_created)

    return render_template("SQLViz.html", query=query_input, dict_of_images=dict_of_images)
