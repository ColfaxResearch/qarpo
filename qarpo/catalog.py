from IPython.core.display import HTML, Markdown
import ipywidgets as widgets
import subprocess
import json
import os.path
import datetime

class DemoCatalog:

    def __init__(self, dir_path, NB_type, branch='master'):
        self.dir_path = dir_path
        self.NB_type = NB_type
        self.branch = branch
        self.messages = {
            "placeholder": "(waiting to check the status; click the Check Status button to check immediately)",
	    "uptodate": "As of {time}, All {NB_type}s are up to date.",
	    "behind": "As of {time}, {NB_type}s require an update.",
	    "ahead": "As of {time}, it seems that you are doing your own version control.",
	    "unable": "As of {time}, we are unable to determine the {NB_type}s status due to a server-side error.",
            "g_foreword": "<br /><b>After the refresh, you will lose any changes you have made to this {NB_type}/all {NB_type}s and any data that your {NB_type} runs may have generated.</b><br/>",
            "local_uptodate": "This {NB_type} is up to date.",
            "global_uptodate": "All {NB_type}s are up to date.",
	
	    "remote": "Remote URL",
	    "lastCheck": "Server-side time of last status check",
	    "gitsaid": "Output of 'git status'"
        }
        self.l_button = "Update this {}".format(self.NB_type)
        #self.g_button = "Update all {}s".format(self.NB_type)
        self.g_button = "Update all Demos and Tutorials"
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
        url, status, lastCheck, fullstatus, local_status = self.GetStatus()
        msgs = self.messages
        l_refresh=widgets.Button(description=self.l_button, layout=widgets.Layout(width='50%'))
        g_refresh=widgets.Button(description=self.g_button, layout=widgets.Layout(width='50%'))
        self.localRefreshButton = l_refresh
        self.globalRefreshButton = g_refresh
        self.localRefreshButton.on_click(self.RefreshRepository)
        self.globalRefreshButton.on_click(self.RefreshRepository)
        w_url = widgets.HTML(value=("{remote}: {remote_url}").format(remote=msgs['remote'], remote_url=url))
        w_time = widgets.HTML(value=("{time}: {lastCheck}").format(time=msgs['lastCheck'], lastCheck=lastCheck))
        w_git = widgets.HTML(value=("{gitsaid}: {gitline}").format(gitsaid=msgs['gitsaid'], gitline=fullstatus))
        w_g_hint = widgets.HTML(value=msgs['g_foreword'].format(NB_type=self.NB_type))

        if int(status) == 0:
            c = 'uptodate'
            g_refresh = widgets.HTML(value=msgs['global_uptodate'].format(NB_type=self.NB_type))
            w_g_hint = widgets.HTML(value="")
        elif int(status) == 1:
            c = 'behind'
        elif int(status) == 2:
            c = 'ahead'
        else:
            c = 'unable'

        if local_status == 0:
            c_l = 'local_uptodate'
            #self.localRefreshButton.disabled = True
            #self.localRefreshButton.description= "This Demo is uptodate"
            l_refresh = widgets.HTML(value=msgs['local_uptodate'].format(NB_type=self.NB_type))
        elif local_status == 1:
            c_l = 'local_not_updated'

        v = msgs[c].format(time=lastCheck, NB_type=self.NB_type)

        display(HTML(self.css))

        w_info=widgets.VBox([l_refresh, g_refresh, w_g_hint, w_url, w_time, w_git])
        w_acc=widgets.Accordion(children=[w_info], selected_index=0)
        w_acc.set_title(0, v)
        w_acc.add_class(c)
        display(w_acc)
        
        
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
        if status != 0:
            local_status = self.GetLocalStatus()
        else:
            local_status = 0
        return url, status, time, fullstatus, local_status

    def GetLocalStatus(self):
        cmd = 'git diff origin/{B} --name-only {P}'.format(B=self.branch, P=self.dir_path)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        output, _ = p.communicate()
        local_status = output.decode()
        if not local_status:
            return 0
        else:
            return 1

    def RefreshRepository(self, evt):
        if evt.description == self.l_button:
            cmd = 'git clean -f -d ; git checkout origin/{B} -- {P}'.format(B=self.branch, P=self.dir_path)
        else:
            #cmd = 'git clean -f -d ; git reset --hard origin/master'
            cmd = 'git clean -f -d ; git checkout -- ./ ; git pull'
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
