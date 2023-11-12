import pymel.core as pm
from PIL import Image
from PIL import ImagePalette
from PIL import ImageShow
import os
import struct
import time
import math

#----------------------------------------------------------------

""" Switches """
""" Mode Selected Meshes or All Meshes in scene """
Selected_Meshes = True

""" Global Wars """
X = 0
Y = 1
Z = 2

""" Functions """

def remap(xMin, xMax, yMin, yMax, t):
    return yMin + (yMax - yMin) * ((t - xMin) / (xMax - xMin))


""" Selects all the meshes in the scene """    
def select_all_meshes():
    mesh_list = pm.ls(type = "mesh")
    for mesh in mesh_list:
        mesh.select(add=True, ado=True)    


""" Returns a list of all meshes in the scene """    
def get_list_of_all_meshes():
    mesh_list = pm.ls(type = "mesh", references=False)
    mesh_no_ref_list = [mesh for mesh in mesh_list if mesh.find('Orig') < 1]
    return mesh_no_ref_list  

""" Returns a list of all selected meshes in the scene """   
def get_list_of_selected_meshes():
    mesh_list = pm.ls(sl = True)
    return mesh_list


""" Returns a list of all CTRL nurbs in scene """
def get_list_of_all_ctrl_nurbs():
    nurbs_shape_list = pm.ls(type = "nurbsCurve")
    ctrl_list = [nurbs.getParent() for nurbs in nurbs_shape_list if nurbs.find('_CTRL') > 0]
    return ctrl_list


""" Returns a list of keyframes from objects in list """
def get_list_of_keyframes(object_list):
    pm.select(clear = True)
    for object in object_list:
        object.select(add=True)
    time_min = pm.playbackOptions(q=True, min=True)
    time_max = pm.playbackOptions(q=True, max=True)
    list_of_keyframes = sorted(list(dict.fromkeys(pm.keyframe(q=True, time=(time_min, time_max)))))  
    pm.select(clear = True)
    return list_of_keyframes


""" Make sense of the currentUnit query command """
def demystify(fpsQuery):
    daFPS = 0
    if fpsQuery == "game": daFPS = 15
    elif fpsQuery == "film": daFPS = 24    
    elif fpsQuery == "pal": daFPS = 25
    elif fpsQuery == "ntsc": daFPS = 30
    elif fpsQuery == "show": daFPS = 48
    elif fpsQuery == "palf": daFPS = 50
    elif fpsQuery == "ntscf": daFPS = 60
    else: daFPS = int(round(float(fpsQuery[:len(fpsQuery)-3])))
    return daFPS
    

""" Returns a list of all the vertecies positions from a list of meshes """
def get_list_of_vertex_positions(mesh_list):
    vtx_pos = []
    for mesh_index, mesh in enumerate(mesh_list):   
        for vtx_index, vtx in enumerate(mesh.vtx):
            pos = vtx.getPosition(space="world")
            vtx_pos.append(pos)
    return vtx_pos    


""" Returns the next n^2 of n """
def get_next_power_of_2(n):
    if n == 0:
        return 1
    if n & (n - 1) == 0:
        return n
    while n & (n - 1) > 0:
        n &= (n - 1)
    return n << 1

    
""" Write "global" vertex index in all meshes vertecies in mesh_list to the red and green vertex color channels """    
def write_vertex_index_to_vertex_color(mesh_list):
    global_vtx_index = 0
    pm.currentTime(0)
    for mesh_index, mesh in enumerate(mesh_list): 
      
        for vtx_index, vtx in enumerate(mesh.vtx):           
            y1, y2, y3, y4 = (global_vtx_index & 0xFFFFFFFF).to_bytes(4, 'big')
            vtx.select()
            y3 = remap(0, 255, 0, 1, y3)
            y4 = remap(0, 255, 0, 1, y4)
            pm.polyColorPerVertex(r=(y3), g=(y4), cdo=True)
            global_vtx_index += 1


