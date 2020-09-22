import os
import getpass
from IPython.core.display import HTML
import ipywidgets as widgets



# Returns the URL to the JupyterHub contents URL for the relative_path
def jupyterHubContentsURL(relative_path,username=None):
    
    # By default, this function will insert the JN user's username
    # You can also use username="none" (string) to get a generic url
    # that will rely on JH to insert the correct username
    if username is None:
        username=getpass.getuser()
        
    # relative_path is specified from the CWD; url_t needs path from the home folder, that's that below:
    path_from_home = os.path.relpath(relative_path, os.path.expanduser("~"))

    # JupyterHub's contents API URL:
    url_t = "/user/{username}/api/contents/{path}"
    url   = url_t.format(username=username,path=path_from_home)
    
    return url




# Returns the URL of the model visualizer that passes the JH contents URL to the model
def modelVisualizerURL(relative_path):
    
    # Model visualizer URL format:
    url_t = "/services/model-visualizer/?url={contents_url}"
    url   = url_t.format(contents_url = jupyterHubContentsURL(relative_path)) 
    
    return url



# Displays an HTML element that links to the visualized model    
def showModelVisualizerLink(relative_path, label=None):
    
    # Get the URL for the link
    url = modelVisualizerURL(relative_path)

    # Form the label for the link. The default label is the filename
    if label is None:
        label_text = os.path.basename(relative_path)
    else:
        label_text = label

    # Form the HTML element for the link:
    link_t = "<a target='_blank' href='{url}'>{label}</a>"
    link   = link_t.format(url=url, label=label_text)
    link_text = f'View model graph:  <span title="View model">&#128065; </span>{link}</span>'
        
    # Display the link
    display(widgets.HTML(value=link_text))
