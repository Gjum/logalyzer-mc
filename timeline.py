import cairo
import timeutils

"""
/-----border------\
| |||||scale||||| |
| ||line_border|| |
| ----uptimes---- |
| ||line_border|| |
| /-name_border-\ |
| | NAME ====== | |
| \-name_border-/ |
|   line_border   |
| (===)    (====) |
|   line_border   |
| (==========)    |
| ||line_border|| |
|---title_border--|
|     [TITLE]     |
\-----border-----/
"""

def color_from_uuid(uuid, settings):
    return settings['color_'+uuid[4]]

default_settings = {
    'font_name': 'sans',
    'bg_color': [0, 0, 0, 0.0],
    'border': 10,
    'line_border': 10,

    'title_border': 15,
    'title_height': 30,
    'title_color': [0, 0, 0],
    'title_shadow_color': [0, 0, 0, 0.0],
    'title_shadow_offset': [2.2, 2.2],

    'scale_line_width': 2,
    'scale_line_width_noon': 4,
    'scale_line_width_midnight': 7,
    'scale_gap': 40,
    'scale_height': 15,
    'scale_color': [0, 0, 0],
    'scale_shadow_color': [0, 0, 0, 0.0],
    'scale_shadow_offset': [1.8, 1.8],

    'name_radius': 5,
    'name_border': 5,
    'name_height': 20,
    'name_color': [1, 1, 1],
    'name_shadow_color': [0, 0, 0, 0.5],
    'name_shadow_offset': [1.8, 1.8],

    'uptimes_height': 10,
    'uptimes_color': [0, 1, 0],

    'color_0': [0.0, 0.0, 0.0],
    'color_1': [0.0, 0.0, 0.7],
    'color_2': [0.0, 0.7, 0.0],
    'color_3': [0.0, 0.7, 0.7],
    'color_4': [0.7, 0.0, 0.0],
    'color_5': [0.7, 0.0, 0.7],
    'color_6': [1.0, 0.7, 0.0],
    'color_7': [0.7, 0.7, 0.7],
    'color_8': [0.3, 0.3, 0.3],
    'color_9': [0.3, 0.3, 1.0],
    'color_a': [0.3, 1.0, 0.3],
    'color_b': [0.3, 1.0, 1.0],
    'color_c': [1.0, 0.3, 0.3],
    'color_d': [1.0, 0.3, 1.0],
    'color_e': [1.0, 1.0, 0.3],
    'color_f': [1.0, 1.0, 1.0],

    'color_from_uuid': color_from_uuid,
}

def color_from_char(color_char, settings):
    color = settings.get('color_'+color_char, [0,0,0])
    return color

# Thanks Phlip! http://stackoverflow.com/a/18792190
class SettingsDict(dict):
    def __init__(self, **kwargs):
        super(SettingsDict, self).__init__(**kwargs)
        self.__dict__ = self

LEFT = 'left'
CENTER = 'center'
RIGHT = 'right'

def draw_text(c, text, color, x_left, y_center, align=LEFT, max_w=None, shadow=None):
    """
    :param c: cairo drawing context
    :param text: the text to draw
    :param color: list or tuple with RGB or RGBA colors, floats from 0.0 to 1.0
    :param x_left: left end of text space
    :param y_center: vertical center of text space
    :param align: 'left', 'center', 'right'
    :param max_w: maximum width the text might use, set this to 0 for center/right alignment starting from x_left
    :param shadow: tuple of (color, (offset_x, offset_y))
    """
    x_bearing, y_bearing, text_width, text_height, x_advance, y_advance = c.text_extents(text)
    if max_w is not None and max_w < text_width:
        return  # do not draw, too little space
    if not max_w:  # set for centering/right aligning
        max_w = 0
    x = x_left - x_bearing
    y = y_center - y_bearing - text_height/2
    if align == CENTER:
        x += (max_w - text_width) / 2
    elif align == RIGHT:
        x += max_w - text_width
    if shadow:
        s_color, s_offset = shadow
        s_dx, s_dy = s_offset
        c.move_to(x + s_dx, y + s_dy)
        c.set_source_rgba(*s_color)
        c.show_text(text)
    c.move_to(x, y)
    c.set_source_rgba(*color)
    c.show_text(text)
    return text_width

def draw_rounded_rect(c, color, x, y, w, h, radius=0, border=None):
    def rect(radius=0):
        if radius == 0:
            c.rectangle(x, y, w, h)
        else:
            radius = min(radius, w / 2, h / 2)
            degrees = 3.1416 * 2 / 360
            c.new_sub_path()
            c.arc(x + w - radius, y + radius, radius, -90 * degrees, 0 * degrees)
            c.arc(x + w - radius, y + h - radius, radius, 0 * degrees, 90 * degrees)
            c.arc(x + radius, y + h - radius, radius, 90 * degrees, 180 * degrees)
            c.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
            c.close_path()
    c.set_source_rgba(*color)
    rect(radius)
    c.fill()
    if border:
        border_w, *border_color = border
        c.set_line_width(border_w)
        c.set_source_rgba(*border_color)
        rect(radius)
        c.stroke()

