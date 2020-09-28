
def jsonValidate(config):
    op_supported =  ['live', '.jpg', '.png', '.mp4', '.avi', '.txt', '.e', '.o', '.mov', '.bmp']
    #Vaidate required inputs: output_type, results_path
    if "results_path" not in config['job']:
        err = "Missing results path"
        return False, err

    if "output_type" not in config['job']:
        err = f"Missing results file extension. Set the output_type to one of the following: {op_supported}"
        return False, err

    #Validate output type [live, .jpg, .png, .mp4, .avi, .txt, .e, .o, .mov, .bmp] 
    if config['job']['output_type'] not in op_supported:
        err = f"The output type {config['job']['output_type']} is not supported. The supported output file extensions: {op_supported}"
        return False, err

    #Validate "control_widgets": ["cancel_job", "telemetry"]
    control_wid_supported = ["cancel_job", "telemetry"]
    if "control_widgets" in config['job']:
        for widget in config['job']['control_widgets']: 
            if widget not in control_wid_supported:
                err = f"Unsupported control widget {widget}"
                return False, err

    return True, ""

