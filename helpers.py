from numpy import array
import re
from apng import APNG
import os
from PIL import Image
from io import BytesIO

def PIL2numpy( img ):
    return array(img)

def userInServer(server, user, mode):
    # Returns True if user is in the server and False otherwise
    # Accepts discord server object and two strings as arguments
    # The user can be specified by mention string, id, or name.
    if mode is 'mention':
        id_digits = re.search("^<@!{0,1}(\d+)>$", user)
        if id_digits:
            member_list = [member.id for member in server.members]
            if id_digits.group(1) in member_list:
                return True
            else:
                return False
        else:
            return False
    elif mode is 'id':
        member_list = [member.id for member in server.members]
        if user in member_list:
            return True
        else:
            return False
    elif mode is 'name':
        member_list = [member.name for member in server.members]
        if user in member_list:
            return True
        else:
            return False
    else:
        print('ERROR: Invalid arguments')
        return False

class parsed_arg(object):
    def __init__(self):
        self.name = None
        self.values = []

def parse_options(args):
    # Parses input message to group options with their values
    # We might have inputs before any options; these inputs should not begin with --
    print(args)
    word = 0
    arg = parsed_arg()
    arg.name = "input"
    parsed_args = []
    while word < len(args):
        print(args[word])
        if args[word].startswith("--"):
            # New option; push the current arg
            parsed_args.append(arg)
            # Reset arg with new name
            arg = parsed_arg()
            arg.name = args[word]
        else:
            # Otherwise, this is a value pertaining to the current option
            arg.values.append(args[word])
        word += 1
    # Push the last arg parsed and return
    parsed_args.append(arg)
    return parsed_args

def APNGtoGIF( apng_path ):
    # Convert apng to animated gif
    name = os.path.splitext(apng_path)[0]
    apng = APNG.open(apng_path)

    # Read in metadata
    max_width = 0
    max_height = 0
    x_offsets = []
    y_offsets = []
    durs = []
    disposals = []

    for png, control in apng.frames:
        if control.width + control.x_offset > max_width:
            max_width = control.width
        if control.height + control.y_offset > max_height:
            max_height = control.height
        x_offsets.append(control.x_offset)
        y_offsets.append(control.y_offset)
        #this should be correct but idk
        #disposals.append(control.depose_op+1)

        # compute duration value
        # note that gif duration is in ms
        durs.append(int(1000*(control.delay/control.delay_den)))

    # Read in image data
    i = 0
    images = []
    for png, control in apng.frames:
        src_img = Image.open(BytesIO(png.to_bytes()))
        if src_img.mode != 'RGBA':
            src_img = src_img.convert('RGBA')
        dims = src_img.size
        width = dims[0]
        height = dims[1]

        img = Image.new('RGBA', (max_width, max_height))
        img.paste(src_img, (x_offsets[i], y_offsets[i], x_offsets[i] + width, y_offsets[i] + height))

        # We have RGBA data but .gifs are a palette-based format
        # Extract alpha channel to use as a mask
        alpha = img.split()[3]

        # Convert base image to palette-based with 255 colors
        img = img.convert('P', palette=Image.ADAPTIVE, colors=255)

        # Paste color 256 (index 255) over all pixels with alpha < 128
        # Guaranteed not to be used because we only used 255 colors
        a_cutoff = 128
        transparent_color = 255
        mask = Image.eval(alpha, lambda a: 255 if a <= a_cutoff else 0)
        img.paste(transparent_color, mask)

        images.append(img)
        i += 1

    #images[0].save(fp=name+'.gif', format='gif', save_all=True,
    #               append_images=images[1:], duration=durs, loop=0,
    #               background=transparent_color,
    #               transparency=transparent_color,
    #               optimize=False, disposal=disposals)
    images[0].save(fp=name + '.gif', format='gif', save_all=True,
                                  append_images=images[1:], duration=durs, loop=0,
                                  background=transparent_color,
                                  transparency=transparent_color,
                                  optimize=False, disposal=2)

