import os
import base64
import shutil
import tempfile
from flask import Blueprint, render_template, request, flash, current_app
from .structure_view import main1, check_syntax
from .detail_view import main2
from PIL import Image, ImageEnhance, ImageDraw
from .SQL_parsing_module import sql_to_dict

auth = Blueprint('auth', __name__)

def enhance_image(image_path):
    out_dir = os.path.dirname(image_path) or "."
    # Open the image
    img = Image.open(image_path)
    img = img.convert("RGBA")

    # Enhance the image (adjust brightness and contrast)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.5)  # Decrease brightness by 50%
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)   # Increase contrast by 50%

    modified_image_path = os.path.join(out_dir, "modified_" + os.path.basename(image_path))
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
    
    out_dir = os.path.dirname(image_path) or "."
    modified_image_path = os.path.join(out_dir, "modified_" + os.path.basename(image_path))
    img.save(modified_image_path, "PNG")

    return modified_image_path

def change_image_color(image_path, target_color):
    img = Image.open(image_path)
    img = img.convert("RGBA")
    datas = img.getdata()
    target_color = Image.new("RGBA", (1, 1), target_color).getpixel((0, 0))
    new_data = [(target_color[0], target_color[1], target_color[2], item[3]) if item[3] != 0 else item for item in datas]
    img.putdata(new_data)
    out_dir = os.path.dirname(image_path) or "."
    modified_image_path = os.path.join(out_dir, "colored_" + os.path.basename(image_path))
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
        try:
            query_dict = sql_to_dict(query_input)  # Parse multiple queries
            dict_of_table_created = {}

            if query_dict:
                for query_num, query in query_dict.items():
                    dict_of_table_created = add_cte_table(dict_of_table_created, query, query_num)

                    workdir = tempfile.mkdtemp(prefix="sqlviz_")
                    try:
                        image_path1 = main1(query, dict_of_table_created, workdir)
                        image_path2 = main2(query, dict_of_table_created, workdir)

                        if image_path1 and os.path.exists(image_path1) and image_path2 and os.path.exists(image_path2):
                            modified_image_path1 = remove_background(image_path1)
                            modified_image_path2 = remove_background(image_path2)

                            modified_image_path1 = enhance_image(modified_image_path1)
                            modified_image_path2 = enhance_image(modified_image_path2)

                            modified_image_path1 = change_image_color(modified_image_path1, "#3266c0")
                            modified_image_path2 = change_image_color(modified_image_path2, "#3266c0")

                            with open(modified_image_path1, 'rb') as image_file:
                                img_data1 = base64.b64encode(image_file.read()).decode('utf-8')
                            with open(modified_image_path2, 'rb') as image_file:
                                img_data2 = base64.b64encode(image_file.read()).decode('utf-8')

                            dict_of_images[query_num] = {
                                'tables_view': img_data1,
                                'query_view': img_data2
                            }

                            for p in (image_path1, image_path2, modified_image_path1, modified_image_path2):
                                try:
                                    if p and os.path.exists(p):
                                        os.remove(p)
                                except OSError:
                                    pass
                        else:
                            flash(f"Failed to generate visualization for Query {query_num}", "error")
                    finally:
                        shutil.rmtree(workdir, ignore_errors=True)
            print(dict_of_table_created)
        except Exception:
            current_app.logger.exception("SQLViz POST failed")
            flash(
                "Could not generate the visualization. On cloud hosts the Graphviz system tools "
                "must be installed and available as the `dot` command (Vercel’s default Python runtime "
                "does not include Graphviz).",
                "error",
            )

    return render_template("SQLViz.html", query=query_input, dict_of_images=dict_of_images)
