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

#Global variable PROG_START
PROG_START = 0

class ProgressUpdate:

    def __init__(self):
        self.progress_data = []
        self.latest_update = []
        self.main_thread = threading.current_thread()
        def _writeToFile(progress, latest_update):
            more_data = True
            while more_data:
                for  id_, (new_data, latest) in enumerate(zip(self.progress_data, self.latest_update)):
                    if not self.main_thread.is_alive():
                        more_data = False
                    file_name, time_diff, frame_count, video_len = new_data
                    file_name, last_c = latest
                    if last_c == frame_count:
                        continue
                    else:
                        self.latest_update[id_] = [file_name, frame_count]
                        progress = round(100*(frame_count/video_len), 1)
                        remaining_time = round((time_diff/frame_count)*(video_len-frame_count), 1)
                        estimated_time = round((time_diff/frame_count)*video_len, 1)
                        with  open(file_name, "w+") as progress_file:
                            progress_file.write(str(progress)+'\n')
                            progress_file.write(str(remaining_time)+'\n')
                            progress_file.write(str(estimated_time)+'\n')
                time.sleep(1)
               

        self.thread = threading.Thread(target=_writeToFile, args=(self.progress_data, self.latest_update))
        if not self.thread.is_alive():
            self.thread.start()


    def progress(self, file_name, time_diff, frame_count, video_len):
        for id_, item in enumerate(self.progress_data):
            file_, _, _, _ = item
            if file_name == file_:
                self.progress_data[id_] = [file_name, time_diff, frame_count, video_len]
                return
        self.progress_data.append([file_name, time_diff, frame_count, video_len])
        self.latest_update.append([file_name, -1])
        
 

def progressUpdate(file_name, time_diff, frame_count, video_len):
    global PROG_START
    if not isinstance(PROG_START, ProgressUpdate):
        print("Create progress tracker")
        PROG_START = ProgressUpdate()
    PROG_START.progress(file_name, time_diff, frame_count, video_len)

    
