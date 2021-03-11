import qarpo
from PIL import Image
from time import time
import os
import json
from argparse import ArgumentParser

def build_argparser():
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", help="Path to a folder with images or path to an image files", required=True,
                        type=str, nargs="+")
    parser.add_argument("-o", "--output_dir", help="If set, it will write a video here instead of displaying it",
                        default=None, type=str)
    return parser

args = build_argparser().parse_args()
job_id = os.environ['PBS_JOBID'].split('.')[0]
result_dir = os.path.join(args.output_dir, job_id)
progress_file_path = os.path.join(result_dir, 'i_progress.txt')
if not os.path.isdir(result_dir):
    print(result_dir)
    os.makedirs(result_dir, exist_ok=True)
print(args.input)
input_img = Image.open(args.input[0])
width, height = input_img.size
op_height, op_width = height//2, width//2
print(width, height, op_width, op_height)
total_op_imgs = 4
img_num = 0
t0 = time()
for i in range(0,height,op_height):
    for j in range(0, width, op_width):
            print(i, j)
            img_num +=1
            qarpo.progressUpdate(progress_file_path, time()-t0, img_num, total_op_imgs)
            box = (j, i, j+op_width, i+op_height)
            a = input_img.crop(box)
            print("image cropped")
            a.save(os.path.join(result_dir, f"IMG_{img_num}.png"))
            
t1 = time()-t0     
stats = {}
stats['time'] = str(round(t1, 1))
stats['frames'] = str(img_num)
stats['fps'] = str(img_num / t1)
stats_file = result_dir+"/stats.json"
with open(stats_file, 'w') as f:
    json.dump(stats, f)            
