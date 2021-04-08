from IPython.core.display import HTML
from IPython.display import display, Image
import ipywidgets as widgets
import subprocess
import threading
import time
import os
from .query_nodes import getFreeJobSlots


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
    ## search_url: string, telemetry dashboard url to be detected in stdout
    ## display_name: string, name of the dashboard
    ## duration: string, time to launch dashboard, only used in the displayed status
    ## queue: string, name of the queue to submit job to
    ## node property: string, node property, needed to detect if nodes with specific properties are available
    ##one_use_token: boolen , set to true if token in the url detected to open the telemetry dashboard is valid for single use
    ##exit_error: string, set to the error string to be searched for in stderr
    ##timeout: int, if job is running for n seconds and url was not detected, delete job using qdel
    ##launch_link_msg: string, link discription for first link in the instance launcher table
    ##reopen_link_msg: string, link discription for second link in the instance launcher table
    ##error_contact_msg: string, error message that is displayed after a timeout
    ##check_all_queues: boolean, set to true if qstat should search for jobs on any queue for the user
    def __init__(self, command, search_url, display_name, duration, queue, node_property, one_use_token = False, exit_error = None, timeout=1000, 
                 launch_link_msg = "Open the session for the first time.", 
                 reopen_link_msg = "Return to your currently running session.",
                 error_contact_msg = 'Please contact the following email for support',
                 check_all_queues = False):
        self.command = command
        self.pointer = search_url
        self.name = display_name
        self.duration = duration
        self.start_button = widgets.Button(description='Start Application', disabled=False, button_style='info')
        self.stop_button = widgets.Button(description='Stop Application', disabled=False, button_style='info')
        self.status = widgets.HTML(value='')
        self.one_use_token = one_use_token
        self.exit_error = exit_error
        #Time out, qdel will be called to kill the job after n seconds
        self.timeout = timeout 
        self.launch_link_msg = launch_link_msg
        self.reopen_link_msg = reopen_link_msg
        self.error_contact_msg = error_contact_msg
        self.start_time = None
        self.check_all_queues = check_all_queues
        if self.check_all_queues:
            prev_job, job_id = self.jobsRunning('')
        else:
            prev_job, job_id = self.jobsRunning(queue)
        if prev_job == True:
            self.new_job = False
            self.jobid = job_id
            self.status.value = loader.replace('{status}', f"Loading {self.name}.<br>JOB ID = {self.jobid}")
            self.detectURL()
            self.display_box = widgets.VBox([self.stop_button, self.status])
        else:
            self.new_job = True
            self.display_box = widgets.VBox([self.start_button, self.status])

        def on_start_clicked(b):
            if self.check_all_queues:
                prev_job, prev_id = self.jobsRunning('')
                if prev_job:
                    self.status.value = f'Job is running: JOB_ID {prev_id}'
                    self.display_box.children = [self.stop_button, self.status]
                    return
            self.status.value = "Loading ..."
            queue_server = os.getenv('PBS_DEFAULT')
            match_properties = [node_property]
            available_slots, free_slots = getFreeJobSlots(queue_server, match_properties, verbose=False)
            if free_slots == 0 :
                self.status.value = f"All nodes are currently in use and the {display_name} cannot be launched at this time. Please try again in a few minutes."
                self.display_box.children = [self.start_button, self.status]
            else:
                self.new_job = True
                self.stop_button.disabled = False
                self.display_box.children = [self.stop_button, self.status]
                self.submitDashboardJob()
    
        def on_stop_clicked(b):
            self.stop_button.disabled = True
            status = f"Cancelling {self.name} job"
            self.cancelJob(status)
            self.status.value = f'{self.name} job terminated'
            self.display_box.children = [self.start_button, self.status]


        self.start_button.on_click(on_start_clicked)
        self.stop_button.on_click(on_stop_clicked)
        display(self.display_box)


    def jobsRunning(self, queue_name):
        command = f'qstat {queue_name}'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, error = p.communicate()
        jobs = output.decode("utf-8")
        if jobs == '':
            return False, ""
        else:
            return True, jobs.rsplit("\n")[2].rsplit(".")[0]

    def submitDashboardJob(self):
        p = subprocess.Popen(self.command, stdout=subprocess.PIPE, shell=True)
        output, error = p.communicate()
        self.jobid = output.decode("utf-8").rstrip().split('.')[0]
        if self.jobid == "":
            self.status.value = f"<span style='color:red'>&#9888;</span> Launching {self.name} failed"
            self.display_box.children = [self.start_button, self.status]
            return
        else:
            self.status.value = loader.replace('{status}', f"Initializing and loading {self.name}. This will take approximately {self.duration}.<br>JOB ID = {self.jobid}")
            self.start_time = time.time()
            self.detectURL()

            
    def detectURL(self):
        op_cmd = [f'qpeek {self.jobid}']
        def _work():
            url_detected = False
            str_ = self.pointer
            while not url_detected:
                #Check if exit_error is provided and if it appeared in stderr log
                if self.start_time is None:
                    self.start_time = time.time()

                if not self.exit_error == None and self.detectErr() and self.load_cancelled or time.time()-self.start_time >= self.timeout:
                    cancel_status = f'{self.name} job {self.jobid} failed. {self.error_contact_msg}'
                    self.cancelJob(cancel_status)
                    self.status.value = cancel_status
                    self.display_box.children = [self.start_button, self.status]
                    return
                p = subprocess.Popen(op_cmd, stdout=subprocess.PIPE, shell=True)
                output,_ = p.communicate()
                output = output.decode().split('\n')
                time.sleep(3.0)
                if output == ['']:
                    p2 = subprocess.Popen([f'qstat {self.jobid}'], stdout=subprocess.PIPE, shell=True)
                    jobstatus,_ = p2.communicate()
                    if jobstatus == b'': 
                        self.status.value = f'{self.name} session terminated'
                        self.display_box.children = [self.start_button, self.status]
                        return
                for x in output:
                    if str_ in x:
                        url_detected = True
                        url = x.rstrip()
                        url_return = url.split("token")[0] if self.one_use_token else url
                        #if self.new_job == True:
                        #    self.redirectURL(url)
                        if self.reopen_link_msg == '':
                            self.status.value = f'{self.name} successfully initialized.<br><table cellpadding="5" style="border:1px black solid"><tr><td style="text-align:left;color:blue;hover:purple;padding:0 15px 0 15px;"><a href="{url}" target="_blank">Launch {self.name}</a></td><td style="text-align:left">{self.launch_link_msg}</td></table><br>JOB ID = {self.jobid}'
                        else:
                            self.status.value = f'{self.name} successfully initialized.<br><table cellpadding="5" style="border:1px black solid"><tr><td style="text-align:left;color:blue;hover:purple;padding:0 15px 0 15px;"><a href="{url}" target="_blank">Launch {self.name}</a></td><td style="text-align:left">{self.launch_link_msg}</td></tr><td style="text-align:left;color:blue;hover:purple;padding:0 15px 0 15px;"><a href="{url_return}" target="_blank">Return to {self.name}</a></td><td style="text-align:left">{self.reopen_link_msg}</td></tr></table><br>JOB ID = {self.jobid}'
                        break

        thread = threading.Thread(target=_work, args=())
        thread.start()

    def detectErr(self):
        err_cmd = [f'qpeek -e {self.jobid}']
        p = subprocess.Popen(err_cmd, stdout=subprocess.PIPE, shell=True)
        output,_ = p.communicate()
        output = output.decode()
        err_detected = True if self.exit_error in output else False
        return err_detected



    
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
        
          

    def cancelJob(self, cancel_status):
        status = loader.replace("{status}", cancel_status)
        cmd = f'qdel {self.jobid}'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        output, err = p.communicate()
        cmd = 'qstat '+self.jobid
        cancelled = False

        while not cancelled:
            self.status.value = status+f'<br>JOB ID = {self.jobid}'
            self.display_box.children = [self.stop_button, self.status]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            output,_ = p.communicate()
            cancelled = True if output.decode().rstrip() == '' else False
            time.sleep(7.0)
        return








