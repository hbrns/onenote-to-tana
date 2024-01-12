import json
import locale
import pytz
import re
import sys
import time
from bs4 import BeautifulSoup, Tag, NavigableString
from datetime import datetime
from snowflake import SnowflakeGenerator
from typing import Any, Dict, List, Tuple, Union

# TIF - Tana Intermediate Format
from tanatypes.tif import *

CHARSET = 'utf-8' 
TIMEZONE = 'Etc/GMT+1'

# Initialize a snowflake generator
uid = SnowflakeGenerator(29)

# Create supertags
# We hit each table with a special supertag so that the user
# can create a command insite Tana to post-process the table,
# e.g., change the view from list to table
supertag_tbl = TanaIntermediateSupertag(str(next(uid)), "Table (by onenote_to_tana)")

def condense_matching_tags(text: str) -> str:
    """Remove tags from a string if the same tag follows next"""
    tags = ['b', 'mark', 'i', 'strike', 'u']
    for tag in tags:
        text = re.sub(f'</{tag}>\s*<{tag}>', ' ', text)
    return text

def compress_text(text: str) -> str:
    text = text.replace('\n', ' ')
    text = ' '.join(text.split())
    text = condense_matching_tags(text)
    return text

def process_child(child: NavigableString) -> str:
    style = []
    href = None
    text = ""
    if 'style' in str(child):
        if 'bold' in str(child):
            style.append('b')
        if 'highlight' in str(child):
            style.append('mark')
        if 'italic' in str(child):
            style.append('i')
        if 'line-through' in str(child):
            style.append('strike')
        if 'underline' in str(child):
            style.append('u')
    elif 'href' in str(child):
        href = child.get('href')
        style.append('URL')
    for string in child.stripped_strings:
        if string[0] not in [',', ';']:
            text = text + ' '
        if style:
            if 'URL' in style:
                text = text + f'[{string}]({href})'
            else:
                text = text + "<{}>{}</{}>".format("><".join(style), string, "></".join(style[-1::-1]))
        else:
            text = text + f'{string}'
    return text

def process_and_convert_table(tag: NavigableString) -> Tuple[int, str, list]:
    table = []
    title = tag["title"].strip()
    if not title:
        title="OneNote Table"
    rows = tag.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        row = []
        for col in cols:
            text = str()
            for child in col.children:
                text += process_child(child)
            text = compress_text(text)
            row.append(text)
        table.append(row)
    simmer = tag.find_all(True)
    n = len(simmer) + 1
    return n, title, table

def process_and_convert_paragraph(tag: NavigableString) -> Tuple[int, str, str]:
    text = str()
    language = tag.get('lang') or 'de_DE'  # default: Deutsches Deutsch
    for child in tag.children:
        text += process_child(child)
    text = compress_text(text)
    simmer = tag.find_all(True)
    n = 1 + len(simmer)
    return n, language, f'{text}' if len(text) > 0 else ''

def process_and_convert_anchor(tag: NavigableString) -> Tuple[int, str]:
    # Link formats:
    # - external content: [See Tana](https://wwww.tana.inc)
    # - internal: [[uid]]
    # - internal with alias: [test page]([[uid]])
    href = tag.get('href')
    return 1, f'[{tag.string}]({href})'

def process_and_convert_heading(tag: NavigableString) -> Tuple[int, str]:
    text = str()
    if tag.string:
        text = f'{tag.string}'
        text = compress_text(text)
    return 1, f'{text}' if len(text) > 0 else ''

def process_and_convert_span(tag: NavigableString) -> Tuple[int, str]:
    text = process_child(tag)
    text = compress_text(text)
    return 1, f'{text}' if len(text) > 0 else ''

def process_div(tag: NavigableString) -> Tuple[int, str]:
    if tag.string:
        raise AttributeError('<div> unexpectedly has text.')
    return 1, ''

def image_alt_to_node(name: str, description: str, createdAt: int, summary: TanaIntermediateSummary) -> TanaIntermediateNode:
    # The regular expression pattern for an URL
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    # Check if the line includes an URL
    urls = re.findall(url_pattern, name)
    for url in urls:
        # Replace the URL with its Tana equivalent
        name = name.replace(url, f'[{url}]({url})')
    child_node = TanaIntermediateNode(
        uid=str(next(uid)), 
        name=name, 
        description=description, 
        children=[], 
        refs=[], 
        createdAt=createdAt, 
        editedAt=int(time.time() * 1000.0), 
        type=NodeType.NODE
    )
    summary.leafNodes += 1
    summary.totalNodes += 1
    return child_node


