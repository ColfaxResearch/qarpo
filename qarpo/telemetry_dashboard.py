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

<div class="loader"></div>{status}


</body>
</html>
'''


class DashboardLauncher():
    def __init__(self, command, search_url, display_name, duration, queue):
        self.command = command
        self.pointer = search_url
        self.name = display_name
        self.duration = duration
        self.start_button = widgets.Button(description='Start Application', disabled=False, button_style='info')
        self.stop_button = widgets.Button(description='Stop Application', disabled=False, button_style='info')
        self.status = widgets.HTML(value='')
        prev_jobs, job_ids = self.jobsRunning(queue)
        if prev_jobs == True:
            print("Jobs still running")
        else:
            self.display_box = widgets.VBox([self.start_button, self.status])

        url = None
        def on_start_clicked(b):
            self.stop_button.disabled = False
            self.display_box.children = [self.stop_button, self.status]
            self.submitDashboardJob()
    
        def on_stop_clicked(b):
            self.stop_button.disabled = True
            self.cancelJob()
            self.status.value = f'{self.name} job terminated'
            self.display_box.children = [self.start_button, self.status]


        self.start_button.on_click(on_start_clicked)
        self.stop_button.on_click(on_stop_clicked)
        display(self.display_box)


    def jobsRunning(queue_name):
        command = f'qstat {queue_name}'
        p = subprocess.Popen(self.command, stdout=subprocess.PIPE, shell=True)
        output, error = p.communicate()
        jobs = output.decode("utf-8")
        print(jobs)
        if jobs = '':
            return False, ""
        else:
            return True, jobs



    def submitDashboardJob(self):
        p = subprocess.Popen(self.command, stdout=subprocess.PIPE, shell=True)
        output, error = p.communicate()
        self.jobid = output.decode("utf-8").rstrip().split('.')[0]
        if self.jobid == "":
            self.status.value = f"<span style='color:red'>&#9888;</span> Launching {self.name} failed"
            self.display_box.children = [self.start_button, self.status]
            return
        else:
            self.status.value = loader.replace('{status}', f"Initializing and loading {self.name}. This will take approximately {self.duration}.")
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
                        self.redirectURL(url)
                        self.status.value = f'{self.name} successfully launched.<br>If the application does not load in a new browser window, disable pop-up blocking in your browser settings and click <a href="{url}">this link</a> to access {self.name}. '
                        break

        thread = threading.Thread(target=_work, args=())
        thread.start()

    
    def redirectURL(self, URL):
        self.time_created = time.time()*1000
        script = new_tab =f'''<script>
                    var d = new Date();
                    var time_now = d.getTime();
                    var timeout = 7000;
                    if (time_now - {self.time_created} < timeout) {{
                        var win = window.open('{URL}', '_blank');
                    }}
                    </script>'''
        new_tab = HTML ('''{}'''.format(script))
        display(new_tab)
          

    def cancelJob(self):
        cmd = f'qdel {self.jobid}'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        output, err = p.communicate()
        self.status.value = loader.replace("{status}",f"Cancelling {self.name} job")
        cmd = 'qstat '+self.jobid
        cancelled = False
        while not cancelled:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            output,_ = p.communicate()
            cancelled = True if output.decode().rstrip() == '' else False
            time.sleep(7.0)












