import os
import getpass
from IPython.core.display import HTML

def displayMultiversionURL(relative_path, current_nb, current_ver, supported_versions ,username=None):

    if username is None:
        username=getpass.getuser()

    path_from_home = os.path.relpath(relative_path, os.path.expanduser("~"))
    link = ""
    for v in supported_versions:
        label_text = f"{v}"
        url = f"/user/{username}/notebooks/{path_from_home}/{current_nb}".replace(current_ver, v)
        link += f"<a target='_blank' href='{url}'>{label_text}</a><br>"

    display(HTML(link))