""" Returns min and max of relative positions """
def get_min_max_of_relative_positions(mesh_list, time_stamps, margin):
    vtx_orig_pos = []

    pos_max = 0
    pos_min = 0    
    pm.currentTime(time_stamps[0])
    
    """ Original vtx positions """
    for mesh_index, mesh in enumerate(mesh_list):   
        for vtx_index, vtx in enumerate(mesh.vtx):
            pos = vtx.getPosition(space="world")
            vtx_orig_pos.append(pos)        

    for key_frame in range(0,len(time_stamps)):
        pm.currentTime(time_stamps[key_frame])
        global_vtx_index = 0
        for mesh_index, mesh in enumerate(mesh_list):   
            for vtx_index, vtx in enumerate(mesh.vtx):
                pos = vtx.getPosition(space="world")
                pos_x, pos_y, pos_z = (pos-vtx_orig_pos[global_vtx_index])
                
                pos_max = max(pos_x, pos_y, pos_z, pos_max)
                pos_min = min(pos_x, pos_y, pos_z, pos_min)

                global_vtx_index += 1    
    

    pos_max = pos_max + margin
    pos_min = pos_min - margin        
    return pos_min, pos_max


""" Returns a power of 2 header list """
def create_header_list(number_of_frames, frame_rate, scale_min, scale_max, next_power_of_2):
    header_list = []
    
    """ Add no of frames to R channel of first pixel """    
    header_list.append(number_of_frames)
    
    """ Add Frame Rate to G channel of first pixel """
    header_list.append(frame_rate)
       
    
    """ Padd B & A channels in first pixel """    
    header_list.append(255)     
    header_list.append(255)
    
    """ Add scale_min and scale_max to second and third pixel """ 
    minBytes = bytearray(struct.pack("f", scale_min))
    maxBytes = bytearray(struct.pack("f", scale_max))  
    
    header_list.append(minBytes[0])
    header_list.append(minBytes[1])
    header_list.append(minBytes[2])            
    header_list.append(minBytes[3])
    
    header_list.append(maxBytes[0])
    header_list.append(maxBytes[1])
    header_list.append(maxBytes[2])            
    header_list.append(maxBytes[3])    
    
    """ Padd pixels if needed """
    padding_range = next_power_of_2 - int(len(header_list)/4)    
    for i in range(padding_range):
        header_list.append(0)
        header_list.append(255)
        header_list.append(255)
        header_list.append(0)
    
    return header_list

def make_diff():
    my_mesh = pm.ls(sl = True)
    print(my_mesh)
    diff = 0.007229555950445166
    pos_orig = []
    pos_new = [0,0,0]
    for mesh_index, mesh in enumerate(my_mesh):  
        print(mesh_index, mesh) 
        for vtx_index, vtx in enumerate(mesh.vtx):
            print(vtx_index, vtx)
            pos = vtx.getPosition(space="world")
            
            print(pos)
            if (vtx_index == 0): 
                pos_orig = vtx.getPosition(space="world")
                print("orig :",pos_orig)
            if (vtx_index == 1):
                print("Vertex 1")
                pos_new[X] = pos_orig[X] + diff
                pos_new[Y] = pos_orig[Y] + diff
                pos_new[Z] = pos_orig[Z] + diff
                vtx.setPosition(pos_new, space='world')
                
            if (vtx_index == 2):
                print("Vertex 2")
                pos_new[X] = pos_orig[X] + diff
                pos_new[Y] = pos_orig[Y] + diff
                pos_new[Z] = pos_orig[Z] + diff
                vtx.setPosition(pos_new, space='world')
                
            if (vtx_index == 3):
                print("Vertex 3")
                vtx.setPosition(pos_orig, space='world')
                
         
