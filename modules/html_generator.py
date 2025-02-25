import os
import re
import time
from pathlib import Path

import markdown
from PIL import Image, ImageOps
from googletrans import Translator

from modules.logging_colors import logger
from modules.utils import get_available_chat_styles

# This is to store the paths to the thumbnails of the profile pictures
image_cache = {}

with open(Path(__file__).resolve().parent / '../css/html_readable_style.css', 'r') as f:
    readable_css = f.read()
with open(Path(__file__).resolve().parent / '../css/html_4chan_style.css', 'r') as css_f:
    _4chan_css = css_f.read()
with open(Path(__file__).resolve().parent / '../css/html_instruct_style.css', 'r') as f:
    instruct_css = f.read()

# Custom chat styles
chat_styles = {}
for k in get_available_chat_styles():
    chat_styles[k] = open(Path(f'css/chat_style-{k}.css'), 'r').read()


def fix_newlines(string):
    string = string.replace('\n', '\n\n')
    string = re.sub(r"\n{3,}", "\n\n", string)
    string = string.strip()
    return string


def replace_blockquote(m):
    return m.group().replace('\n', '\n> ').replace('\\begin{blockquote}', '').replace('\\end{blockquote}', '')

def translate_to_turkish(string):
  translator = Translator()
  # if translator.detect(string).lang == 'tr':
  #     return string
  
  translated_text = translator.translate(string, src='en', dest='tr')
  return translated_text.text

def convert_to_markdown(string):
    
    # Blockquote
    pattern = re.compile(r'\\begin{blockquote}(.*?)\\end{blockquote}', re.DOTALL)
    string = pattern.sub(replace_blockquote, string)

    # Code
    string = string.replace('\\begin{code}', '```')
    string = string.replace('\\end{code}', '```')
    string = re.sub(r"(.)```", r"\1\n```", string)

    result = ''
    is_code = False
    for line in string.split('\n'):
        if line.lstrip(' ').startswith('```'):
            is_code = not is_code

        result += line
        if is_code or line.startswith('|'):  # Don't add an extra \n for tables or code
            result += '\n'
        else:
            result += '\n\n'

    if is_code:
        result = result + '```'  # Unfinished code block

    result = result.strip()

    # Unfinished list, like "\n1.". A |delete| string is added and then
    # removed to force a <ol> to be generated instead of a <p>.
    if re.search(r'(\d+\.?)$', result):
        delete_str = '|delete|'

        if not result.endswith('.'):
            result += '.'

        result = re.sub(r'(\d+\.)$', r'\g<1> ' + delete_str, result)

        html = markdown.markdown(result, extensions=['fenced_code', 'tables'])
        pos = html.rfind(delete_str)
        if pos > -1:
            html = html[:pos] + html[pos + len(delete_str):]
    else:
        html = markdown.markdown(result, extensions=['fenced_code', 'tables'])

    return html

def convert_to_markdown2(string):
    
    string = translate_to_turkish(string)
    # Blockquote
    pattern = re.compile(r'\\begin{blockquote}(.*?)\\end{blockquote}', re.DOTALL)
    string = pattern.sub(replace_blockquote, string)

    # Code
    string = string.replace('\\begin{code}', '```')
    string = string.replace('\\end{code}', '```')
    string = re.sub(r"(.)```", r"\1\n```", string)

    result = ''
    is_code = False
    for line in string.split('\n'):
        if line.lstrip(' ').startswith('```'):
            is_code = not is_code

        result += line
        if is_code or line.startswith('|'):  # Don't add an extra \n for tables or code
            result += '\n'
        else:
            result += '\n\n'

    if is_code:
        result = result + '```'  # Unfinished code block

    result = result.strip()

    # Unfinished list, like "\n1.". A |delete| string is added and then
    # removed to force a <ol> to be generated instead of a <p>.
    if re.search(r'(\d+\.?)$', result):
        delete_str = '|delete|'

        if not result.endswith('.'):
            result += '.'

        result = re.sub(r'(\d+\.)$', r'\g<1> ' + delete_str, result)

        html = markdown.markdown(result, extensions=['fenced_code', 'tables'])
        pos = html.rfind(delete_str)
        if pos > -1:
            html = html[:pos] + html[pos + len(delete_str):]
    else:
        html = markdown.markdown(result, extensions=['fenced_code', 'tables'])

    return html

def generate_basic_html(string):
    string = convert_to_markdown(string)
    string = f'<style>{readable_css}</style><div class="container">{string}</div>'
    return string


def process_post(post, c):
    t = post.split('\n')
    number = t[0].split(' ')[1]
    if len(t) > 1:
        src = '\n'.join(t[1:])
    else:
        src = ''
    src = re.sub('>', '&gt;', src)
    src = re.sub('(&gt;&gt;[0-9]*)', '<span class="quote">\\1</span>', src)
    src = re.sub('\n', '<br>\n', src)
    src = f'<blockquote class="message_4chan">{src}\n'
    src = f'<span class="name">Anonymous </span> <span class="number">No.{number}</span>\n{src}'
    return src


