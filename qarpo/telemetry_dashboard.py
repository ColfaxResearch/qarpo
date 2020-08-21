from IPython.core.display import HTML
from IPython.display import display, Image
import ipywidgets as widgets
import subprocess
import threading
import time



loader = '''<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
.loader {
  border: 16px solid #f3f3f3;
  border-radius: 50%;
  border-top: 16px solid #3498db;
  width: 20px;
  height: 20px;
  -webkit-animation: spin 2s linear infinite; /* Safari */
  animation: spin 2s linear infinite;
}

@-webkit-keyframes spin {
  0% { -webkit-transform: rotate(0deg); }
  100% { -webkit-transform: rotate(360deg); }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
</head>
<body>

<div class="loader"></div> Loading DL workbench, this will take few minutes

</body>
</html>
'''


class DashboardLauncher():
    def __init__(self, command, search_url):
        self.command = command
        self.pointer = search_url
        self.start_button = widgets.Button(description='Launch Dashboard', disabled=False, button_style='info')
        self.stop_button = widgets.Button(description='Stop Dashboard', disabled=False, button_style='info')
        self.loader = widgets.HTML(value='')
        self.display_box = widgets.VBox([self.start_button, self.loader])
        url = None
        def on_start_clicked(b):
            self.display_box.children = [self.stop_button, self.loader]
            self.submitDashboardJob()
    
        def on_stop_clicked(b):
            self.cancelJob()
            self.loader.value = 'DL workbench job terminated'
            self.display_box.children = [self.start_button, self.loader]


        self.start_button.on_click(on_start_clicked)
        self.stop_button.on_click(on_stop_clicked)
        display(self.display_box)

    def submitDashboardJob(self):
        p = subprocess.Popen(self.command, stdout=subprocess.PIPE, shell=True)
        output, error = p.communicate()
        self.jobid = output.decode("utf-8").rstrip().split('.')[0]
        if self.jobid == "":
            self.loader.value = "<span style='color:red'>&#9888;</span> Launch DL dashboard failed"
            return
        else:
            self.loader.value = f'''{loader}'''
            self.detectURL()

    def detectURL(self):
        op_cmd = [f'qpeek {self.jobid}']
        def _work():
            url_detected = False
            while not url_detected:
                p = subprocess.Popen(op_cmd, stdout=subprocess.PIPE, shell=True)
                output,_ = p.communicate()
                output = output.decode().split('\n')
                time.sleep(3.0)
                str_ = self.pointer
                for x in output:
                    if str_ in x:
                        url_detected = True
                        url = x.rstrip()
                        self.loader.value = "You'll be redirected to DL workbench"
                        self.redirectURL(url)
                        break

        thread = threading.Thread(target=_work, args=())
        thread.start()

    
    def redirectURL(self, URL):
        script=f"<script>var win = window.open('{URL}', '_blank');</script>"
        display(HTML ('''{}'''.format(script)))
          

    def cancelJob(self):
        cmd = f'qdel {self.jobid}'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        output, err = p.communicate()