def process_image_and_convert_to_node(tag: NavigableString, images: Dict, createdAt: int, supertag: TanaIntermediateSupertag, summary: TanaIntermediateSummary) -> Tuple[int, List[TanaIntermediateNode], List[Dict[str, Union[str, int]]]]:
    alt = tag.get('alt')
    # img_src = tag.get('src')
    # found = img_src in images
    # print(f'<IMAGE> source="{img_src}" found={found}, text=>>>\n{alt}\n<<<<')

    text = ' '
    potentially_corrupted = False
    if alt:
        # print(f'text=>>>\n{alt}\n<<<<')
        potentially_corrupted = True

        # Remove all occurrences of "Untitled picture" followed by any extension
        text = re.sub(r'Untitled picture\.\w+', '', alt)

    # Split the alt. text into lines
    lines = text.split('\n')

    current_line = ""
    image_description_node = []
    image_nodes = []
    image_attributes = []
    # Create a TanaIntermediateNode object from all the <img> elements
    for i, line in enumerate(lines):
        # Remove '\r' from the line
        line = line.replace('\r', '')

        # If this is the first line, treat it as its own node
        if 0 == i:
            description = ''
            if potentially_corrupted:
                description = 'OneNote potentially corrupted on transit. Must be copied by hand to fix.'
            if line:
                if line[0] == ' ':
                    line = 'Untitled picture'
                    image_description_node.append(image_alt_to_node(line, description, createdAt, summary))
                else:
                    image_nodes.append(image_alt_to_node(line, description, createdAt, summary))
                summary.leafNodes += 1
                summary.totalNodes += 1
            continue

        # Skip empty lines
        if not line.strip():
            if current_line:
                if current_line[0] == current_line[-1]:
                    image_description_node.append(image_alt_to_node(current_line.strip(), "Assumed image to text.", createdAt, summary))
                else:
                    image_nodes.append(image_alt_to_node(current_line, '', createdAt, summary))
                summary.leafNodes += 1
                summary.totalNodes += 1
                current_line = ""
        else:
            # If the current line is not empty,
            # add a space before appending the new line
            if current_line:
                current_line += " "
            current_line += line

    # Add the last line if it's not empty
    if current_line:
        # image_nodes.append(image_alt_to_node(current_line, '', createdAt, summary))
        image_nodes.append(image_alt_to_node(current_line, '', -1, summary))
        summary.leafNodes += 1
        summary.totalNodes += 1

    # add image as a node (unsupported)
    child_node = TanaIntermediateNode(
        uid=str(next(uid)), 
        name=f"(Images are not supported) [Upvote #21](https://ideas.tana.inc/posts/21-tana-api-add-data-to-tana-and-access-it-with-api).", 
        description=f'<i>Tana TIF currently does not support importing <u>inline</u> images.</i>', 
        children=image_description_node, 
        refs=[], 
        createdAt=999999, # createdAt, 
        editedAt=int(time.time() * 1000.0),
        type=NodeType.NODE,
        )
    image_nodes.append(child_node)
    summary.leafNodes += 1
    summary.totalNodes += 1

    return 1, image_nodes, image_attributes

def table_to_node(table: list, name: str, createdAt: int, supertag: TanaIntermediateSupertag, summary: TanaIntermediateSummary) -> Tuple[TanaIntermediateNode, List[Dict[str, Union[str, int]]]]:
    # Create table node
    table_node = TanaIntermediateNode(uid=str(next(uid)), 
        name=name, 
        children=[], 
        createdAt=createdAt,
        editedAt=int(time.time() * 1000.0),
        type=NodeType.NODE.value,
        supertags=[supertag.uid])
    for i, row in enumerate(table):
        if i == 0:  # Heading row
            heading_nodes = []
            for index, cell in enumerate(row):
                name = cell if cell != '' else str(index)
                node = TanaIntermediateNode(
                    uid=str(next(uid)), 
                    name=name, 
                    createdAt=createdAt,
                    editedAt=int(time.time() * 1000.0),
                    type=NodeType.FIELD
                )
                heading_nodes.append(node)
                summary.fields += 1
        else:  # Data row
            row_node = TanaIntermediateNode(
                uid=str(next(uid)), 
                name=chr(64 + i), 
                children=[], 
                createdAt=createdAt,
                editedAt=int(time.time() * 1000.0),
                type=NodeType.NODE
            )
            for j, cell in enumerate(row):
                cell_node = TanaIntermediateNode(
                    uid=str(next(uid)), 
                    name=cell, 
                    createdAt=createdAt,
                    editedAt=int(time.time() * 1000.0),
                    type=NodeType.NODE
                )
                summary.leafNodes += 1
                summary.totalNodes += 1
                heading_node = TanaIntermediateNode(
                    uid=str(next(uid)), 
                    name=heading_nodes[j].name, 
                    children=[cell_node], 
                    createdAt=createdAt,
                    editedAt=int(time.time() * 1000.0),
                    type=NodeType.FIELD)
                row_node.children.append(heading_node)
                summary.fields += 1
            table_node.children.append(row_node)
            summary.leafNodes += 1
            summary.totalNodes += 1
    attributes = [{"name": (name if name != '' else str(index)), "count": 0} for index, name in enumerate(table[0])]
    return table_node, attributes