def generate_4chan_html(f):
    posts = []
    post = ''
    c = -2
    for line in f.splitlines():
        line += "\n"
        if line == '-----\n':
            continue
        elif line.startswith('--- '):
            c += 1
            if post != '':
                src = process_post(post, c)
                posts.append(src)
            post = line
        else:
            post += line

    if post != '':
        src = process_post(post, c)
        posts.append(src)

    for i in range(len(posts)):
        if i == 0:
            posts[i] = f'<div class="op">{posts[i]}</div>\n'
        else:
            posts[i] = f'<div class="reply">{posts[i]}</div>\n'

    output = ''
    output += f'<style>{_4chan_css}</style><div id="parent"><div id="container">'
    for post in posts:
        output += post

    output += '</div></div>'
    output = output.split('\n')
    for i in range(len(output)):
        output[i] = re.sub(r'^(&gt;(.*?)(<br>|</div>))', r'<span class="greentext">\1</span>', output[i])
        output[i] = re.sub(r'^<blockquote class="message_4chan">(&gt;(.*?)(<br>|</div>))', r'<blockquote class="message_4chan"><span class="greentext">\1</span>', output[i])

    output = '\n'.join(output)
    return output


def make_thumbnail(image):
    image = image.resize((350, round(image.size[1] / image.size[0] * 350)), Image.Resampling.LANCZOS)
    if image.size[1] > 470:
        image = ImageOps.fit(image, (350, 470), Image.LANCZOS)

    return image


def get_image_cache(path):
    cache_folder = Path("cache")
    if not cache_folder.exists():
        cache_folder.mkdir()

    mtime = os.stat(path).st_mtime
    if (path in image_cache and mtime != image_cache[path][0]) or (path not in image_cache):
        img = make_thumbnail(Image.open(path))

        old_p = Path(f'cache/{path.name}_cache.png')
        p = Path(f'cache/cache_{path.name}.png')
        if old_p.exists():
            old_p.rename(p)

        output_file = p
        img.convert('RGB').save(output_file, format='PNG')
        image_cache[path] = [mtime, output_file.as_posix()]

    return image_cache[path][1]


def generate_instruct_html(history):
    output = f'<style>{instruct_css}</style><div class="chat pretty_scrollbar" id="chat"><div class="messages">'
    for i, _row in enumerate(history):
        row = [convert_to_markdown(entry) for entry in _row]

        if row[0]:  # don't display empty user messages
            output += f"""
                  <div class="user-message">
                    <div class="text">
                      <div class="message-body">
                        {row[0]}
                      </div>
                    </div>
                  </div>
                """

        output += f"""
              <div class="assistant-message">
                <div class="text">
                  <div class="message-body">
                    {row[1]}
                  </div>
                </div>
              </div>
            """

    output += "</div></div>"

    return output

def generate_instruct_html2(history):
    output = f'<style>{instruct_css}</style><div class="chat pretty_scrollbar" id="chat"><div class="messages">'
    for i, _row in enumerate(history):
        row = [convert_to_markdown2(entry) for entry in _row]

        if row[0]:  # don't display empty user messages
            output += f"""
                  <div class="user-message">
                    <div class="text">
                      <div class="message-body">
                        {row[0]}
                      </div>
                    </div>
                  </div>
                """

        output += f"""
              <div class="assistant-message">
                <div class="text">
                  <div class="message-body">
                    {row[1]}
                  </div>
                </div>
              </div>
            """

    output += "</div></div>"

    return output


def generate_cai_chat_html(history, name1, name2, style, reset_cache=False):
    output = f'<style>{chat_styles[style]}</style><div class="chat pretty_scrollbar" id="chat"><div class="messages">'

    # We use ?name2 and ?time.time() to force the browser to reset caches
    img_bot = f'<img src="file/cache/pfp_character.png?{name2}">' if Path("cache/pfp_character.png").exists() else ''
    img_me = f'<img src="file/cache/pfp_me.png?{time.time() if reset_cache else ""}">' if Path("cache/pfp_me.png").exists() else ''

    for i, _row in enumerate(history):
        row = [convert_to_markdown(entry) for entry in _row]

        if row[0]:  # don't display empty user messages
            output += f"""
                  <div class="message">
                    <div class="circle-you">
                      {img_me}
                    </div>
                    <div class="text">
                      <div class="username">
                        {name1}
                      </div>
                      <div class="message-body">
                        {row[0]}
                      </div>
                    </div>
                  </div>
                """

        output += f"""
              <div class="message">
                <div class="circle-bot">
                  {img_bot}
                </div>
                <div class="text">
                  <div class="username">
                    {name2}
                  </div>
                  <div class="message-body">
                    {row[1]}
                  </div>
                </div>
              </div>
            """

    output += "</div></div>"
    return output


def generate_chat_html(history, name1, name2, reset_cache=False):
    output = f'<style>{chat_styles["wpp"]}</style><div class="chat pretty_scrollbar" id="chat"><div class="messages">'

    for i, _row in enumerate(history):
        row = [convert_to_markdown(entry) for entry in _row]

        if row[0]:  # don't display empty user messages
            output += f"""
              <div class="message">
                <div class="text-you">
                  <div class="message-body">
                    {row[0]}
                  </div>
                </div>
              </div>
            """

        output += f"""
          <div class="message">
            <div class="text-bot">
              <div class="message-body">
                {row[1]}
              </div>
            </div>
          </div>
        """

    output += "</div></div>"
    return output


def chat_html_wrapper(history, name1, name2, mode, style, reset_cache=False):
    if mode == 'instruct':
        return generate_instruct_html(history['visible'])
    elif style == 'wpp':
        return generate_chat_html(history['visible'], name1, name2)
    else:
        return generate_cai_chat_html(history['visible'], name1, name2, style, reset_cache)
    
def chat_html_wrapper2(history, name1, name2, mode, style, reset_cache=False):
    if mode == 'instruct':
        return generate_instruct_html2(history['visible'])
    elif style == 'wpp':
        return generate_chat_html(history['visible'], name1, name2)
    else:
        return generate_cai_chat_html(history['visible'], name1, name2, style, reset_cache)