class Interface:

    def __init__(self, config):
        container_list = []
        # to disable the disclaimer display, set disclaimer=""
        self.disclaimer = config["disclaimer"] if "disclaimer" in config else defaultDisclaimer()
        self.command = config["job"]["command"] if "command" in config["job"] else ""
        self.output_type = config["job"]["output_type"]
        self.results_path = config["job"]["results_path"]
        if "results_defines" in config["job"]:
            self.results_defines = config["job"]["results_defines"]
            self.command = self.command.replace(self.results_defines, self.results_path)
        self.progress_list = config["job"]["progress_indicators"] if "progress_indicators" in config["job"] else None
        self.control_widgets = config["job"]["control_widgets"] if "control_widgets" in config["job"] else []
        if "plots" in config["job"]:
            self.plot = config["job"]["plots"]
            self.plot_button = widgets.Button(description='Plot results' , disabled=True, button_style='info')
            self.plot_img = widgets.HTML('')
            self.plot_disclaimer = widgets.HTML(self.disclaimer)
            container_list = [self.plot_button, self.plot_img, self.plot_disclaimer]
        else:
            self.plot = None
        self.status = widgets.HTML("No jobs submitted yet")
        self.submit = widgets.Button(description='Submit', disabled=False, button_style='info')
        self.submit.disabled = False if "inputs" in config else True
        self.input_ = []
        self.jobDict = {}
        self.tab = widgets.Tab()
        self.tab.children = []
        self.display_tab = False
        data=config["inputs"] if "inputs" in config else []
        self.container = widgets.VBox([self.status, self.tab]+container_list)


                      
        for item in data:
            for key, val in item.items():
                dict_ = {}
                name = key
                dict_['name'] = key
                if val['type'] == "select":
                    list_ = []
                    for x in val['options']:
                        list_.append(x['name'])
                    widget = widgets.Select(options=list_, description='', disabled=False, rows=len(list_), layout = Layout(width='auto'))
                    dict_["options"] = val["options"]
                elif val['type'] == "text":
                    widget = widgets.Text(value=val['default'], description="", layout = Layout(width='100%'), disabled=False)
                dict_['widget'] = widget
                dict_['type'] = val["type"]
                dict_['defines'] = val['defines'] 
                dict_['title'] = widgets.Label(val['display_name'])
                self.input_.append(dict_)

    def submitJob(self, command): 
        if isinstance(command, str):
            self.command = command
        else:
            command = self.command
        for widget in self.input_:

            value = widget["widget"].value
            if widget["type"] == "select":
                try:
                    defines_dict = next(item for item in widget["options"] if item['name'] == value)
                except:
                    self.status.value = "<span style='color:red'>&#9888;</span> Job submission failed, Invalid selection"
                    return

                if 'defines' in defines_dict:
                    for key2, val2 in defines_dict['defines'].items():
                        command = command.replace(key2, val2)
                elif "dummy" in defines_dict and defines_dict["dummy"] == "True":
                    self.status.value = "<span style='color:red'>&#9888;</span> Job submission failed, {}".format(defines_dict['name'])
                    return
            else:    
                for item in widget['defines']:
                    command = command.replace(item, value) 
        if not command in self.jobDict.keys():
            self.jobDict[command] = {}
            self.jobDict[command]['box_id'] = None
        elif self.jobStillRunning(command):
            self.status.value = "<span style='color:red'>&#10008;</span> Unable to submit: another job with the same arguments is still running"
            return

        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, error = p.communicate()
        jobid = output.decode("utf-8").rstrip().split('.')[0]
        if jobid != "":
            self.status.value = "<span style='color:green'>&#10004;</span> Job submitted, job ID: {jobid}".format(jobid=jobid)
        else:
            self.status.value = "<span style='color:red'>&#9888;</span> Job submission failed"
            del self.jobDict[command]
            return

        self.jobDict[command]['jobid'] = jobid 
        std_path = self.results_path+jobid
        if not os.path.isdir(std_path):
            os.makedirs(std_path, exist_ok=True)
        command2 = "qalter -o {outpath} -e {errorpath} {jobid}".format(outpath=std_path+"/stdout", errorpath=std_path+"/stderr", jobid=jobid)
        p2 = subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
        output2,_ = p2.communicate()
        self.jobDict[command]['selector'] = {}
        for item in self.input_:
            self.jobDict[command]['selector'][item['title'].value] = item['widget'].value
        self.jobDict[command]['output_path'] = self.results_path+jobid
        self.outputDisplay(jobid, command, 0, 100)
        if self.plot:
            self.plot_button.on_click(self.summaryPlot)

    def displayUI(self):
        n_widgets = []
        for widget in self.input_:
            n_widgets.append(widgets.VBox([widget['title'], widget['widget']]))
        UI = widgets.VBox(n_widgets)
        display(UI)        
        if not self.submit.disabled:
            display(self.submit)
        display(self.container)

        def on_value_change(change):
            controller = next(widget for widget in self.input_ if widget['widget'].description == change['owner'].description) 
            selected = next( option for option in controller['options'] if option['name'] == change['new'])
            for key, val in selected['controls'].items():
                controlled = next(widget for widget in self.input_ if widget['name'] == key)
                controlled['widget'].options = val

        for widget in self.input_:
            if widget['type'] == 'select':
                for item in widget['options']:
                    observer = True if 'controls' in item else False
                widget['observer'] = observer
            if 'observer' in widget and widget['observer']:
                widget['widget'].observe(on_value_change, 'value') 
        def wrapSubmit(event):
            self.submitJob(self.command)
                
        self.submit.on_click(wrapSubmit)

    def liveOutputMonitor(self, job_id, output_widget, command):
        op_cmd = [f'qpeek {job_id}']

        def _work(output_widget, op_cmd, command):
            while command in self.jobDict and self.jobStillRunning(command):
                p = subprocess.Popen(op_cmd, stdout=subprocess.PIPE, shell=True)
                output,_ = p.communicate()
                if output != b'':
                    output_widget.value=''' {new_op} '''.format(new_op = output.decode().replace('\n', '<br>'))
                time.sleep(5.0)
            while command in self.jobDict and not  os.path.exists(f"{self.jobDict[command]['output_path']}/stdout"):
                time.sleep(1.0)
            if command in self.jobDict:
                with open (f"{self.jobDict[command]['output_path']}/stdout", "r") as f:
                    output_widget.value=''' {new_op} '''.format(new_op = f.read().replace('\n', '<br>'))

        thread = threading.Thread(target=_work, args=(output_widget, op_cmd, command))
        thread.start()

    def outputDisplay(self, jobid, command, min_, max_):
        '''
        Progress indicator reads first line in the file "path" 
        jobid: id of the job submitted
        command: qsub command 
        min_: min_ value for the progress bar
        max_: max value in the progress bar
        '''
        progress_info = []
        progress_wid = []
        path = self.results_path+jobid
        style = {'description_width': 'initial'}
        title = widgets.HTML("")
        if self.progress_list:
            for item in self.progress_list:
                progress_info.append(path+'/'+item['file_name'])
                progress_wid.append(widgets.FloatProgress(value=min_, min=min_, max=max_, description=item["title"], bar_style='info', orientation='horizontal', style=style))
                progress_wid.append(widgets.HTML(value='...waiting to start', placeholder='0', description='', style=style))  #Estimated time
                progress_wid.append(widgets.HTML(value='', placeholder='0', description='', style=style))            #Remaining time

            for name in progress_info:
                f = open(name, "w")
                f.close()
        def _work():
            box_layout = widgets.Layout(display='flex', flex_flow='column', align_items='stretch', border='ridge', width='100%', height='')
            frame_layout = widgets.Layout(display='flex', flex_flow='column', align_items='stretch', border='', width='100%', height='')
            table = '''<table><style type="text/css" scoped>td{ padding:5px; border: 1px solid #9e9e9e; line-height:1.2em;}td:first-child{font-weight:bold;}</style><tbody>'''
            for item in self.input_:
                table += '''<tr><td>{name}</td><td>{value}</td></tr>'''.format(name=item['title'].value, value=item['widget'].value)
            table += '''<tr><td>Submission command</td><td>{command}</td></tr>'''.format(command=command)
            table += '''</tbody></table>'''
            title = widgets.HTML(value = '''{table}'''.format(table=table))
            op_monitor = widgets.HTML(value='', layout={'width': '100%', 'height': 'auto', 'border': '1px solid gray'})
            op_display_button = widgets.Button(description='Display output', disabled=True, button_style='info')
            op_display = widgets.HTML(value='')
            control_widgets = []
            from .control_widgets import ControlWidget
            for item in self.control_widgets:
                wid = ControlWidget(item, self.jobDict, self, command).button
                control_widgets.append(wid)

            if self.output_type == "live":
                self.liveOutputMonitor(jobid, op_monitor, command)
                op_list = [op_monitor]
            else:
                op_list = [op_display_button, op_display]
            
            widget_list = [title]+progress_wid+op_list+control_widgets

            if self.jobDict[command]['box_id'] == None:
                frame = widgets.HBox(widget_list, layout=frame_layout)
                cur_tabs = list(self.tab.children)
                cur_tabs.append(frame)
                self.tab.children = tuple(cur_tabs)
                self.tab.set_title(str(len(self.tab.children)-1),  '{jobid}'.format(jobid=jobid))
                frame_id = len(self.tab.children)-1
                self.jobDict[command]['box_id'] = frame_id
                self.tab.selected_index = frame_id
            else:
                frame_id = self.jobDict[command]['box_id']
                frame = self.tab.children[frame_id]
                #output.value = ""
                op_display_button.disabled=True
                frame.children = widget_list
                self.tab.set_title(str(frame_id), '{jobid}'.format(jobid=jobid))
                self.tab.selected_index = frame_id
            # progress
            id_ = 0
            self.tab.set_title(str(frame_id), 'Queued: {jobid}'.format(jobid=jobid))
            cmd = "qstat | grep "+jobid
            running = False
            while not running:
                p = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
                output,_ = p.communicate()
                stat = output.decode("utf-8").rsplit()
                running = True if 'R' in stat else False
 
            self.tab.set_title(str(frame_id), 'Running: {jobid}'.format(jobid=jobid))
            for output_file in progress_info: 
                progress_bar =  progress_wid[id_]
                est_time =  progress_wid[id_+1]
                remain_time =  progress_wid[id_+2]
                last_status = 0.0
                remain_val = '0'
                est_val = '0'
                while last_status < 100:
                    if os.path.isfile(output_file):
                        with open(output_file, "r") as fh:
                            line1 = fh.readline()     #Progress 
                            line2 = fh.readline()      #Remaining time
                            line3 = fh.readline()      #Estimated total time
                            if line1 and line2 and line3:
                                last_status = float(line1)
                                remain_val = line2
                                est_val = line3
                            progress_bar.value = last_status
                            if remain_val > '0':
                                remain_time.value = 'Remaining: {} seconds'.format(remain_val)
                                est_time.value = 'Total estimated: {} seconds'.format(est_val) 
                            else:
                                remain_time.value = '...waiting to start' 
                    else:
                        cmd = ['ls']
                        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                        output,_ = p.communicate()
                    time.sleep(0.1)
                remain_time.value = 'Done' 
                os.remove(output_file)
                id_ += 3

            while command in self.jobDict and  self.jobStillRunning(command):
                time.sleep(3) 
            if self.plot:
                self.plot_button.disabled=False
            self.tab.set_title(str(frame_id), 'Done: {jobid}'.format(jobid=jobid))
            op_display_button.disabled=False
            def wrapHTML(event):
                op_display.value = self.outputHTML(path)

            op_display_button.on_click(wrapHTML)

        thread = threading.Thread(target=_work, args=())
        thread.start()
        time.sleep(0.1)


    def jobStillRunning (self, command):
        ''' Input: command
            Return: True if job still running, false if job terminated
        '''
        cmd = 'qstat '+self.jobDict[command]['jobid']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        output,_ = p.communicate()
        return output.decode("utf-8").rstrip() != ''

    def outputHTML(self, result_path):
        '''
        device: tuple of edge and accelerator
        '''
        op_list = []
        stats = result_path+'/stats.json'
        for file_ in os.listdir(result_path):
            if file_.endswith(self.output_type):
                op_list.append(file_)
        if os.path.isfile(stats):
            with open(stats) as f:
                data = json.load(f)
            time = data['time']
            frames = data['frames']
            stats_line = "<p>{frames} frames processed in {time} seconds</p>".format(frames=frames, time=time)
        else:
            stats_line = ""
        string = ""
        height = '480' if len(op_list) == 1 else '240'
        if self.output_type == ".mp4":
            for x in op_list:
                op_vid = '/user/{user_id}/files/{wd_path}/{rd_path}/{file_}'.format(user_id=pwd.getpwuid(os.getuid()).pw_name, wd_path=os.getcwd().split('/', 3)[3], rd_path=result_path, file_=x)
                string += "<video alt=\"\" controls autoplay height=\"{height}\"><source src=\"{op}\" type=\"video/mp4\" /></video>".format(op=op_vid, height=height)
        elif self.output_type == ".png":
            for x in op_list:
                op_img = '/user/{user_id}/files/{wd_path}/{rd_path}/{file_}'.format(user_id=pwd.getpwuid(os.getuid()).pw_name, wd_path=os.getcwd().split('/', 3)[3], rd_path=result_path, file_=x)
                string += "<img src='{img}' width='783' height='{height}'>".format(img=op_img, height=height)
        elif self.output_type == ".txt":
            for x in op_list:
                op_txt = os.path.join(result_path, x)
                with open(op_txt, 'r') as f:
                    string += str(f.readlines())

        return '''<h2></h2>
                    {stats_line}
                    {op}
                    '''.format(op=string, stats_line=stats_line)
                    

    def summaryPlot(self, event):
        ''' Bar plot input:
           x_axis: label of the x axis
           y_axis: label of the y axis
           title: title of the graph
        '''
        
        warnings.filterwarnings('ignore')
        clr = 'xkcd:blue'
        html = '''<html><body>'''
        for item in self.plot: 
            fig = plt.figure(figsize=(15, 7))
            title = item['title']
            type = item['type']
            y_axis = item['ylabel'] if 'ylabel' in item else None 
            x_axis = item['xlabel'] if 'xlabel' in item else None 
            selector = item['selector'] if 'selector' in item else None 
            plt.title(title , fontsize=20, color='black', fontweight='bold')
            plt.ylabel(y_axis, fontsize=16, color=clr)
            plt.xlabel(x_axis, fontsize=16, color=clr)
            val = []
            arch = {}
            diff = 0

            for key, val in self.jobDict.items():
                job = self.jobDict[key]
                path = os.path.join(val['output_path'], 'stats.json')
                if selector:
                    label = ''
                    for list_item in selector:
                        label += val['selector'][list_item] + '\n'
                    label += "Job ID: "+val['jobid']
                else :
                    label = "Job ID: "+val["jobid"]
                if os.path.isfile(path) and not self.jobStillRunning(key):
                    with open(path, "r") as f:
                        data = json.load(f)
                    value = float(data[type])
                    arch[label] = round(value, 2)

            if len(arch) < 5:
                rotation=0
                align="center"
            else:
                rotation=45
                align="right"
            plt.xticks(fontsize=16, rotation=rotation, rotation_mode='anchor', horizontalalignment=align)
            plt.yticks(fontsize=16)
            if len(arch) != 0:
                # set offset
                max_val = max(arch.values()) 
                offset = max_val/100
                plt.ylim(top=(max_val+20*offset))
                for dev, val in arch.items():
                    y = val+offset
                    plt.text(diff, y, val, fontsize=14, multialignment="center",horizontalalignment="center", verticalalignment="bottom",  color='black')
                    diff += 1
                    plt.bar(dev, val, width=0.5, align='center', label=dev, color=clr)
                imgdata = io.BytesIO()
                plt.tight_layout()
                fig.savefig(imgdata, format='png')
                html += '''<img src="data:image/png;base64,{}"/>'''.format(base64.encodebytes(imgdata.getvalue()).decode()) 
                plt.close()
            else:
                plt.close()
        html += '''</body></html>'''
        self.plot_img.value = html
