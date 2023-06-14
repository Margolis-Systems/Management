import main
import configs
import users


def plot_edit():
    permission = users.validate_user()
    if not permission:
        return users.logout()
    elif permission < 90:
        return main.index()
    shape = '1'
    if main.request.values:
        shape = list(main.request.values)[0]
    form = dict(main.request.form)
    if form:
        shape = form['shape'].split('/')[-1].replace('.png', '')
        new_pos = []
        for item in form:
            if '_x' in item:
                new_pos.append([int(form[item]), int(form[item.replace('x', 'y')])])
        if new_pos:
            configs.shapes[shape]['positions'] = new_pos
        create_shape_plot(shape, range(1, len(new_pos)+1))
        main.mongo.update_one('data_lists', {'name': 'shapes'}, {'data': configs.shapes}, '$set')
        return main.redirect('/plot_edit?'+shape)
    shape_data = configs.shapes[shape].copy()
    shape_data['edges'] = range(shape_data['edges'])
    shape = "/static/images/shapes/" + shape + ".png"
    return main.render_template('/plot_edit.html', shape=shape, shape_data=shape_data)


def create_shape_plot(shape, data):
    import os
    from PIL import Image, ImageDraw, ImageFont
    font_size = 20
    positions = configs.shapes[shape]['positions']
    static_dir = os.path.dirname(__file__)+'\\static\\'
    img_dir = static_dir + 'images\\shapes_orig\\' + str(shape) + '.jpg'
    if os.path.exists(img_dir):
        img = Image.open(img_dir)
    else:
        img = Image.open(static_dir + 'images\\shapes\\0.png')
    draw = ImageDraw.Draw(img)
    for i in range(len(data)):
        text_box_pos = positions[i][0], positions[i][1] - 4
        bbox = draw.textbbox(text_box_pos, str(data[i]), font=ImageFont.truetype("impact.ttf", font_size + 4))
        draw.rectangle(bbox, fill="white")
        draw.text(positions[i], str(data[i]), font=ImageFont.truetype("impact.ttf", font_size), fill="black")
    file_out = img_dir.replace('_orig', '')
    img.save(file_out, quality=95)
    return file_out