def append_vertex_positions_and_normals(header_list, mesh_list, time_stamps, scale_min, scale_max):

    header_length = int(len(header_list)/4)
    output_pos_list = []
    output_normal_list = []
    original_pos_list = []
    
    pm.currentTime(time_stamps[0])
    
    """ Original vtx positions """
    for mesh_index, mesh in enumerate(mesh_list):   
        for vtx_index, vtx in enumerate(mesh.vtx):
            pos = vtx.getPosition(space="world")
            original_pos_list.append(pos)  
    
    """ Go through every frame """
    first_frame = int(time_stamps[0])
    last_frame = int(time_stamps[-1])+1
    for frame in range(first_frame ,last_frame):
        global_vtx_index = 0
        pm.currentTime(frame)
        for mesh_index, mesh in enumerate(mesh_list):         
            for vtx_index, vtx in enumerate(mesh.vtx):  
            
                """ Get new position, calculate position difference and append scaled value """  
                pos = vtx.getPosition(space="world") 

                pos[X] = remap(scale_min, scale_max, 0, 255, pos[X] - original_pos_list[global_vtx_index][X])
                pos[Y] = remap(scale_min, scale_max, 0, 255, pos[Y] - original_pos_list[global_vtx_index][Y])
                pos[Z] = remap(scale_min, scale_max, 0, 255, pos[Z] - original_pos_list[global_vtx_index][Z])
                
                output_pos_list.append(int(round(pos[X])))
                output_pos_list.append(int(round(pos[Y])))
                output_pos_list.append(int(round(pos[Z])))           
                output_pos_list.append(255)                           
                
                """ Get vtx normal and append to next pixel """
                myNormal = vtx.getNormal('world')
                normalX = int(remap(-1, 1, 0, 65535, myNormal[X]))
                normalY = int(remap(-1, 1, 0, 65535, myNormal[Y]))
                                                                          
                """ X-Component """
                y1, y2, y3, y4 = (normalX & 0xFFFFFFFF).to_bytes(4, 'big')
                output_normal_list.append(y3)
                output_normal_list.append(y4)
                               
                """ Y-Component """
                y1, y2, y3, y4 = (normalY & 0xFFFFFFFF).to_bytes(4, 'big')
                output_normal_list.append(y3)
                output_normal_list.append(y4)

                global_vtx_index += 1
        
       
        padding_range = int(header_length - global_vtx_index)
        if (header_length > global_vtx_index):
            for i in range(padding_range):
                output_pos_list.append(255)
                output_pos_list.append(255)
                output_pos_list.append(0)
                output_pos_list.append(0) 
                output_normal_list.append(255)
                output_normal_list.append(255)
                output_normal_list.append(0)
                output_normal_list.append(0)
       
    return header_list + output_pos_list + output_normal_list               


""" Returns a list with appended and scaled vertex positions relative to first frame """
def append_vertex_positons(header_list, mesh_list, time_stamps, scale_min, scale_max):

    header_length = int(len(header_list)/4)
    output_list = []
    original_pos_list = []
    
    pm.currentTime(time_stamps[0])
    
    """ Original vtx positions """
    for mesh_index, mesh in enumerate(mesh_list):   
        for vtx_index, vtx in enumerate(mesh.vtx):
            pos = vtx.getPosition(space="world")
            original_pos_list.append(pos)  
    
    """ Go through every frame """
    
    first_frame = int(time_stamps[0])
    last_frame = int(time_stamps[-1])+1
    for frame in range(first_frame ,last_frame):
        global_vtx_index = 0
        pm.currentTime(frame)
        for mesh_index, mesh in enumerate(mesh_list):         
            for vtx_index, vtx in enumerate(mesh.vtx):  
            
                """ Get new position, calculate position difference and append scaled value """  
                pos = vtx.getPosition(space="world") 
                pos[0] = remap(scale_min, scale_max, 0, 255, pos[X] - original_pos_list[global_vtx_index][X])
                pos[1] = remap(scale_min, scale_max, 0, 255, pos[Y] - original_pos_list[global_vtx_index][Y])
                pos[2] = remap(scale_min, scale_max, 0, 255, pos[Z] - original_pos_list[global_vtx_index][Z])
    
                output_list.append(int(round(pos[X])))
                output_list.append(int(round(pos[Y])))
                output_list.append(int(round(pos[Z])))            
                output_list.append(255)


                global_vtx_index += 1
        
       
        padding_range = int(header_length - global_vtx_index)
        if (header_length > global_vtx_index):
            for i in range(padding_range):
                output_list.append(255)
                output_list.append(255)
                output_list.append(0)
                output_list.append(0) 
             
    return header_list + output_list