def draw_timeline(draw_data, img_path, title='', im_width=None, settings=default_settings, **kwargs):
    for key in kwargs:
        settings[key] = kwargs[key]
    s = SettingsDict(**settings)

    t_start, t_end, lines, uptimes = draw_data
    if not im_width:
        im_width = int((t_end - t_start) / 3600 * s.scale_gap)  # TODO

    # calculate sizes
    title_box_height = s.title_height + s.title_border \
        if len(title) > 0 and s.title_height > 0 else 0
    scale_box_height = s.scale_height + 2 * s.line_border \
        if s.scale_height > 0 else 0
    line_height = 2 * s.name_border + s.name_height
    line_box_height = s.line_border + line_height
    im_height = 2 * s.border \
                + title_box_height + scale_box_height + s.uptimes_height + s.line_border \
                + line_box_height * (len(lines) - 1) + line_height
    inner_width = im_width - 2 * s.border
    h_stretch = inner_width / (t_end - t_start)
    s.name_radius = min(s.name_radius, s.name_height / 2 + s.name_border)
    name_horiz_border = max(s.name_border, s.name_radius)

    # start drawing
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, im_width, im_height)
    c = cairo.Context(surface)
    c.select_font_face(s.font_name)
    c.set_source_rgba(*s.bg_color)
    c.paint()

    # draw title
    c.set_font_size(s.title_height)
    draw_text(c, title, s.title_color, s.border, im_height - (s.border + s.title_height / 2), CENTER,
              im_width - s.border, shadow=(s.title_shadow_color, s.title_shadow_offset))

    # draw scale
    c.set_source_rgba(*s.scale_color)
    c.set_line_width(s.scale_line_width)
    c.set_font_size(s.scale_height)
    scale_line_y = s.border + s.scale_height
    scale_line_dy = line_box_height * len(lines) + s.line_border * 2 + s.uptimes_height
    for sec in range((t_start // 3600) * 3600, t_end + 3600, 3600):
        if sec < t_start or sec > t_end:
            continue  # out of range by rounding
        hour_text = timeutils.epoch_to_date_str(sec, '%k')  # hour 0-23, space padded
        if hour_text == ' 0': c.set_line_width(s.scale_line_width_midnight)
        elif hour_text == '12': c.set_line_width(s.scale_line_width_noon)
        scale_line_x = int(s.border + (sec - t_start) * h_stretch) - c.get_line_width() / 2
        c.move_to(scale_line_x, scale_line_y)
        c.rel_line_to(0, scale_line_dy)
        c.stroke()
        if hour_text in (' 0', '12'): c.set_line_width(s.scale_line_width)
        # TODO rotate by 90 degrees
        draw_text(c, hour_text, s.scale_color, scale_line_x, s.border + s.scale_height / 2,
                  CENTER, None, shadow=(s.scale_shadow_color, s.scale_shadow_offset))

    # TODO draw uptimes
    for uptime in uptimes:
        pass
    c.set_source_rgba(0, 0, 0)
    c.set_line_width(s.uptimes_height)
    c.move_to(s.border, scale_box_height + s.uptimes_height / 2)
    c.line_to(im_width - s.border, scale_box_height + s.uptimes_height / 2)
    c.stroke()
    
    c.set_source_rgba(*s.uptimes_color)
    c.set_line_width(s.uptimes_height / 2)
    c.move_to(s.border, scale_box_height + s.uptimes_height / 2)
    c.line_to(im_width - s.border, scale_box_height + s.uptimes_height / 2)
    c.stroke()

    # draw sessions
    y_offset = s.border + scale_box_height + s.uptimes_height
    c.set_font_size(s.name_height)
    for i, line in enumerate(lines):
        y = i * line_box_height + y_offset
        for session in line:
            uuid, t_from, t_to, name = session
            color = s.color_from_uuid(uuid, settings)
            x = s.border + (t_from - t_start) * h_stretch
            w = (t_to - t_from) * h_stretch
            draw_rounded_rect(c, color, x, y, w, line_height, s.name_radius)
            t_x = x + name_horiz_border
            t_y = y + s.name_border + s.name_height / 2
            draw_text(c, name, s.name_color, t_x, t_y, max_w=w - 2 * name_horiz_border,
                      shadow=(s.name_shadow_color, s.name_shadow_offset))

    # save image
    surface.write_to_png(img_path)

def get_draw_data(logs, from_date=None, to_date=None):
    lines = list(logs.collect_user_sessions(from_date, to_date).values())
    uptimes = logs.collect_uptimes(from_date, to_date)
    t_start = timeutils.date_str_to_epoch(from_date) \
              or min(s[1] for sessions in lines for s in sessions)
    t_end = timeutils.date_str_to_epoch(to_date) \
            or max(s[2] for sessions in lines for s in sessions)
    return t_start, t_end, lines, uptimes


if __name__ == '__main__':
    import logalyzer
    logs = logalyzer.LogDirectory('test_logs/')
    draw_data = get_draw_data(logs, None, '2015-01-04 21:00:00')
    draw_timeline(draw_data, 'test.png', 'Title! Yey!')