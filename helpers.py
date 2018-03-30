
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

