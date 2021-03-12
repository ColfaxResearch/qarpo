Qarpo library provides a jupyter notebook user interface to provide the following:


1- Submit jobs to node in a cluster  
2- Track progress of jobs running  
3- Display job's output results  
4- Plot metric results for the completed jobs  

For more details about how to use qarpo in your jupyter notebook, check qarpo/Examples.  

How to generate a .whl file and install qarpo library:  


run:  
    cd qarpo    
    python3 setup.py sdist bdist_wheel    
    pip3 install <path to qarpo>/dist/<generated .whl file>    


OR
run:  

    cd qarpo  
    make  
    pip3 install <path to qarpo>/dist/<generated .whl file>  
