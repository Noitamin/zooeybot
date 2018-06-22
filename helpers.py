
from numpy import array
import re

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


