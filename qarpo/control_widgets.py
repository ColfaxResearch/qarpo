from IPython.core.display import HTML
import threading
from IPython.display import display, Image
import ipywidgets as widgets
from ipywidgets import Layout
import time
import queue
import subprocess
import datetime
import matplotlib
import matplotlib.pyplot as plt
import os, pwd 
import warnings
import json
import random
import io
import urllib, base64
import urllib.parse
from .disclaimer import *
from .demoutils_tabs import Interface



class ControlWidget(Interface):


    def __init__(self, item, jobDict, Int_obj, command):
        self.jobDict = jobDict
        self.Int_obj = Int_obj
        self.command = command
        if item == "cancel_job":
            self.button = self.addCancelButton()
        elif item == "dashboard":
            self.button = self.addTelemetryButton()
        elif item == "telemetry":
            self.button = self.addTelemetryButton()
    
    
    def addCancelButton(self):
        #Cancel job button and function on click
        cancel_job_button = widgets.Button(description='Cancel job', disabled=False, button_style='info')
        def cancelJob(event):
            if self.Int_obj.jobStillRunning(self.command):
                cmd = 'qdel '+self.jobDict[self.command]['jobid']
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
                frame_id = self.jobDict[self.command]['box_id']
                self.Int_obj.tab.set_title(str(frame_id), f'Done: {self.jobDict[self.command]["jobid"]}')
            cancel_job_button.disabled=True
        cancel_job_button.on_click(cancelJob)
        return cancel_job_button
    
        
    
    def addTelemetryButton(self):
        telemetry_button = widgets.Button(description='Telemetry', disabled=False, button_style='info')
        telemetry_out = widgets.Output()
        telemetry_box = widgets.VBox([telemetry_button, telemetry_out])

        def displayTelemetry(event):
                if self.Int_obj.jobStillRunning(self.command):
                    with telemetry_out:
                        telemetry_out.clear_output()
                        status = "<p>Telemetry results are not ready yet</p>"
                        display(HTML ('''{}'''.format(status)))
                else:
                    with telemetry_out:
                        URL = "https://devcloud.intel.com/edge/metrics/d/"+self.jobDict[self.command]['jobid']
                        script=f"<script>var win = window.open('{URL}', '_blank');</script>"
                        display(HTML ('''{}'''.format(script)))
        telemetry_button.on_click(displayTelemetry)
        return telemetry_box

