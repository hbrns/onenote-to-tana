# Utility functions

import email
import re
from email import policy
from datetime import datetime, timezone
from xml.etree import ElementTree
from string import printable
from typing import Dict, Tuple

# ISO 8601 date and time common format
def iso8601(date_string: str):
    # To read a date-time string in ISO 8601 format:
    # date_string = "2023-12-26T14:21:09.000Z"
    date_object = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")

    # Now date_object is a datetime object.
    print(date_object)

    # To write a date-time string in ISO 8601 format:
    # Let's assume we have a datetime object.
    date_object = datetime.now(timezone.utc)

    # Now we convert it to a string in ISO 8601 format.
    date_string = date_object.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z"
    print(date_string)
    return date_object

def safe_str(name: str) -> str:
    """
    Takes a string parameter 'name' and returns a new string where
    any character that are not allowed in filenames are replaced
    with a hyphen '-'. It also ensures the new string does not start
    or end with a space, period, hyphen, or underline.
    """
    # Define a regular expression that matches any character not
    # in the set of printable ASCII characters or any of the
    # following special characters: < > : " / \ | ? *
    # 'pattern' is a raw string so that all escape codes in the
    # string will be ignored and treated as literal characters.
    pattern = r"[^{}]|<|>|:|\"|/|\\|\||\?|\*".format(printable)
    # pattern = r"[/\\?%*:|\"<>\x7F\x00-\x1F]"
    safe_name = re.sub(pattern, "-", name)

    # Ensure the 'safe_name' does not start or end with
    # a space, period, hyphen, or underline
    # return re.sub(r"^[ .-_]+|[ .-_]+$", "", safe_name)
    ret = re.sub(r"^[ .-_]+|[ .-_]+$", "", f'{safe_name}')
    print(f'{name} -> "{safe_name}" -> "{ret}"')
    return "noname" if ret == "" else ret

def check_substring_in_keys(dictionary: Dict, substring: str) -> Dict:
    """
    The function returns a new dictionary that includes only the
    key-value pairs from 'dictionary' where the key contains
    'substring' as a substring.
    """
    return {key: dictionary[key] for key in dictionary if substring in key}

def extract_mht_contents(mht_file: str) -> Tuple[str, Dict[str, str]]:
    """
    Extract the contents of a Microsoft Hypertext Archive (MHT) file. 
    The function takes an MHT file as input and opens it in binary mode.
    It then reads the file as an email message, since MHT files are 
    essentially MIME-encoded files.
    """

    with open(mht_file, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    if not msg:
        print(f"Error: No email message found in file '{mht_file}'.")
        raise email.errors.MessageError

    html = None
    xml = None
    images = {}
    for part in msg.walk():
        content_type = part.get_content_type()
        # print(f'part type = {content_type}')
        if content_type == 'text/html':
            html = part.get_content()
        # in case of multipart/related, a text/xml should describe the additional parts
        elif content_type == "image/png" or content_type == "image/jpeg":
            # image = part.get_content() # decode, ready to store on filesystem
            # image = part.get_payload(decode=False) # raw MIME image data
            pass
        elif content_type == "text/xml":
            xml = part.get_content()

    if xml is not None:
        # print(f'xml = {xml}')
        # Parse the XML string
        root = ElementTree.fromstring(xml)
        # Define the namespace
        namespaces = {'o': 'urn:schemas-microsoft-com:office:office'} 
        # Find the 'HRef' attribute of 'o:MainFile' element
        main_file = root.find('o:MainFile', namespaces)
        main_path = main_file.attrib['HRef']
        # Split the path into components
        components = main_path.split('/')
        # The last component is the filename with extension
        filename_with_extension = components[-1]
        # Split the filename into name and extension
        fname, _ = filename_with_extension.rsplit('.', 1)
        fname += '_files'
        # 'fname' should now hold the path used as reference in the
        # HTML part, e.g., for images
        for file in root.findall('o:File', namespaces):
            file_path = file.attrib['HRef']
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_name = f'{fname}/{file_path}'
                for part in msg.walk():
                    if part.get_content_type() in ["image/png", "image/jpg", "image/jpeg"]:
                        images[image_name] = part.get_payload(decode=False)
    return html, images