""" Returns a list with appended and scaled vertex normalz """
def append_normals(header_list, header_pos_list, mesh_list, time_stamps):
    header_length = int(len(header_list)/4)
    output_list = []
    
    """ Go through every frame """
    
    first_frame = int(time_stamps[0])
    last_frame = int(time_stamps[-1])+1
    for frame in range(first_frame ,last_frame):
        global_vtx_index = 0
        pm.currentTime(frame)
        for mesh_index, mesh in enumerate(mesh_list):         
            for vtx_index, vtx in enumerate(mesh.vtx):  
                
                """ Get vtx normal and append to next pixel """
                myNormal = vtx.getNormal('world')
                normalX = int(remap(-1, 1, 0, 65535, myNormal[X]))
                normalY = int(remap(-1, 1, 0, 65535, myNormal[Y]))
                                                                          
                """ X-Component """
                y1, y2, y3, y4 = (normalX & 0xFFFFFFFF).to_bytes(4, 'big')
                output_list.append(y3)
                output_list.append(y4)
                               
                """ Y-Component """
                y1, y2, y3, y4 = (normalY & 0xFFFFFFFF).to_bytes(4, 'big')
                output_list.append(y3)
                output_list.append(y4)

                global_vtx_index += 1
        
       
        padding_range = int(header_length - global_vtx_index)
        if (header_length > global_vtx_index):
            for i in range(padding_range):
                output_list.append(255)
                output_list.append(255)
                output_list.append(0)
                output_list.append(0) 
             
    return header_pos_list + output_list


""" Adds padding to end of list to get a power of 2 texture """
def add_padding_to_eol(buffer_list, buffer_width, buffer_height):
    output_list = []
    
    len_buffer_list = len(buffer_list)/4
    expected_len_buffer_list = buffer_width * buffer_height
    missing_buffer_len = int(expected_len_buffer_list - len_buffer_list )

    if (missing_buffer_len > 0):
        for i in range(missing_buffer_len):
            output_list.append(255)
            output_list.append(0)
            output_list.append(255)
            output_list.append(0)     
        
    return buffer_list + output_list
    
#----------------------------------------------------------------
#----------------------------------------------------------------
""" Main program """
#----------------------------------------------------------------
#----------------------------------------------------------------
def make_dat_texture():
    print("Let'sa GOOO!!")
    print()
    start_time = time.time() 
    
    print("Collecting information...")

    mesh_list = []
    if (Selected_Meshes):
        mesh_list = get_list_of_selected_meshes()
    else:
        mesh_list = get_list_of_all_meshes()
    
    keyframes = get_list_of_keyframes(mesh_list) 
    
    nr_of_vtx = len(get_list_of_vertex_positions(mesh_list))
 
    first_frame = int(keyframes[0])
    last_frame = int(keyframes[-1])
    nr_of_frames = last_frame - first_frame + 1
    
    fps = demystify(pm.currentUnit(query=True, time=True))

    """ Derive next power of 2 to get width and height of texture """
    buffer_width = get_next_power_of_2(nr_of_vtx) 
    buffer_height = get_next_power_of_2(nr_of_frames*2+1)
    

    
