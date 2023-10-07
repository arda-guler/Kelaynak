# Kelaynak
6-degrees-of-freedom flight simulator in Python using OpenGL.

https://github.com/arda-guler/Kelaynak/assets/80536083/e1346a53-d37a-4e39-ba81-9e22fa5de809

## Requirements
glfw==2.5.5

keyboard==0.13.5

numpy==1.24.2

pygame==2.1.2

PyOpenGL==3.1.6

scipy==1.9.1

## How To Use
Run **main.py** to start with a premade aircraft on a premade scene in first person view. 

Edit **main.py** to create your own aircraft or switch to third person view. (Examples are present within the file.)

Edit **rigidbody.py** to create your own flight dynamics models (preferably by adding new classes, examples are present within the file.).

Add new models into **data/models/** to create your own vessels and scenery objects. (It has a custom but simple syntax, lines starting in 'V|' define vertices, lines starting in 'L|' define which vertices are connected by lines.)

*This documentation should be updated, but this is the best I can do at the moment.*
