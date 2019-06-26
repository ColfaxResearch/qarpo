
# The default path for the job is your home directory, so we change directory to where the files are.
cd $PBS_O_WORKDIR
mkdir -p $1

OUTPUT_FILE=$1
DEVICE=$2
FP_MODEL=$3


if [ "$2" = "HETERO:FPGA,CPU" ]; then
    # Environment variables and compilation for edge compute nodes with FPGAs
    export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/altera/aocl-pro-rte/aclrte-linux64/
    source /opt/fpga_support_files/setup_env.sh
    aocl program acl0 /opt/intel/computer_vision_sdk/bitstreams/a10_vision_design_bitstreams/5-0_PL1_FP11_MobileNet_Clamp.aocx
fi
# Running the object detection code
SAMPLEPATH=$PBS_O_WORKDIR
python3 app/classification_sample.py  -m app/model/${FP_MODEL}/crnn.xml  \
                                           -i app/board4.jpg \
                                           -o $OUTPUT_FILE \
                                           -d $DEVICE
                                           
