
# Forward

Initially a custom experimental tool to make sure I wasn't running into conceptual or implementation bugs for an RL frame dimensionality reduction idea, I am currently in the process of turning it into a more general tool for rapidly throwing together no-frills interfaces with Python.

The idea is to make it simple for researchers to generate exploratory UIs to help debug, inspect, investigate, and develop data analysis and machine learning ideas.

See a live version [here](http://ec2-54-176-62-21.us-west-1.compute.amazonaws.com).

## Use

Run `./interface.sh` in the interface folder. The script builds a Docker image, which may take several minutes to run the first time, and instantiates a throwaway container in which it runs the server. The system expects roms in the interface/roms folder.
