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
import os 
import warnings
import json
import random
import io
import urllib, base64
import urllib.parse

def progressUpdate(file_name, time_diff, frame_count, video_len):
        progress = round(100*(frame_count/video_len), 1)
        remaining_time = round((time_diff/frame_count)*(video_len-frame_count), 1)
        estimated_time = round((time_diff/frame_count)*video_len, 1)
        with  open(file_name, "w") as progress_file:
            progress_file.write(str(progress)+'\n')
            progress_file.write(str(remaining_time)+'\n')
            progress_file.write(str(estimated_time)+'\n')
    
class Demo:

	def __init__(self, config):
		self.jobDict = {}
		self.input_ = {}
		self.jobscript = config["jobs"]["script"]
		self.tab = widgets.Tab()
		self.plot_button = widgets.Button(description='Plot results' , disabled=True, button_style='info')
		self.plot_img = widgets.HTML('')

		self.tab.children = []
		self.display_tab = False
		index=0
		data=config["inputs"]
		self.results = config["jobs"]["results_path"].split()[1]
		self.results_prefix = config["jobs"]["results_path"].split()[0]
		self.summary_plot = config["jobs"]["plot_details"]
		self.plot_selector = config["jobs"]["plot_selector"]
		self.progress_list = config["jobs"]["progress_indicator"]
		self.output_plot = widgets.Output()
		for item in data:
			for key, val in item.items():
				self.input_[key] = {}
				if val['type'] == "select":

					list_ = []
					dict_ = {}
					for x in val['options']:
						list_.append(x['display_name'])
						dict_[x['display_name']] = {}
						dict_[x['display_name']]['args'] = x['arguments']
						dict_[x['display_name']]['torque'] = x['properties']
					select_wid = widgets.Select(options=list_, description='', disabled=False, rows=len(list_), layout = Layout(width='fixed'))
					self.input_[key]['index'] = index
					self.input_[key]['widget'] = select_wid
					self.input_[key]['type'] = 'select'
					self.input_[key]['prefix'] = val['prefix'] 
					self.input_[key]['title'] = widgets.Label(val['display_name'])
					self.input_[key]['value'] = dict_
				elif val['type'] == "text":
					text_wid = widgets.Text(value=val['default'], description="", layout = Layout(width='100%'), disabled=False)
					self.input_[key]['index'] = index
					self.input_[key]['widget'] = text_wid
					self.input_[key]['type'] = 'text'
					self.input_[key]['prefix'] = val['prefix'] 
					self.input_[key]['title'] = widgets.Label(val['display_name'])
					self.input_[key]['value'] = val['default']
				index += 1
	                               

	def displayUI(self):
		n_widgets = list(range(len(self.input_)))
		for key, val in self.input_.items():
			n_widgets[val['index']] = widgets.VBox([val['title'], val['widget']])
		UI = widgets.VBox(n_widgets)
		display(UI)		
		status = widgets.HTML("")
		submit = widgets.Button(description='Submit', disabled=False, button_style='info')
		display(status)
		display(submit)
		def submitJob(event): 
			command = "qsub {script} ".format(script=self.jobscript)
			torq = "-l nodes=1:"
			args = ""
			for key, val in self.input_.items():
				if val['type'] == "select":
					args += val['prefix']+val['value'][val['widget'].value]['args']+" "
					torq += val['value'][val['widget'].value]['torque']
				elif val['type'] == "text":
					args += val['prefix']+val['widget'].value+" "
			command += " {torq} -F \" {args} {prefix} {results}\"".format(torq=torq, args=args, prefix=self.results_prefix, results=self.results)
			if not command in self.jobDict.keys():
				self.jobDict[command] = {}
				self.jobDict[command]['box_id'] = None
			elif self.jobStillRunning(command):
				status.value = "<span style='color:red'>&#10008;</span> Unable to submit: another job with the same arguments is still running"
				return

			p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
			output,_ = p.communicate()
			jobid = output.decode("utf-8").rstrip()
			self.jobDict[command]['jobid'] = jobid 
			std_path = self.results+jobid
			command2 = "qalter -o {outpath} -e {errorpath} {jobid}".format(outpath=std_path+"/stdout", errorpath=std_path+"/stderr", jobid=jobid)
			p2 = subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
			output2,_ = p2.communicate()
			self.jobDict[command]['selector'] = {}
			for key, val in self.input_.items():
				self.jobDict[command]['selector'][val['title'].value] = val['widget'].value
			self.jobDict[command]['output_path'] = self.results+jobid
			if output != "":
				status.value = "<span style='color:green'>&#10004;</span> Job submitted, job ID: {jobid}".format(jobid=jobid)
			else:
				status.value = "<span style='color:red'>&#9888;</span> Job submission failed"
				return

			self.progressIndicator(jobid, command, 0, 100)
			self.plot_button.on_click(self.summaryPlot)

		submit.on_click(submitJob)

	def progressIndicator(self, jobid, command, min_, max_):
		'''
		Progress indicator reads first line in the file "path" 
		jobid: id of the job submitted
		command: qsub command 
		min_: min_ value for the progress bar
		max_: max value in the progress bar
		'''
		prog_list = []
		path = self.results+jobid
		for item in self.progress_list:
			prog_list.append((path+'/'+item['file name'], item['title']))
		style = {'description_width': 'initial'}
		title = widgets.HTML("")
		progress_bar_1 = widgets.FloatProgress(
			 value=min_,
			 min=min_,
			 max=max_,
			 description='',
			 bar_style='info',
			 orientation='horizontal',
			 style=style
		 )
		remain_time_1 = widgets.HTML(
			 value='...waiting to start',
			 placeholder='0',
			 description='',
			 style=style
		 )
		est_time_1 = widgets.HTML(
			 value='',
			 placeholder='0',
			 description='',
			 style=style
		 )
		progress_bar_2 = widgets.FloatProgress(
			 value=min_,
			 min=min_,
			 max=max_,
			 description='',
			 bar_style='info',
			 orientation='horizontal',
			 style=style
		 )
		remain_time_2 = widgets.HTML(
			 value='...waiting to start',
			 placeholder='',
			 description='',
			 style=style
		 )
		est_time_2 = widgets.HTML(
			 value='',
			 placeholder='0',
			 description='',
			 style=style
		 )
		op_display = widgets.Button(
			 description='Display output',
			 disabled=True,
			 button_style='info' 
		 )
		op_video = widgets.HTML(
			 value='',
			 placeholder='',
			 description='',
			 style=style
		 )

		#Check if results directory exists, if not create it and create the progress data file 
		if not os.path.isdir(path):
			os.makedirs(path, exist_ok=True)
		file_name = [] 
		for name, title in prog_list:
			f = open(name, "w")
			f.close()
		
		def _work():
			box_layout = widgets.Layout(display='flex', flex_flow='column', align_items='stretch', border='ridge', width='100%', height='')
			frame_layout = widgets.Layout(display='flex', flex_flow='column', align_items='stretch', border='', width='100%', height='')
			widget_list = []
			table = '''<table><style type="text/css" scoped>td{ padding:5px; border: 1px solid #9e9e9e; line-height:1.2em;}td:first-child{font-weight:bold;}</style><tbody>'''
			for i in range(len(self.input_.items())):
				val = next((val for key, val in self.input_.items() if val['index'] == i))
				table += '''<tr><td>{name}</td><td>{value}</td></tr>'''.format(name=val['title'].value, value=val['widget'].value)
			table += '''<tr><td>Submission command</td><td>{command}</td></tr>'''.format(command=command)
			table += '''</tbody></table>'''
			title = widgets.HTML(value = '''{table}'''.format(table=table))
			progress_bar_1.description = prog_list[0][1]
			if len(prog_list) > 1:
				progress_bar_2.description = prog_list[1][1]
				widget_list = [title, progress_bar_1, est_time_1, remain_time_1, progress_bar_2, est_time_2, remain_time_2, op_display, op_video]
			else:
				widget_list = [title, progress_bar_1, est_time_1, remain_time_1, op_display, op_video]

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
				prev_frame = list(frame.children)
				for item in prev_frame:
					item.close()
				frame.children = widget_list
				self.tab.set_title(str(frame_id), '{jobid}'.format(jobid=jobid.split(".")[0]))
				self.tab.selected_index = frame_id
			if not self.display_tab: 
				display(self.tab)
				display(self.plot_button)
				display(self.plot_img)
				self.display_tab = True
			# progress
			id_ = 1
			self.tab.set_title(str(frame_id), 'Queued: {jobid}'.format(jobid=jobid.split(".")[0]))
			for output_file, title in prog_list: 
				progress_bar =  widget_list[id_]
				est_time =  widget_list[id_+1]
				remain_time =  widget_list[id_+2]
				last_status = 0.0
				remain_val = '0'
				est_val = '0'
				while last_status < 100:
					if os.path.isfile(output_file):
						with open(output_file, "r") as fh:
							line1 = fh.readline() 	#Progress 
							line2 = fh.readline()  	#Remaining time
							line3 = fh.readline()  	#Estimated total time
							if line1 and line2 and line3:
								last_status = float(line1)
								remain_val = line2
								est_val = line3
							progress_bar.value = last_status
							if remain_val > '0':
								self.tab.set_title(str(frame_id), 'Running: {jobid}'.format(jobid=jobid.split(".")[0]))
								remain_time.value = 'Remaining: '+remain_val+' seconds' 
								est_time.value = 'Total estimated: '+est_val+' seconds' 
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
			op_display.disabled=False
			self.plot_button.disabled=False
			self.tab.set_title(str(frame_id), 'Done: {jobid}'.format(jobid=jobid.split(".")[0]))
			def wrapVideoHTML(event):
				op_video.value = self.videoHTML(path)
			op_display.on_click(wrapVideoHTML)

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

	def videoHTML(self, result_path):
		'''
		device: tuple of edge and accelerator
		'''
		videos_list = []
		stats = result_path+'/stats.json'
		for vid in os.listdir(result_path):
			if vid.endswith(".mp4"):
				videos_list.append(result_path+'/'+vid)
		if os.path.isfile(stats):
			with open(stats) as f:
				data = json.load(f)
			time = data['time']
			frames = data['frame']
			stats_line = "<p>{frames} frames processed in {time} seconds</p>".format(frames=frames, time=time)
		else:
			stats_line = ""
		video_string = ""
		height = '480' if len(videos_list) == 1 else '240'
		for x in range(len(videos_list)):
			video_string += "<video alt=\"\" controls autoplay height=\""+height+"\"><source src=\""+videos_list[x]+"\" type=\"video/mp4\" /></video>"
		output ='''{stats_line}{videos}'''.format(videos=video_string, stats_line=stats_line)
		return output



	def summaryPlot(self, event):
		''' Bar plot input:
		   x_axis: label of the x axis
		   y_axis: label of the y axis
		   title: title of the graph
		'''
		warnings.filterwarnings('ignore')
		clr = 'xkcd:blue'
		html = '''<html><body>'''
		for item in self.summary_plot: 
			fig = plt.figure(figsize=(15, 5))
			plot = list(item.keys())[0]
			title = item[plot]['title']
			y_axis = item[plot]['ylabel'] if 'ylabel' in item[plot] else plot 
			x_axis = item[plot]['xlabel'] if 'xlabel' in item[plot] else self.plot_selector 
			plt.title(title , fontsize=20, color='black', fontweight='bold')
			plt.ylabel(y_axis, fontsize=16, color=clr)
			plt.xlabel(x_axis, fontsize=16, color=clr)
			val = []
			arch = {}
			diff = 0
			for key, val in self.jobDict.items():
				job = self.jobDict[key]
				path = os.path.join(val['output_path'], 'stats.json')
				label = val['selector'][self.plot_selector]
				if os.path.isfile(path) and not self.jobStillRunning(key):
					with open(path, "r") as f:
						data = json.load(f)
					value = float(data[plot])
					arch[label] = round(value)
					f.close()
			if len(arch) <= 9:
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
				plt.ylim(top=(max_val+10*offset))
				for dev, val in arch.items():
					y = val+offset
					plt.text(diff, y, val, fontsize=14, multialignment="center",horizontalalignment="center", verticalalignment="bottom",  color='black')
					diff += 1
					plt.bar(dev, val, width=0.5, align='center', label = dev, color=clr)
				imgdata = io.BytesIO()
				plt.tight_layout()
				fig.savefig(imgdata, format='png')
				html += '''<img src="data:image/png;base64,{}"/>'''.format(base64.encodebytes(imgdata.getvalue()).decode()) 
				plt.close()
			else:
				plt.close()
		html += '''</body></html>'''
		self.plot_img.value = html
