
# Forward

Initially a custom experimental tool to make sure I wasn't running into conceptual or implementation bugs for an RL idea, I am currently in the process of turning it into a more general tool for rapidly throwing together no-frills interfaces in Python.

The idea is to make it easy for researchers to generate exploratory UIs to aid in the development of data analysis and machine learning ideas.

See a live version [here](http://ec2-54-176-62-21.us-west-1.compute.amazonaws.com).

## Use

Run `./interface.sh` in the interface folder. The script builds a Docker image, which may take several minutes the first time, and instantiates a throwaway container in which it runs the server. The system expects roms in the interface/roms folder.
