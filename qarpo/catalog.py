from IPython.core.display import HTML, Markdown
import ipywidgets as widgets
import subprocess
import json
import os.path
import datetime

class DemoCatalog:

    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.messages = {
            "placeholder": "(waiting to check the status; click the Check Status button to check immediately)",
	    "uptodate": "As of {time}, All Demos are up to date.",
	    "behind": "As of {time}, Demos require an update.",
	    "ahead": "As of {time}, it seems that you are doing your own version control.",
	    "unable": "As of {time}, we are unable to determine the demos status due to a server-side error.",
	    "l_foreword": "Click the button below to pull the latest update for this demo from GitHub.",
            "g_foreword": "<br /><b>After the refresh, you will lose any changes you have made to this demo/all demos and any data that your demo runs may have generated.</b><br/>",
	
	    "remote": "Remote URL",
	    "lastCheck": "Server-side time of last status check",
	    "gitsaid": "Output of 'git status'"
        }
        self.l_button = "Refresh This Demo Only"
        self.g_button = "Refresh All Demos"
        self.reloadCode = "<script>window.location.reload()</script>"
        self.autorunFirstDelay = "1500"
        self.autorunInterval = "-1"
        self.toggle = "Show/Hide Code Cells" 
        self.css = """<style>
                    a.big-jupyter-button, button.jupyter-button
                    {
                        line-height:40px;
                        height:40px;
                        display:inline-block;
                        background-color:#0071c5;
                        color:white;
                        border:none;
                        font-size:100%;
                        font-weight:bold;
                        cursor:pointer;
                        padding-left:1em;
                        padding-right:1em;
                        margin-top:10px;
                        text-decoration:none !important;
                    }
                    a.big-jupyter-button:hover
                    {
                        -webkit-box-shadow: 0 2px 2px 0 rgba(0, 0, 0, .14), 0 3px 1px -2px rgba(0, 0, 0, .2), 0 1px 5px 0 rgba(0, 0, 0, .12);
                    
                        box-shadow: 0 2px 2px 0 rgba(0, 0, 0, .14), 0 3px 1px -2px rgba(0, 0, 0, .2), 0 1px 5px 0 rgba(0, 0, 0, .12);
                    }
                    div.ahead > div.p-Collapse > div.p-Collapse-header
                    {
                        background-color:#8800aa;
                        color:white;
                    }
                    div.behind > div.p-Collapse > div.p-Collapse-header
                    {
                        background-color:#ffaa00;
                        color:white;
                    }
                    div.unable > div.p-Collapse > div.p-Collapse-header
                    {
                        background-color:#cc0000;
                        color:white;
                    }
                    div.uptodate > div.p-Collapse > div.p-Collapse-header
                    {
                        background-color:#008800;
                        color:white;
                    }
                    .rendered_html h2, .rendered_html h2:first-child, .rendered_html h3
                    {
                        margin-top:3em;
                    }
                    
                    
                    </style>"""


    def ShowRepositoryControls(self):
        url, status, lastCheck, fullstatus = self.GetStatus()
        l_refresh=widgets.Button(description=self.l_button, layout=widgets.Layout(width='50%'))
        g_refresh=widgets.Button(description=self.g_button, layout=widgets.Layout(width='50%'))

        msgs = self.messages
        if int(status) == 0:
            c = 'uptodate'
        elif int(status) == 1:
            c = 'behind'
        elif int(status) == 2:
            c = 'ahead'
        else:
            c = 'unable'
        v = msgs[c].format(time=lastCheck)

        display(HTML(self.css))

        w_url = widgets.HTML(value=("{remote}: {remote_url}").format(remote=msgs['remote'], remote_url=url))
        w_time = widgets.HTML(value=("{time}: {lastCheck}").format(time=msgs['lastCheck'], lastCheck=lastCheck))
        w_git = widgets.HTML(value=("{gitsaid}: {gitline}").format(gitsaid=msgs['gitsaid'], gitline=fullstatus))
        w_l_hint = widgets.HTML(value=msgs['l_foreword'])
        w_g_hint = widgets.HTML(value=msgs['g_foreword'])
        w_info=widgets.VBox([l_refresh, g_refresh, w_g_hint, w_url, w_time, w_git])
        w_acc=widgets.Accordion(children=[w_info], selected_index=0)
        w_acc.set_title(0, v)
        w_acc.add_class(c)
        display(w_acc)
        
        self.localRefreshButton = l_refresh
        self.globalRefreshButton = g_refresh
        self.localRefreshButton.on_click(self.RefreshRepository)
        self.globalRefreshButton.on_click(self.RefreshRepository)


    def GetStatus(self):
        cmd = 'git config --get remote.origin.url; git fetch origin'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        output, _ = p.communicate()
        url = output.decode().split("\n")[0]
        cmd = 'git status'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        output, err = p.communicate()
        fullstatus = output.decode().split("\n")[1]
        if fullstatus.find('branch is up to date') != -1:
            status = 0
        elif fullstatus.find('branch is behind') != -1:
            status = 1
        elif fullstatus.find('branch is ahead') != -1:
            status = 2
        else:
            status = 3
        time = datetime.datetime.now().strftime("%d/%m/%y %H:%M:%S")
        return url, status, time, fullstatus


    def RefreshRepository(self, evt):
        if evt.description == self.l_button:
            cmd = 'git clean -f -d ; git checkout origin/master -- {}'.format(self.dir_path)
            #self.localRefreshButton.disabled = True
        else:
            cmd = 'git clean -f -d ; git reset --hard origin/master'
            #cmd = 'git clean -f -d ; git checkout -- ./ ; git pull'
            #self.globalRefreshButton.disabled = True
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        output,_ = p.communicate()
        display(HTML(self.reloadCode))


    def Anchor(self, name):
        display(HTML("<a class='"+name+"'></a>"))


    def Autorun(self, name):
        display(HTML("<script>"+
                     "function ClickRunGenerate() {"+
                     "  var code_cells = document.getElementsByClassName('code_cell');"+
                     "  if (code_cells.length > 0) {"+
                     "    var i;"+
                     "    for (i = 0; i < code_cells.length; i++) {"+
                     "      var anch = code_cells[i].getElementsByClassName('"+name+"');"+
                     "      if (anch.length > 0) {"+
                     "        var rtc = code_cells[i].getElementsByClassName('run_this_cell');"+
                     "        if (rtc.length > 0) {"+
                     "          var j;"+
                     "          for (j = 0; j < rtc.length; j++) {"+
                     "            rtc[j].click();"+
                     "          }"+
                     "        }"+
                     "      }"+
                     "    }"+
                     "  }"+
                     "  if ("+self.autorunInterval+" > 0) {"+
                     "    setTimeout(ClickRunGenerate, "+self.autorunInterval+");"+
                     "  }"+
                     "}"+
                     "setTimeout(ClickRunGenerate, "+self.autorunFirstDelay+");"+
                     "</script>"))


    def ToggleCode(self):
        display(HTML("<script>"+
                     "codeShow=true;"+
                     "function CodeToggle() {"+
                     "  if (codeShow) {"+
                     "    $('div.input').hide();"+
                     "  } else {"+
                     "    $('div.input').show();"+
                     "  }"+
                     "  codeShow = !codeShow;"+
                     "}"+
                     "$( document ).ready(CodeToggle);"+
                     "</script>"+
                     "<form action='javascript:CodeToggle()'><input type='submit' value='"+self.toggle+"'></form>"))