def process_beginnings(title_str: str, date_str: str, time_str: str, language: str) -> TanaIntermediateNode:
    # Combine the date and time into a single string
    date_time_str = f"{date_str} {time_str}"
    # Use a default character set 
    # FIXME: get charset attribute from <head>
    charset = CHARSET
    # Compile the name of the locale
    locale_name = f'{language}.{charset}'
    # Store current locale
    old_loc = locale.getlocale(locale.LC_TIME)
    try:
        # Set the LC_TIME locale category
        locale.setlocale(locale.LC_TIME, locale_name)
    except locale.Error as e:
        print(f'ERROR: locale = "{locale_name} - {e}')
        locale.setlocale(locale.LC_TIME, f'de.{charset}')   # TODO: make that a CLI option

    # Convert the date and time string to a datetime object
    date_time_obj = datetime.strptime(date_time_str, '%A, %d. %B %Y %H:%M')
    # Localize the datetime object to the "GMT+1" timezone
    date_time_obj = pytz.timezone(TIMEZONE).localize(date_time_obj)
    # Convert the localized datetime object to a timestamp in milliseconds
    timestamp_millis = int(date_time_obj.timestamp() * 1000.0)
    # Switch back to previous locale
    locale.setlocale(locale.LC_TIME, old_loc)
    # Create a Node object from the first <p> element
    node = TanaIntermediateNode(
        uid=str(next(uid)), 
        name=title_str, 
        description=f'{date_str}, {time_str}', 
        children=[], 
        refs=[], 
        createdAt=timestamp_millis, 
        editedAt=int(time.time() * 1000.0), 
        type=NodeType.NODE
    )
    return node

