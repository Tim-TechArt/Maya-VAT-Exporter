# Maya-VAT-Exporter
Exports Vertex Animation Texture from Maya

Developed for Maya 2023 using PyMEL for interacting with Maya, Pillow to write data to DDS


## Key Features 
* 8bit RGBA DDS format
* Utilizes header information in DDS
  - First Header Pixel
    - R Channel: Number of Frames
    - G Channel: FPS
  - Second & Third Header Pixel
    - Calculated min and max position of animation to always have optimized scale value for vertex positions
* Allways honnor power of two texture with padding
* Split up Vertex index and saves it in vertex color channel R & G to manage a total of 65535 vertecies
* Uses relative positions from first frame
* 

## Dependencies:


  ### PyMEL:

  To site-packages:	
  
    mayapy -m pip install pymel
  To your user space:	
  
    mayapy -m pip install --user pymel
  
  See PyMEL Installing and importing documentation: https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-2AA5EFCE-53B1-46A0-8E43-4CD0B2C72FB4



  ### Pillow

    cd C:\Program Files\Autodesk\Maya2023\bin
    mayapy -m pip install Pillow
  See Pillow Installation documentation: https://pillow.readthedocs.io/en/latest/installation.html


  
## How-To