#-----------------------------------------------------------------------
    """ Write vertex index to every vertex of all meshes in list  """
    print("Writing vertex index to vertex colors...")
    write_vertex_index_to_vertex_color(mesh_list)
    
    
#-----------------------------------------------------------------------
    """ Get min & max position relative to first frame for normalize vertex positions with padding """
    print("Getting min and max positions for optimized scaling...")
    scale_min, scale_max = get_min_max_of_relative_positions(mesh_list, keyframes, 0.1)
    
    
#-----------------------------------------------------------------------
    """ Create Header information """
    print("Creating header...")
    header_list = create_header_list(nr_of_frames, fps, scale_min, scale_max, buffer_width)

    
#-----------------------------------------------------------------------
    """ Loops through the vertices of all meshes and store difference in pos into new array """
    print("Appending vertex-positions and normals to buffert...")
    header_vertex_pos_normals_list = append_vertex_positions_and_normals(header_list, mesh_list, keyframes, scale_min, scale_max)
    #header_vertex_pos_list = append_vertex_positons(header_list, mesh_list, keyframes, scale_min, scale_max)
   
    
#-----------------------------------------------------------------------
    """ Loops through the vertices of all meshes and store difference in pos into new array """   
    #print("Appending vertex-normals to buffert...") 
    #header_vertex_pos_normals_list = append_normals(header_list, header_vertex_pos_list, mesh_list, keyframes)
    
    
#-----------------------------------------------------------------------
    """ Add padding to end of list """
    print("Appending padding to end of buffert...")
    header_vertex_pos_padding_list = add_padding_to_eol(header_vertex_pos_normals_list, buffer_width, buffer_height)
    
    
#-----------------------------------------------------------------------



#------------------------------------------
    """ Write data to file in DDS format """
    
    
    
    print("--- Analiiiizing ---")
    print("Buffer width :", buffer_width)
    print("Buffer height:", buffer_height)
    print("no of VTXs   :", nr_of_vtx)
    print("no of frames :", nr_of_frames)
    print("fps          :", fps)
    print("Scale_min    :", scale_min)
    print("Scale_max    :", scale_max)
    print()
    print("--- List lenghts ---")
    
    header_len = len(header_list)/4
    print("Header list        :", str(header_len), "     Expected :", buffer_width)
    vtx_list = (len(header_vertex_pos_normals_list)/4) - header_len
    
    print("vertex pos list    :", str(vtx_list/2), "    Expected :", buffer_width*nr_of_frames)
    tot_len = len(header_vertex_pos_padding_list)/4
    
    print("Total with padding :", str(tot_len) , "    Expected :", buffer_width*buffer_height)
    print()
    
    
    IM_created = ImagePalette.ImagePalette(mode='RGBA', palette=header_vertex_pos_padding_list)
    IMTB = IM_created.tobytes()
    
    IMFB = Image.frombuffer("RGBA", (buffer_width, buffer_height), IMTB, decoder_name='raw')
    
    texturePath = "D:\Textures\Vats\\"
    textureName = pm.system.sceneName().split('/')[-1].split('.')[0]
    textureExtension = ".dds"
    texturePathName = texturePath + textureName + textureExtension
    
    """ Check if directory exist else create it then save the file """
    print("Saving dds...")
    if os.path.exists(texturePath):
        IMFB = IMFB.save(texturePathName)
        print("File saved to : ", texturePathName)
    else:
        os.makedirs(texturePath)
        if os.path.exists(texturePath):
            IMFB = IMFB.save(texturePathName)
            print("File saved to : ", texturePathName)
        else:
            print("dir fault")
    #-----------------------------------------------
    
    elapsedTime = time.time() - start_time
    if (elapsedTime < 1) : sec = "of a second!!"
    if (elapsedTime == 1) : sec = "second!!"
    if (elapsedTime > 1) : sec = "seconds!! CALL YOUR LOCAL OPTIMIZER - 555-345345"
    print("It'sa done!! everything took just", elapsedTime, sec)
    