def convert_onenote_page(html_file: str, html_images: Dict, summary: TanaIntermediateSummary, nodes: List[TanaIntermediateNode], attributes: List[TanaIntermediateAttribute], supertags: List[TanaIntermediateSupertag]) -> Tuple[TanaIntermediateSummary, List[TanaIntermediateNode], List[TanaIntermediateAttribute], List[TanaIntermediateSupertag]]:
    top_level_node = None
    parent_node_current = None
    parent_node_previous = None

    # Initialize the assumed creation date and time, and note title
    date_str = str()
    language = str()    # the language the date is encoded in
    time_str = str()
    title_str = str()

    slurry = BeautifulSoup(html_file, 'html.parser')
    solids = slurry.find_all(True)

    p = 1 # paragraph <p> counter

    i = 0
    # Iterate over all tags in the document
    while i < len(solids):
        tag = solids[i]
        tag_name = tag.name.casefold()

        # Handle division or section
        if tag_name == 'div':
            # this will raise an exception if 'text' is not empty
            n, text = process_div(tag)

        # Handle paragraphs
        elif tag_name == 'p':
            n, language, text = process_and_convert_paragraph(tag)
            # special treatment for the start of an OneNote
            if p in [1,2,3]:
                # print(f'[{p}] -> {text[1:]} <-')
                if 1 == p:
                    title_str = text
                if 2 == p:
                    date_str = text
                if 3 == p:
                    time_str = text
                    top_level_node = process_beginnings(title_str, date_str, time_str, language)
                    summary.topLevelNodes += 1
                    summary.totalNodes += 1
                    # Initialize the parent node
                    parent_node_current = top_level_node
                    parent_node_previous = top_level_node
                    # Append the Node object to the list of nodes
                    nodes.append(top_level_node)
                p += 1
                i += n
                continue
            if 0 < len(text):
                # Create a TanaIntermediateNode object from the <p> element
                child_node = TanaIntermediateNode(
                    uid=str(next(uid)), 
                    name=text, 
                    description="", 
                    children=[], 
                    refs=[], 
                    createdAt=parent_node_current.createdAt, 
                    editedAt=int(time.time() * 1000.0), 
                    type=NodeType.NODE
                )
                # Add our tag line to the OneNote tag line
                if "Created with OneNote." in text:
                    child_node.description = 'Imported into Tana with <b><i>onenote-to-tana</i></b>.'
                    top_level_node.children.append(child_node)
                else:
                    # Append the ChildNode object to the children of the parent node
                    parent_node_current.children.append(child_node)
                # Increment the summary attribute
                summary.leafNodes += 1
                summary.totalNodes += 1

        # Handle tables
        # Does currently not support tables inside of tables
        elif tag_name == 'table':
            n, title, table = process_and_convert_table(tag)
            table_node, table_attributes = table_to_node(table, title, parent_node_current.createdAt, supertag_tbl, summary)
            parent_node_current.children.append(table_node)
            attributes += table_attributes
            # Remove duplicates by converting each dictionary in the list to a tuple, 
            # make a dict out of these, then convert it back to a list of dictionaries.
            # Note: preserves the last occurrence of each duplicate.
            #       If that is not intended, instead use:
            # attributes = list(dict((attr['name'], attr) for attr in reversed(attributes)).values())[::-1]
            attributes = list(dict((attr['name'], attr) for attr in attributes).values())
            # Increment the summary attribute
            summary.leafNodes += 1
            summary.totalNodes += 1

        # Handle images
        elif tag_name == 'img':
            image_nodes = []
            if not parent_node_current:
                n = 1
                print(f'ERROR: parent node went missing.')
            else:
                n, image_nodes, image_attributes = process_image_and_convert_to_node(tag, html_images, parent_node_current.createdAt, supertag_tbl, summary)
                # as 'image_nodes' is a list and not a single node,
                # use 'extend' instead of 'append' here
                parent_node_current.children.extend(image_nodes)
                attributes += image_attributes
                # Remove duplicates by converting each dictionary in the list to a tuple, 
                # make a dict out of these, then convert it back to a list of dictionaries.
                # Note: preserves the last occurrence of each duplicate.
                #       If that is not intended, instead use:
                # attributes = list(dict((attr['name'], attr) for attr in reversed(attributes)).values())[::-1]
                attributes = list(dict((attr['name'], attr) for attr in attributes).values())
                # Increment the summary attribute already done in
                # 'process_image_and_convert_to_node' method, skipping

        # Handle headlines
        elif tag_name in ('h1', 'h2', 'h3', 'h4', 'h5'):
            n, text = process_and_convert_heading(tag)
            # Create a TanaIntermediateNode object from the <h2> element
            child_node = TanaIntermediateNode(
                uid=str(next(uid)), 
                name=text, 
                description="", 
                children=[], 
                refs=[], 
                createdAt=parent_node_current.createdAt, 
                editedAt=int(time.time() * 1000.0), 
                type=NodeType.NODE
            )
            # Append the ChildNode object to the children of the Node object
            parent_node_previous.children.append(child_node)
            # Set the parent node to the heading ChildNode
            parent_node_previous = parent_node_current
            parent_node_current = child_node
            # Increment the summary attribute
            summary.leafNodes += 1
            summary.totalNodes += 1

        # Handle breaks and no breaks (not)
        elif tag_name in ('br', 'nobr'):
            n = 1

        # Handle head/non-body (not)
        elif tag_name in ('html', 'head', 'meta', 'link', 'body'):
            n = 1

        # Handle other tags
        else:
            # Handle unsupported tags gracefully
            print(f"Unsupported tag: {tag_name}")
            n = 1
        i += n
    
    return summary, nodes, attributes, supertags

def convert_pages_all(onenote_app: Any, pages: Dict, outfile: str = None) -> None:
    import tempfile
    from onenote.pages import process_page

    # Create summary
    summary = TanaIntermediateSummary(0, 0, 0, 0, 0, 0)

    supertags = [supertag_tbl]

    # Create attributes
    attributes = []  # Initialize attributes as an empty list

    # Create nodes
    nodes = []

    # Within a temporary directory publish the OneNote pages as MHT,
    # process the MHT to extract the HTML and images from it
    # and turn those into a collection of 'tanatypes'.
    with tempfile.TemporaryDirectory() as temp_dir:
        for page in pages.values():
            html_string, html_images = process_page(
                onenote_app, 
                temp_dir, 
                page
                )
            summary, nodes, attributes, supertags = convert_onenote_page(
                html_string, 
                html_images, 
                summary, 
                nodes, 
                attributes, 
                supertags
                )

    # Create a Tana Intermediate File dictionary
    tana_dictionary = TanaIntermediateFile(summary, nodes, attributes, supertags)

    # Convert dictionary to a JSON string and write the JSON data to a file
    if outfile:
        try:
            with open(outfile, 'w') as tif_json_file:
                json.dump(tana_dictionary.to_dict(), tif_json_file, indent=3)
        except IOError:
            print(f"ERROR: Could not write to file: {outfile}")
    else:
        json.dump(tana_dictionary.to_dict(), sys.stdout, indent=3)
